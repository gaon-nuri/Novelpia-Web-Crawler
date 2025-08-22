# novel_crawler/crawl.py
"""웹 크롤러"""
from logging import error, getLogger, info, warning
from random import choice
from typing import Generator
from urllib.parse import urljoin

from fake_useragent import FakeUserAgent
from requests import Response, get, post
from requests.exceptions import (ConnectionError, HTTPError, RequestException, Timeout)
from tenacity import (retry, retry_if_exception_type, stop_after_attempt, wait_exponential)

from src.const.const import BASE_URL, LOG_KEY_NAME
from src.exceptions import CrawlNovelError, ReqNovelError

logger = getLogger(__name__)


def init_default_header() -> dict[str:str]:
    rand_header: dict[str:str] = pick_rand_header()
    default_header = rand_header
    # default_header = add_npd_cookie(rand_header)
    return default_header


def pick_rand_header() -> dict[str:str]:
    """무작위로 사용자 에이전트를 선택하여 요청 헤더를 만드는 함수.
    이는 서버가 봇을 차단하는 것을 방지할 수 있습니다.

    :return: 무작위 헤더
    """
    from fake_useragent import UserAgent
    ua: FakeUserAgent = UserAgent()
    ua_option_tu: tuple = (ua.chrome, ua.edge, ua.firefox)
    rand_ua: str = choice(ua_option_tu)
    rand_header: dict[str:str] = {'User-Agent': rand_ua}
    return rand_header


def is_valid_url(unknown_url) -> None:
    from requests import Response
    res: Response = get(unknown_url, headers=init_default_header())
    try:
        domain: str = res.headers.get("Access-Control-Allow-Origin")
    except KeyError as ke:
        err_msg: str = "유효하지 않은 URL"
        logger.error(ke.add_note(err_msg))
        raise
    from ..const.const import BASE_URL
    if domain != BASE_URL:
        err_msg: str = "잘못된 URL 도메인"
        ve = ValueError(err_msg)
        logger.error(ve)
        raise ve


def delayed_func_from_range(func, delays=(1, 3)):
    """요청 간에 지연 시간을 두어 서버 부하를 줄이는 함수

    :param func:
    :param delays: 요청 간 지연 시간
    :return: HTML
    """
    # 작업 후 지연
    from random import uniform
    rand_delay = uniform(*delays)
    info(f"{rand_delay:.2f}초 대기합니다.")
    from time import sleep
    sleep(rand_delay)
    return func


# @delayed_func_from_range
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=1, max=10),
    retry=retry_if_exception_type((ConnectionError, Timeout, CrawlNovelError))
)
def fetch_page_from_url(url):
    """
    URL에서 페이지를 가져오는 함수. 재시도 로직과 오류 처리를 포함.

    Args:
        url (str): 가져올 URL.

    Returns:
        str: 페이지의 HTML 콘텐츠.

    Raises:
        CrawlNovelError: 크롤링 중 발생한 특정 오류.
    """
    not_found_code: int = 404
    forbidden_code: int = 403
    try:
        response = get(url, headers=init_default_header(), timeout=10)
        response.raise_for_status()
        return response.text
    except HTTPError as e:
        if e.response.status_code == not_found_code:
            error(f"{not_found_code} 오류: {url} 페이지를 찾을 수 없습니다.")
            raise CrawlNovelError(f"{not_found_code} Not Found") from e
        elif e.response.status_code == forbidden_code:
            error(f"{forbidden_code} 오류: 접근이 금지되었습니다. {url}")
            raise CrawlNovelError(f"{forbidden_code} Forbidden") from e
        else:
            error(f"HTTP 오류 발생: {e.response.status_code} - {url}")
            raise CrawlNovelError(f"HTTP Error {e.response.status_code}") from e
    except Timeout:
        warning(f"타임아웃 발생: {url}")
        raise
    except ConnectionError:
        warning(f"연결 오류 발생: {url}")
        raise
    except RequestException as e:
        error(f"요청 오류 발생: {e}")
        raise CrawlNovelError("Request Exception") from e


