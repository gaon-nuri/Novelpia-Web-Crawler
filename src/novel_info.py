"""소설 정보를 크롤링하는 코드"""
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Generator
from urllib.parse import urljoin

from bs4 import BeautifulSoup as Soup
from bs4.element import Tag
from bs4.filter import SoupStrainer as Strainer
from requests import post

from .const.const import BASIC_HEADERS, HOST, PARSER
from .func.common import Page
from .func.userIO import print_under_new_line


# noinspection PyMissingOrEmptyDocstring
class Novel(Page):
    """노벨피아 소설 정보 클래스.

    :var _writer_nick: 작가 닉네임
    :var _writer_mem_no: 작가 회원 번호
    :var _novel_age: 허용 독자 연령 (전연령/15금/19금)
    :var _novel_type: 연재 유형 (자유/PLUS)
    :var _novel_live: 연재 상태 (연재 중, 완결: 0, 연재지연: 1, 연재중단: 2 中 1)
    :var _up_status: 연재 상태 (연재 중, 완결, 삭제, 연습작품, 연재지연, 연재중단 中 1)
    :var _types: 유형
    :var _main_genre: 1차 분류 태그
    :var _tags: 해시 태그로 된 bulleted list
    :var _novel_story: 줄거리로 된 Markdown Callout
    :var _start_date: 연재 시작일
    :var _last_write_date: 최근 (예정) 연재일
    :var _reg_date: 소설 등록일
    :var _status_date: 노벨피아 서버 정보 갱신일
    :var _alarm: 일람 수
    :var _prefer: 선호 수
    :var _count_book: 회차 수
    :var _count_pick: 인생픽 순위
    :var _is_contest: 공모전 수상 경력
    :var _is_osmu: OSMU (탑툰 內 웹툰화 등) 경력
    """

    __slots__ = Page.__slots__ + (
        "_writer_nick",
        "_mem_no",
        "_up_status",
        "_main_genre",
        "_novel_genre",
        "_novel_type",
        "_novel_story",
        "_types",
        "_tags",
        "_start_date",
        "_last_view_date",
        "_last_write_date",
        "_reg_date",
        "_status_date",
        "_del_date",
        "_complete_date",
        "_reg_date",
        "_update_dt",
        "_alarm",
        "_count_book",
        "_count_pick",
        "_count_like",
        "_count_alarm",
        "_novel_age",
        "_novel_live",
        "_is_del",
        "_is_complete",
        "_is_contest",
        "_is_osmu",
    )

    def __init__(self,
                 info_dic: dict = None,
                 up_status: str = None,
                 types: set[str] = None,
                 tags: str = None,
                 novel_story: str = None,
                 ):

        super().__init__()

        if info_dic is None:
            info_dic = {}

        self._start_date = None
        self._last_write_date = None
        self._reg_date = None
        self._update_dt = None
        self._status_date = None
        self._count_pick = None
        self._count_book = None
        self._count_like = None
        self._count_alarm = None
        self._novel_live = None
        self._novel_genre = None
        self._tags = tags
        self._writer_nick = None
        if types is None:
            types = set()
        self._up_status = up_status
        self._types = types
        self._novel_story = novel_story

        alias_dic: dict = {
            "novel_no": "code",
            "novel_name": "title",
        }
        for key, value in info_dic.items():
            property_name: str = "_" + key
            if property_name in self.__slots__:
                if key == "novel_type":
                    if value == 1:
                        self.types.add("PLUS")
                    elif value == 2:
                        self.types.add("자유")

                elif key == "novel_genre":
                    self.novel_genre = value
                elif key == "novel_story":
                    self.novel_story = value

                elif key == "novel_live":
                    if value == 1:
                        self.up_status = "연재 지연"
                    if value == 2:
                        self.up_status = "연재 중단"

                elif key == "is_del":
                    self.up_status = "삭제"
                elif key == "is_complete":
                    self.up_status = "완결"

                else:
                    self.__setattr__(property_name, value)
                continue
            if key in alias_dic:
                if key == "novel_no":
                    from .const.const import HOST

                    self.code = value
                    self.url = urljoin(HOST, f"/novel/{value}")
                else:
                    alias = alias_dic[key]
                    self.__setattr__(alias, value)

    def __str__(self):
        return novel_info_to_md(self)

    @property
    def writer_nick(self) -> str:
        return self._writer_nick

    @writer_nick.setter
    def writer_nick(self, writer_name: str):
        if writer_name.isprintable():
            self._writer_nick = writer_name

    @property
    def count_pick(self) -> str:
        return self._count_pick

    @count_pick.setter
    def count_pick(self, count_pick: str):
        if count_pick.isprintable():
            self._count_pick = count_pick

    @property
    def novel_genre(self) -> str:
        return self._novel_genre

    @novel_genre.setter
    def novel_genre(self, tags: str) -> None:
        from re import findall

        strings: list[str] = findall(r'\"\w+\"', tags)

        self.tags = strings

    @property
    def tags(self) -> str:
        return self._tags

    @tags.setter
    def tags(self, tags: list[str]) -> None:
        length: int = len(tags)
        if length < 1:
            print_under_new_line("태그를 한 개 이상 입력해 주세요.")
        else:
            self._tags = "\n  - " + "\n  - ".join(tags)
            """
            태그의 각 줄 앞에 '-'를 붙여서 Markdown list (Obsidian 태그) 형식으로 변환
            tags:
              - 판타지
              - 중세
            """

    @staticmethod
    def assure_not_none(required_type: type, value: Any):
        if value is not None:
            return value
        else:
            return required_type()

    def date_setter(self, key: str, value: str):
        try:
            datetime.fromisoformat(value)  # value: "2024-12-13"
        except ValueError as err:
            err.add_note(*err.args)
            print_under_new_line("[오류]", f"{err = }")
            raise
        else:
            protected_key: str = "_" + key
            self.__setattr__(protected_key, value)

    @property
    def start_date(self) -> str:
        return self.assure_not_none(str, self._start_date)

    @start_date.setter
    def start_date(self, up_date_s: str) -> None:
        self.date_setter("start_date", up_date_s)

    @property
    def last_write_date(self) -> str:
        return self.assure_not_none(str, self._last_write_date)

    @last_write_date.setter
    def last_write_date(self, up_date_s: str) -> None:
        self.date_setter("last_write_date", up_date_s)

    @property
    def reg_date(self) -> str:
        return self.assure_not_none(str, self._reg_date)

    @reg_date.setter
    def reg_date(self, up_date_s: str) -> None:
        self.date_setter("reg_date", up_date_s)

    @property
    def update_dt(self) -> str:
        return self.assure_not_none(str, self._update_dt)

    @update_dt.setter
    def update_dt(self, up_date_s: str) -> None:
        self.date_setter("update_dt", up_date_s)

    @property
    def status_date(self) -> str:
        return self.assure_not_none(str, self._status_date)

    @status_date.setter
    def status_date(self, up_date_s: str) -> None:
        self.date_setter("status_date", up_date_s)

    def __pick_one_from(self, key: str, val: str, vals: frozenset) -> None:
        super().pick_one_from(key, val, vals)

    def __add_one_from(self, key: str, val: str, vals: frozenset) -> None:
        return super().add_one_from(key, val, vals)

    def __set_signed_int(self, key: str, val: int) -> None:
        super().set_signed_int(key, val)

    @property
    def novel_live(self) -> int:
        return self._novel_live

    @property
    def up_status(self) -> str:
        return self._up_status

    @up_status.setter
    def up_status(self, up_status: str) -> None:
        up_status_options = frozenset(["연재 중", "완결", "연재지연", "연재중단", "삭제", "연습작품"])
        self.__pick_one_from("_up_status", up_status, up_status_options)

    @property
    def types(self) -> set[str]:
        return self._types

    @types.setter
    def types(self, type: str) -> None:
        types = frozenset(["성인", "자유", "PLUS", "독점", "챌린지"])
        self.__add_one_from("_types", type, types)

    @property
    def count_book(self) -> int:
        return self._count_book

    @count_book.setter
    def count_book(self, count_book: int) -> None:
        self.__set_signed_int("_count_book", count_book)

    @property
    def count_alarm(self) -> int:
        return self._count_alarm

    @count_alarm.setter
    def count_alarm(self, count_alarm: int) -> None:
        self.__set_signed_int("_count_alarm", count_alarm)

    @property
    def count_like(self) -> int:
        return self._count_like

    @count_like.setter
    def count_like(self, count_like: int) -> None:
        self.__set_signed_int("_count_like", count_like)

    @property
    def novel_story(self) -> str:
        return self._novel_story

    @novel_story.setter
    def novel_story(self, novel_story: str) -> None:
        """줄거리의 각 줄 앞에 '>'를 붙여서 Markdown Callout 블록으로 변환 후 저장하는 함수

        :param novel_story: 줄거리
        """
        lines = [line.lstrip("#") for line in novel_story.splitlines() if line != ""]
        novel_story_lines: list[str] = ["> [!TLDR] 시놉시스"] + lines
        summary_callout = "\n> ".join(novel_story_lines) + "\n"
        """
        > [!TLDR] 시놉시스
        > 괴담, 저주, 여학생 등….
        > 집착해선 안 될 것들이 내게 집착한다
        """
        self._novel_story = summary_callout


