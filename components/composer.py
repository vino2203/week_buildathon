import streamlit as st
import PyPDF2

def process_uploaded_file(uploaded_file):
    """Simple helper to extract text from a few common file types."""
    if not uploaded_file:
        return None
        
    try:
        text = ""
        if uploaded_file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        elif uploaded_file.name.endswith('.txt'):
            text = uploaded_file.getvalue().decode("utf-8")
        else:
            return f"Unsupported file type. Please upload PDF or TXT."
        return text
    except Exception as e:
        return f"Error reading file: {str(e)}"

def render_composer():
    """Renders the chat input and file uploader."""
    
    # We use a container fixed at the bottom
    # However, st.chat_input is naturally anchored to the bottom.
    
    prompt = st.chat_input("Ask about government schemes...")
    
    return prompt
