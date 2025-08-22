"""소설 알람, 선호작 설정/해제 관련 코드"""

from enum import IntEnum
from logging import getLogger
from typing import cast, Any, Optional

from exceptions import NoValueError, NotLoggedInError, ReqNovelError
from func.common import load_mem_no_from_env
from func.crawl import abs_url_from_rel_url, res_from_post_req
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
    set_alarm: bool = (novel_act == 1)
    set_like: bool = (novel_act == 2)
    do_login: bool = (log_kind != 0)
    if set_alarm:
        return toggle_novel_alarm(do_login, novel_code)
    elif set_like and do_login:
        return toggle_novel_like(novel_code)
    else:
        err_msg = "구현되지 않은 설정 번호"
        raise log_and_return_error(NotImplementedError(err_msg))


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
    stat_name_en, stat_name_kr = stat_names
    rel_url: str = "/proc/novel_" + stat_name_en
    abs_url: str = abs_url_from_rel_url(rel_url)

    from dotenv import dotenv_values
    config = dotenv_values()
    csrf_token: Optional[str] = config.get("CSRF_SUB")
    if not csrf_token:
        err_msg = "CSRF 문자열을 환경 변수에서 찾을 수 없어요."
        raise log_and_return_error(NoValueError(err_msg))
    req_data: dict = req_data_from_params(csrf_token, novel_code)

    from requests import Response
    res: Response = res_from_post_req(abs_url, req_data)
    from src.exceptions import ParseResError
    try:
        # {'status': '200', 'errmsg': '', {'novel': [{ ... }], 'allCount': 2}}
        flag_li: list[str] = res.text.split("|")
        stats = int(flag_li[1])

    except AttributeError as ae:
        raise ParseResError("[오류]", ae)
    except IndexError as ie:
        raise ParseResError("[오류]", ie)
    except Exception as err:
        raise ReqNovelError("[오류]", err)

    from func.common import suffix_from_words
    suffix: str = suffix_from_words(stat_name_kr, "을")

    # 상태 코드 정의
    class ToggleNovelAct(IntEnum):
        ON = 1
        OFF = 2
        LOGIN = 3

    msg: str # to avoid mypy error: no-redef
    if flag_li[0] == "on":  # on|1896||0
        msg = f"{novel_code}번 소설의 {stat_name_kr}{suffix} 등록했어요."
        logger.info(msg)
        return ToggleNovelAct.ON, stats
    elif flag_li[0] == "off":  # off|1895||
        msg = f"{novel_code}번 소설의 {stat_name_kr}{suffix} 해제했어요."
        logger.info(msg)
        return ToggleNovelAct.OFF, stats
    elif flag_li[0] == "login":
        le = NotLoggedInError(f"{stat_name_kr} 설정을 위해서는 로그인이 필요해요.")
        logger.error(le)
        return ToggleNovelAct.LOGIN, stats
    else:
        raise ReqNovelError(toggle_novel_act, f"{stat_name_kr} 설정 실패")


def req_data_from_params(csrf_token: str, novel_code: str):
    if csrf_token:
        req_data_dic: dict = {"novel_no": novel_code, "csrf": csrf_token, }
        return req_data_dic
    else:
        err_msg = "CSRF 문자열을 입력받지 못했어요."
        raise log_and_return_error(NoValueError(err_msg))


def novel_gen_from_mem(log_kind: int, novel_code: Optional[str] = None) -> tuple[Novel, int]:
    """좋아요 목록에서 소설을 설정하는 로직

    :param novel_code: 소설 번호
    :param log_kind: 로그인 유형 (1은 일반 계정, 2는 구독 계정)
    :return: Novel 객체 제너레이터, 선호작 수
    """
    mem_no: int = load_mem_no_from_env(log_kind)
    novel_obj: Optional[Novel] = None
    if novel_code:
        novel_cnt, novel_dic_gen = novel_dic_gen_from_mem(mem_no)
        novel_gen = novel_gen_from_dic_gen(novel_dic_gen)
        for novel_obj in novel_gen:
            pass
    else:
        novel_cnt, novel_dic_li = novel_dic_li_from_mem(mem_no)
        if novel_cnt != 1:
            err_msg = "잘못된 선호작 수량"
            raise log_and_return_error(ValueError(err_msg))
        novel_dic: dict[str, Optional[int|str]] = novel_dic_li[-1]
        novel_obj = novel_from_dic(novel_dic, 0)
    
    if not novel_obj:
        err_msg = "소설 객체를 생성하지 못했어요."
        raise ValueError(err_msg)
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
    from src.func.crawl import fav_novel_json_from_mem
    res_json = fav_novel_json_from_mem(mem_no)

    from json import loads as dic_from_json
    from json import JSONDecodeError
    try:
        res_dic: dict[str, Any] = dic_from_json(res_json)
        """{'status': '200', 'errmsg': '', {'novel': [{ ... }], 'allCount': 2}}"""
    except JSONDecodeError as je:
        je.add_note("JSON 파싱 오류")
        raise log_and_return_error(je)
    # {'novel': [{ ... }], 'allCount': 2}
    result_dic: dict[str, int|list[dict[str, Optional[int|str]]]] = res_dic["result"]
    novel_cnt = result_dic["allCount"]
    novel_cnt = cast(int, novel_cnt)
    novel_dic_li = result_dic["novel"]
    novel_dic_li = cast(list[dict[str, Optional[int|str]]], novel_dic_li)
    return novel_cnt, novel_dic_li


def novel_gen_from_dic_gen(novel_dic_gen):
    """소설 정보가 담긴 Dict를 Novel 객체로 변환하는 함수

    :param novel_dic_gen: 소설 정보가 담긴 Dict 목록
    :return: Novel 객체
    """
    novels: list[Novel] = []
    try:
        for novel_dic_no, novel_dic in enumerate(novel_dic_gen):
            novel: Novel = novel_from_dic(novel_dic, novel_dic_no)
            novels.append(novel)
            yield from novels
    # 선호작 X
    except StopIteration as si:
        si.add_note("선호작이 없습니다.")
        raise log_and_return_error(si)


def novel_from_dic(novel_dic: dict[str, Optional[int|str]], novel_dic_no: int) -> Novel:
    novel_code: str = str(novel_dic["novel_no"])
    act_alarm: int = 1
    success, alarms = pick_novel_act(novel_code, act_alarm, 1)
    assert success == 3

    act_like: int = 2
    success, likes = pick_novel_act(novel_code, act_like, 1)
    assert success == 3

    novel_dic["count_alarm"] = alarms
    novel_dic["count_like"] = likes

    logger.info(f"{novel_dic_no + 1}번째 소설로 Novel 객체를 생성했어요.")
    novel = Novel(novel_dic)
    return novel