def toggle_novel_action(novel_code: str, action_n: int = 0, login: int = 0, csrf: str = None) -> tuple[int, int]:
    """소설 알람 또는 선호작 설정을 등록/해제하는 함수

    :param novel_code: 소설 번호
    :param action_n: 변경할 설정 (0은 알람, 1은 선호작)
    :param login: 로그인 유형 (0은 비 로그인, 1은 일반 계정, 2는 구독 계정)
    :param csrf: 웹 페이지 CSRF 토큰 (선호작 설정용)
    :return: 상태 코드, 최종 알람/선호 수
    """
    from .func.common import add_login_key

    action_s: str = "alarm" if action_n == 0 else "like"
    url: str = urljoin(HOST, "/proc/novel_" + action_s)

    data: dict = {
        "novel_no": novel_code,
    }
    # 선호 설정
    if action_n == 1:
        stat: str = "선호"
        if csrf:
            data["csrf"] = csrf
        elif login:
            print_under_new_line("CSRF 문자열을 입력받지 못했어요.")
            return False, -1

    # 알람 설정
    else:
        stat: str = "알람"

    if not login:
        if not action_n:
            print()
        print(f"로그인 없이 {stat} 수만 추출할게요.")

    headers: dict = BASIC_HEADERS.copy()
    if login == 1:
        login_key, headers = add_login_key(headers)
    elif login == 2:
        plus_login_key, headers = add_login_key(headers, True)

    res = post(url, data, headers=headers)

    status_codes: dict[str:int] = {
        "예외": 0,
        "등록": 1,
        "해제": 2,
        "로그인": 3,
        "그 외": 4,
    }
    try:
        # {'status': '200', 'errmsg': '', {'novel': [{ ... }], 'allCount': 2}}
        flag_li: list[str] = res.text.split("|")
        stats = int(flag_li[1])

    # 요청 실패
    except Exception as err:
        print_under_new_line("[오류]", toggle_novel_action, f"{err = }")

        return status_codes["예외"], -1

    # 요청 성공
    else:
        # 등록 승인
        if flag_li[0] == "on":  # on|1896||0
            msg: str = f"{novel_code}번 소설의 {stat}을/를 등록했어요."
            print_under_new_line(msg)

            return status_codes["등록"], stats

        # 해제 승인
        elif flag_li[0] == "off":  # off|1895||
            msg: str = f"{novel_code}번 소설의 {stat}을/를 해제했어요."
            print(msg)

            return status_codes["해제"], stats

        # 거부 (로그인 필요)
        elif flag_li[0] == "login":
            if login:
                print_under_new_line(f"{stat} 설정을 위해서는 로그인이 필요해요.")

            return status_codes["로그인"], stats

        # 거부 (그 외)
        else:
            return status_codes["그 외"], -1


