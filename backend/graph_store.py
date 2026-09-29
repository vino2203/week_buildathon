import os
import re
from typing import List
from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain_core.documents import Document

from backend.config import TN_SCHEMES_DIR

load_dotenv()

# Keyword -> Topic used to link related schemes together
TOPIC_KEYWORDS = {
    "Solar": ["solar"],
    "Irrigation": ["irrigation", "pump", "drip", "sprinkler", "water harvesting", "desilting"],
    "Seeds": ["seed", "rhizobium", "gypsum", "minikit"],
    "Horticulture": ["horticulture", "palmyrah", "oil palm"],
    "Mechanization": ["mechanization", "mechanisation", "equipment", "generator"],
    "Training": ["training", "skill", "demonstration"],
    "MSME": ["msme", "micro", "enterprise", "industrial estate", "stamp duty", "tansidco", "sipcot"],
    "Finance": ["term loan", "credit", "subsidy on", "capital subsidy", "tariff"],
}


def get_driver():
    """Returns a Neo4j driver, or None if credentials are not configured."""
    uri, user, password = (os.getenv(k) for k in ("NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD"))
    if not (uri and user and password):
        return None
    return GraphDatabase.driver(uri, auth=(user, password))


def _session(driver):
    return driver.session(database=os.getenv("NEO4J_DATABASE") or None)


def _field(text: str, label: str) -> str:
    match = re.search(rf"{label}:\s*(.+)", text, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _topics(name: str, text: str) -> List[str]:
    haystack = f"{name} {text[:1500]}".lower()
    return [t for t, words in TOPIC_KEYWORDS.items() if any(w in haystack for w in words)]


def build_graph(directory: str = TN_SCHEMES_DIR):
    """
    Loads Tamil Nadu scheme files into Neo4j as:
    (Scheme)-[:IN_REGION]->(Region), (Scheme)-[:HAS_TOPIC]->(Topic),
    (Scheme)-[:FOR_BENEFICIARY]->(Beneficiary), (Scheme)-[:OFFERS]->(BenefitType)
    """
    driver = get_driver()
    if driver is None:
        raise RuntimeError("NEO4J_URI / NEO4J_USERNAME / NEO4J_PASSWORD are not set in .env")

    with driver, _session(driver) as session:
        session.run("CREATE CONSTRAINT scheme_name IF NOT EXISTS FOR (s:Scheme) REQUIRE s.name IS UNIQUE")
        session.run("MERGE (:Region {name: 'Tamil Nadu'})")

        count = 0
        for filename in sorted(os.listdir(directory)):
            if not filename.endswith(".txt"):
                continue
            with open(os.path.join(directory, filename), encoding="utf-8") as f:
                text = f.read()
            name = filename[:-4]
            session.run(
                """
                MERGE (s:Scheme {name: $name})
                SET s.source = $source, s.funding = $funding
                WITH s
                MATCH (r:Region {name: 'Tamil Nadu'})
                MERGE (s)-[:IN_REGION]->(r)
                """,
                name=name, source=os.path.join(directory, filename),
                funding=_field(text, "Funding Pattern"),
            )
            for topic in _topics(name, text):
                session.run(
                    "MATCH (s:Scheme {name: $n}) MERGE (t:Topic {name: $t}) MERGE (s)-[:HAS_TOPIC]->(t)",
                    n=name, t=topic)
            for label, node, rel in (("Beneficiaries", "Beneficiary", "FOR_BENEFICIARY"),
                                     ("Types of Benefits", "BenefitType", "OFFERS")):
                value = _field(text, label)
                if value:
                    session.run(
                        f"MATCH (s:Scheme {{name: $n}}) MERGE (x:{node} {{name: $v}}) MERGE (s)-[:{rel}]->(x)",
                        n=name, v=value)
            count += 1
    print(f"Loaded {count} schemes into Neo4j.")
    return count


def related_schemes(docs: List[Document], limit: int = 5) -> List[str]:
    """
    Given retrieved documents, returns names of other schemes that share a Topic
    with them. Returns [] if Neo4j is unavailable so retrieval never breaks.
    """
    names = [os.path.splitext(os.path.basename(d.metadata.get("source", "")))[0] for d in docs]
    names = [n for n in names if n]
    driver = get_driver()
    if not names or driver is None:
        return []
    try:
        with driver, _session(driver) as session:
            result = session.run(
                """
                MATCH (s:Scheme)-[:HAS_TOPIC]->(t:Topic)<-[:HAS_TOPIC]-(o:Scheme)
                WHERE s.name IN $names AND NOT o.name IN $names
                RETURN o.name AS name, o.funding AS funding, count(t) AS shared
                ORDER BY shared DESC, name LIMIT $limit
                """,
                names=names, limit=limit)
            return [f"{r['name']}" + (f" (Funding: {r['funding']})" if r["funding"] else "") for r in result]
    except Exception as e:
        print(f"[Neo4j] Graph lookup skipped: {e}")
        return []


if __name__ == "__main__":
    build_graph()
