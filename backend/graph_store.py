import os
import re
from typing import List
from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain_core.documents import Document

from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.config import TN_SCHEMES_DIR, CENTRAL_TEXT_PATH

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


def ensure_indexes(session):
    session.run("CREATE FULLTEXT INDEX scheme_text IF NOT EXISTS FOR (s:Scheme) ON EACH [s.name, s.text]")
    session.run("CREATE FULLTEXT INDEX chunk_text IF NOT EXISTS FOR (c:Chunk) ON EACH [c.text]")


STOPWORDS = {"what", "is", "are", "the", "a", "an", "of", "for", "to", "in", "on", "and", "or", "how", "can",
             "i", "me", "my", "do", "does", "any", "available", "which", "who", "get", "under", "with", "about"}


def _lucene_escape(query: str) -> str:
    """Strips Lucene special characters and stopwords so full-text search focuses on content words."""
    words = re.sub(r'[+\-&|!(){}\[\]^"~*?:\\/]', " ", query).split()
    return " ".join(w for w in words if w.lower() not in STOPWORDS)


def graph_retrieve(query: str, category: str = "tn", k: int = 4) -> List[Document]:
    """
    Retrieves scheme text / chunks from Neo4j (Aura) via full-text search.
    category: 'tn' or 'central'. Returns [] if Neo4j is unavailable.
    """
    cat = {"tn": "state_tn", "central": "central"}.get(category, category)
    driver = get_driver()
    q = _lucene_escape(query).strip()
    if driver is None or not q:
        return []
    try:
        with driver, _session(driver) as session:
            rows = session.run(
                """
                CALL () {
                  CALL db.index.fulltext.queryNodes('scheme_text', $q) YIELD node, score
                  WHERE node.category = $cat AND node.text IS NOT NULL
                  RETURN node.name AS name, node.source AS source, substring(node.text, 0, 3000) AS text, score
                  UNION
                  CALL db.index.fulltext.queryNodes('chunk_text', $q) YIELD node, score
                  MATCH (node)-[:PART_OF]->(s:Scheme) WHERE s.category = $cat
                  RETURN s.name AS name, s.source AS source, node.text AS text, score
                }
                RETURN name, source, text, score ORDER BY score DESC LIMIT $k
                """, q=q, cat=cat, k=k)
            return [Document(page_content=r["text"],
                             metadata={"source": r["source"], "name": r["name"],
                                       "retriever": "neo4j", "score": r["score"]})
                    for r in rows]
    except Exception as e:
        print(f"[Neo4j] Graph retrieval skipped: {e}")
        return []


def build_graph(directory: str = TN_SCHEMES_DIR):
    """
    Uploads every scheme document (full text) into Neo4j, one by one, as:
    (Scheme)-[:IN_REGION]->(Region), (Scheme)-[:HAS_TOPIC]->(Topic),
    (Scheme)-[:FOR_BENEFICIARY]->(Beneficiary), (Scheme)-[:OFFERS]->(BenefitType)
    """
    driver = get_driver()
    if driver is None:
        raise RuntimeError("NEO4J_URI / NEO4J_USERNAME / NEO4J_PASSWORD are not set in .env")

    with driver, _session(driver) as session:
        session.run("CREATE CONSTRAINT scheme_name IF NOT EXISTS FOR (s:Scheme) REQUIRE s.name IS UNIQUE")
        ensure_indexes(session)
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
                SET s.source = $source, s.funding = $funding, s.text = $text, s.category = 'state_tn'
                WITH s
                MATCH (r:Region {name: 'Tamil Nadu'})
                MERGE (s)-[:IN_REGION]->(r)
                """,
                name=name, source=os.path.join(directory, filename),
                funding=_field(text, "Funding Pattern"), text=text,
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
            print(f"[{count}] Uploaded: {name}")

        _load_central(session)
    print(f"Loaded {count} Tamil Nadu schemes + Central schemes document into Neo4j.")
    return count


def _load_central(session, path: str = CENTRAL_TEXT_PATH, chunk_size: int = 4000):
    """Uploads the Central schemes file as one Scheme node with its text split into linked Chunk nodes."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    name = os.path.splitext(os.path.basename(path))[0]
    session.run("MERGE (:Region {name: 'Central Government'})")
    session.run(
        """
        MERGE (s:Scheme {name: $name})
        SET s.source = $source, s.category = 'central'
        WITH s
        MATCH (r:Region {name: 'Central Government'})
        MERGE (s)-[:IN_REGION]->(r)
        """, name=name, source=path)
    chunks = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=200).split_text(text)
    for i, chunk in enumerate(chunks):
        session.run(
            """
            MATCH (s:Scheme {name: $name})
            MERGE (c:Chunk {id: $id})
            SET c.index = $i, c.text = $text
            MERGE (c)-[:PART_OF]->(s)
            """, name=name, id=f"{name}-{i}", i=i, text=chunk)
        print(f"[central] Uploaded chunk {i + 1}/{len(chunks)}")


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