def get_like_novel_info_dics(user_mem_no: int) -> tuple[None, None] | tuple[int, Generator]:
    """회원의 선호작 정보를 서버에 요청하고 파싱한 응답을 반환하는 함수

    :param user_mem_no: 회원 번호
    :return: 선호작 수, 소설 정보 목록들
    """
    url: str = urljoin(HOST, "/proc/user")
    data: dict = {
        "mode": "get_member_favorite_novel",
        "mem_no": str(user_mem_no),
        "paging[rowCount]": "1000",
        "paging[curPage]": "1",
        "paging[order]": "date",
        "paging[sort][date]": 1,
    }
    res = post(url, data, headers=BASIC_HEADERS)
    res_json: str = res.text

    from json import loads, JSONDecodeError

    try:
        # {'status': '200', 'errmsg': '', {'novel': [{ ... }], 'allCount': 2}}
        res_dic: dict = loads(res_json)
    except JSONDecodeError as je:
        print_under_new_line("[오류]", f"{je = }")

        return None, None
    else:
        # {'novel': [{ ... }], 'allCount': 2}
        res_dic = res_dic["result"]
        count: int = res_dic["allCount"]
        info_dics: Generator = (dic for dic in res_dic["novel"])

        return count, info_dics


def info_dics_to_novels(info_dics: Generator, count: int):
    """소설 정보가 담긴 Dict를 Novel 객체로 변환하는 함수

    :param info_dics: 소설 정보가 담긴 Dict 목록
    :param count: Dict 수
    :return: Novel 객체
    """
    novels: list[Novel] = []

    for i in range(count):
        try:
            info_dic: dict = next(info_dics)

        # 선호작 X
        except StopIteration as si:
            raise RuntimeError(novel_info_main, f"{si = }")

        else:
            # 소설 번호 추출
            novel_code: str = info_dic["novel_no"]

            # 알람 수 추출
            success, alarms = toggle_novel_action(novel_code)
            assert success == 3

            # 좋아요 수 추출
            success, likes = toggle_novel_action(novel_code, 1)
            assert success == 3

            # 알람, 좋아요 수 저장
            info_dic["count_alarm"] = alarms
            info_dic["count_like"] = likes

            # Novel 객체 생성 및 저장
            novel = Novel(info_dic)
            novels.append(novel)
            print_under_new_line(f"{i + 1}번째 소설로 Novel 객체를 생성했어요.")

    yield from novels