def crawl_novel_dic_from_code(novel_code):
    """
    소설을 크롤링하고 데이터를 반환하는 함수.

    Args:
        novel_code (str): 소설 코드.

    Return:
        novel (Novel): 소설 클래스 객체

    Raises:
        CrawlNovelError: 크롤링 중 발생한 특정 오류.
    """
    rel_url: str = "/novel/" + novel_code
    abs_url: str = abs_url_from_rel_url(rel_url)
    try:
        page: str = fetch_page_from_url(abs_url)
        # page: str = delayed_func_from_range(rel_url)
        from src.parsers import novel_obj_from_page
        novel = novel_obj_from_page(page)
        info(f"소설 '{novel.title}'을 성공적으로 크롤링했습니다.")
        return novel
    except CrawlNovelError as ne:
        error(f"소설 크롤링 중 오류 발생: {ne}")
    except Exception as e:
        error(f"예상치 못한 오류 발생: {e}")
    raise


def fav_novel_json_from_mem(member_no):
    rel_url: str = "/proc/user"
    abs_url: str = abs_url_from_rel_url(rel_url)
    data_dic: dict = {
        "mode": "get_member_favorite_novel",
        "mem_no": str(member_no),
        "paging[rowCount]": "1000",
        "paging[curPage]": "1",
        "paging[order]": "date",
        "paging[sort][date]": "1",
    }
    sub_mem: int = 1
    res: Response = res_from_post_req(abs_url, data_dic, sub_mem)
    res_json: str = res.text
    return res_json


def abs_url_from_rel_url(rel_url: str):
    """노벨피아 內 상대 URL로 절대 URL을 완성하여 반환하는 함수

    :param rel_url: 상대 URL
    :return: 절대 URL
    """
    from urllib.parse import urljoin
    from src.const.const import BASE_URL

    abs_url: str = urljoin(BASE_URL, rel_url)
    return abs_url


def res_from_post_req(url: str, data: dict = None, log_kind: int = 2) -> Response:
    """POST 요청을 보내는 함수를 반환하는 외부 함수

    :param url: 요청 URL
    :param data: 전송할 데이터
    :param log_kind: 로그인 유형 (1은 일반 계정, 2는 구독 계정)
    :return: POST 요청을 보내는 함수
    """
    plus_mem: int = 2
    default_header: dict[str:str] = init_default_header()
    if log_kind == 1:
        log_key, log_header = log_header_from_default_header(default_header)
    elif log_kind == plus_mem:
        log_key, log_header = log_header_from_default_header(default_header, True)
    else:
        ve = ValueError("잘못된 log_kind 값")
        logger.error(ve)
        raise ve
    assert log_key
    from requests import post
    res: Response = post(url, data, headers=log_header)
    return res


def fetch_ep_view_gen_from_code_gen(novel_code: str, ep_code_gen: Generator, ep_cnt: int):
    """입력받은 소설의 회차들의 조회수를 응답받아 반환하는 함수

    :param novel_code: 소설 번호
    :param ep_code_gen: 회차 번호 제너레이터
    :param ep_cnt: 회차의 수
    :return: 조회수 목록
    """
    rel_url: str = "/proc/novel"
    abs_url: str = urljoin(BASE_URL, rel_url)
    data_dic: dict = {
        "cmd": "get_episode_cnt_view",
        "episode_arr[]": ["episode_cnt_view novel_cnt_view_"] * ep_cnt,
        "novel_no": novel_code,
    }
    for ep_no, ep_code in enumerate(ep_code_gen):
        data_dic["episode_arr[]"][ep_no] += ep_code
    res = post(abs_url, data_dic, headers=init_default_header())
    view_cnt_json = res.text
    """{
        "status": 200,  # 유효한 요청
        "rel_url": "",
        "errmsg": "",
        "list": [{"episode_num": 3, "cnt_view": "1,057"}, ...]
    }"""
    ep_view_gen: Generator[int] = ep_view_gen_from_json(view_cnt_json)
    yield from ep_view_gen


