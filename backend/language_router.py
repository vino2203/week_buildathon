import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

class QueryNormalization(BaseModel):
    """Schema for extracting language and normalized queries."""
    detected_language: str = Field(
        description="The detected language of the input: 'English', 'Tamil', 'Tanglish', or 'Mixed'"
    )
    normalized_query_english: str = Field(
        description="The normalized meaning of the query strictly translated into clear English."
    )
    normalized_query_tamil: str = Field(
        description="The normalized meaning of the query strictly translated into clear Tamil script."
    )

def get_query_normalizer_chain():
    """Builds and returns the LangChain router chain for query normalization."""
    # 1. Initialize the LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # 2. Attach the structured output schema
    structured_llm = llm.with_structured_output(QueryNormalization)
    
    # 3. Define the prompt using the user's exact requirements
    system_prompt = """You are a query normalization and language detection engine
for an agriculture government scheme assistant.

The user may write in:
- English
- Tamil
- Tanglish
- Mixed Tamil + English
- Spelling variations
- Phonetic Tamil written using English characters

Examples:

"1 acrekku aevolavu moottai nel kidaikkum"
→ "1 ஏக்கருக்கு எவ்வளவு மூட்டை நெல் கிடைக்கும்?"
→ "How many bags of paddy can be obtained from one acre?"

"vivasaayigalukku enna scheme irukku"
→ "விவசாயிகளுக்கு என்ன திட்டம் இருக்கு?"
→ "What schemes are available for farmers?"

"pm kisan ku epdi apply panradhu"
→ "PM-KISANக்கு எப்படி apply செய்வது?"
→ "How to apply for PM-KISAN?"

"nelku enna subsidy irukku"
→ "நெல்லுக்கு என்ன subsidy இருக்கு?"
→ "What subsidy is available for paddy?"

Do NOT reject a query merely because it is Tanglish.

Return the normalized meaning of the query."""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{query}")
    ])
    
    # 4. Chain them together
    chain = prompt | structured_llm
    
    return chain

def normalize_query(query: str) -> QueryNormalization:
    """
    Detects language and normalizes the query into English and Tamil.
    """
    chain = get_query_normalizer_chain()
    result = chain.invoke({"query": query})
    return result

if __name__ == "__main__":
    # Test cases
    test_queries = [
        "What are the central government schemes for farmers?", 
        "விவசாயிகளுக்கான திட்டங்கள் என்ன?",                   
        "vivasaayigalukkana schemes enna?",                    
        "How to apply for PM Kisan scheme?"                    
    ]
    
    print("Testing Query Normalizer...")
    for q in test_queries:
        res = normalize_query(q)
        print(f"Query: '{q}'\nDetected: {res.detected_language}\nEnglish: {res.normalized_query_english}\nTamil: {res.normalized_query_tamil}\n")