def get_novel_up_dates(novel_code: str, sort: str = "DOWN") -> str | None:
    """소설의 첫/마지막 연재일을 추출하여 반환하는 함수

    :param novel_code: 소설 번호
    :param sort: 정렬 방식
    :return: 첫/마지막 연재일
    """
    from .func.episode import get_ep_list, extract_ep_tags, get_ep_up_dates

    list_html: str = get_ep_list(novel_code, sort)
    ep_no: int = 1
    ep_tags: Generator = extract_ep_tags(list_html, frozenset([ep_no]))

    try:
        ep_tag: Tag = next(ep_tags)
    except StopIteration as err:
        exit("[오류] " + f"{err = }")

    # 회차 게시 일자 추출
    ep_tag_gen: Generator = (ep_tag for ep_tag in [ep_tag])
    up_dates: Generator[str] | None = get_ep_up_dates(ep_tag_gen)
    if not up_dates:
        return None

    up_date: str = next(up_dates)

    return up_date


@contextmanager
def chk_novel_up_status(novel: Novel, html: str):
    """소설 페이지에서 추출한 정보와 발생한 오류를 반환하는 함수

    :param novel: 소설 정보가 담긴 Novel 인스턴스
    :param html: 소설 페이지 HTML
    :return: Novel/BeautifulSoup 클래스 객체와 오류
    """
    ################################################################################
    # 페이지 제목 추출
    ################################################################################
    only_title = Strainer("title")
    title_soup = Soup(html, PARSER, parse_only=only_title)

    # '노벨피아 - 웹소설로 꿈꾸는 세상! - '의 22자 제거
    from .const.const import HTML_TITLE_PREFIX

    html_title: str = title_soup.text[len(HTML_TITLE_PREFIX):]
    """
    - 브라우저 상에 제목표시줄에 페이지 위치나 소설명이 표기됨.
    - 공지 참고: <2021년 01월 13일 - 노벨피아 업데이트 변경사항(https://novelpia.com/notice/20/view_4149/)>
    """
    # 페이지 제목 저장
    novel.title = html_title

    ################################################################################
    # HTML body 內 제목 추출
    ################################################################################

    # HTML 中 소설 정보가 담긴 부분만 파싱
    from .const.selector import NOVEL_INFO_CSS

    only_info = Strainer("div", {"class": NOVEL_INFO_CSS})
    info_soup = Soup(html, PARSER, parse_only=only_info)

    from .const.selector import NOVEL_TITLE_CSS

    # 노벨피아 자체 제목 태그 추출
    title_tag: Tag = info_soup.select_one(NOVEL_TITLE_CSS)

    # 제목 태그 유무 확인
    try:
        novel_title: str = title_tag.text

    # 제목 태그 無 (서비스 상태 비정상, 소설 정보를 받지 못함)
    except AttributeError as attr_err:
        from .func.common import parse_alert_msg_w_error, get_postposition

        # 오류 메시지 추출
        with parse_alert_msg_w_error(html) as (msg, err):
            msg_to_code: dict = {
                "삭제된 소설 입니다.": 204,
                "잘못된 접근입니다.": 403,
                "잘못된 소설 번호 입니다.": 404,
            }
            if err:
                print_under_new_line("[오류]", f"{err = }")
                print_under_new_line("[오류] 알 수 없는 이유로 소설 정보를 추출하지 못했어요.")

                yield novel, None, err

            code = msg_to_code[msg]

            if code == 204:
                postposition: str = get_postposition(html_title, "은")
                msg = f"<{html_title}>{postposition} {msg}"

                novel.up_status = "삭제"

            elif code == 403:
                msg = f"<{html_title}>에 대한 {msg}"

                novel.types.add("자유")
                novel.up_status = "연습작품"

            elif code == 404:
                novel = None

            # 오류 메시지 출력
            print_under_new_line("[노벨피아]", msg)

            yield novel, None, attr_err

    # 제목 태그 有 (서비스 상태 정상)
    else:
        # 제목 검사 후 반환
        assert_msg: str = f"[오류] 제목 불일치: 페이지 제목 '{html_title}'과 소설 제목 '{novel_title}'가 달라요."
        assert html_title == novel_title, assert_msg
        novel.title = novel_title

        yield novel, info_soup, None


