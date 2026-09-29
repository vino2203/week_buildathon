import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from backend.retriever import retrieve_pipeline
from backend.generator import RTCFR_SYSTEM_PROMPT, TOT_SYSTEM_PROMPT, format_docs

from backend.language_router import normalize_query

class ChatService:
    @staticmethod
    def get_streaming_response(query: str, region_preference: str, uploaded_file_content: str = None, language: str = "English"):
        """
        Streams the response back to Streamlit using the RAG pipeline.
        """
        # 1. Normalize the Query
        try:
            norm_result = normalize_query(query)
            search_query = norm_result.normalized_query_english
        except Exception as e:
            search_query = query # Fallback if normalization fails
            
        # Map UI selection to pipeline category
        category_map = {
            "Tamil Nadu (State)": "tn",
            "Central Government": "central",
            "Both (State & Central)": "both"
        }
        category = category_map.get(region_preference, "tn")
        
        # 2. Retrieve Documents
        if category == "both":
            docs_tn = retrieve_pipeline(search_query, "tn")
            docs_central = retrieve_pipeline(search_query, "central")
            context_docs = docs_tn[:2] + docs_central[:2]
            system_prompt = TOT_SYSTEM_PROMPT
        else:
            context_docs = retrieve_pipeline(search_query, category)
            system_prompt = RTCFR_SYSTEM_PROMPT
            
        # Inject Language Preference
        system_prompt += f"\n\nCRITICAL REQUIREMENT: You MUST formulate your final answer entirely in {language}."
            
        context_str = format_docs(context_docs)
        
        # Inject file content if provided
        if uploaded_file_content:
            context_str += f"\n\n[USER UPLOADED FILE CONTENT]:\n{uploaded_file_content}"
        
        # 2. Setup Streaming LLM
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2, streaming=True)
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{question}")
        ])
        
        chain = prompt | llm
        
        # Yield chunks for st.write_stream
        for chunk in chain.stream({"context": context_str, "question": query}):
            yield chunk.content
