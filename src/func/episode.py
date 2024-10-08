"""회차 관련 함수들

"""
from datetime import datetime
from typing import Generator
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from bs4.element import ResultSet, Tag
from bs4.filter import SoupStrainer
from requests import post

from src.const.const import DEFAULT_TIME, EP_TYPES_NAMED_TUPLE, HOST
from src.func.common import PARSER, Page
from src.func.userIO import print_under_new_line


# noinspection PyMissingOrEmptyDocstring
class Ep(Page):
    """노벨피아 회차 정보 클래스.

    :var _types: 유형 (자유/PLUS, 19금 여부)
    :var _num: 화수
    :var _letter: 글자 수
    :var _comment: 댓글 수
    """
    __slots__ = Page.__slots__ + (
        "_types",
        "_num",
        "_letter",
        "_comment",
    )

    def __init__(self,
                 title: str = '',
                 code: str = '',
                 url: str = '',
                 ctime: str = DEFAULT_TIME,
                 mtime: str = DEFAULT_TIME,
                 count_good: int = -1,
                 count_view: int = -1,
                 types: set[str] = None,
                 num: int = -1,
                 letter: int = -1,
                 comment: int = -1,
                 ):

        super().__init__(title, code, url, ctime, mtime, count_good, count_view)
        if not types:
            types = set()
        self._num = num
        self._types = types
        self._comment = comment
        self._letter = letter

    def __str__(self):
        from typing import Generator

        md_gen: Generator = ep_content_to_md(self, [])
        return ''.join(md_gen)

    def __pick_one_from(self, key: str, val: str, vals: frozenset):
        return super().pick_one_from(key, val, vals)

    def __add_one_from(self, key: str, val: str, vals: frozenset):
        return super().add_one_from(key, val, vals)

    def __set_signed_int(self, key: str, val: int):
        return super().set_signed_int(key, val)

    @property
    def types(self) -> set[str]:
        return self._types

    @types.setter
    def types(self, type: str):
        all_types = frozenset(EP_TYPES_NAMED_TUPLE)
        self.__add_one_from("_types", type, all_types)

    @property
    def num(self) -> int:
        return self._num

    @num.setter
    def num(self, num: str):
        if isinstance(num, int):
            self._num = num

        elif isinstance(num, str):
            # 정규 회차
            if num.startswith("EP"):
                num_i = int(num.lstrip("EP."))
                self.__set_signed_int("_num", num_i)

            # 보너스 회차
            if num == "BONUS":
                self._num = "BONUS"

        # 잘못된 입력
        else:
            raise ValueError(f"{num}은(는) 올바른 화수가 아니에요.")

    @property
    def letter(self) -> int:
        return self._letter

    @letter.setter
    def letter(self, letter: int):
        self.__set_signed_int("_letter", letter)

    @property
    def comment(self) -> int:
        return self._comment

    @comment.setter
    def comment(self, comment: int):
        self.__set_signed_int("_comment", comment)


def get_ep_list(novel_code: str, sort: str = "DOWN", page: int = 1, plus_login: bool = False) -> str:
    """서버에 회차 목록을 요청하고, 성공 시 HTML 응답을 반환하는 함수

    :param novel_code: 소설 번호
    :param sort: "DOWN", 첫화부터 / "UP", 최신화부터
    :param page: 요청할 페이지 번호
    :param plus_login: 로그인 키 사용 여부 (링크 추출용)
    :return: 게시일 순으로 정렬된 회차 목록의 한 페이지 (HTML)
    """
    # Chrome DevTools 에서 복사한 POST 요청 URL 및 양식 데이터
    req_url: str = urljoin(HOST, "/proc/episode_list")
    form_data: dict = {"novel_no": novel_code, "sort": sort, "page": page - 1}  # 1페이지 -> page = 0, ...
    from src.const.const import BASIC_HEADERS

    if plus_login:
        from src.func.common import add_login_key

        # 요청 헤더에 로그인 키 추가
        login_key, headers = add_login_key(BASIC_HEADERS, True)
    else:
        headers: dict = BASIC_HEADERS

    res = post(req_url, form_data, headers=headers)  # res: <Response [200]>
    ep_list_html: str = res.text

    return ep_list_html