def ep_view_gen_from_json(view_cnt_json):
    from src.func.common import load_dic_from_json
    res_dic = load_dic_from_json(view_cnt_json)
    view_cnt_dics = res_dic["list"]
    view_cnts: list[int] = []
    for ep_no, dic in enumerate(view_cnt_dics):  # dic: {'cnt_view': '1', 'episode_no': 12606}
        view_cnt = int(dic["cnt_view"].replace(",", ""))
        view_cnts.append(view_cnt)
    # 잘못된 요청 데이터 (ep_code_gen > episode_arr[], novel_code > novel_no)
    if not view_cnts:
        err_msg = "조회수를 받지 못했어요"
        from src.exceptions import ParseResError
        pre = ParseResError(err_msg)
        logger.error(pre)
        raise pre
    yield from view_cnts


def fetch_ep_li_pg_from_code(novel_code: str, sort: str = "DOWN", page: int = 1,
                             do_plus_login: bool = False) -> str:
    """서버에 회차 목록을 요청하고, 성공 시 HTML 응답을 반환하는 함수

    :param novel_code: 소설 번호
    :param sort: "DOWN", 첫화부터 / "UP", 최신화부터
    :param page: 요청할 페이지 번호
    :param do_plus_login: 로그인 키 사용 여부 (링크 추출용)
    :return: 게시일 순으로 정렬된 회차 목록의 한 페이지 (HTML)
    """
    rel_url: str = "/proc/episode_list"
    abs_url: str = urljoin(BASE_URL, rel_url)
    form_data: dict = {
        "novel_no": novel_code,
        "sort": sort,
        "page": page - 1
    }  # 1페이지 -> page = 0, ...
    rand_header: dict[str:str] = init_default_header()
    if do_plus_login:
        log_key, header = log_header_from_default_header(rand_header, True)
        assert log_key
    else:
        header: dict = rand_header
    res = post(abs_url, form_data, headers=header)  # res: <Response [200]>
    ep_list_page: str = res.text
    return ep_list_page


def mybook_pg_from_url(url: str):
    """서버에 내 서재 페이지를 요청하고, HTML 응답을 반환하는 함수

    :param url: 요청 URL
    :return: HTML 응답, 접속 실패 시 None
    """
    # 구독 계정으로 로그인
    rand_header: dict[str:str] = init_default_header()
    npd_cookie, headers = log_header_from_default_header(rand_header, True)

    from requests.exceptions import ConnectionError
    # 소설 메인 페이지의 HTML 문서를 요청
    try:
        from requests import get
        res = get(url=url, headers=headers)  # res: <Response [200]>
        html: str = res.text
        assert html
        return html
    except* ConnectionError as err_group:
        from ..func.common import parse_err_msg_from_err
        err_msg: str = parse_err_msg_from_err(err_group)
        re = ReqNovelError(err_msg)
        logger.error(re)
        raise re


def log_header_from_default_header(headers: dict[str: str], plus: bool = False) -> tuple[str, dict]:
    """입력받은 헤더에 로그인 키를 추가해서 반환하는 함수

    :param headers: 로그인 키를 추가할 헤더
    :param plus: 구독 계정 사용 여부
    :return: 추가한 로그인 키, 새 헤더
    """
    env_var_name: str = LOG_KEY_NAME
    if plus:
        env_var_name += "_PLUS"
    else:
        env_var_name += "_SUB"
    from src.func.common import load_env_var_from_name
    log_key = load_env_var_from_name(env_var_name)
    cookie: str = "LOGINKEY=" + log_key
    headers["Cookie"] = cookie
    return log_key, headers


def add_npd_cookie(headers: dict[str: str]) -> tuple[str, dict]:
    """입력받은 헤더에 일일 NPD Cookie를 추가해서 반환하는 함수

    :param headers: Cookie 를 추가할 헤더
    :return: 추가한 Cookie, 새 헤더
    """
    from datetime import date
    day_str: str = date.today().strftime("%d%m1")  # 8월 15일 -> 15081
    cookie: str = "NPD" + day_str + "=meta;"
    headers["Cookie"] = cookie
    return cookie, headers


if __name__ == "__main__":
    sample_novel_codes = ["1", "2", "999999"]  # 예시 소설 코드들
    for code in sample_novel_codes:
        novel_data = crawl_novel_dic_from_code(code)
        if novel_data:
            print(f"크롤링한 소설 데이터: {novel_data}")
        else:
            print(f"{code}번 소설 데이터를 가져올 수 없습니다.")
