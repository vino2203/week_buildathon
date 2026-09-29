import streamlit as st
from frontend.repositories.session_store import SessionStore
from datetime import datetime, timedelta

def render_sidebar():
    with st.sidebar:
        st.markdown("### 🏛️ GovScheme AI")
        
        # New Chat Button
        if st.button("➕ New Chat", use_container_width=True, type="primary"):
            SessionStore.create_chat()
            st.rerun()
            
        st.divider()
        
        # Settings
        st.markdown("#### Settings")
        
        # We integrate the region selection into the sidebar settings
        if "region_preference" not in st.session_state:
            st.session_state.region_preference = "Both (State & Central)"
            
        st.session_state.region_preference = st.radio(
            "Select Scheme Region",
            ["Tamil Nadu (State)", "Central Government", "Both (State & Central)"],
            index=["Tamil Nadu (State)", "Central Government", "Both (State & Central)"].index(st.session_state.region_preference)
        )
        
        st.divider()
        
        # Language Preference
        st.markdown("#### Language")
        if "language_preference" not in st.session_state:
            st.session_state.language_preference = "English"
            
        st.session_state.language_preference = st.radio(
            "Select Language",
            ["English", "Tamil", "Tanglish"],
            index=["English", "Tamil", "Tanglish"].index(st.session_state.language_preference)
        )
        
        st.divider()
        
        # Document Upload
        st.markdown("#### Document Upload")
        uploaded_file = st.file_uploader("Upload PDF or TXT", type=['pdf', 'txt'], label_visibility="collapsed")
        
        file_content = None
        if uploaded_file:
            # We import here to avoid circular imports if any, but better to import PyPDF2 at top.
            # I will just write a simple extractor here or import from composer.
            from components.composer import process_uploaded_file
            file_content = process_uploaded_file(uploaded_file)
            if file_content and not file_content.startswith("Error"):
                st.success(f"Attached: {uploaded_file.name}")
            else:
                st.error(file_content)
                file_content = None
                
        st.divider()
        
        # Conversation History
        st.markdown("#### History")
        chats = SessionStore.get_all_chats()
        
        if not chats:
            st.caption("No past conversations.")
        else:
            for chat in chats:
                # Highlight active chat
                is_active = (chat["id"] == st.session_state.active_chat_id)
                btn_label = f"{'🟢 ' if is_active else '📄 '}{chat['title']}"
                
                col1, col2 = st.columns([0.85, 0.15])
                with col1:
                    if st.button(btn_label, key=f"btn_{chat['id']}", use_container_width=True):
                        SessionStore.set_active_chat(chat["id"])
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"del_{chat['id']}", help="Delete chat"):
                        SessionStore.delete_chat(chat["id"])
                        st.rerun()
                        
    return file_content
