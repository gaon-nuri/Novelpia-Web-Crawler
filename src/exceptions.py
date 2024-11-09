# novel_crawler/exceptions.py
"""프로젝트에서 사용할 커스텀 예외를 정의합니다."""


class CrawlNovelError(RuntimeError):
    """소설 크롤링 중 발생하는 예외"""
    pass


class ParseError(RuntimeError):
    """파싱 중 발생하는 예외"""
    pass


class ParseNovelError(ParseError):
    """소설 파싱 중 발생하는 예외"""
    pass


class TagNotFoundError(ParseError):
    """태그 부재 시 발생하는 예외"""
    pass


class ParseResError(ParseError):
    """서버 응답 파싱 중 발생하는 예외"""
    pass


class NoAlertMsgError(ParseError):
    """오류 창에 메시지가 없을 시 발생하는 예외"""
    pass


class ReqNovelError(Exception):
    """HTTP 요청 중 발생하는 예외"""
    pass


class NotLoggedInError(ReqNovelError):
    """로그인 필요 시 발생하는 예외"""
    pass


class ReqPrivateNovelError(ReqNovelError, PermissionError):
    """비공개 소설 요청 시 발생하는 예외"""
    pass


class ReqDeletedNovelError(ReqNovelError):
    """삭제된 소설 요청 시 발생하는 예외"""
    pass


class WriteFileError(OSError):
    """파일 쓰기 중 발생하는 예외"""
    pass


class NoValueError(ValueError):
    """값이 없을 때 발생하는 예외"""
    pass

# 추가적인 커스텀 예외들을 정의할 수 있습니다.
