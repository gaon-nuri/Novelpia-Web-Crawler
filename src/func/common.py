"""공통 함수들

"""
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from src.const.const import DEFAULT_TIME, LOGIN_KEY_NAME, PARSER
from src.func.userIO import print_under_new_line


class UserMeta(type):
    """아무 것도 하지 않는 사용자 메타 클래스."""
    pass


class Descriptor:
    """디스크립터 클래스를 데코레이터로 사용"""
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, owner):
        from functools import partial

        return partial(self.func, instance)


class DescriptorND:
    """비데이터 (함수) 디스크립터 클래스"""
    def __init__(self, func):
        self.func = func

    def __set_name__(self, owner, name):
        self._name = "_" + name

    def __get__(self, instance, owner):
        print("get")
        from functools import partial

        return partial(self.func, instance)
        # def inner(*args, **kwargs):
        #     return self._func(*args, **kwargs)
        # return inner


class MutableAttribute:
    """데이터 (변경 가능 속성) 디스크립터 클래스"""
    def __init__(self, value=None):
        self.value = value

    def __set_name__(self, owner, name):
        self._name = "_" + name

    def __get__(self, instance, owner):
        print("get")
        if self._name in instance.__dict__:
            return instance.__dict__[self._name]
        else:
            return self.value

    def __set__(self, instance, value):
        print("set")
        instance.__dict__[self._name] = value

    def __delete__(self, instance):
        print("del")
        del self.value


class ImmutableAttribute:
    """데이터 (변경 불가능 속성) 디스크립터 클래스"""

    def __init__(self, func):
        self.func = func

    def __get__(self, instance, owner):
        print("get")
        return self.func(instance)

    def __set__(self, instance, value):
        print("set")
        raise AttributeError("갱신이 불가합니다.")

    def __delete__(self, instance):
        print("del")
        raise AttributeError("삭제가 불가합니다.")


