import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")

TN_SCHEMES_DIR = os.path.join(DATA_DIR, "Tamil_nadu_state_schemes")
CENTRAL_SCHEMES_DIR = os.path.join(DATA_DIR, "Central_goverment_schemes")
CENTRAL_PDF_PATH = os.path.join(CENTRAL_SCHEMES_DIR, "SCHEMES.pdf")
CENTRAL_TEXT_PATH = os.path.join(CENTRAL_SCHEMES_DIR, "SCHEMES_extracted.txt")

FAISS_INDEX_TN = os.path.join(DATA_DIR, "faiss_index_tn")
FAISS_INDEX_CENTRAL = os.path.join(DATA_DIR, "faiss_index_central")
