"""소설 알람, 선호작 설정/해제 관련 코드"""

from enum import IntEnum
from logging import getLogger
from typing import Any, Optional

from exceptions import NoValueError, NotLoggedInError, ReqNovelError
from func.common import load_mem_no_from_env
from novel_info import Novel

logger = getLogger(__name__)


def log_and_return_error(exception: Exception) -> Exception:
    """
    로그를 남기고 예외를 발생시키는 함수

    :param exception: 발생시킬 예외 객체
    :return: 예외 객체
    """
    logger.error(exception)
    return exception


def pick_novel_act(novel_code: str, novel_act: int, log_kind: int = 0) -> tuple[int, int]:
    """소설 알람 또는 선호작 설정을 등록/해제하는 함수

    :param novel_code: 소설 번호
    :param novel_act: 작업 유형 (1은 알람, 2는 선호)
    :param log_kind: 로그인 유형 (0은 비 로그인, 1은 일반 계정, 2는 구독 계정)
    :return: 상태 코드 (등록: 1, 해제: 2, 로그인 필요: 3), 최종 알람/선호 수
    """
    do_login: bool = (log_kind != 0)
    match novel_act:
        case 1:             # 알람 설정
            return toggle_novel_alarm(do_login, novel_code)
        case 2 if do_login: # 선호작 설정 (로그인 필요)
            return toggle_novel_like(novel_code)
        case _:
            err = NotImplementedError("구현되지 않은 설정 번호")
            raise log_and_return_error(err)


def toggle_novel_like(novel_code):
    stat_names = "like", "선호"
    return toggle_novel_act(novel_code, stat_names)


def toggle_novel_alarm(do_login, novel_code):
    stat_name_en, stat_name_kr = "alarm", "알람"
    if not do_login:
        logger.error(f"비 로그인 모드. {stat_name_kr} 수만 추출할게요.")
    stat_names = stat_name_en, stat_name_kr
    return toggle_novel_act(novel_code, stat_names)


def toggle_novel_act(novel_code: str, stat_names: tuple[str, str]):
    from requests import Response
    from func.crawl import abs_url_from_rel_url, res_from_post_req

    def fetch_stat(stat_name: str, _novel_code: str) -> Response:
        """ 소설 알람 또는 선호작 설정을 서버에 요청하는 함수

        Args:
            stat_name (str): 상태 이름 (alarm|like)
            _novel_code (str): 소설 번호

        Returns:
            Response: HTTP 응답 객체
        
        Raises:
            NoValueError: CSRF 문자열을 환경 변수에서 찾을 수 없을 때 발생
            ReqNovelError: 요청 소설 작업 중 오류 발생 시
        """
        def setup_req_data(__novel_code: str) -> dict[str, str]:
            """ 요청 데이터를 설정하는 함수

            Args:
                __novel_code (str): 소설 번호

            Returns:
                dict[str, str]: 요청 데이터 딕셔너리

            Raises:
                NoValueError: CSRF 문자열을 환경 변수에서 찾을 수 없을 때 발생
            """
            from dotenv import dotenv_values
            csrf_token: Optional[str] = dotenv_values().get("CSRF_SUB")
            if csrf_token:
                return req_data_from_params(csrf_token, __novel_code)
            err = NoValueError("CSRF 문자열을 환경 변수에서 찾을 수 없어요.")
            raise log_and_return_error(err)

        abs_url = abs_url_from_rel_url(f"/proc/novel_{stat_name}")
        return res_from_post_req(abs_url, setup_req_data(_novel_code))

    def parse_response(res: Response) -> tuple[list[str], int]:
        """
        응답을 파싱하여 상태와 통계 수를 반환하는 함수
        
        :param res: HTTP 응답 객체
        :return: 상태 코드 리스트와 통계 수
        :raises ParseResError: 응답 파싱 중 오류 발생 시
        :raises ReqNovelError: 요청 소설 작업 중 오류 발생 시
        """
        from src.exceptions import ParseResError
        try:
            # {'status': '200', 'errmsg': '', {'novel': [{ ... }], 'allCount': 2}}
            flags: list[str] = res.text.split("|")
            return flags, int(flags[1])
        except (AttributeError, IndexError) as err:
            raise ParseResError("[오류]", err)

    def log_result_and_return_flag(flag: str) -> int:
        """결과를 로그에 남기고 상태 코드를 반환하는 함수

        Args:
            flag (str): 상태 코드 (on|off|login)

        Raises:
            ReqNovelError: 요청 소설 작업 중 오류 발생 시

        Returns:
            int: 상태 코드
        """
        msg: str # to avoid mypy error: no-redef
        match flag:
            case "on" | "off":  # 예: on|1896||0, off|1895||
                act = "등록" if flag == "on" else "해제"
                enum = ToggleNovelAct.ON if flag == "on" else ToggleNovelAct.OFF
                msg = f"{novel_code}번 소설의 {stat_name_kr}{suffix} {act}했어요."
                logger.info(msg)
                return enum
            case "login":
                msg = f"{stat_name_kr} 설정을 위해서는 로그인이 필요해요."
                logger.error(NotLoggedInError(msg))
                return ToggleNovelAct.LOGIN
            case _:
                raise ReqNovelError(toggle_novel_act, f"{stat_name_kr} 설정 실패")

    stat_name_en, stat_name_kr = stat_names

    response: Response = fetch_stat(stat_name_en, novel_code)
    
    flag_li, stats = parse_response(response)

    from func.common import suffix_from_words
    suffix: str = suffix_from_words(stat_name_kr, "을")

    # 상태 코드 정의
    class ToggleNovelAct(IntEnum):
        ON = 1
        OFF = 2
        LOGIN = 3

    return log_result_and_return_flag(flag_li[0]), stats