def get_ep_view_counts(novel_code: str, ep_codes: Generator, ep_count: int):
    """입력받은 소설의 회차들의 조회수를 응답받아 반환하는 함수

    :param novel_code: 소설 번호
    :param ep_codes: 회차 번호 제너레이터
    :param ep_count: 회차의 수
    :return: 조회수 목록
    """
    url: str = urljoin(HOST, "/proc/novel")
    form_data: dict = {
        "cmd": "get_episode_count_view",
        "episode_arr[]": ["episode_count_view novel_count_view_"] * ep_count,
        "novel_no": novel_code,
    }
    from src.const.const import BASIC_HEADERS

    for i, code in enumerate(ep_codes):
        form_data["episode_arr[]"][i] += code

    res = post(url, form_data, headers=BASIC_HEADERS)

    view_cnt_json = res.text
    """{
        "status": 200,  # 유효한 요청
        "code": "",
        "errmsg": "",
        "list": [{"episode_num": 3, "count_view": "1,057"}, ...]
    }"""
    from src.func.common import load_json_w_error

    ################################################################################
    # 응답에서 회차별 조회 수 목록을 추출
    ################################################################################
    with load_json_w_error(view_cnt_json) as (res_dic, err):
        # 잘못된 요청 URL, 작업(cmd), 헤더
        # JSONDecodeError('Expecting value: line 1 column 1 (char 0)')
        if err:
            yield None
        else:
            view_cnt_dics = res_dic["list"]

    view_counts: list[int] = []

    ################################################################################
    # 회차별 조회 수 추출
    ################################################################################
    for i, dic in enumerate(view_cnt_dics):  # dic: {'count_view': '1', 'episode_no': 12606}
        view_count = int(dic["count_view"].replace(",", ""))
        view_counts.append(view_count)

    # 잘못된 요청 데이터 (ep_codes > episode_arr[], novel_code > novel_no)
    if not view_counts:
        print_under_new_line("조회수를 받지 못했어요")

        yield None

    yield from view_counts


def extract_ep_tags(list_html: str, ep_num_queue: frozenset[int]):
    """입력받은 회차 목록에서 선택한 회차들의 태그를 추출하여 하나씩 반환하는 함수

    :param list_html: 회차 목록 HTML
    :param ep_num_queue: 태그를 추출할 회차 서수의 집합
    :return: 회차 태그의 집합
    """
    from src.const.selector import EP_TABLE_CSS

    ################################################################################
    # 회차 Table 추출
    ################################################################################
    only_ep = SoupStrainer("table", {"class": EP_TABLE_CSS})
    soup = BeautifulSoup(list_html, PARSER, parse_only=only_ep)

    # 작성된 회차 無
    if len(soup.contents) == 0:
        print_under_new_line("[노벨피아] 작성된 글을 찾을 수 없습니다.")

        yield None

    from src.const.selector import EP_TAGS_CSS

    ################################################################################
    # 회차 Tag 목록 추출
    ################################################################################
    ep_tags: ResultSet[Tag] = soup.select(EP_TAGS_CSS, limit=20)

    for ep_num in ep_num_queue:
        assert ep_num > 0, "잘못된 회차 서수"

        # 회차 검색
        try:
            ep_tag: Tag = ep_tags[ep_num - 1]

        # 회차 못 찾음
        except IndexError:
            print_under_new_line("[오류]", ep_num, "번째 회차를 찾지 못했어요.")

        # 회차 찾음
        else:
            ep_tags.append(ep_tag)

    yield from ep_tags


def get_ep_up_dates(ep_tags: Generator):
    """목록에서 추출한 회차 Tag 들의 Set 에서 각각의 게시 일자를 추출하여 반환하는 함수

    :param ep_tags: 회차 Tag 목록
    :return: 입력받은 회차들의 게시 일자. 작성된 회차가 없으면 None, 입력된 회차가 없으면 list[None]
    """
    ep_up_dates: list[str | None] = []

    for ep_tag in ep_tags:
        if ep_tag is None:
            ep_up_dates.append(None)
            continue

        bold_tags: ResultSet[Tag] = ep_tag.select("b", limit=2)
        up_date_str: str = bold_tags[1].text.strip()  # 21.01.18 또는 '19시간전'

        # 24시간 이내에 게시
        if up_date_str.endswith("전"):  # upload_date: '1시간전' / '1분전'
            from datetime import timedelta
            today: datetime = datetime.today()

            if up_date_str[-2] == "분":
                min_past = int(up_date_str[:-2])
                up_datetime: datetime = today - timedelta(minutes=min_past)

                up_date_str = up_datetime.isoformat(timespec="minutes")  # 2024-07-25
            else:
                hour_past = int(up_date_str[:-3])
                up_datetime: datetime = today - timedelta(hours=hour_past)

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

            # 잘못된 잔여 시간
            else:
                raise ValueError("잘못된 예약 시간: " + up_date_str)

        # 연재 일자가 과거의 날짜
        else:
            from datetime import date

            ctime: date = datetime.strptime(up_date_str, "%y.%m.%d").date()  # 21.01.18 > 2021-01-18
            up_date_str = ctime.isoformat()

        ep_up_dates.append(up_date_str)

    yield from ep_up_dates


