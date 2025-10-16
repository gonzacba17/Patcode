"""Tests para SQLiteMemoryManager"""
import pytest
from pathlib import Path
from agents.memory.sqlite_memory_manager import SQLiteMemoryManager
from agents.memory.models import Message
from datetime import datetime


@pytest.fixture
def temp_memory(tmp_path):
    """Fixture con base de datos temporal"""
    db_path = tmp_path / "test_memory.db"
    manager = SQLiteMemoryManager(db_path)
    yield manager
    if db_path.exists():
        db_path.unlink()


def test_add_and_retrieve_message(temp_memory):
    """Test básico de agregar y recuperar"""
    msg = Message(
        role='user',
        content='Test message',
        timestamp=datetime.now().isoformat(),
        session_id='test-session'
    )
    
    msg_id = temp_memory.add_message(msg)
    assert msg_id > 0
    
    messages = temp_memory.get_recent_messages('test-session')
    assert len(messages) == 1
    assert messages[0].content == 'Test message'
    assert messages[0].role == 'user'


def test_multiple_messages(temp_memory):
    """Test con múltiples mensajes"""
    session_id = 'test-session'
    
    for i in range(5):
        msg = Message(
            role='user' if i % 2 == 0 else 'assistant',
            content=f'Message {i}',
            timestamp=datetime.now().isoformat(),
            session_id=session_id
        )
        temp_memory.add_message(msg)
    
    messages = temp_memory.get_recent_messages(session_id, limit=100)
    assert len(messages) == 5
    
    contents = [msg.content for msg in messages]
    assert 'Message 0' in contents
    assert 'Message 4' in contents


def test_search_messages(temp_memory):
    """Test de búsqueda"""
    session_id = 'test-session'
    
    for i in range(5):
        content = f'Message {i} with keyword' if i % 2 == 0 else f'Message {i}'
        msg = Message(
            role='user',
            content=content,
            timestamp=datetime.now().isoformat(),
            session_id=session_id
        )
        temp_memory.add_message(msg)
    
    results = temp_memory.search_messages('keyword', session_id=session_id)
    assert len(results) == 3


def test_session_summary(temp_memory):
    """Test de resumen de sesión"""
    session_id = 'test-session'
    
    for i in range(3):
        msg = Message(
            role='user',
            content=f'Message {i}',
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
            tokens=10
        )
        temp_memory.add_message(msg)
    
    summary = temp_memory.get_session_summary(session_id)
    assert summary is not None
    assert summary.message_count == 3
    assert summary.total_tokens == 30
    assert summary.session_id == session_id


def test_multiple_sessions(temp_memory):
    """Test con múltiples sesiones"""
    for session in ['session-1', 'session-2']:
        for i in range(3):
            msg = Message(
                role='user',
                content=f'Message {i} for {session}',
                timestamp=datetime.now().isoformat(),
                session_id=session
            )
            temp_memory.add_message(msg)
    
    session1_msgs = temp_memory.get_recent_messages('session-1')
    session2_msgs = temp_memory.get_recent_messages('session-2')
    
    assert len(session1_msgs) == 3
    assert len(session2_msgs) == 3
    
    all_sessions = temp_memory.get_all_sessions()
    assert len(all_sessions) == 2
    assert 'session-1' in all_sessions
    assert 'session-2' in all_sessions


def test_delete_session(temp_memory):
    """Test eliminación de sesión"""
    session_id = 'test-session'
    
    for i in range(5):
        msg = Message(
            role='user',
            content=f'Message {i}',
            timestamp=datetime.now().isoformat(),
            session_id=session_id
        )
        temp_memory.add_message(msg)
    
    messages = temp_memory.get_recent_messages(session_id)
    assert len(messages) == 5
    
    deleted = temp_memory.delete_session(session_id)
    assert deleted == 5
    
    messages = temp_memory.get_recent_messages(session_id)
    assert len(messages) == 0


def test_get_stats(temp_memory):
    """Test estadísticas globales"""
    for session_num in range(2):
        session_id = f'session-{session_num}'
        for i in range(3):
            msg = Message(
                role='user',
                content=f'Message {i}',
                timestamp=datetime.now().isoformat(),
                session_id=session_id,
                tokens=10
            )
            temp_memory.add_message(msg)
    
    stats = temp_memory.get_stats()
    assert stats['total_messages'] == 6
    assert stats['total_sessions'] == 2
    assert stats['total_tokens'] == 60


def test_export_session(temp_memory, tmp_path):
    """Test exportación de sesión"""
    session_id = 'test-session'
    
    for i in range(3):
        msg = Message(
            role='user',
            content=f'Message {i}',
            timestamp=datetime.now().isoformat(),
            session_id=session_id
        )
        temp_memory.add_message(msg)
    
    export_path = tmp_path / "export.json"
    temp_memory.export_session(session_id, export_path)
    
    assert export_path.exists()
    
    import json
    with open(export_path, 'r') as f:
        data = json.load(f)
    
    assert data['session_id'] == session_id
    assert data['message_count'] == 3
    assert len(data['messages']) == 3


def test_message_with_metadata(temp_memory):
    """Test mensajes con metadata"""
    msg = Message(
        role='user',
        content='Test with metadata',
        timestamp=datetime.now().isoformat(),
        session_id='test-session',
        tokens=15,
        metadata={'source': 'test', 'priority': 'high'}
    )
    
    temp_memory.add_message(msg)
    
    messages = temp_memory.get_recent_messages('test-session')
    assert len(messages) == 1
    assert messages[0].metadata is not None
    assert messages[0].metadata['source'] == 'test'
    assert messages[0].metadata['priority'] == 'high'
    assert messages[0].tokens == 15
