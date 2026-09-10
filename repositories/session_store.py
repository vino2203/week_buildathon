import streamlit as st
import uuid
from datetime import datetime

class SessionStore:
    """
    Manages chat history and UI state in Streamlit's session_state.
    Designed so it can be swapped out with a database later.
    """
    @staticmethod
    def init_state():
        if "conversations" not in st.session_state:
            # Structure: { conv_id: {"title": str, "messages": list, "updated_at": datetime} }
            st.session_state.conversations = {}
        if "active_chat_id" not in st.session_state:
            st.session_state.active_chat_id = None
        if "theme" not in st.session_state:
            st.session_state.theme = "light"

    @staticmethod
    def create_chat() -> str:
        chat_id = str(uuid.uuid4())
        st.session_state.conversations[chat_id] = {
            "title": "New Conversation",
            "messages": [],
            "updated_at": datetime.now()
        }
        st.session_state.active_chat_id = chat_id
        return chat_id

    @staticmethod
    def get_active_messages():
        if not st.session_state.active_chat_id:
            return []
        return st.session_state.conversations[st.session_state.active_chat_id]["messages"]

    @staticmethod
    def add_message(role: str, content: str):
        if not st.session_state.active_chat_id:
            SessionStore.create_chat()
            
        chat_id = st.session_state.active_chat_id
        
        # If this is the first user message, rename the title automatically
        if len(st.session_state.conversations[chat_id]["messages"]) == 0 and role == "user":
            st.session_state.conversations[chat_id]["title"] = content[:30] + "..." if len(content) > 30 else content
            
        st.session_state.conversations[chat_id]["messages"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now()
        })
        st.session_state.conversations[chat_id]["updated_at"] = datetime.now()

    @staticmethod
    def delete_chat(chat_id: str):
        if chat_id in st.session_state.conversations:
            del st.session_state.conversations[chat_id]
        if st.session_state.active_chat_id == chat_id:
            st.session_state.active_chat_id = None
            
    @staticmethod
    def set_active_chat(chat_id: str):
        if chat_id in st.session_state.conversations:
            st.session_state.active_chat_id = chat_id

    @staticmethod
    def get_all_chats():
        """Returns sorted chats by updated_at descending"""
        chats = []
        for chat_id, data in st.session_state.conversations.items():
            chats.append({
                "id": chat_id,
                "title": data["title"],
                "updated_at": data["updated_at"]
            })
        return sorted(chats, key=lambda x: x["updated_at"], reverse=True)