def extract_ep_info(list_html: str, ep_no: int = 1):
    """목록에 적힌 회차의 각종 정보를 추출하여 반환하는 함수

    :param list_html: 회차 목록 HTML
    :param ep_no: 추출할 회차의 목록 내 서수 (1부터 20까지)
    :return: 제목, 화수, 번호, 무료/성인 여부, 글자/댓글/조회/추천 수, 게시 일자
    """
    ep_tags: Generator = extract_ep_tags(list_html, frozenset({ep_no}))

    try:
        for _ in range(ep_no - 1):
            next(ep_tags)
        ep_tag: Tag = next(ep_tags)

        if not ep_tag:
            return None

    except StopIteration as si:
        print("[오류]", f"{si = }")
        return None

    # 회차 찾음, Ep 클래스 객체 생성
    ep = Ep()

    headline: Tag = ep_tag.select_one("b")  # 각종 텍스트 추출

    ################################################################################
    # 제목 추출 및 저장
    ################################################################################
    # <i class="icon ion-bookmark" id="bookmark_978" style="display:none;"></i>계월향의 꿈
    title: str = headline.select_one("i").next.text  # '001. 능력 각성'
    ep.title = title

    from src.const.selector import EP_TYPES_CSS

    ################################################################################
    # 유형 추출
    ################################################################################
    span_tags: ResultSet[Tag] | None = headline.select(EP_TYPES_CSS, limit=2)  # <span class="b_free s_inv">무료</span>

    # 예약 회차
    if not span_tags:
        from src.const.selector import EP_VIEW_CSS

        ################################################################################
        # 회차 번호 추출
        ################################################################################
        view_tag: Tag = ep_tag.select_one(EP_VIEW_CSS)
        click: str = view_tag.attrs["onclick"]  # click: "$('.loads').show();location = '/viewer/3790123';"
        start_index: int = click.find("viewer") + len("viewer") + 1
        ep_code: str = click[start_index: -2]

        # 회차 번호 저장
        ep.code = ep_code

        return ep

    types = (tag.attrs['class'][0] for tag in span_tags)  # ['b_free', 's_inv']
    from src.const.const import EP_TYPES_NAMED_TUPLE

    # 유형 저장
    if 'b_free' in types:
        ep.types.add(EP_TYPES_NAMED_TUPLE.free)

    if 'b_19' in types:
        ep.types.add(EP_TYPES_NAMED_TUPLE.adult)

    from src.const.selector import EP_STATS_CSS

    # 각종 정보 추출
    stats: Tag = ep_tag.select_one(EP_STATS_CSS)

    ################################################################################
    # 회차 화수 표기 추출
    ################################################################################
    # stats.span: <span style="~">EP.0</span>
    ep_num_tag: Tag = stats.select_one("span").extract()
    ep_num: str = ep_num_tag.text  # 'EP.1' / 'BONUS'
    """
    - 회차 목록 내 추천, 댓글 수 표기 기능이 늦게 나와서 작품 연재 시기에 따라서 회차 화수 표기의 인덱스가 다를 수 있음
    - 추천 수 추가 공지: <2021년 01월 08일 - 노벨피아 업데이트 변경사항(https://novelpia.com/notice/20/view_1392/)>
    - 댓글, 추천, 조회수 표기 공지: <2021년 01월 12일 - 노벨피아 업데이트 변경사항(https://novelpia.com/notice/20/view_3248/)>
    """
    # 화수 저장
    ep.num = ep_num

    # 각종 수치 추출
    stats_tag: Tag = stats.span

    ################################################################################
    # 회차 번호 추출
    ################################################################################
    # <span class="episode_count_view novel_count_view_7146">0</span>
    from src.const.selector import EP_VIEW_COUNT_CSS

    view_tag: Tag = stats_tag.select_one(EP_VIEW_COUNT_CSS).extract()

    from typing import Iterable

    # ("episode_count_view", "novel_count_view_7146")
    types: str | Iterable[str] = view_tag.attrs['class']
    ep_code: str = types[1].lstrip("novel_count_view_")

    # 회차 번호 및 URL 저장
    ep.code = ep_code

    viewer_url: str = urljoin(HOST, "/viewer/")
    ep.url = urljoin(viewer_url, ep_code)

    ################################################################################
    # 게시/크롤링 일자 추출 및 저장
    ################################################################################
    ep_tag_gen: Generator = (ep_tag for ep_tag in [ep_tag])
    ep_up_date_gen: Generator = get_ep_up_dates(ep_tag_gen)
    ep.ctime = next(ep_up_date_gen)

    ################################################################################
    # 소설 번호 추출
    ################################################################################
    from src.const.selector import EP_LINK_CSS

    only_link = SoupStrainer("div", {"class": EP_LINK_CSS.lstrip(".")})
    link_soup = BeautifulSoup(list_html, PARSER, parse_only=only_link)

    page_link_tag: Tag = link_soup.select_one(EP_LINK_CSS)
    click: str = page_link_tag.attrs["onclick"]  # "localStorage['novel_page_15597'] = '1'; episode_list();"
    novel_code: str = click[click.find("page") + len("page") + 1: click.find("]") - 1]

    ################################################################################
    # 조회수 추출
    ################################################################################
    ep_code_gen: Generator = (ep_code for ep_code in [ep_code])
    view_counts: Generator = get_ep_view_counts(novel_code, ep_code_gen, 1)

    # 조회수 저장
    try:
        ep.count_view = next(view_counts)
    except StopIteration as si:
        print_under_new_line("[오류]", f"{si = }")

    ################################################################################
    # 글자/댓글/추천 수 추출 및 저장
    ################################################################################
    from src.const.selector import EP_LETTER_COUNT_CSS, EP_COMMENT_COUNT_CSS, EP_RECOMMEND_COUNT_CSS

    def extract_stat(cls_sel: str) -> int | None:
        """CSS 클래스 선택자를 입력받아 수치를 추출하여 반환하는 함수

        :param cls_sel: 추출할 태그의 CSS 클래스 선택자
        :return: 추출한 수치
        """
        stat_tag: Tag = stats_tag.select_one("i." + cls_sel)

        if stat_tag is not None:
            stat = int(stat_tag.next.strip().replace(",", ""))
            return stat

        stat_name: str

        if cls_sel == EP_LETTER_COUNT_CSS:
            stat_name = "글자 수"
        elif cls_sel == EP_COMMENT_COUNT_CSS:
            stat_name = "댓글 수"
        elif cls_sel == EP_RECOMMEND_COUNT_CSS:
            stat_name = "추천 수"
        else:
            stat_name = "선택한 수치"

        print_under_new_line(stat_name, "를 찾지 못했어요")

        return None

    ep.letter, ep.comment, ep.count_good = map(extract_stat,
                                               [EP_LETTER_COUNT_CSS, EP_COMMENT_COUNT_CSS, EP_RECOMMEND_COUNT_CSS])
    """
    노벨피아 글자 수 기준은 공백 문자 및 일부 문장 부호 제외.
    공지 참고: https://novelpia.com/faq/all/view_383218/
    """
    return ep