# noinspection PyMissingOrEmptyDocstring
class Page(metaclass=UserMeta):
    """노벨피아 웹 페이지 클래스.

    :var _title: 제목
    :var _code: 고유 번호
    :var _url: URL
    :var _ctime: 공개 시각
    :var _mtime: 갱신 시각
    :var _got_time: 크롤링 시각
    :var _count_good: 추천 수
    :var _count_view: 조회 수
    """
    __slots__ = (
        "_title",
        "_code",
        "_url",
        "_ctime",
        "_mtime",
        "_got_time",
        "_count_good",
        "_count_view"
    )

    def __init__(self,
                 title: str = '',
                 code: str = '',
                 url: str = '',
                 ctime: str = DEFAULT_TIME,
                 mtime: str = DEFAULT_TIME,
                 count_good: int = -1,
                 count_view: int = -1
                 ):
        from datetime import datetime

        self._got_time = datetime.today().isoformat(timespec='minutes')
        self._title = title
        self._code = code
        self._url = url
        self._ctime = ctime
        self._mtime = mtime
        self._count_good = count_good
        self._count_view = count_view

    def __str__(self):
        page_info_dic: dict = {}
        for key in self.__slots__:
            page_info_dic[key] = self.__getattribute__(key)
        return str(page_info_dic)

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, title: str):
        if isinstance(title, str) and title.isprintable():
            self._title = title

    @property
    def code(self) -> str:
        return self._code

    @code.setter
    def code(self, code: str):
        if all([isinstance(code, str), code.isnumeric(), int(code) > 0]):
            self._code = code
        else:
            print_under_new_line(f"{self}.code를 {code}(으)로 바꿀 수 없어요.")
            print("소설 번호를 자연수로 설정해 주세요.")

    @property
    def url(self) -> str:
        return self._url

    @url.setter
    def url(self, url: str):
        from requests import get, Response
        from src.const.const import BASIC_HEADERS

        res: Response = get(url, headers=BASIC_HEADERS)

        try:
            domain: str = res.headers.get("Access-Control-Allow-Origin")
        except KeyError as ke:
            print_under_new_line("[오류]", f"{ke = }")
            print(f"{type(self)}.url을 {url}(으)로 바꿀 수 없어요.")
        else:
            from src.const.const import HOST

            if domain == HOST:
                self._url = url
            else:
                print(f"{type(self)}.url을 {url}(으)로 바꿀 수 없어요.")

    @property
    def ctime(self) -> str:
        return self._ctime

    @ctime.setter
    def ctime(self, up_date_s: str):
        try:
            datetime.fromisoformat(up_date_s)  # up_date_s: "2024-12-13"
        except TypeError as err:
            print_under_new_line("[오류]", f"{err = }")
            # raise
        else:
            self._ctime = up_date_s

    @property
    def got_time(self) -> str:
        return self._got_time

    @got_time.setter
    def got_time(self, now: datetime):
        self._got_time = now.isoformat(timespec="minutes")

    def pick_one_from(self, key: str, val: str, vals: frozenset):
        """입력 값이 목록에 들어 있으면 키의 값을 입력 값으로 설정하는 함수

        :param key: 클래스 번수 이름
        :param val: 클래스 변수 값
        :param vals: 목록
        """
        if val in vals:
            self.__setattr__(key, val)
        else:
            print_under_new_line(f"{self}.{key}를 {val}(으)로 바꿀 수 없어요.")
            print(*vals, "중에서 선택해 주세요.")

    def add_one_from(self, key: str, val: str, vals: frozenset):
        """입력 값이 목록에 들어 있으면 키의 값에 입력 값을 더하는 함수

        :param key: 클래스 번수 이름
        :param val: 클래스 변수 값
        :param vals: 목록
        """
        if val in vals:
            self_value = self.__getattribute__(key)
            assert isinstance(self_value, list)

            self.__setattr__(key, self_value.append(val))
        else:
            print_under_new_line(f"{self}.{key}에 {val}(을)를 추가할 수 없어요.")
            print(*vals, "중에서 선택해 주세요.")

    def set_signed_int(self, key: str, val: int):
        """입력 값이 양수이면 키의 값을 입력 값으로 설정하는 함수

        :param key: 클래스 변수 이름
        :param val: 클래스 변수 값
        """
        if val is None:
            self.__setattr__(key, -1)
        elif val >= 0:
            self.__setattr__(key, val)
        else:
            print_under_new_line(f"{self}.{key}를 {val}(으)로 바꿀 수 없어요.")
            print("0 이상의 정수로 설정해 주세요.")

    @property
    def count_good(self):
        return self._count_good

    @count_good.setter
    def count_good(self, count_good: int):
        self.set_signed_int("_count_good", count_good)

    @property
    def count_view(self):
        return self._count_view

    @count_view.setter
    def count_view(self, count_view: int):
        self.set_signed_int("_count_view", count_view)


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
        print_under_new_line("[오류]", f"{ke = }")
        print(f"[오류] 환경 변수 '{env_var_name}' 을 찾지 못했어요.")

        yield None, ke
    else:
        yield env_var, None


def add_login_key(headers: dict[str: str], plus: bool = False) -> tuple[str, dict]:
    """입력받은 헤더에 로그인 키를 추가해서 반환하는 함수

    :param headers: 로그인 키를 추가할 헤더
    :param plus: 구독 계정 사용 여부
    :return: 추가한 로그인 키, 새 헤더
    """
    env_var_name: str = LOGIN_KEY_NAME

    if plus:
        env_var_name += "_PLUS"

    with get_env_var_w_error(env_var_name) as (login_key, ke):
        if ke:
            print("로그인 없이 진행할게요.")
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
    from src.const.const import BASIC_HEADERS

    npd_cookie, headers = add_npd_cookie(BASIC_HEADERS)

    from requests.exceptions import ConnectionError
    from urllib3.exceptions import MaxRetryError
    from requests import get

    try:
        # 소설 메인 페이지의 HTML 문서를 요청
        res = get(url=url, headers=headers)  # res: <Response [200]>

    # 연결 실패
    except* ConnectionError as err_group:
        # 오류 메시지 추출
        ce: ConnectionError = err_group.exceptions[0]
        mre: MaxRetryError = ce.args[0]
        err_msg: str = mre.reason.args[0]

        start_index: int = err_msg.find("Failed")
        end_index: int = err_msg.find("Errno")

        ce = ConnectionError(err_msg[start_index: end_index - 3])

        yield None, ce
        # raise re from err_group

    # 성공
    else:
        html: str = res.text

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
    from src.const.const import POSTPOSITIONS_NAMED_TUPLE

    for v, c in zip(*POSTPOSITIONS_NAMED_TUPLE):
        if postposition in (v, c):
            if ends_with_vowel:
                return v
            return c