def set_novel_from_likes(login: int, novel_code: str = None) -> tuple[Generator, int]:
    """계정의 선호작 목록에서 추출한 정보를 Novel 객체들로 변환하는 함수

    :param novel_code: 소설 번호
    :param login: 로그인 유형 (1은 일반 계정, 2는 구독 계정)
    :return: Novel 객체 목록, 선호작 수
    """
    from dotenv import dotenv_values

    config = dotenv_values()
    csrf: str = config["CSRF"]

    if novel_code:
        toggle_novel_action(novel_code, 1, login, csrf)

    env_var_name: str | None = None

    if login == 1:
        env_var_name: str = "SUB_MEM_NO"
    elif login == 2:
        env_var_name: str = "PLUS_MEM_NO"

    assert env_var_name

    mem_no = int(config[env_var_name])
    count, info_dics = get_like_novel_info_dics(mem_no)
    novels: Generator = info_dics_to_novels(info_dics, count)

    if novel_code:
        success, stats = toggle_novel_action(novel_code, 1, login, csrf)
        assert success

    return novels, count


def novel_info_to_md(novel: Novel) -> str:
    """추출한 소설 정보를 Markdown 문서로 변환하는 함수
    
    :param novel: 소설 정보가 담긴 Novel 인스턴스
    :return: Markdown 문서
    """
    print_under_new_line(f"[알림] {novel.title}.md 파일에 '유입 경로' 속성을 추가했어요. Obsidian 으로 직접 수정해 주세요.")

    from .const.const import NOVEL_STATUSES_NAMED_TUPLE as STATUS_TU

    deleted: str = STATUS_TU.deleted

    # 삭제된 소설, Markdown 미작성
    if novel.up_status == deleted:
        return deleted

    type_bools: list[str] = [type + ": True" for type in novel.types]
    types: str = "\n".join(type_bools)

    # 소설 서비스 상태 정상, Markdown 작성
    lines: list[str] = [
        "aliases:\n  - (직접 적어 주세요)",
        "유입 경로: (직접 적어 주세요)",
        "작가명: " + novel.writer_nick,
        "소설 링크: " + novel.url,
        "tags:" + novel.tags,
        types,
        novel.up_status + ": True"
    ]
    from .const.const import DEFAULT_TIME

    dates: list[str] = [
        "완독일: " + DEFAULT_TIME,
        "연재 시작일: " + novel.start_date,
        "최근(예정) 연재일: " + novel.last_write_date,
        "소설 등록일: " + novel.reg_date,
        "소설 갱신일: " + novel.update_dt,
        "원격 갱신일: " + novel.status_date,
        "로컬 갱신일: " + novel.got_time,
    ]
    stats: list[str] = [
        f"회차 수: {novel.count_book}",
        f"알람 수: {novel.count_alarm}",
        f"선호 수: {novel.count_like}",
        f"추천 수: {novel.count_good}",
        f"조회 수: {novel.count_view}",
    ]
    lines = ["---"] + lines + dates + stats
    lines.append("---\n")

    summary_callout: str = novel.novel_story
    if summary_callout:
        lines.append(summary_callout)

    md_string: str = "\n".join(lines)

    return md_string