def has_prologue(novel_code: str) -> bool:
    """소설의 회차 목록에서 프롤로그의 유무를 반환하는 함수.

    :param novel_code: 확인할 소설 번호
    :return: 프롤로그 유무 (참/거짓)
    """

    """
    - '프롤로그' 카테고리로 등록된 회차는 EP.0으로 표시
    - 에필로그 기능은 노벨피아에서 2022년 5월 16일 부로 삭제함.
    - 공지 참고: https://novelpia.com/notice/all/view_1274648/
    """

    ep_list_html: str = get_ep_list(novel_code)
    ep: Ep = extract_ep_info(ep_list_html)

    return not ep or ep.num == 0


def ep_content_to_md(ep: Ep, ep_lines: list[str]):
    """추출한 회차 정보와 본문 줄별 목록을 받아 Markdown 제너레이터를 반환하는 함수

    :param ep: Ep 클래스의 객체
    :param ep_lines: 회차 본문 줄별 목록
    """
    property_lines: list[str] = [
        "공개 일자: " + ep.ctime,
        "회차 링크: " + ep.url,
        "화수: " + str(ep.num),
        "댓글 수: " + str(ep.comment),
        "글자 수: " + str(ep.letter),
        "조회 수: " + str(ep.count_view),
        "추천 수: " + str(ep.count_good)
    ]
    property_lines = ["---"] + property_lines
    property_lines.append("---")

    property_str: str = "\n".join(property_lines) + "\n"
    md_lines: list[str] = [property_str] + ep_lines

    yield from md_lines


def ep_content_to_html(ep: Ep, lines: list[str]):
    """회차 제목과 본문을 입력받아 HTML 문서 제너레이터를 반환하는 함수

    :param ep: Ep 클래스 객체
    :param lines: 회차 본문 줄 목록
    :return: HTML 문서를 한 줄씩 반환하는 제너레이터
    """
    print(ep)
    contents: list[str] = []
    # style_attr: str = '\"font-size: 18px; line-height: 125%; max-width: 900px; margin: 0px auto;\"'
    # '<div style=' + style_attr + '>\n'

    tabs: str = "\t\t\t\t"
    line_break: str = tabs + "<br>\n"

    # 본문 HTML 조립
    for line in lines:
        if line == "&nbsp;\n":
            contents.append(line_break)
        else:
            paragraph: str = tabs + "<p>" + line.rstrip() + "</p>\n"
            contents.append(paragraph)

    # css_file_path = Path.cwd().joinpath("html/style.css")

    yield from contents