def req_data_from_params(csrf_token: str, novel_code: str):
    if csrf_token:
        return {"novel_no": novel_code, "csrf": csrf_token}
    err = NoValueError("CSRF 문자열을 입력받지 못했어요.")
    raise log_and_return_error(err)


def novel_gen_from_mem(log_kind: int, novel_code: Optional[str] = None) -> tuple[Novel, int]:
    """ 회원의 선호작 중 특정 소설 객체를 반환하는 함수

    Args:
        log_kind (int): 로그인 유형 (0은 비 로그인, 1은 일반 계정, 2는 구독 계정)
        novel_code (Optional[str], optional): 소설 번호.
            - 기본값은 None으로, 이 경우 가장 최근 소설을 반환합니다.

    Returns:
        tuple[Novel, int]: 소설 객체와 선호작 수
    
    Raises:
        ValueError: 선호작이 없거나 잘못된 선호작 수량일 때 발생
        NoValueError: CSRF 문자열을 환경 변수에서 찾을 수 없을 때 발생
        NotLoggedInError: 로그인 필요 시 발생
        ReqNovelError: 요청 소설 작업 중 오류 발생 시
        StopIteration: 선호작이 없을 때 발생
    
    Todo:
        - 예외 처리 개선: 각 예외에 대한 구체적인 메시지와 로그
        - 매개변수 처리: novel_code가 None일 때의 처리 로직 개선
        - 타입 힌트 추가: 함수 매개변수와 반환값에 대한 타입 힌트 추가
        - 문서화: 함수와 매개변수에 대한 자세한 설명 추가
        - 테스트 케이스 작성: 각 함수에 대한 단위 테스트 케이스 작성
        - 코드 스타일 개선: PEP 8 스타일 가이드에 맞게 코드 정리
        - 성능 최적화: 소설 정보 요청 및 파싱 과정에서의 성능 최적화
        - 예외 처리: JSON 파싱 오류, 요청 실패 등의 예외 처리 개선
        - 로깅: 각 단계에서의 로깅 추가 및 개선
        - 타입 안정성: Optional 타입을 사용하는 부분에서의 타입 안정성 확보
        - 코드 중복 제거: novel_dic_gen_from_mem와 novel_dic_li_from_mem 함수의 중복 코드 제거
        - 함수 이름 개선: 함수 이름을 더 명확하게 변경
        - 코드 리팩토링: 전체적인 코드 구조 개선 및 리팩토링
    """
    def find_novel(num: int, code: str) -> tuple[Novel, int]:
        """ 회원의 선호작 중 특정 소설 객체를 반환하는 함수

        Args:
            num (int): 회원 번호
            code (str): 소설 번호

        Raises:
            ValueError: 선호작이 없거나 잘못된 선호작 수량일 때 발생

        Returns:
            tuple[Novel, int]: 소설 객체와 선호작 수
        """
        cnt, dic_gen = novel_dic_gen_from_mem(num)
        novel_gen = (novel_from_dic(dic, num)
                     for num, dic
                     in enumerate(dic_gen))
        return next(novel_gen), cnt
    
    def get_any_novel(num: int) -> tuple[Novel, int]:
        """ 회원의 선호작 중 가장 최근 소설 객체를 반환하는 함수

        Args:
            num (int): 회원 번호

        Raises:
            ValueError: 선호작이 없거나 잘못된 선호작 수량일 때 발생
        
        Returns:
            tuple[Novel, int]: 소설 객체와 선호작 수
        """
        cnt, dic_li = novel_dic_li_from_mem(num)
        return novel_from_dic(dic_li[-1], 0), cnt
    
    mem_no: int = load_mem_no_from_env(log_kind)
    novel_obj, novel_cnt = (
        find_novel(mem_no, novel_code)
    ) if novel_code else get_any_novel(mem_no)
    
    if not novel_obj:
        raise ValueError("소설 객체를 생성하지 못했어요.")
    return novel_obj, novel_cnt


