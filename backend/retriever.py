import os
from backend.config import DATA_DIR
from backend.graph_store import graph_retrieve
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

class DocumentGrade(BaseModel):
    """Binary score for relevance check."""
    binary_score: str = Field(description="Documents are relevant to the question, 'yes' or 'no'")

class DocumentRank(BaseModel):
    """Score for re-ranking documents."""
    relevance_score: int = Field(description="Score from 1 to 5 indicating how relevant the document is to the question. 5 is highly relevant.")

def get_hybrid_retriever(category: str):
    """
    Builds a Hybrid Retriever (FAISS + BM25) for either 'tn' or 'central'.
    """
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    # Load the correct FAISS index based on category
    faiss_path = os.path.join(DATA_DIR, f"faiss_index_{category}")
    print(f"Loading FAISS index from {faiss_path}...")
    vectorstore = FAISS.load_local(faiss_path, embeddings, allow_dangerous_deserialization=True)
    
    # Extract documents from FAISS docstore to build BM25
    docs = list(vectorstore.docstore._dict.values())
    
    # Initialize Retrievers
    faiss_retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    bm25_retriever = BM25Retriever.from_documents(docs)
    bm25_retriever.k = 5
    
    return bm25_retriever, faiss_retriever

def hybrid_retrieve(query: str, bm25_retriever, faiss_retriever) -> List[Document]:
    """Retrieve from both and combine using Reciprocal Rank Fusion (RRF)."""
    docs_bm25 = bm25_retriever.invoke(query)
    docs_faiss = faiss_retriever.invoke(query)
    
    rrf_scores = {}
    doc_map = {}
    
    # K parameter for RRF
    k_param = 60
    
    for rank, doc in enumerate(docs_bm25):
        key = doc.page_content
        rrf_scores[key] = rrf_scores.get(key, 0) + 1 / (rank + k_param)
        doc_map[key] = doc
        
    for rank, doc in enumerate(docs_faiss):
        key = doc.page_content
        rrf_scores[key] = rrf_scores.get(key, 0) + 1 / (rank + k_param)
        doc_map[key] = doc
        
    # Sort by RRF score
    sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Return top 5
    return [doc_map[k] for k, v in sorted_docs[:5]]


def self_rag_grade(query: str, docs: List[Document]) -> List[Document]:
    """
    Self-RAG Step: Grades the retrieved documents and filters out irrelevant ones.
    """
    print(f"\n[Self-RAG] Grading {len(docs)} documents...")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm_grader = llm.with_structured_output(DocumentGrade)
    
    system = """You are a grader assessing relevance of a retrieved document to a user question. \n 
    If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n
    It does not need to be a stringent test. The goal is to filter out erroneous retrievals. \n
    Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""
    
    grade_prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", "Retrieved document: \n\n {document} \n\n User question: {question}")
    ])
    
    retrieval_grader = grade_prompt | structured_llm_grader
    
    filtered_docs = []
    for d in docs:
        score = retrieval_grader.invoke({"question": query, "document": d.page_content})
        grade = score.binary_score
        if grade == "yes":
            filtered_docs.append(d)
            
    print(f"[Self-RAG] Survived grading: {len(filtered_docs)}/{len(docs)} documents.")
    return filtered_docs

def rerank_documents(query: str, docs: List[Document], top_k: int = 3) -> List[Document]:
    """
    Re-Rank Step: Scores the surviving documents from 1-5 and sorts them.
    """
    if not docs:
        return []
        
    print(f"[Re-Rank] Scoring and sorting {len(docs)} documents...")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm_ranker = llm.with_structured_output(DocumentRank)
    
    system = """You are a relevance ranker. Score the document from 1 to 5 based on how well it answers the user's question. 5 is a perfect match."""
    
    rank_prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", "Retrieved document: \n\n {document} \n\n User question: {question}")
    ])
    
    ranker = rank_prompt | structured_llm_ranker
    
    scored_docs = []
    for d in docs:
        result = ranker.invoke({"question": query, "document": d.page_content})
        scored_docs.append((result.relevance_score, d))
    
    # Sort by score descending
    scored_docs.sort(key=lambda x: x[0], reverse=True)
    
    # Return Top K
    ranked_docs = [doc for score, doc in scored_docs[:top_k]]
    print(f"[Re-Rank] Returning top {len(ranked_docs)} documents.")
    return ranked_docs

def bm25_rank(query: str, docs: List[Document], k: int = 8) -> List[Document]:
    """BM25 ordering over a candidate pool (used to merge Aura and FAISS results)."""
    if not docs:
        return []
    bm25 = BM25Retriever.from_documents(docs)
    bm25.k = min(k, len(docs))
    return bm25.invoke(query)


def retrieve_pipeline(query: str, category: str = "tn"):
    """
    Retrieval Pipeline:
      Branch A (Aura/Neo4j): graph full-text retrieval -> Self-RAG grading
      Branch B (FAISS):      FAISS + BM25 hybrid retrieval -> Re-Ranking
      Final:                 merge A + B -> BM25 -> Re-Ranking
    """
    print(f"--- Starting Pipeline for query: '{query}' ---")

    # Branch A: Aura + Self-RAG
    aura_docs = graph_retrieve(query, category)
    print(f"[Aura] Retrieved {len(aura_docs)} documents.")
    aura_docs = self_rag_grade(query, aura_docs) if aura_docs else []

    # Branch B: FAISS + BM25 -> Re-Rank
    bm25_retriever, faiss_retriever = get_hybrid_retriever(category)
    faiss_docs = rerank_documents(query, hybrid_retrieve(query, bm25_retriever, faiss_retriever), top_k=5)

    # Final: merge, dedupe, BM25 + Re-Rank
    merged, seen = [], set()
    for d in aura_docs + faiss_docs:
        key = d.page_content.strip()
        if key not in seen:
            seen.add(key)
            merged.append(d)
    print(f"[Final] Merged pool: {len(merged)} documents (Aura {len(aura_docs)}, FAISS {len(faiss_docs)}).")
    return rerank_documents(query, bm25_rank(query, merged), top_k=3)

if __name__ == "__main__":
    # Test the retriever pipeline
    test_query = "What are the subsidies for solar pumps?"
    
    final_results = retrieve_pipeline(test_query, category="tn")
    
    print("\n--- Final Top Results ---")
    for i, doc in enumerate(final_results, 1):
        print(f"\nResult {i}:")
        print(f"Source: {doc.metadata.get('source', 'Unknown')}")
        print(f"Snippet: {doc.page_content[:200].replace(chr(10), ' ')}")
