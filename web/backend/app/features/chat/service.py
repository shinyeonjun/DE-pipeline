"""
Chat Service - AI 챗봇 비즈니스 로직 (함수형 리팩토링 + RAG 하이브리드)
데이터 분석(SQL) 경로와 지식 검색(RAG) 경로를 라우팅하여 처리합니다.
"""
import traceback
from typing import List, Dict, Any, Optional
from app.core import settings
from .utils.llm import call_llm
from .steps import (
    route_query,
    analyze_question,
    normalize_entities,
    # select_views, # DEPRECATED
    retrieve_data,
    retrieve_knowledge,
    format_rag_context,
    analyze_data,
    generate_response,
    generate_suggestions
)


class AIChatService:
    """
    AI 챗봇 서비스
    Query Router를 통해 데이터 분석 / 지식 검색 경로를 자동 선택합니다.
    """
    
    def __init__(self, ollama_host: str, model: str):
        self.ollama_host = ollama_host
        self.model = model
        self.conversation_history = []
        self.session_histories = {} # 세션별 대화 기록 가상 저장 (DB 폴백용)
    
    async def _get_persistent_history(self, session_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """DB에서 세션별 대화 기록을 가져옵니다."""
        try:
            from app.core.database import supabase
            result = supabase.table("chat_history")\
                .select("role", "content")\
                .eq("session_id", session_id)\
                .order("created_at", desc=True)\
                .limit(limit * 2)\
                .execute()
            
            # 최신 순으로 가져왔으므로 다시 시간 순으로 정렬
            history = result.data[::-1] if result.data else []
            return history
        except Exception as e:
            print(f"[History] DB 조회 실패, 메모리 캐시 사용: {e}")
            return self.session_histories.get(session_id, [])[-limit*2:]

    async def _save_message(self, session_id: str, role: str, content: str):
        """대화를 DB에 영구 저장합니다."""
        try:
            from app.core.database import supabase
            supabase.table("chat_history").insert({
                "session_id": session_id,
                "role": role,
                "content": content
            }).execute()
        except Exception as e:
            print(f"[History] DB 저장 실패: {e}")
            # 메모리 캐시 업데이트
            if session_id not in self.session_histories:
                self.session_histories[session_id] = []
            self.session_histories[session_id].append({"role": role, "content": content})

    async def chat(self, user_message: str, session_id: str = "default") -> Dict[str, Any]:
        """챗봇 응답 파이프라인 (병렬화 및 영속성 강화 버전)"""
        
        print(f"[Chat] ========================================")
        print(f"[Chat] 사용자 질문: {user_message}")
        print(f"[Chat] ========================================")
        
        all_thinking = []
        
        try:
            # 0. 히스토리 로드 (영속화 비활성화 - 메모리만 사용)
            # history = await self._get_persistent_history(session_id)
            history = self.session_histories.get(session_id, [])[-10:]
            
            # 0.5단계: 질문 라우팅
            print(f"[Chat] [0단계] Query 라우팅 중...")
            route_result = await route_query(user_message, self.ollama_host, self.model)
            query_route = route_result.get("route", "data")
            all_thinking.append(f"[0단계] 라우팅: {query_route} ({route_result.get('thinking', '')})")
            print(f"[Chat] [0단계] 라우팅 결과: {query_route}")
            
            # ============================================
            # KNOWLEDGE 경로 (RAG)
            # ============================================
            if query_route == "knowledge":
                print(f"[Chat] [RAG] 지식 검색 경로 시작...")
                
                # RAG 검색 (AI 기반 하이브리드)
                rag_result = await retrieve_knowledge(user_message, self.ollama_host, self.model)
                documents = rag_result.get("documents", [])
                all_thinking.append(f"[RAG] 검색 결과: {len(documents)}개 문서")
                
                if documents:
                    # 검색된 문서로 응답 생성
                    rag_context = format_rag_context(documents)
                    rag_response = await self._generate_rag_response(user_message, rag_context)
                    all_thinking.append(f"[RAG] 응답 생성 완료")
                    
                    if session_id not in self.session_histories:
                        self.session_histories[session_id] = []
                    self.session_histories[session_id].append({"role": "user", "content": user_message})
                    self.session_histories[session_id].append({"role": "assistant", "content": rag_response})
                    # await self._save_message(session_id, "user", user_message)
                    # await self._save_message(session_id, "assistant", rag_response)
                    
                    return {
                        "response": rag_response,
                        "tools_used": ["knowledge_base"],
                        "session_id": session_id,
                        "response_type": "text",
                        "thinking": "\n".join(all_thinking),
                        "suggested_questions": [],
                        "insights": [],
                        "related_analyses": []
                    }
                else:
                    # RAG 검색 실패 시 데이터 경로로 폴백
                    print(f"[Chat] [RAG] 검색 결과 없음 → 데이터 경로로 폴백")
                    all_thinking.append(f"[RAG] 검색 결과 없음, 데이터 경로로 폴백")
                    query_route = "data"
            
            # ============================================
            # DATA 경로 (기존 SQL 파이프라인)
            # ============================================
            # 1단계: 통합 질문 분석 (질문 분석 + View 선택 + 스키마 동기화)
            print(f"[Chat] [1단계] 통합 질문 분석 및 스키마 로드 중...")
            
            # Phase 2: Self-Healing Metadata (DB에서 실시간 스키마 로드)
            from app.core.base_service import BaseService
            view_schema = await BaseService.get_ai_view_schema()
            
            last_turn_summary = ""
            if len(history) >= 2:
                last_user = history[-2].get("content", "")
                last_bot = history[-1].get("content", "")
                if last_user and last_bot:
                    last_turn_summary = f"User: {last_user}\nAssistant: {last_bot[:200]}..."

            # Phase 1: Zero-Latency (통합 분석 호출)
            question_analysis = await analyze_question(
                user_message, 
                self.ollama_host, 
                self.model,
                view_schema=view_schema,
                last_turn_summary=last_turn_summary
            )
            all_thinking.append(f"[1단계] {question_analysis.get('thinking', '통합 분석 완료')}")
            
            print(f"[Chat] [1단계] 통합 분석 완료.")


            # Short Circuit: 일상 대화
            if question_analysis.get("intent") == "conversation":
                print(f"[Chat] [Short-Circuit] 일상 대화 감지.")
                conversation_response = await self._generate_conversational_response(user_message, history)
                all_thinking.append(f"[대화] 일상 대화 처리 완료")
                
                if session_id not in self.session_histories:
                    self.session_histories[session_id] = []
                self.session_histories[session_id].append({"role": "user", "content": user_message})
                self.session_histories[session_id].append({"role": "assistant", "content": conversation_response})
                # await self._save_message(session_id, "user", user_message)
                # await self._save_message(session_id, "assistant", conversation_response)

                return {
                    "response": conversation_response,
                    "tools_used": [],
                    "session_id": session_id,
                    "response_type": "text",
                    "thinking": "\n".join(all_thinking),
                    "suggested_questions": [],
                    "insights": [],
                    "related_analyses": []
                }
            
            # ============================================
            # 2단계: View 로드 (통합 분석 결과 사용)
            # ============================================
            required_views_raw = question_analysis.get("required_views", [])
            selected_views = []
            
            if isinstance(required_views_raw, list):
                for v in required_views_raw:
                    if isinstance(v, dict) and "name" in v:
                        selected_views.append((v["name"], v.get("limit", 20)))
                    elif isinstance(v, str): # 하위 호환
                        selected_views.append((v, 20))

            if not selected_views and question_analysis.get("intent") != "conversation":
                # 최후의 수단: 기본 뷰
                selected_views = [("ai_current_trending", 20)]
            
            all_thinking.append(f"[2단계] 선택된 View: {[v[0] for v in selected_views]}")
            print(f"[Chat] [2단계] 선택된 View: {[v[0] for v in selected_views]}")
            
            # ============================================
            # 3단계: 데이터 조회 (병렬 처리)
            # ============================================
            print(f"[Chat] [3단계] 데이터 병렬 조회 시작...")
            
            filters = question_analysis.get("filters", [])
            sort = question_analysis.get("sort")

            # retrieve_data를 내부적으로 병렬화하거나 여기서 개별 호출
            all_data, tools_used, view_summaries, data_retrieval_thinking = await retrieve_data(
                selected_views,
                filters=filters,
                sort=sort
            )
            all_thinking.append(f"[3단계] {data_retrieval_thinking}")
            
            print(f"[Chat] [3단계] 조회 완료: {len(all_data)}개 View 성공")
            
            # 데이터가 없는 경우에도 generate_response로 넘겨서 LLM이 설명하도록 함
            if not all_data:
                print(f"[Chat] 조회된 데이터 없음. LLM 설명 모드로 전환.")
                # 빈 all_data를 유지하고 진행
            
            # ============================================
            # 4단계: 종합 분석
            # ============================================
            print(f"[Chat] [4단계] 데이터 종합 분석 중...")
            comprehensive_analysis = ""
            if all_data:
                comprehensive_analysis, _ = analyze_data(all_data, user_message, question_analysis)
            all_thinking.append(f"[4단계] 종합 분석 완료")
            
            # ============================================
            # 5단계: 답변 생성
            # ============================================
            print(f"[Chat] [5단계] 최종 답변 생성 중...")
            result = await generate_response(
                user_message,
                all_data,
                comprehensive_analysis,
                history, # 변경: self.conversation_history 대신 history 사용
                self.ollama_host,
                self.model,
                question_analysis=question_analysis
            )
            all_thinking.append(f"[5단계] {result.get('thinking', '답변 생성 완료')}")
            
            # ============================================
            # 6단계: 능동적 제안 (비동기, 실패 허용)
            # ============================================
            print(f"[Chat] [6단계] 능동적 제안 생성 중...")
            suggestions = {}
            try:
                suggestions = await generate_suggestions(
                    user_message,
                    result["response"],
                    all_data,
                    question_analysis,
                    self.ollama_host,
                    self.model
                )
                all_thinking.append(f"[6단계] 제안 생성 완료")
            except Exception as e:
                print(f"[WARN] 제안 생성 실패 (계속 진행): {e}")
                all_thinking.append(f"[6단계] 제안 생성 실패: {e}")
                suggestions = {}
            
            # 대화 저장 (영속화 비활성화 - 메모리만 사용)
            if session_id not in self.session_histories:
                self.session_histories[session_id] = []
            self.session_histories[session_id].append({"role": "user", "content": user_message})
            self.session_histories[session_id].append({"role": "assistant", "content": result["response"]})
            # await self._save_message(session_id, "user", user_message)
            # await self._save_message(session_id, "assistant", result["response"])
            
            # Safe tools_used
            safe_tools_used = []
            for item in tools_used:
                if isinstance(item, tuple):
                    safe_tools_used.append(item[0])
                else:
                    safe_tools_used.append(str(item))
            
            print(f"[Chat] 처리 완료")
            print(f"[Chat] ========================================")
            
            return {
                "response": result["response"],
                "tools_used": safe_tools_used,
                "session_id": session_id,
                "response_type": result.get("response_type", "text"),
                "structured_data": result.get("structured_data"),
                "thinking": "\n".join(all_thinking),
                "suggested_questions": suggestions.get("suggested_questions", []),
                "insights": suggestions.get("insights", []),
                "related_analyses": suggestions.get("related_analyses", [])
            }
            
        except Exception as e:
            print(f"[ERROR] Chat 처리 중 에러: {type(e).__name__}: {e}")
            traceback.print_exc()
            error_msg = str(e)
            all_thinking.append(f"[ERROR] {error_msg}")
            
            return {
                "response": f"오류가 발생했습니다: {error_msg}",
                "error": error_msg,
                "session_id": session_id,
                "tools_used": [],
                "thinking": "\n".join(all_thinking)
            }
    
    def clear_history(self):
        """대화 히스토리 초기화"""
        self.conversation_history = []
    
    async def _generate_conversational_response(self, user_message: str) -> str:
        """데이터 조회 없이 일상 대화에 대한 응답 생성"""
        
        system_prompt = """당신은 YouTube 데이터 분석 전문가 AI입니다. 
데이터 조회 없이 사용자의 인사에 답하거나, 자신을 소개하거나, 가벼운 대화를 나누세요.
항상 친절하고 전문적인 태도를 유지하세요. 
만약 사용자가 데이터를 요구하는 질문을 했는데 'conversation'으로 분류되었다면, 
"죄송하지만 그 질문은 데이터를 조회해야 정확히 답변드릴 수 있습니다. 구체적으로 질문해 주시겠어요?"라고 정중히 답하세요.
한국어로 답변하세요."""

        messages = [
            {"role": "system", "content": system_prompt},
        ]
        
        messages.extend(self.conversation_history[-4:])
        messages.append({"role": "user", "content": user_message})
        
        try:
            # call_llm 유틸리티 사용
            response = await call_llm(
                self.ollama_host, 
                self.model, 
                messages, 
                temperature=0.7
            )
            return response.get("message", {}).get("content", "안녕하세요! 유튜브 데이터 분석을 도와드리는 AI입니다.")
        except Exception as e:
            print(f"[Conversational] LLM 호출 실패: {e}")
            
        return "안녕하세요! 유튜브 트렌드 분석에 대해 무엇이든 물어보세요."

    async def _generate_rag_response(self, user_message: str, rag_context: str) -> str:
        """RAG 검색 결과를 기반으로 응답 생성"""
        
        # 디버깅: 컨텍스트 길이 출력
        print(f"[RAG Response] 컨텍스트 길이: {len(rag_context)} chars")
        
        system_prompt = f"""너는 유튜브 전문가 친구야. 쉽고 친근하게 설명해줘!

아래 [지식]을 바탕으로 바로 답변해. 되묻지 말고 알고 있는 내용을 최대한 설명해줘.

[지식]
{rag_context}

[말투 규칙]
- 친구한테 설명하듯이 쉽게 말해
- 이모지 적절히 사용해 🎯
- 핵심만 깔끔하게 정리해
- 전문 용어는 풀어서 설명해
- 절대 "더 자세히 알려주세요", "어떤 부분이 궁금하세요?" 같은 되묻기 하지 마
- 바로 본론으로 들어가서 설명해

한국어로 답변해."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        try:
            response = await call_llm(
                self.ollama_host, 
                self.model, 
                messages, 
                temperature=0.5,  # 약간 더 창의적으로
                num_predict=2048  # 더 긴 응답 허용
            )
            answer = response.get("message", {}).get("content", "")
            
            if not answer or len(answer) < 20:
                print(f"[RAG Response] 응답이 너무 짧음: {answer}")
                return "죄송합니다. 답변을 생성하는 중 문제가 발생했습니다. 다시 질문해 주세요."
            
            return answer
        except Exception as e:
            print(f"[RAG Response] LLM 호출 실패: {e}")
            return "죄송합니다. 지식 검색 응답을 생성하는 데 문제가 발생했습니다."

    def get_available_views(self):
        """사용 가능한 View 목록 반환"""
        from .views import VIEW_CATALOG
        return [
            {
                "name": view_type.value,
                "description": info.description,
                "columns": info.columns
            }
            for view_type, info in VIEW_CATALOG.items()
        ]


# 싱글톤 인스턴스
_chat_service_instance = None

def get_chat_service() -> AIChatService:
    """채팅 서비스 싱글톤 인스턴스 반환"""
    global _chat_service_instance
    if _chat_service_instance is None:
        _chat_service_instance = AIChatService(
            ollama_host=settings.ollama_host,
            model=settings.ollama_model
        )
    return _chat_service_instance