def novel_dic_gen_from_mem(mem_no: int, novel_cnt: int = -1):
    novel_dic_cnt, novel_dic_li = novel_dic_li_from_mem(mem_no)
    if novel_cnt != -1:
        assert novel_dic_cnt == novel_cnt
    novel_dic_gen = (dic for dic in novel_dic_li)
    return len(novel_dic_li), novel_dic_gen


def novel_dic_li_from_mem(mem_no: int) -> tuple[int, list[dict[str, Optional[int|str]]]]:
    """회원의 선호작 정보를 서버에 요청하고 파싱한 응답을 반환하는 함수

    :param mem_no: 회원 번호
    :return: 선호작 수, 소설 정보 목록들
    """
    def validate_novel_count(cnt: int) -> int:
        """ 선호작 수량을 검증하는 함수

        Args:
            cnt (int): 선호작 수량

        Returns:
            int: 검증된 선호작 수량

        Raises:
            ValueError: 선호작이 없거나 잘못된 선호작 수량일 때 발생
        """
        if cnt == 0:
            raise log_and_return_error(ValueError("선호작이 없어요."))
        if cnt != 1:
            raise log_and_return_error(ValueError("잘못된 선호작 수량"))
        return cnt

    from src.func.crawl import fav_novel_json_from_mem
    from json import loads
    # {'novel': [{ ... }], 'allCount': 2}
    res_dic: dict[str, Any] = loads(fav_novel_json_from_mem(mem_no))
    result_dic: dict[str, Any] = res_dic["result"]
    return validate_novel_count(result_dic["allCount"]), result_dic["novel"]


def novel_from_dic(novel_dic: dict[str, Optional[int|str]], novel_dic_no: int) -> Novel:
    def fetch_stat(act_type: int) -> int:
        """소설 알람 또는 선호작 수를 가져오는 함수.

        Args:
            act_type (int): 1은 알람, 2는 선호작

        Returns:
            int: 소설 알람 또는 선호작 수

        Raises:
            AssertionError: 로그인 필요 시 발생

        Example:
            >>> fetch_stat(1)
            5 # 알람 수
            >>> fetch_stat(2)
            10 # 선호작 수
        """
        success, stats = pick_novel_act(novel_code, act_type, 1)
        assert success == 3
        return stats

    novel_code: str = str(novel_dic["novel_no"])

    novel_dic["count_alarm"] = fetch_stat(1) # 1: 알람
    novel_dic["count_like"] = fetch_stat(2)  # 2: 선호작

    logger.info(f"{novel_dic_no + 1}번째 소설로 Novel 객체를 생성했어요.")
    return Novel(novel_dic)
