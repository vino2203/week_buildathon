import pytest
from unittest.mock import patch, MagicMock

# Mock Streamlit's session state before importing the store
class DummySessionState(dict):
    def __getattr__(self, name):
        return self.get(name)
    def __setattr__(self, name, value):
        self[name] = value

@pytest.fixture
def mock_st():
    with patch("repositories.session_store.st") as mock_st:
        mock_st.session_state = DummySessionState()
        yield mock_st

def test_init_state(mock_st):
    from repositories.session_store import SessionStore
    SessionStore.init_state()
    assert hasattr(mock_st.session_state, "conversations")
    assert mock_st.session_state.conversations == {}
    assert mock_st.session_state.active_chat_id is None
    assert mock_st.session_state.theme == "light"

def test_create_chat(mock_st):
    from repositories.session_store import SessionStore
    SessionStore.init_state()
    
    chat_id = SessionStore.create_chat()
    assert chat_id is not None
    assert chat_id in mock_st.session_state.conversations
    assert mock_st.session_state.active_chat_id == chat_id
    assert mock_st.session_state.conversations[chat_id]["title"] == "New Conversation"

def test_add_message_and_rename_title(mock_st):
    from repositories.session_store import SessionStore
    SessionStore.init_state()
    
    # Adding a message should auto-create a chat if none is active
    SessionStore.add_message("user", "Hello world!")
    
    chat_id = mock_st.session_state.active_chat_id
    assert chat_id is not None
    messages = SessionStore.get_active_messages()
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello world!"
    
    # Check that title was automatically updated based on the first user message
    assert mock_st.session_state.conversations[chat_id]["title"] == "Hello world!"

def test_delete_chat(mock_st):
    from repositories.session_store import SessionStore
    SessionStore.init_state()
    
    chat_id = SessionStore.create_chat()
    SessionStore.delete_chat(chat_id)
    
    assert chat_id not in mock_st.session_state.conversations
    assert mock_st.session_state.active_chat_id is None

def test_file_validation_composer():
    from components.composer import process_uploaded_file
    
    # Test unsupported file
    class FakeFile:
        name = "image.png"
        
    result = process_uploaded_file(FakeFile())
    assert "Unsupported file type" in result
    
    # Test TXT file
    class FakeTxt:
        name = "test.txt"
        def getvalue(self):
            return b"Hello world"
            
    result = process_uploaded_file(FakeTxt())
    assert result == "Hello world"