@contextmanager
def load_json_w_error(res_json: str):
    """입력받은 JSON을 dict로 가져오고 해당 dict와 오류 내역을 반환하는 함수

    :param res_json: 응답 JSON
    """
    from json import JSONDecodeError, loads

    try:
        dic: dict = loads(res_json)
    except JSONDecodeError as je:
        print_under_new_line("[오류]", f"{je = }")
        je.add_note("응답 JSON: " + res_json)

        yield None, je
    else:
        yield dic, None


@contextmanager
def extract_alert_msg_w_error(html: str):
    """소설 페이지에서 알림 창의 오류 메시지를 추출하는 함수

    :param html: 소설 페이지 HTML
    :return: 오류 메시지
    """
    from bs4 import BeautifulSoup as Soup

    soup = Soup(html, PARSER)
    try:
        from src.const.selector import NOVEL_ALERT_MSG_CSS

        msg_tag = soup.select_one(NOVEL_ALERT_MSG_CSS)

    # 알림 창이 나오지 않음
    except AttributeError as ae:
        ae.add_note(f"{soup.prettify() = }")
        print_under_new_line("[오류]", f"{ae = }")

        yield None, ae

    # 알림 추출
    else:
        try:
            alert_msg: str = msg_tag.text
            """
            * 잘못된 소설 번호 입니다. (제목, 줄거리 無)
            * 삭제된 소설 입니다. (제목 有, 줄거리 無)
            * 잘못된 접근입니다. (제목 有, 줄거리 無)
            * 본 작품은 연습작으로 등록되어 있습니다. (작가 본인만 열람 가능합니다)
            - 연습등록작품은 작가만 열람이 가능
            - 공지 참고: <2021년 01월 13일 - 노벨피아 업데이트 변경사항(https://novelpia.com/notice/20/view_4149/)>
            """
        # 메시지 無
        except AttributeError as ae:
            print_under_new_line("[오류]", f"{ae = }")
            print(f"{msg_tag = }")

            yield None, ae
        else:
            if alert_msg == "잘못된 소설 번호 입니다.":
                pass
            yield alert_msg, None


@contextmanager
def opened_x_error(file_path: Path, mode: str = "xt", encoding: str = "utf-8", skip: bool = False, overwrite: bool = False):
    """입력받은 대로 파일을 열고 파일과 오류 내역을 반환하는 함수

    :param file_path: 파일 경로
    :param mode: 파일 모드 (읽기, 쓰기, 붙이기, ..)
    :param encoding: 파일의 인코딩 (기본 UTF-8)
    :param skip: 동명의 파일 존재 시 건너뛸 지 여부
    :param overwrite: 덮어 쓰기 여부
    """
    assert mode.find("b") == -1
    assure_path_exists(file_path)

    try:
        f = open(file_path, mode, encoding='utf-8')

    # 기존 파일을 "xt" 모드로 열었음
    except FileExistsError as fe:
        from time import ctime

        # 파일 수정 시간 추출
        mtime: str = ctime(file_path.stat().st_mtime)
        asked_overwrite, can_overwrite = False, False

        # 덮어 쓸 지 질문
        if not skip:
            question: str = "[확인] " + mtime + "에 수정된 파일이 있어요. 덮어 쓸까요?"

            from .userIO import input_permission

            asked_overwrite, can_overwrite = input_permission(question)

        # 덮어 쓰기
        if overwrite or (asked_overwrite and can_overwrite):
            print_under_new_line("[알림]", file_path, "파일에 덮어 썼어요.")  # 기존 파일 有, 덮어쓰기
            with opened_x_error(file_path, "wt", encoding, True, True) as (f, fe_in):
                yield f, fe_in

        # 기존 파일 유지
        else:
            print_under_new_line("[알림] 이미 동명의 파일이 있어요.")
            yield None, fe

    # 그 외 파일 입출력 오류
    except OSError as err:
        yield None, err

    else:
        print_under_new_line("[알림]", file_path, "파일을 열었어요.")
        try:
            yield f, None
        finally:
            f.close()
            print("[알림]", file_path, "파일을 닫았어요.")