def novel_to_md_file(novel: Novel, skip: bool = False, overwrite: bool = False):
    """입력받은 소설 정보를 파일에 쓰는 함수

    :param novel: 소설 정보가 담긴 Novel 인스턴스
    :param skip: 덮어 쓰기 질문을 건너뛸 지 여부
    :param overwrite: 덮어 쓰기 여부
    """
    from .func.common import get_env_var_w_error

    with get_env_var_w_error("NOVEL_INFO_MD_DIR") as (env_md_dir, key_err):
        # 환경 변수 無
        if key_err:
            novel_dir = Path(Path.cwd(), "novel")
            md_dir = Path(novel_dir, "markdown")

        # 환경 변수의 Markdown 폴더 경로 사용
        else:
            md_dir: Path = Path(env_md_dir, "소설 정보")

    print_under_new_line("[알림] Markdown 파일은", md_dir, "에 쓸게요.")

    hardened_title: str = novel.title.replace("/", "|")  # 제목의 "/"로 인한 폴더 생성 방지
    padded_code: str = novel.code.zfill(6)  # 노벨피아 총 소설 수는 약 30만 개 (6자리)
    file_name: str = padded_code + " - " + hardened_title  # '6자리 번호 - 제목'

    file_path = Path(md_dir, file_name).with_suffix(".md")  # 기본 경로: ../novel/markdown/제목.md

    # Markdown 형식으로 변환하기
    md_file_content = novel_info_to_md(novel)

    # Markdown 폴더 확보 및 새 파일 열기
    from .func.common import opened_x_error
    with opened_x_error(file_path, "xt", 'utf-8', skip, overwrite) as (f, err):
        if err:
            print_under_new_line("[오류]", f"{err = }")
            print("[오류]", file_path, "파일을 열지 못했어요.")
        else:
            # print(md_file_content, file=f)
            f.write(md_file_content)
            print("[알림]", file_path, "파일을 썼어요.")


def novel_info_main() -> None:
    """직접 실행할 때만 호출되는 메인 함수"""
    from .func.userIO import input_num

    # 소설 번호 입력 받기
    novel_code: str = str(input_num("소설 번호"))

    # Novel 객체 생성
    novels, count = set_novel_from_likes(1, novel_code)
    novel: Novel = next(novels)

    # Markdown 파일 열기
    novel_to_md_file(novel, overwrite=True)


if __name__ == "__main__":
    novel_info_main()
