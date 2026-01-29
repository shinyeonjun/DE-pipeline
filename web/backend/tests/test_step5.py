"""
Step 추가 테스트 - step5_response_generation.py
"""
import pytest
from app.features.chat.steps.step5_response_generation import (
    generate_data_based_response,
    format_number
)


class TestGenerateDataBasedResponse:
    """데이터 기반 폴백 응답 생성 테스트"""
    
    def test_trending_data_response(self):
        """트렌딩 데이터가 있을 때 응답 생성"""
        # Arrange
        all_data = {
            "ai_current_trending": {
                "data": [
                    {"순위": 1, "제목": "테스트 영상", "채널명": "테스트 채널", "조회수": 1000000, "카테고리": "Music"},
                    {"순위": 2, "제목": "두번째 영상", "채널명": "다른 채널", "조회수": 500000, "카테고리": "Gaming"},
                ]
            }
        }
        
        # Act
        result = generate_data_based_response(all_data, "인기 동영상 보여줘")
        
        # Assert
        assert "현재 인기 있는 동영상" in result
        assert "테스트 채널" in result
        assert "1위" in result

    def test_trending_data_sorting_correction(self):
        """데이터가 역순(하위권부터)으로 들어왔을 때 1위부터 정렬되는지 확인"""
        # Arrange
        all_data = {
            "ai_current_trending": {
                "data": [
                    {"순위": 200, "제목": "200위 영상", "채널명": "채널 200", "조회수": 27000, "카테고리": "Gaming"},
                    {"순위": 199, "제목": "199위 영상", "채널명": "채널 199", "조회수": 157000, "카테고리": "Gaming"},
                    {"순위": 1, "제목": "1위 영상", "채널명": "채널 1", "조회수": 5000000, "카테고리": "Gaming"},
                ]
            }
        }
        
        # Act
        result = generate_data_based_response(all_data, "인기 동영상 알려줘")
        
        # Assert
        # 1위 영상이 먼저 나타나야 함
        assert "1위 영상" in result
        # 1위 영상의 위치가 200위 영상보다 앞에 있어야 함
        assert result.find("1위 영상") < result.find("200위 영상")
    
    def test_empty_data_response(self):
        """데이터가 없을 때 기본 응답"""
        # Arrange
        all_data = {"ai_current_trending": {"data": []}}
        
        # Act
        result = generate_data_based_response(all_data, "테스트")
        
        # Assert
        assert "차트에서" in result or "분석 중" in result
    
    def test_category_stats_response(self):
        """카테고리 통계 데이터 응답"""
        # Arrange
        all_data = {
            "ai_category_stats": {
                "data": [
                    {"카테고리": "Music", "영상수": 50, "평균_조회수": 100000},
                    {"카테고리": "Gaming", "영상수": 30, "평균_조회수": 80000},
                ]
            }
        }
        
        # Act
        result = generate_data_based_response(all_data, "카테고리 분석")
        
        # Assert
        assert "카테고리별 분석" in result
        assert "Music" in result


class TestFormatNumber:
    """숫자 포맷팅 테스트"""
    
    def test_millions(self):
        """백만 단위 포맷팅"""
        assert "M" in format_number(1500000) or "백만" in format_number(1500000) or "1.5" in format_number(1500000)
    
    def test_thousands(self):
        """천 단위 포맷팅"""
        result = format_number(50000)
        assert "K" in result or "5만" in result or "50" in result
    
    def test_zero(self):
        """0 처리"""
        assert format_number(0) is not None
