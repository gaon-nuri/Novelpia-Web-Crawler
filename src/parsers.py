# novel_crawler/parsers.py
"""HTML 파싱과 관련된 함수들을 포함합니다."""
from contextlib import contextmanager
from datetime import datetime
from logging import error, getLogger, info, warning
from typing import Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup as Soup
from bs4.element import ResultSet, Tag
from bs4.filter import SoupStrainer as Strainer

from .const.const import PAGE_TITLE_PREFIX, PARSER
from .const.sel.css_novel_info import (NOVEL_INFO_CSS, NOVEL_TITLE_CSS, NOVEL_URL_CSS, NOVEL_WRITER_NAME_CSS)
from .exceptions import NoAlertMsgError, NoValueError, ParseNovelError, ReqDeletedNovelError, ReqPrivateNovelError, \
    TagNotFoundError
from .func.userio import print_under_new_line
from .models import Novel

logger = getLogger(__name__)


class NovelPageParser:
    # HTML 파싱과 관련된 함수들을 포함합니다.
    def __init__(self, page: str):
        self.page = page
        self.soup = Soup(page, PARSER)
        self.novel = Novel()
        self.cache = {}

    def page_url_from_meta_tag(self) -> None:
        """메타 태그에서 URL을 추출하여 Novel 객체에 설정."""
        from bs4.element import Tag
        meta_tag: Tag = self.soup.select_one(NOVEL_URL_CSS)
        # 'PageElement | None'에서 참조 'get'을(를) 찾을 수 없어요
        if not (meta_tag and meta_tag.get("content")):
            err_msg = "메타 URL 태그를 찾을 수 없어요."
            te = TagNotFoundError(err_msg)
            error(te)
            raise te
        unparsed_url: str = meta_tag.attrs["content"]
        self.novel.url = unparsed_url
        parsed_url = urlparse(unparsed_url)
        self.novel.code = parsed_url.path.split("/")[-1]
        info(f"URL 추출 완료: {unparsed_url}")

    def page_title_from_title_tag(self) -> None:
        """타이틀 태그를 파싱하여 Novel 객체에 소설 제목을 설정."""
        try:
            page_title_tag = self.soup.select_one("title")
            self.novel.title = page_title_tag.text[len(PAGE_TITLE_PREFIX):].strip()
        except AttributeError as ae:
            ae.add_note("타이틀 태그를 찾을 수 없어요.")
            error(ae)
            raise TagNotFoundError(ae)
        self.cache["page_title"] = self.novel.title
        info(f"타이틀 추출 완료: {self.novel.title}")

    def novel_obj_from_div_tag(self) -> None:
        """소설 정보가 담긴 div 태그를 파싱하여 Novel 객체에 설정."""
        div_tag: Optional[Tag] = self.soup.select_one("div", class_=NOVEL_INFO_CSS)
        if div_tag is None:
            err_msg = "소설 정보 DIV 태그를 찾을 수 없어요."
            te = TagNotFoundError(err_msg)
            warning(te)
            raise te
        self.cache["info_soup"] = div_tag
        # 추가적인 소설 정보 파싱 로직을 여기에 구현
        info("소설 정보 파싱 완료.")

    def novel_title_from_div_tag(self) -> None:
        """소설 제목을 파싱하고 Novel 객체에 설정."""
        title_div = self.soup.select_one("div", class_=NOVEL_TITLE_CSS)
        if title_div is None:
            err_msg = "소설 제목 DIV 태그를 찾을 수 없어요."
            te = TagNotFoundError(err_msg)
            error(te)
            raise te
        novel_title = title_div.text.strip()
        page_title = self.cache.get("page_title")
        if page_title != novel_title:
            msg = f"페이지 제목 '{page_title}'과 소설 제목 '{novel_title}'가 달라요."
            error(msg)
            raise ParseNovelError(msg)
        self.novel.title = novel_title
        info(f"소설 제목 확인 완료: {self.novel.title}")

    def writer_name_from_a_tag(self) -> None:
        """작가명 태그를 파싱하여 Novel 객체에 설정."""
        writer_tag = self.soup.select_one("a", class_=NOVEL_WRITER_NAME_CSS)
        if writer_tag is None:
            err_msg: str = "작가명 태그를 찾을 수 없어요."
            self.novel.writer_nick = "Unknown"
            warning(err_msg)
            raise TagNotFoundError(err_msg)
        writer_nick = writer_tag.text.strip()
        self.novel.writer_nick = writer_nick
        info(f"작가명 추출 완료: {writer_nick}")

    def handle_page_errors(self) -> None:
        """
        페이지에서 발생한 오류 메시지를 처리하고 Novel 객체의 상태를 업데이트.
        
        Raises:
            ParseNovelError: 특정 오류 메시지에 대응하는 예외.
        """
        from .func.common import suffix_from_words
        with alert_msg_and_err_from_page(self.page) as (msg, err):
            msg_to_code: dict[str:str] = {
                "삭제된 소설 입니다.": "DELETED",
                "잘못된 접근입니다.": "INVALID_ACCESS",
                "잘못된 소설 번호 입니다.": "INVALID_NOVEL_CODE",
            }
            code: str = msg_to_code.get(msg)
            if code is None:
                error(f"알 수 없는 오류 메시지: {msg}")
                raise ParseNovelError(f"알 수 없는 오류 메시지: {msg}")
            from .const.const import NOVEL_STATS_NAMED_TU as STATUSES
            if code == "DELETED":
                self.novel.up_status = STATUSES.deleted
                suffix = suffix_from_words(self.cache.get("page_title", ""), "은")
                err_msg = f"[노벨피아] <{self.cache.get('page_title', '')}>{suffix} {msg}"
                error(err_msg)
                raise ReqDeletedNovelError(err_msg)
            if code == "INVALID_ACCESS":
                self.novel.kinds.append("자유")
                self.novel.up_status = STATUSES.draft
                err_msg = f"[노벨피아] <{self.cache.get('page_title', '')}>에 대한 {msg}"
                error(err_msg)
                raise ReqPrivateNovelError(err_msg)

    def parse(self) -> Novel:
        """전체 파싱 과정을 실행하여 Novel 객체를 반환."""
        try:
            self.page_url_from_meta_tag()
            self.page_title_from_title_tag()
            self.novel_obj_from_div_tag()
            self.novel_title_from_div_tag()
            self.writer_name_from_a_tag()
            info(f"[알림] {self.novel.writer_nick} 작가의 <{self.novel.title}>은 정상적으로 서비스 중인 소설이에요.")
            return self.novel
        except ParseNovelError as npe:
            error(f"파싱 중 오류 발생: {npe}")
            self.handle_page_errors()


