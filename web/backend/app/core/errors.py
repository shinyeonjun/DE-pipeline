"""
공통 오류 처리 helper

내부 예외 메시지(DB 주소, 쿼리, 스택 정보 등)는 서버 로그에만 남기고,
클라이언트에는 일반적인 메시지와 코드만 돌려준다.
"""
import logging

from fastapi import HTTPException

logger = logging.getLogger("app.errors")

INTERNAL_ERROR_CODE = "INTERNAL_ERROR"
INTERNAL_ERROR_DETAIL = "Internal server error"


def internal_error(context: str) -> HTTPException:
    """현재 처리 중인 예외를 로그에 남기고, 클라이언트용 500 응답을 만든다.

    ``except`` 블록 안에서 ``raise internal_error("...") from e`` 형태로 사용한다.
    """
    logger.exception("Unhandled error in %s", context)
    return HTTPException(status_code=500, detail=INTERNAL_ERROR_DETAIL)
