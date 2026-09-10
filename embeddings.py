import os
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from chunking import chunk_documents
from dotenv import load_dotenv

# Load environment variables (OPENAI_API_KEY)
load_dotenv()

def create_and_save_vector_stores(save_path_tn: str = "faiss_index_tn", save_path_central: str = "faiss_index_central"):
    """
    Generates embeddings for all chunked documents and saves them to separate local FAISS indices.
    """
    print("Step 1: Generating chunks...")
    chunks = chunk_documents()
    
    # Split chunks by category
    tn_chunks = [c for c in chunks if c.metadata.get("category") == "state_tn"]
    central_chunks = [c for c in chunks if c.metadata.get("category") == "central"]
    
    print("\nStep 2: Initializing OpenAI Embeddings (text-embedding-3-small)...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    print(f"Step 3: Creating FAISS Vector Store for {len(tn_chunks)} TN chunks...")
    vector_store_tn = FAISS.from_documents(tn_chunks, embeddings)
    vector_store_tn.save_local(save_path_tn)
    print(f"Saved TN FAISS index locally to '{save_path_tn}'.")
    
    print(f"\nStep 4: Creating FAISS Vector Store for {len(central_chunks)} Central chunks...")
    vector_store_central = FAISS.from_documents(central_chunks, embeddings)
    vector_store_central.save_local(save_path_central)
    print(f"Saved Central FAISS index locally to '{save_path_central}'.")
    
    print("\nBoth Vector Stores successfully created and saved!\n")
    return vector_store_tn, vector_store_central

if __name__ == "__main__":
    create_and_save_vector_stores()