def novel_obj_from_page(page: str) -> Novel:
    """
    입력받은 소설의 메인 페이지 HTML에서 정보를 추출하여 Novel 객체를 반환합니다.

    Args:
        page (str): 소설 정보를 추출할 HTML 문자열.

    Returns:
        Optional[Novel]: 추출한 정보가 담긴 Novel 객체 또는 None.
    """
    parser = NovelPageParser(page)
    novel = parser.parse()
    return novel


@contextmanager
def alert_msg_and_err_from_page(page: str) -> tuple[Optional[str], Optional[Exception]]:
    """알림 메시지를 파싱하는 로직 \n
    1. 잘못된 소설 번호 입니다. (제목, 줄거리 無)
    2. 삭제된 소설 입니다. (제목 有, 줄거리 無)
    3. 잘못된 접근입니다. (제목 有, 줄거리 無)
    4. 본 작품은 연습작으로 등록되어 있습니다. (작가 본인만 열람 가능합니다) \n
    - 연습등록작품은 작가만 열람이 가능
    - 공지 참고: <2021년 01월 13일 - 노벨피아 업데이트 변경사항(https://novelpia.com/notice/20/view_4149/)>

    :param page: 소설 페이지 HTML
    :return: 오류 메시지
    """
    from src.const.const import PARSER
    soup = Soup(page, PARSER)
    from src.const.sel.css_novel_info import NOVEL_ALERT_MSG_CSS
    msg_tag = soup.select_one(NOVEL_ALERT_MSG_CSS)
    if msg_tag is None:
        nve = NoValueError()
        nve.add_note(f"{soup.prettify() = }")
        err_msg = f"[오류] {nve}"
        logger.error(err_msg)
        raise nve
    err_type_from_msg: dict[str:Exception] = {
        "잘못된 소설 번호 입니다.": ReqPrivateNovelError,
    }
    try:
        alert_msg = msg_tag.text
    # 메시지 無
    except AttributeError as ae:
        err_msg: str = f"[오류] {ae} {msg_tag}"
        logger.error(err_msg)
        raise NoAlertMsgError(err_msg)
    err_type = err_type_from_msg[alert_msg]
    if err_type == ReqPrivateNovelError:
        raise err_type(alert_msg)
    msg, err = alert_msg, None
    yield msg, err


def ep_tag_gen_from_page(list_page: str, ep_num_queue: list[int]):
    """입력받은 회차 목록에서 선택한 회차들의 태그를 추출하여 하나씩 반환하는 함수

    :param list_page: 회차 목록 HTML
    :param ep_num_queue: 태그를 추출할 회차 서수의 집합
    :return: 회차 태그의 집합
    """
    from src.const.sel.css_ep import EP_TABLE_CSS
    only_ep = Strainer("table", {"class": EP_TABLE_CSS})
    soup = Soup(list_page, PARSER, parse_only=only_ep)

    # 작성된 회차 無
    if len(soup.contents) == 0:
        print_under_new_line("[노벨피아] 작성된 글을 찾을 수 없어요.")
        yield None

    from src.const.sel.css_ep import EP_TAGS_CSS
    ep_tags: ResultSet[Tag] = soup.select(EP_TAGS_CSS, limit=20)
    for ep_num in ep_num_queue:
        assert ep_num > 0, "잘못된 회차 서수"
        try:
            ep_tag: Tag = ep_tags[ep_num - 1]
        except IndexError as ie:
            err_msg = f"[오류] {ep_num} 번째 회차를 찾지 못했어요."
            ie.add_note(err_msg)
            logger.error(ie)
            raise
        ep_tags.append(ep_tag)
    yield from ep_tags


