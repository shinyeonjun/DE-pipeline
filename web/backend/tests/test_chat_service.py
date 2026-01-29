"""
Step 4: QA Engineer - TDD (Test First)
Chat Service 유닛 테스트

테스트 대상:
1. LRUSessionHistory 클래스 - 세션 메모리 관리
2. _generate_conversational_response 메서드 시그니처
"""
import pytest
from collections import OrderedDict
from typing import List, Dict, Any


class TestLRUSessionHistory:
    """LRU 기반 세션 히스토리 클래스 테스트 (TDD - Red Phase)"""
    
    def test_get_empty_session_returns_empty_list(self):
        """존재하지 않는 세션 조회 시 빈 리스트 반환"""
        # Arrange
        from app.features.chat.service import LRUSessionHistory
        cache = LRUSessionHistory(max_sessions=10)
        
        # Act
        result = cache.get("non_existent_session")
        
        # Assert
        assert result == []
    
    def test_append_and_get_single_message(self):
        """단일 메시지 추가 후 조회"""
        # Arrange
        from app.features.chat.service import LRUSessionHistory
        cache = LRUSessionHistory(max_sessions=10)
        
        # Act
        cache.append("session1", "user", "Hello")
        result = cache.get("session1")
        
        # Assert
        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "Hello"
    
    def test_max_sessions_eviction(self):
        """max_sessions 초과 시 가장 오래된 세션 제거 (LRU)"""
        # Arrange
        from app.features.chat.service import LRUSessionHistory
        cache = LRUSessionHistory(max_sessions=3)
        
        # Act - 4개 세션 추가 (max=3)
        cache.append("session1", "user", "msg1")
        cache.append("session2", "user", "msg2")
        cache.append("session3", "user", "msg3")
        cache.append("session4", "user", "msg4")  # session1이 제거되어야 함
        
        # Assert
        assert cache.get("session1") == []  # 가장 오래된 세션 제거됨
        assert len(cache.get("session4")) == 1  # 최신 세션 유지
    
    def test_max_messages_per_session(self):
        """세션당 max_messages 초과 시 오래된 메시지 제거"""
        # Arrange
        from app.features.chat.service import LRUSessionHistory
        cache = LRUSessionHistory(max_sessions=10, max_messages_per_session=3)
        
        # Act - 5개 메시지 추가 (max=3)
        for i in range(5):
            cache.append("session1", "user", f"msg{i}")
        
        result = cache.get("session1")
        
        # Assert
        assert len(result) == 3  # 최대 3개만 유지
        assert result[0]["content"] == "msg2"  # 오래된 msg0, msg1은 제거
        assert result[2]["content"] == "msg4"
    
    def test_lru_access_updates_order(self):
        """get 호출 시 LRU 순서 업데이트"""
        # Arrange
        from app.features.chat.service import LRUSessionHistory
        cache = LRUSessionHistory(max_sessions=2)
        
        # Act
        cache.append("session1", "user", "msg1")
        cache.append("session2", "user", "msg2")
        cache.get("session1")  # session1 접근 → LRU 순서 업데이트
        cache.append("session3", "user", "msg3")  # session2가 제거되어야 함
        
        # Assert
        assert len(cache.get("session1")) == 1  # session1은 유지
        assert cache.get("session2") == []  # session2는 제거됨


class TestConversationalResponse:
    """일상 대화 응답 생성 메서드 시그니처 테스트"""
    
    def test_method_accepts_history_parameter(self):
        """_generate_conversational_response가 history 파라미터를 받아야 함"""
        # Arrange
        from app.features.chat.service import AIChatService
        import inspect
        
        # Act
        sig = inspect.signature(AIChatService._generate_conversational_response)
        params = list(sig.parameters.keys())
        
        # Assert
        assert "history" in params, "history 파라미터가 메서드 시그니처에 없습니다"
    
    def test_history_has_default_value(self):
        """history 파라미터는 기본값(None 또는 [])을 가져야 함"""
        # Arrange
        from app.features.chat.service import AIChatService
        import inspect
        
        # Act
        sig = inspect.signature(AIChatService._generate_conversational_response)
        history_param = sig.parameters.get("history")
        
        # Assert
        assert history_param is not None
        assert history_param.default is not inspect.Parameter.empty, \
            "history 파라미터에 기본값이 없습니다"


class TestChatServiceIntegration:
    """Chat 서비스 통합 테스트"""
    
    def test_service_uses_lru_session_history(self):
        """AIChatService가 LRUSessionHistory를 사용하는지 확인"""
        # Arrange
        from app.features.chat.service import AIChatService, LRUSessionHistory
        
        # Act
        service = AIChatService(
            ollama_host="http://localhost:11434",
            model="test-model"
        )
        
        # Assert
        assert hasattr(service, 'session_histories')
        assert isinstance(service.session_histories, LRUSessionHistory), \
            "session_histories가 LRUSessionHistory 인스턴스가 아닙니다"
