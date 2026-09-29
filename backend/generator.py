import os
from typing import List
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from backend.retriever import retrieve_pipeline

# Load environment variables
load_dotenv()

# ==========================================
# PROMPTS
# ==========================================

RTCFR_SYSTEM_PROMPT = """You are an expert government scheme advisor for citizens. (Role)
Your task is to answer the user's query about government schemes accurately and helpfully based on the retrieved context. (Task)
Use the following retrieved documents to formulate your answer:
{context} (Context)
Provide a clear, step-by-step response. Use bullet points for eligibility and benefits. (Format)
CRITICAL RESTRICTION: Do not hallucinate under any circumstances. If the answer is not explicitly stated in the context above, you MUST state that you cannot find information about this in the scheme documents. Do NOT make up an answer. Translate this refusal into the requested output language. Do not mention the context directly to the user. (Restriction)"""

TOT_SYSTEM_PROMPT = """You are an expert policy advisor. The user is asking about schemes across both State (Tamil Nadu) and Central governments. 
Please solve this step-by-step using a Tree of Thoughts process based ONLY on the provided context:

Context:
{context}

Process:
1. Brainstorming: Identify the potential state schemes and central schemes from the context that apply to the query.
2. Evaluation: Evaluate how these schemes overlap, differ, or complement each other regarding the user's query.
3. Synthesis: Combine the best options into a single, cohesive, comparative recommendation.
4. Final Output: Present the synthesized answer clearly to the user, breaking down the State vs. Central benefits.

CRITICAL RESTRICTION: Do not hallucinate under any circumstances. If the provided context does not contain relevant information for State or Central schemes regarding the query, you MUST state that you cannot find information about this in the scheme documents. Do NOT make up an answer. Translate this refusal into the requested output language. Do NOT use your internal knowledge.

Format your final response clearly with headings for the State and Central schemes."""

# ==========================================
# GENERATION LOGIC
# ==========================================

def format_docs(docs: List[Document]) -> str:
    return "\n\n".join(f"Source: {doc.metadata.get('source', 'Unknown')}\n{doc.page_content}" for doc in docs)

def generate_answer(query: str, category: str = "tn"):
    """
    Pipeline 3: Retrieves documents and generates an answer using RTCFR or ToT frameworks.
    """
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    
    # 1. Retrieve Documents
    print(f"\n--- Retrieving documents for category: '{category}' ---")
    if category == "both":
        docs_tn = retrieve_pipeline(query, "tn")
        docs_central = retrieve_pipeline(query, "central")
        # Combine top results (Top 2 from each to keep context size manageable)
        context_docs = docs_tn[:2] + docs_central[:2]
        system_prompt = TOT_SYSTEM_PROMPT
        print("-> Using ToT (Tree of Thoughts) Framework")
    else:
        context_docs = retrieve_pipeline(query, category)
        system_prompt = RTCFR_SYSTEM_PROMPT
        print("-> Using RTCFR (Role-Task-Context-Format-Restriction) Framework")
        
    context_str = format_docs(context_docs)
    
    # 2. Generate
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{question}")
    ])
    
    chain = prompt | llm
    
    print("\n--- Generating Answer ---")
    response = chain.invoke({"context": context_str, "question": query})
    
    return response.content

if __name__ == "__main__":
    test_query = "What are the subsidies for solar pumps?"
    
    print("========================================")
    print("TEST 1: Single Category (RTCFR Prompt)")
    print("========================================")
    answer_single = generate_answer(test_query, category="tn")
    print("\n=== FINAL ANSWER (Single) ===")
    print(answer_single)
    print("\n")
    
    print("========================================")
    print("TEST 2: Both Categories (ToT Prompt)")
    print("========================================")
    answer_both = generate_answer(test_query, category="both")
    print("\n=== FINAL ANSWER (Both) ===")
    print(answer_both)
