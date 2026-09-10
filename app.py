import streamlit as st
import os

# Must be the very first Streamlit command
st.set_page_config(
    page_title="GovScheme AI",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

from repositories.session_store import SessionStore
from components.sidebar import render_sidebar
from components.chat_area import render_messages
from components.composer import render_composer
from services.chat_service import ChatService

def load_css():
    """Loads custom CSS for premium styling."""
    css_path = os.path.join(os.path.dirname(__file__), "styles", "main.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def main():
    # Initialize State
    SessionStore.init_state()
    
    # Load Premium Styles
    load_css()
    
    # Render UI Components
    file_content = render_sidebar()
    
    # Render chat history
    suggestion_clicked = render_messages()
    
    # Render Composer
    user_input = render_composer()
    
    # If the user clicked a suggestion, treat it as input
    if suggestion_clicked and not user_input:
        user_input = suggestion_clicked
    
    # Handle new message
    if user_input:
        # Display user message instantly
        SessionStore.add_message("user", user_input)
        with st.chat_message("user"):
            st.markdown(user_input)
            
        # Display assistant response placeholder with streaming
        with st.chat_message("assistant"):
            region = st.session_state.get("region_preference", "Tamil Nadu (State)")
            language = st.session_state.get("language_preference", "English")
            
            try:
                # stream the response
                with st.spinner("Thinking... wait pannunga, pathutueruken.... ⏳"):
                    response_stream = ChatService.get_streaming_response(user_input, region, file_content, language)
                    full_response = st.write_stream(response_stream)
                
                # Save to history
                SessionStore.add_message("assistant", full_response)
                
            except Exception as e:
                # Graceful Error Handling
                error_msg = "I'm sorry, I encountered an error while fetching the schemes. Please try again."
                st.error(f"Error Details (Hidden in Prod): {str(e)}")
                st.markdown(error_msg)
                SessionStore.add_message("assistant", error_msg)

if __name__ == "__main__":
    main()
