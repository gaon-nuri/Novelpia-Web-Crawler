"""소설 정보를 크롤링하는 코드"""
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup as Soup
from bs4.element import Tag
from bs4.filter import SoupStrainer as Strainer
# from dotenv import load_dotenv
from dotenv import dotenv_values

from src.const.const import DEFAULT_TIME, PARSER, RANK_PLACE_HOLDER
from src.func.common import Page
from src.func.userIO import print_under_new_line

# assert load_dotenv(), "환경 변수를 찾지 못했어요."
config = dotenv_values()


# noinspection PyMissingOrEmptyDocstring
class Novel(Page):
    """노벨피아 소설 정보 클래스.

    :var _writer_nick: 작가 닉네임
    :var _writer_mem_no: 작가 회원 번호
    :var _novel_age: 허용 독자 연령 (전연령/15금/19금)
    :var _novel_type: 연재 유형 (자유/PLUS)
    :var _novel_live: 연재 상태 (연재 중, 완결: 0, 연재지연: 1, 연재중단: 2 中 1)
    :var _status: 연재 상태 (연재 중, 완결, 삭제, 연습작품, 연재지연, 연재중단 中 1)
    :var _types: 유형
    :var _main_genre: 1차 분류 태그
    :var _tags: 해시 태그로 된 bulleted list
    :var _synopsis: 줄거리로 된 Markdown Callout
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
        "_writer_mem_no",
        "_novel_type",
        "_status",
        "_types",
        "_main_genre",
        "_tags",
        "_synopsis",
        "_start_date",
        "_last_write_date",
        "_reg_date",
        "_status_date",
        "_alarm",
        "_prefer",
        "_count_book",
        "_count_pick",
        "_novel_age",
        "_novel_live",
        "_is_contest",
        "_is_osmu",
    )

    def __init__(self,
                 code: str = '',
                 url: str = '',
                 writer_nick: str = '',
                 writer_mem_no: int = -1,
                 novel_name: str = '',
                 status: str = '',
                 types: set[str] = None,
                 main_genre: int = -1,
                 tags: str = '',
                 synopsis: str = '',
                 start_date: str = DEFAULT_TIME,
                 last_write_date: str = DEFAULT_TIME,
                 reg_date: str = DEFAULT_TIME,
                 status_date: str = DEFAULT_TIME,
                 alarm: int = -1,
                 prefer: int = -1,
                 count_book: int = -1,
                 count_good: int = -1,
                 count_view: int = -1,
                 count_pick: str = RANK_PLACE_HOLDER,
                 novel_age: int = 0,
                 novel_type: int = 1,
                 novel_live: int = -1,
                 is_contest: int = -1,
                 is_osmu: str = "null",
                 ):

        super().__init__(novel_name, code, url, reg_date, status_date, count_good, count_view)

        self._status = None
        self._writer_nick = writer_nick
        self._writer_mem_no = writer_mem_no
        self._novel_age = novel_age
        self._novel_type = novel_type
        if types is None:
            types = set()
        self._status = status
        self._novel_live = novel_live
        self._types = types
        self._main_genre = main_genre
        self._tags = tags
        self._synopsis = synopsis
        self._start_date = start_date
        self._last_write_date = last_write_date
        self._reg_date = reg_date
        self._status_date = status_date
        self._alarm = alarm
        self._prefer = prefer
        self._count_book = count_book
        self._count_pick = count_pick
        self._is_contest = is_contest
        self._is_osmu = is_osmu

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
    def tags(self) -> str:
        return self._tags

    @tags.setter
    def tags(self, tags: set[str]):
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

    @property
    def last_write_date(self) -> str:
        return self._last_write_date

    @last_write_date.setter
    def last_write_date(self, up_date_s: str):
        try:
            datetime.fromisoformat(up_date_s)  # up_date_s: "2024-12-13"
        except ValueError as err:
            err.add_note(*err.args)
            print_under_new_line("[오류]", f"{err = }")
            raise
        else:
            self._last_write_date = up_date_s

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
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, status: str):
        status_options = frozenset(["연재 중", "완결", "연재지연", "연재중단", "삭제", "연습작품"])
        self.__pick_one_from("_status", status, status_options)

    @property
    def types(self) -> set[str]:
        return self._types

    @types.setter
    def types(self, type: str):
        types = frozenset(["성인", "자유", "PLUS", "독점", "챌린지"])
        self.__add_one_from("_types", type, types)

    @property
    def count_book(self) -> int:
        return self._count_book

    @count_book.setter
    def count_book(self, count_book: int):
        self.__set_signed_int("_count_book", count_book)

    @property
    def alarm(self) -> int:
        return self._alarm

    @alarm.setter
    def alarm(self, alarm: int):
        self.__set_signed_int("_alarm", alarm)

    @property
    def prefer(self) -> int:
        return self._prefer

    @prefer.setter
    def prefer(self, prefer: int):
        self.__set_signed_int("_prefer", prefer)

    @property
    def synopsis(self) -> str:
        return self._synopsis

    @synopsis.setter
    def synopsis(self, novel_story: str):
        """줄거리의 각 줄 앞에 '>'를 붙여서 Markdown Callout 블록으로 변환 후 저장하는 함수

        :param novel_story: 줄거리
        """
        lines = [line.lstrip("#") for line in novel_story.splitlines() if line != ""]
        synopsis_lines: list[str] = ["> [!TLDR] 시놉시스"] + lines
        summary_callout = "\n> ".join(synopsis_lines) + "\n"
        """
        > [!TLDR] 시놉시스
        > 괴담, 저주, 여학생 등….
        > 집착해선 안 될 것들이 내게 집착한다
        """
        self._synopsis = summary_callout


def toggle_novel_like(novel_code: str) -> tuple[bool, int]:
    """소설을 선호작으로 등록/해제하는 함수

    :param novel_code: 소설 번호
    """
    from requests import post
    from urllib.parse import urljoin

    from src.func.common import add_login_key
    from src.const.const import BASIC_HEADERS, HOST

    csrf: str = config["CSRF"]
    url: str = urljoin(HOST, "/proc/novel_like")
    data: dict = {
        "novel_no": novel_code,
        "csrf": csrf,
    }
    login_key, headers = add_login_key(BASIC_HEADERS)
    res = post(url, data, headers=headers)

    try:
        # {'status': '200', 'errmsg': '', {'novel': [{ ... }], 'allCount': 2}}
        flag_li: list[str] = res.text.split("|")
        likes = int(flag_li[1])

    # 요청 실패
    except Exception as err:
        print_under_new_line("[오류]", toggle_novel_like, f"{err = }")
        return False, -1

    # 요청 성공
    else:
        # 등록 승인
        if flag_li[0] == "on":  # on|19094||0
            msg: str = novel_code + "번 소설을 선호작으로 등록했어요."
            print_under_new_line(msg)
            return True, likes

        # 해제 승인
        elif flag_li[0] == "off":  # off|19093||
            msg: str = novel_code + "번 소설을 선호작에서 해제했어요."
            print_under_new_line(msg)
            return True, likes

        # 거부 (로그인 필요)
        elif flag_li[0] == "login":
            print_under_new_line("선호작 등록을 위해서는 로그인이 필요해요.")
            return False, likes

        # 거부 (그 외)
        else:
            return False, -1


def get_like_novel_info_dics(user_mem_no: int):
    """회원의 선호작 정보를 서버에 요청하고 파싱한 응답을 반환하는 함수

    :param user_mem_no: 회원 번호
    :return: 선호작 수, 소설 정보 목록들
    """
    from requests import post
    from urllib.parse import urljoin
    from src.const.const import BASIC_HEADERS, HOST

    url: str = urljoin(HOST, "/proc/user")
    data: dict = {
        "mode": "get_member_favorite_novel",
        "mem_no": str(user_mem_no),
        "paging[rowCount]": "10",
        "paging[curPage]": "1",
        "paging[order]": "date",
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
        info_dics: list[dict] = res_dic["novel"]

        return count, info_dics


def extract_like_novels_status():
    """삭제, 완결, 연재지연/중단, 연재 중 하나로 상태를 추출하는 함수."""

    mem_no = int(config["SUB_MEM_NO"])
    count, dics = get_like_novel_info_dics(mem_no)
    status_dic: dict[int: str] = {}

    for dic in dics:
        novel_no: int = dic["novel_no"]
        status_dic[novel_no] = "연재 중"
        if dic["is_del"]:
            status_dic[novel_no] = "삭제"
        elif dic["is_complete"]:
            status_dic[novel_no] = "완결"
        elif dic["novel_live"] == 1:
            status_dic[novel_no] = "연재 지연"
        elif dic["novel_live"] == 2:
            status_dic[novel_no] = "연재 중단"

    return status_dic


def get_novel_up_dates(novel_code: str, sort: str = "DOWN") -> str | None:
    """소설의 첫/마지막 연재일을 추출하여 반환하는 함수

    :param novel_code: 소설 번호
    :param sort: 정렬 방식
    :return: 첫/마지막 연재일
    """
    from src.func.episode import get_ep_list, extract_ep_tags, get_ep_up_dates
    from typing import Generator

    list_html: str = get_ep_list(novel_code, sort)
    ep_no: int = 1
    ep_tags: Generator = extract_ep_tags(list_html, frozenset([ep_no]))

    from bs4.element import Tag

    try:
        ep_tag: Tag = next(ep_tags)
    except StopIteration as err:
        exit("[오류] " + f"{err = }")

    # 회차 게시 일자 추출
    ep_tag_gen: Generator = (ep_tag for ep_tag in [ep_tag])
    up_dates: Generator[str] | None = get_ep_up_dates(ep_tag_gen)
    up_date: str = next(up_dates)

    if not up_dates:
        return None
    else:
        return up_date


@contextmanager
def chk_novel_status(novel: Novel, html: str):
    """소설 페이지에서 추출한 정보와 발생한 오류를 반환하는 함수

    :param novel: 소설 정보가 담긴 Novel 인스턴스
    :param html: 소설 페이지 HTML
    :return: Novel/BeautifulSoup 클래스 객체와 오류
    """
    # 페이지 제목 추출
    only_title = Strainer("title")
    title_soup = Soup(html, PARSER, parse_only=only_title)

    # '노벨피아 - 웹소설로 꿈꾸는 세상! - '의 22자 제거
    from src.const.const import HTML_TITLE_PREFIX

    html_title: str = title_soup.text[len(HTML_TITLE_PREFIX):]
    """
    - 브라우저 상에 제목표시줄에 페이지 위치나 소설명이 표기됨.
    - 공지 참고: <2021년 01월 13일 - 노벨피아 업데이트 변경사항(https://novelpia.com/notice/20/view_4149/)>
    """
    novel.title = html_title

    # HTML 中 소설 정보가 담긴 부분만 파싱
    from src.const.selector import NOVEL_INFO_CSS

    only_info = Strainer("div", {"class": NOVEL_INFO_CSS})
    info_soup = Soup(html, PARSER, parse_only=only_info)

    # 노벨피아 자체 제목 태그 추출
    from src.const.selector import NOVEL_TITLE_CSS

    title_tag: Tag = info_soup.select_one(NOVEL_TITLE_CSS)

    # 소설 서비스 상태 확인
    try:
        novel_title: str = title_tag.text

    # 서비스 상태 비정상, 소설 정보를 받지 못함
    except AttributeError as attr_err:

        # 오류 메시지 추출
        from src.func.common import extract_alert_msg_w_error, get_postposition

        with extract_alert_msg_w_error(html) as (alert_msg, err):
            if err:
                print_under_new_line("[오류]", f"{err = }")
                print_under_new_line("[오류] 알 수 없는 이유로 소설 정보를 추출하지 못했어요.")

            elif alert_msg == "삭제된 소설 입니다.":
                postposition: str = get_postposition(html_title, "은")
                alert_msg = f"<{html_title}>{postposition} {alert_msg}"

                novel.status = "삭제"

            elif alert_msg == "잘못된 접근입니다.":
                alert_msg = f"<{html_title}>에 대한 {alert_msg}"

                novel.types.add("자유")
                novel.status = "연습작품"

            elif alert_msg == '잘못된 소설 번호 입니다.':
                novel = None

            # 오류 메시지 출력
            print_under_new_line("[노벨피아]", alert_msg)

            yield novel, None, attr_err

    # 서비스 상태 정상
    else:
        # 제목 검사 후 반환
        assert_msg: str = f"[오류] 제목 불일치: 페이지 제목 '{html_title}'과 소설 제목 '{novel_title}'가 달라요."
        assert html_title == novel_title, assert_msg
        novel.title = novel_title

        yield novel, info_soup, None


def extract_novel_info(html: str) -> Novel | None:
    """입력받은 소설의 메인 페이지 HTML에서 정보를 추출하여 반환하는 함수

    :param html: 소설 정보를 추출할 HTML
    :return: 추출한 정보가 담긴 Novel 인스턴스
    """
    novel = Novel()
    # print_under_new_line(novel)

    from src.const.selector import NOVEL_URL_CSS

    only_meta_url = Strainer("meta", {"property": NOVEL_URL_CSS})
    url_soup = Soup(html, PARSER, parse_only=only_meta_url)

    ################################################################################
    # 소설 메인 페이지 URL 추출
    ################################################################################
    meta_url_tag: Tag = url_soup.meta  # meta_url_tag: <meta content="w1" property="og:url"/>
    url: str = meta_url_tag.get("content")

    # URL 저장
    novel.url = url

    ################################################################################
    # 소설 번호 추출
    ################################################################################
    from urllib.parse import urlparse
    novel_code: str = urlparse(url).path.split("/")[-1]  # "https://novelpia.com/novel/1" > "1"

    # 소설 번호 저장
    novel.code = novel_code

    ################################################################################
    # 제목 추출 및 소설 서비스 상태 확인
    ################################################################################
    with chk_novel_status(novel, html) as (novel, soup, err):
        if err:
            return novel
        else:
            info_soup = soup

    ################################################################################
    # 작가명 추출
    ################################################################################
    from src.const.selector import NOVEL_WRITER_NAME_CSS

    only_writer = Strainer("a", {"class": NOVEL_WRITER_NAME_CSS})
    writer_soup = Soup(html, PARSER, parse_only=only_writer)
    author: str = writer_soup.text.strip()  # '제울'

    # 작가명 저장
    novel.writer_nick = author

    print_under_new_line(f"[알림] {author} 작가의 <{novel.title}>은 정상적으로 서비스 중인 소설이에요.")

    ################################################################################
    # 소설 유형 및 연재 상태 추출
    ################################################################################
    from src.const.selector import NOVEL_BADGE_CSS

    badge_tag: Tag = info_soup.select_one(NOVEL_BADGE_CSS)
    from typing import Generator

    flag_list: Generator = (badge.text for badge in badge_tag.select("span"))
    from src.const.const import NOVEL_TYPES_NAMED_TUPLE, NOVEL_STATUSES_NAMED_TUPLE

    novel.status = NOVEL_STATUSES_NAMED_TUPLE.ongoing

    for flag in flag_list:
        if flag in NOVEL_TYPES_NAMED_TUPLE:
            if flag == NOVEL_TYPES_NAMED_TUPLE.adult:
                flag = "성인"
            novel.types.add(flag)
        elif flag in NOVEL_STATUSES_NAMED_TUPLE:
            novel.status = flag

    ################################################################################
    # 해시태그 목록 추출 (최소 2개 - 중복 포함 4개)
    ################################################################################
    from src.const.selector import NOVEL_HASH_TAG_CSS

    tag_set = info_soup.select(NOVEL_HASH_TAG_CSS)
    """
    - 소설 등록시 최소 2개 이상의 해시태그를 지정해야 등록, 수정이 가능.
    - 모바일/PC 페이지가 같이 들어 있어서 태그가 중복 추출됨.
    - 최소 해시태그 추가 공지: <2021년 01월 13일 - 노벨피아 업데이트 변경사항(https://novelpia.com/notice/20/view_4149/)>
    - 모바일 태그 표기 공지: <2021년 01월 14일 - 노벨피아 업데이트 변경사항(https://novelpia.com/notice/20/view_4783/)>
    """
    indices = int(len(tag_set) / 2)  # PC, 모바일 중복 해시 태그 제거
    hash_tags: list[str] = [i.string.lstrip("#") for i in tag_set[:indices]]  # ['판타지','현대', '하렘']

    # 해시 태그 저장
    novel.tags = hash_tags

    ################################################################################
    # 조회, 추천수 추출
    ################################################################################
    from src.const.selector import NOVEL_STAT_CSS

    pro_ep_stats: list[str] = [i.text.replace(",", "") for i in info_soup.select(NOVEL_STAT_CSS, limit=4)]
    novel.count_view, novel.count_good = map(int, pro_ep_stats[1::2])

    ################################################################################
    # 인생픽 순위 추출
    ################################################################################
    from src.const.selector import NOVEL_SOLE_PICK_RANK_CSS

    sole_pick_rank: str = info_soup.select(NOVEL_SOLE_PICK_RANK_CSS, limit=2)[1].extract().text
    from src.const.const import RANK_PLACE_HOLDER

    # 인생픽 순위 공개 중, 속성 추가
    if sole_pick_rank.endswith("위"):  # 40위
        novel.count_pick = sole_pick_rank  # 인생픽: 40위 (Markdown 속성 문법)

    # 비공개 상태일 시 넘어가기
    elif sole_pick_rank == RANK_PLACE_HOLDER:
        pass

    ################################################################################
    # 선호/알람/회차 수 추출
    ################################################################################
    pro_user_stats: list = [i.string.replace(",", "") for i in info_soup.select("span.writer-name")]
    pro_user_stats[2] = pro_user_stats[2].removesuffix("회차")  # 239회차 > 239
    pro_user_stats = list(map(int, pro_user_stats[::-1]))  # [7694, 879, 239]

    # 회차/선호/알람 수 저장
    novel.count_book, novel.alarm, novel.prefer = pro_user_stats

    # 프롤로그 존재 시 회차 수 1 가산
    # EP.0 ~ EP.10 이면 10회차로 나오니 총 회차 수는 여기에 1을 더해야 함
    from src.func.episode import has_prologue

    if has_prologue(novel_code):
        pro_user_stats[2] += 1

    ################################################################################
    # 줄거리 추출 및 저장
    ################################################################################
    novel.synopsis = info_soup.select_one("div.synopsis").text

    ################################################################################
    # 첫/마지막 연재 일자 추출 및 저장
    ################################################################################
    if novel.count_book != 0:
        novel.ctime, novel.last_write_date = map(get_novel_up_dates, [novel_code] * 2, ["DOWN", "UP"])

    return novel


def novel_info_to_md(novel: Novel) -> str:
    """추출한 소설 정보를 Markdown 문서로 변환하는 함수
    
    :param novel: 소설 정보가 담긴 Novel 인스턴스
    :return: Markdown 문서
    """
    print_under_new_line(f"[알림] {novel.title}.md 파일에 '유입 경로' 속성을 추가했어요. Obsidian 으로 직접 수정해 주세요.")

    from src.const.const import NOVEL_STATUSES_NAMED_TUPLE as STATUS_TU

    deleted: str = STATUS_TU.deleted

    # 삭제된 소설, Markdown 미작성
    if novel.status == deleted:
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
        types
    ]
    from src.const.const import DEFAULT_TIME

    dates: list[str] = [
        "완독일: " + DEFAULT_TIME,
        "연재 시작일: " + novel.ctime,
        "최근(예정) 연재일: " + novel.last_write_date,
        "정보 수집일: " + novel.got_time,
    ]
    stats: list[str] = [
        f"회차 수: {novel.count_book}",
        f"알람 수: {novel.alarm}",
        f"선호 수: {novel.prefer}",
        f"추천 수: {novel.count_good}",
        f"조회 수: {novel.count_view}",
    ]
    lines = ["---"] + lines + dates + stats
    lines.append("---")

    summary_callout: str = novel.synopsis
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
    from src.func.common import get_env_var_w_error

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
    from src.func.common import opened_x_error
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
    from src.func.userIO import input_num

    # 소설 번호 입력 받기
    code: str = str(input_num("소설 번호"))

    from urllib.parse import urljoin

    base_url: str = "https://novelpia.com/novel/"
    url: str = urljoin(base_url, code)  # https://novelpia.com/novel/1

    # 소설 페이지 응답 받기
    from src.func.common import get_novel_main_w_error
    with get_novel_main_w_error(url) as (html, err):
        if err is not None:
            print_under_new_line(f"{err = }")

    # 소설 정보 추출하기
    novel: Novel = extract_novel_info(html)

    # Markdown 파일 열기
    novel_to_md_file(novel)


if __name__ == "__main__":
    novel_info_main()
