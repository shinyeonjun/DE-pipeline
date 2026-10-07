"""
Step 5 테스트 - step5_response_generation.py

LLM 호출이 실패했을 때 쓰는 폴백 요약(generate_data_summary)과 숫자 포맷팅을 검증한다.
"""
from app.features.chat.steps.step5_response_generation import (
    generate_data_summary,
    format_number,
)


class TestGenerateDataSummary:
    """데이터 기반 폴백 요약 생성 테스트"""

    def test_trending_data_summary(self):
        """트렌딩 데이터가 있을 때 질문, 건수, 채널명, 순위가 포함된다"""
        all_data = {
            "ai_current_trending": {
                "data": [
                    {"순위": 1, "제목": "테스트 영상", "채널명": "테스트 채널", "조회수": 1000000, "카테고리": "Music"},
                    {"순위": 2, "제목": "두번째 영상", "채널명": "다른 채널", "조회수": 500000, "카테고리": "Gaming"},
                ]
            }
        }

        result = generate_data_summary(all_data, "인기 동영상 보여줘")

        assert "인기 동영상 보여줘" in result
        assert "ai_current_trending" in result
        assert "2개 데이터" in result
        assert "테스트 채널" in result
        assert "| 1 |" in result
        assert "1.0M" in result

    def test_trending_data_sorted_by_rank(self):
        """데이터가 역순(하위권부터)으로 들어와도 1위부터 정렬된다"""
        all_data = {
            "ai_current_trending": {
                "data": [
                    {"순위": 200, "제목": "200위 영상", "채널명": "채널 200", "조회수": 27000, "카테고리": "Gaming"},
                    {"순위": 199, "제목": "199위 영상", "채널명": "채널 199", "조회수": 157000, "카테고리": "Gaming"},
                    {"순위": 1, "제목": "1위 영상", "채널명": "채널 1", "조회수": 5000000, "카테고리": "Gaming"},
                ]
            }
        }

        result = generate_data_summary(all_data, "인기 동영상 알려줘")

        assert result.find("1위 영상") < result.find("199위 영상") < result.find("200위 영상")

    def test_empty_data_has_no_table(self):
        """데이터가 없으면 질문 안내 문장만 남고 표는 만들지 않는다"""
        all_data = {"ai_current_trending": {"data": []}}

        result = generate_data_summary(all_data, "테스트")

        assert "테스트" in result
        assert "|" not in result

    def test_filters_are_shown(self):
        """적용된 필터가 요약에 표시된다"""
        all_data = {
            "ai_category_stats": {
                "data": [{"카테고리": "Music", "영상수": 50}],
                "filters_applied": [{"field": "카테고리", "value": "Music"}],
            }
        }

        result = generate_data_summary(all_data, "음악 카테고리")

        assert "필터: 카테고리=Music" in result

    def test_category_stats_summary(self):
        """카테고리 통계는 카테고리별 영상 수 목록으로 표시된다"""
        all_data = {
            "ai_category_stats": {
                "data": [
                    {"카테고리": "Music", "영상수": 50, "평균_조회수": 100000},
                    {"카테고리": "Gaming", "영상수": 30, "평균_조회수": 80000},
                ]
            }
        }

        result = generate_data_summary(all_data, "카테고리 분석")

        assert "- Music: 50개 동영상" in result
        assert "- Gaming: 30개 동영상" in result


class TestFormatNumber:
    """숫자 포맷팅 테스트"""

    def test_millions(self):
        assert format_number(1500000) == "1.5M"

    def test_thousands(self):
        assert format_number(50000) == "50.0K"

    def test_small_numbers_use_comma(self):
        assert format_number(999) == "999"

    def test_zero(self):
        assert format_number(0) == "0"

    def test_none(self):
        assert format_number(None) == "-"

    def test_non_numeric_is_passed_through(self):
        assert format_number("N/A") == "N/A"