def ep_up_date_gen_from_tags(ep_tag_gen):
    """목록에서 추출한 회차 Tag 들의 Set 에서 각각의 게시 일자를 추출하여 반환하는 함수

    :param ep_tag_gen: 회차 Tag 목록
    :return: 입력받은 회차들의 게시 일자. 작성된 회차가 없으면 None, 입력된 회차가 없으면 list[None]
    """
    ep_up_date_li: list[Optional[str]] = []
    for ep_tag in ep_tag_gen:
        if ep_tag is None:
            ep_up_date_li.append(None)
            continue

        bold_tag_rs: ResultSet[Tag] = ep_tag.select("b", limit=2)
        up_date_str: str = bold_tag_rs[1].text.strip()  # 21.01.18 또는 '19시간전'

        # 24시간 이내에 게시
        if up_date_str.endswith("전"):  # upload_date: '1시간전' / '1분전'
            from datetime import timedelta
            today: datetime = datetime.today()
            if up_date_str[-2] == "분":
                min_past = int(up_date_str[:-2])
                up_datetime = today - timedelta(minutes=min_past)
                up_date_str = up_datetime.isoformat(timespec="minutes")  # 2024-07-25
            else:
                hour_past = int(up_date_str[:-3])
                up_datetime = today - timedelta(hours=hour_past)
                up_date_str = up_datetime.isoformat(timespec="hours")  # 2024-07-25

        # 예약 회차
        elif up_date_str.endswith("후"):
            today: datetime = datetime.today()
            # 예약 회차는 공개 하루 전부터 노출
            end_index: int = -1
            for i in range(len(up_date_str)):
                if up_date_str[i].isnumeric():
                    end_index: int = i
            assert end_index != -1

            # 남은 시간이 1시간 미만
            if up_date_str[end_index + 1] == "분":
                min_left = int(up_date_str[:end_index + 1])
                from datetime import timedelta
                up_datetime = today + timedelta(minutes=min_left)
                up_date_str = up_datetime.isoformat(timespec="minutes")

            # 남은 시간이 1시간 이상 하루 미만
            elif up_date_str[end_index + 1] == "시":
                hour_left = int(up_date_str[:end_index + 1])
                from datetime import timedelta
                if hour_left == 24:
                    up_datetime = today + timedelta(days=1)
                else:
                    up_datetime = today + timedelta(hours=hour_left)
                # 'N+1 시간 후'일 경우 N 시간 < 실제 잔여 시간 <= N+1 시간
                up_date_str = up_datetime.isoformat(timespec="hours")
            else:  # 잘못된 잔여 시간
                raise ValueError("잘못된 예약 시간: " + up_date_str)
        else:  # 연재 일자가 과거의 날짜
            from datetime import date
            ctime: date = datetime.strptime(up_date_str, "%y.%m.%d").date()  # 21.01.18 > 2021-01-18
            up_date_str = ctime.isoformat()
        ep_up_date_li.append(up_date_str)
    yield from ep_up_date_li


def novel_tags_from_page(page: str):
    """내 서재 페이지에서 링크가 담긴 HTML 태그를 추출하는 함수

    :param page: 내 서재 페이지 HTML
    """
    # HTML 응답 파싱
    from src.const.sel.css_mybook import MY_BOOK_TABLE_ROW_CSS, MY_BOOK_TITLE_CSS
    from src.const.const import PARSER

    only_my = Strainer("div", {"class": MY_BOOK_TABLE_ROW_CSS})
    my_soup = Soup(page, PARSER, parse_only=only_my).extract()
    # my_books = my_soup.select("div.novelbox", limit=30)

    only_title = Strainer("b", {"class": MY_BOOK_TITLE_CSS})
    titles = my_soup.find_all(only_title)

    yield from titles


def url_from_div_tag(div_tag: Tag):
    """HTML div 태그에서 URL을 추출하는 함수

    :param div_tag: onclick 속성을 가진 div
    :return: URL 상대 경로
    """
    click: str = div_tag.attrs["onclick"]  # click: "$('.loads').show();location = '/novel/3790123';"
    start_index: int = click.find("/novel")
    url_path: str = click[start_index: -2]

    return url_path
