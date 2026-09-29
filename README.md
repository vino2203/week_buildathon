# AI-Powered Agricultural Schemes & Subsidy Assistant (Tamil Nadu & Central Government)

An intelligent multilingual conversational RAG assistant that streamlines discovery of agricultural welfare schemes and subsidies for farmers, FPOs, and rural stakeholders across Tamil Nadu State and Central Government jurisdictions.

---

## 🌟 Key Features

- **Jurisdiction-Based Routing**: Filter schemes specifically for:
  - Tamil Nadu State Schemes
  - Central Government Schemes
  - Combined (Both jurisdictions)
- **Multilingual Support**: Interactive support in English and Tamil (தமிழ்), including localized responses and Tamil language understanding.
- **Hybrid Retrieval (RAG)**: Combines dense vector search (**FAISS**) with lexical keyword search (**BM25**) for accurate scheme matching.
- **Document & Subsidy Analysis**: Provides eligibility criteria, subsidy amounts, required verification documents, and application steps.
- **Document / PDF Context Upload**: Upload land records, certificates, or farmer documents to verify eligibility against government guidelines.
- **Modern Streamlit UI**: Intuitive, responsive chat interface with preset quick prompts and streaming responses.

---

## 🏗️ Architecture

```
User Query / Document
       │
       ▼
Language & Jurisdiction Router
       │
  ┌────┴─────────────────────────┐
  ▼                              ▼
Central Gov Index          Tamil Nadu State Index
(FAISS + BM25)             (FAISS + BM25)
  └────┬─────────────────────────┘
       ▼
Hybrid Retriever (Reciprocal Rank Fusion)
       │
       ▼
LLM Generator (GPT-4o / LangChain)
       │
       ▼
Streaming Multilingual Response (Tamil / English)
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- OpenAI API Key

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/vino2203/week_buildathon.git
   cd week_buildathon
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   LANGCHAIN_API_KEY=your_langchain_api_key_here
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_PROJECT=scheme-rag
   ```

### Running the Application

Launch the Streamlit app:
```bash
streamlit run frontend/app.py
```

---

## 📁 Repository Structure

```
├── backend/                    # Retrieval, generation and data pipeline
│   ├── config.py               # Shared paths (data, FAISS indexes)
│   ├── retriever.py            # Hybrid FAISS + BM25 retriever
│   ├── generator.py            # LLM response generation and prompt chains
│   ├── language_router.py      # Multilingual and jurisdictional routing logic
│   ├── embeddings.py           # Vector store creation and indexing
│   ├── chunking.py             # Document chunking strategies
│   ├── data_ingestion.py       # Text and PDF ingestion pipeline
│   ├── services/               # Chat service orchestration
│   └── scripts/                # Scrapers and PDF conversion (run as modules)
├── frontend/                   # Streamlit UI
│   ├── app.py                  # Application entry point
│   ├── components/             # Chat, sidebar, composer
│   ├── repositories/           # Session and state management
│   └── styles/                 # CSS
├── tests/                      # pytest suite
├── data/                       # Scheme documents and FAISS indexes
├── BRD.txt                     # Business Requirements Document
└── requirements.txt            # Python package dependencies
```
