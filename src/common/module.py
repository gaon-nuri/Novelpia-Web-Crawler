from contextlib import contextmanager
from json import JSONDecodeError, loads
from pathlib import Path

from bs4 import BeautifulSoup

# Windows Chrome User-Agent String
ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'


@contextmanager
def get_env_var_w_error(env_var_name: str):
    """입력받은 이름의 환경 변수를 찾고 값과 오류를 반환하는 제너레이터 함수

    :param env_var_name: 환경 변수의 이름
    :return: 환경 변수의 값과 오류 (각각 없으면 None)
    """
    try:
        from os import environ
        env_var: str = environ[env_var_name]
    except KeyError as ke:
        from src.common.userIO import print_under_new_line
        print_under_new_line(f"예외 발생: {ke = }")
        print(f"환경 변수 '{env_var_name}' 을 찾지 못했어요.")
        yield None, ke
    else:
        yield env_var, None


def add_login_key(headers: dict[str: str]) -> tuple[str, dict]:
    """입력받은 헤더에 로그인 키를 추가해서 반환하는 함수

    :param headers: 로그인 키를 추가할 헤더
    :return: 추가한 로그인 키, 새 헤더
    """
    with get_env_var_w_error("LOGINKEY") as (login_key, ke):
        if login_key is None:
            from src.common.userIO import print_under_new_line
            print_under_new_line("로그인 없이 진행할게요.")
        else:
            cookie: str = "LOGINKEY=" + login_key
            headers["Cookie"] = cookie

        return login_key, headers


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


def assure_path_exists(path_to_assure: Path) -> None:
    """파일/폴더의 상위 폴더가 다 있으면 넘어가고 없으면 만드는 함수.

    :param path_to_assure: 상위 폴더를 확보할 파일/폴더의 경로
    """
    parent_paths: [Path] = path_to_assure.parents
    for i, parent_path in enumerate(parent_paths):

        # 상위 폴더 유무 확인
        if parent_path.exists():
            print()

            # 상위 폴더 有, 작업 불필요
            if i == 0:
                print("[알림]", parent_path, "폴더가 이미 있으니 그대로 쓸게요.")

            # 상위 폴더 有, 재귀(?)적으로 하위 폴더 생성
            for j in range(i):
                child_path: Path = parent_paths[range(i)[i - 1 - j]]
                child_path.mkdir()
                print("[알림]", child_path, "폴더를 생성했어요.")
            break


@contextmanager
def get_novel_main_w_error(url: str):
    """서버에 소설의 메인 페이지를 요청하고, HTML 응답을 반환하는 함수

    :param url: 요청 URL
    :return: HTML 응답, 접속 실패 시 None
    """
    headers: dict = {'User-Agent': ua}
    npd_cookie, headers = add_npd_cookie(headers)

    from requests.exceptions import ConnectionError
    from urllib3.exceptions import MaxRetryError

    # 소설 메인 페이지의 HTML 문서를 요청
    try:
        from requests import get
        res = get(url=url, headers=headers)  # res: <Response [200]>

    # 연결 실패
    except* ConnectionError as err_group:
        ce: ConnectionError = err_group.exceptions[0]
        mre: MaxRetryError = ce.args[0]
        err_msg: str = mre.reason.args[0]

        start_index: int = err_msg.find("Failed")
        end_index: int = err_msg.find("Errno")

        re = RuntimeError(err_msg[start_index: end_index - 3])

        yield None, re
        # raise re from err_group

    # 성공
    else:
        html: str = res.text
        # assert html != "", "빈 HTML"
        yield html, None


def get_postposition(kr_word: str, postposition: str) -> str:
    """입력받은 한글 단어의 종성에 맞는 조사의 이형태를 반환하는 함수

    :param kr_word: 한글 문자열
    :param postposition: 원래 조사
    :return: 모음 - True / 모음 외 나머지 - False
    """
    ends_with_vowel: bool = ((ord(kr_word[-1]) - 0xAC00) % 28 == 0)
    """
    한글 글자 인덱스 = (초성 인덱스 * 21 + 중성 인덱스) * 28 + 종성 인덱스 + 0xAC00\n
    참고: https://en.wikipedia.org/wiki/Korean_language_and_computers#Hangul_in_Unicode
    """
    v_post: tuple = ("가", "를", "는", "야")
    c_post: tuple = ("이", "을", "은", "아")

    for v, c in zip(v_post, c_post):
        if postposition in (v, c):
            if ends_with_vowel:
                return v
            return c


@contextmanager
def load_json_w_error(res_json: str):
    try:
        dic: dict = loads(res_json)
    except JSONDecodeError as je:
        from src.common.userIO import print_under_new_line
        print_under_new_line("예외 발생: " + f"{je = }")
        je.add_note("응답 JSON: " + res_json)
        yield None, je
    else:
        yield dic, None


@contextmanager
def extract_alert_msg_w_error(soup: BeautifulSoup):
    """소설 메인 페이지에서 알림 창의 오류 메시지를 추출하는 함수

    :param soup: BeautifulSoup 객체
    :return: 오류 메시지
    """
    from src.common.userIO import print_under_new_line
    try:
        msg_tag = soup.select_one("#alert_modal .mg-b-5")

    # 알림 창이 나오지 않음
    except AttributeError as err:
        print_under_new_line("예외 발생:",  f"{err = }")
        yield None, err

    # 알림 추출
    else:
        alert_msg: str = msg_tag.text
        """
        0: 잘못된 소설 번호 입니다. (제목, 줄거리 無)
        2: 삭제된 소설 입니다. (제목 有, 줄거리 無)
        200000: 잘못된 접근입니다. (제목 有, 줄거리 無)
        - 연습등록작품은 작가만 열람이 가능
        - 공지 참고: <2021년 01월 13일 - 노벨피아 업데이트 변경사항(https://novelpia.com/notice/20/view_4149/)>
        """
        if alert_msg == "잘못된 소설 번호 입니다.":
            pass

        yield alert_msg, None


@contextmanager
def opened_x_error(file_name: Path, mode: str = "xt", encoding: str = "utf-8"):
    assert mode.find("b") == -1
    assure_path_exists(file_name)
    from src.common.userIO import print_under_new_line
    try:
        f = open(file_name, mode)

    # 기존 텍스트 파일을 "xt" 모드로 열 때
    except FileExistsError as err:
        from time import ctime
        mtime: str = ctime(file_name.stat().st_mtime)

        # 덮어쓸 것인지 질문
        print_under_new_line("예외 발생:", f"{err = }")
        question: str = "[확인] " + mtime + "에 수정된 파일이 있어요. 덮어 쓸까요?"

        from src.common.userIO import input_permission
        asked_overwrite, can_overwrite = input_permission(question)

        # 덮어 쓰기
        if asked_overwrite and can_overwrite:
            print_under_new_line("[알림]", file_name, "파일에 덮어 썼어요.")  # 기존 파일 有, 덮어쓰기
            with opened_x_error(file_name, "wt", encoding) as (f, err):
                yield f, err

        # 기존 파일 유지
        else:
            print_under_new_line("[알림] 기존 파일이 있으니 파일 생성은 건너 뛸게요.")
            with opened_x_error(file_name, "rt", encoding) as (f, err):
                yield f, err

    except OSError as err:
        yield None, err

    else:
        print_under_new_line("[알림]", file_name, "을 열었어요.")
        try:
            yield f, None
        finally:
            f.close()


if __name__ == "__main__":
    import doctest
    doctest.testmod()
