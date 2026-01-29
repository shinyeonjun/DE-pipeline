"""
Step 4: QA Engineer - TDD (Test First)
Chat Router 유닛 테스트

테스트 대상:
1. 에러 발생 시 상세 메시지가 사용자에게 노출되지 않는지 확인
2. 에러 코드만 반환되는지 확인

Note: httpx 버전 호환성을 위해 직접 httpx.AsyncClient 사용
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestChatRouterSecurity:
    """Chat Router 보안 테스트 (TDD - Red Phase)"""
    
    @pytest.mark.asyncio
    async def test_internal_error_hides_details(self):
        """내부 에러 발생 시 상세 정보가 응답에 포함되지 않아야 함"""
        # Arrange
        from app.features.chat.router import chat
        from app.features.chat.schemas import ChatRequest
        
        request = ChatRequest(message="테스트 질문", session_id="test-session")
        
        # 강제로 에러를 발생시키기 위해 서비스 mock
        with patch('app.features.chat.router.get_chat_service') as mock_service:
            mock_instance = MagicMock()
            mock_instance.chat = AsyncMock(
                side_effect=Exception("SENSITIVE_DATABASE_ERROR: Connection failed to 192.168.1.100")
            )
            mock_service.return_value = mock_instance
            
            # Act
            response = await chat(request)
        
        # Assert - 민감한 정보가 포함되어 있으면 안 됨
        assert "192.168.1.100" not in response.response, \
            "IP 주소가 응답에 노출되었습니다"
        assert "SENSITIVE_DATABASE_ERROR" not in response.response, \
            "내부 에러 메시지가 응답에 노출되었습니다"
    
    @pytest.mark.asyncio
    async def test_error_response_uses_generic_code(self):
        """에러 발생 시 일반적인 에러 코드만 반환해야 함"""
        # Arrange
        from app.features.chat.router import chat
        from app.features.chat.schemas import ChatRequest
        
        request = ChatRequest(message="테스트", session_id="test")
        
        with patch('app.features.chat.router.get_chat_service') as mock_service:
            mock_instance = MagicMock()
            mock_instance.chat = AsyncMock(
                side_effect=ValueError("Some internal validation error")
            )
            mock_service.return_value = mock_instance
            
            # Act
            response = await chat(request)
        
        # Assert - 에러 코드는 일반적인 형식이어야 함
        assert response.error in ["INTERNAL_ERROR", "SERVICE_ERROR", None, ""], \
            f"구체적인 에러 메시지가 error 필드에 노출됨: {response.error}"
    
    @pytest.mark.asyncio
    async def test_user_friendly_error_message(self):
        """사용자에게는 친화적인 에러 메시지만 표시해야 함"""
        # Arrange
        from app.features.chat.router import chat
        from app.features.chat.schemas import ChatRequest
        
        request = ChatRequest(message="안녕", session_id="s1")
        
        with patch('app.features.chat.router.get_chat_service') as mock_service:
            mock_instance = MagicMock()
            mock_instance.chat = AsyncMock(side_effect=RuntimeError("Critical failure"))
            mock_service.return_value = mock_instance
            
            # Act
            response = await chat(request)
        
        # Assert - 사용자 친화적 메시지 포함 확인
        assert "죄송" in response.response or "오류" in response.response or "다시 시도" in response.response, \
            "사용자 친화적인 에러 메시지가 아닙니다"
        
        # 기술적 용어 미포함 확인
        assert "RuntimeError" not in response.response
        assert "Critical failure" not in response.response

