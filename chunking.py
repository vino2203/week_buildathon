import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from data_ingestion import get_all_scheme_documents

def chunk_documents(chunk_size: int = 1000, chunk_overlap: int = 200):
    """
    Loads all documents and splits them into smaller chunks using 
    RecursiveCharacterTextSplitter.
    """
    print(f"Initializing RecursiveCharacterTextSplitter (size={chunk_size}, overlap={chunk_overlap})...")
    
    # 1. Load the raw documents
    raw_docs = get_all_scheme_documents()
    
    # 2. Configure the text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )
    
    # 3. Split the documents
    print("Splitting documents into chunks...")
    chunked_docs = text_splitter.split_documents(raw_docs)
    
    print(f"Successfully split {len(raw_docs)} raw documents into {len(chunked_docs)} chunks.\n")
    return chunked_docs

if __name__ == "__main__":
    # Test the chunking logic
    chunks = chunk_documents()
    
    # Inspect a few chunks to verify size and metadata
    if chunks:
        print("--- Sample Chunk 1 (State TN) ---")
        print("Metadata:", chunks[0].metadata)
        print(f"Length: {len(chunks[0].page_content)} characters")
        print("Snippet:", chunks[0].page_content[:200].replace('\n', ' '))
        
        print("\n--- Sample Chunk (Central) ---")
        central_chunks = [c for c in chunks if c.metadata.get("category") == "central"]
        if central_chunks:
            print("Metadata:", central_chunks[0].metadata)
            print(f"Length: {len(central_chunks[0].page_content)} characters")
            print("Snippet:", central_chunks[0].page_content[:200].replace('\n', ' '))
