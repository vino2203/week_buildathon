import streamlit as st
from frontend.repositories.session_store import SessionStore

def render_welcome_screen():
    """Displays a premium empty state when there are no messages."""
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center; color: var(--accent-color);'>🏛️ GovScheme AI</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: var(--text-secondary);'>Your intelligent assistant for State and Central government schemes. Ask me anything to get started.</p>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # We can add suggested prompts back or just leave it empty.
        pass
            
    return None

def render_messages():
    """Renders the chat history."""
    messages = SessionStore.get_active_messages()
    
    if not messages:
        return render_welcome_screen()
        
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    return None
