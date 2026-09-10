import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.documents import Document

def load_tamil_nadu_schemes(directory_path: str = "Tamil_nadu_state_schemes"):
    """
    Loads all text files from the Tamil Nadu schemes directory.
    Adds metadata indicating the source category.
    """
    print(f"Loading Tamil Nadu schemes from {directory_path}...")
    loader = DirectoryLoader(
        directory_path,
        glob="**/*.txt",
        loader_cls=TextLoader,
        show_progress=True
    )
    documents = loader.load()
    
    # Inject metadata for routing
    for doc in documents:
        doc.metadata["category"] = "state_tn"
        doc.metadata["state"] = "Tamil Nadu"
        
    print(f"Loaded {len(documents)} Tamil Nadu scheme documents.\n")
    return documents

def load_central_schemes(file_path: str = "Central_goverment_schemes/SCHEMES_extracted.txt"):
    """
    Loads the extracted text file containing Central Government schemes.
    Adds metadata indicating the source category.
    """
    print(f"Loading Central Government schemes from {file_path}...")
    loader = TextLoader(file_path)
    documents = loader.load()
    
    # Inject metadata for routing
    for doc in documents:
        doc.metadata["category"] = "central"
        
    print(f"Loaded {len(documents)} Central scheme document (Raw File).\n")
    return documents

def get_all_scheme_documents():
    """
    Loads both Tamil Nadu and Central scheme documents and combines them.
    """
    tn_docs = load_tamil_nadu_schemes()
    central_docs = load_central_schemes()
    
    combined_docs = tn_docs + central_docs
    print(f"Total documents loaded: {len(combined_docs)}")
    return combined_docs

if __name__ == "__main__":
    # Test the ingestion logic
    docs = get_all_scheme_documents()
    
    # Print sample metadata and snippet from the first TN doc and the Central doc
    if docs:
        print("\n--- Sample Document 1 (Tamil Nadu) ---")
        print("Metadata:", docs[0].metadata)
        print("Snippet:", docs[0].page_content[:200].replace('\n', ' '))
        
        # The central document should be the very last one in the list
        central_doc = docs[-1]
        print("\n--- Sample Document (Central) ---")
        print("Metadata:", central_doc.metadata)
        print("Snippet:", central_doc.page_content[:200].replace('\n', ' '))
