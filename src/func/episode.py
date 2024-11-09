"""회차 관련 함수들

"""
from typing import Generator, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from bs4.element import ResultSet, Tag
from bs4.filter import SoupStrainer

from .crawl import fetch_ep_li_pg_from_code, fetch_ep_view_gen_from_code_gen
from ..const.const import BASE_URL, PARSER
from ..func.userio import print_under_new_line
from ..models import Ep
from ..parsers import ep_tag_gen_from_page, ep_up_date_gen_from_tags


def ep_obj_from_page(list_page: str, ep_no: int = 1):
    """목록에 적힌 회차의 각종 정보를 추출하여 반환하는 함수

    :param list_page: 회차 목록 HTML
    :param ep_no: 추출할 회차의 목록 내 서수 (1부터 20까지)
    :return: 제목, 화수, 번호, 무료/성인 여부, 글자/댓글/조회/추천 수, 게시 일자
    """
    ep_tags: Generator = ep_tag_gen_from_page(list_page, [ep_no])

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

    from ..const.sel.css_ep import EP_TYPES_CSS

    ################################################################################
    # 유형 추출
    ################################################################################
    span_tags: ResultSet[Tag] | None = headline.select(EP_TYPES_CSS, limit=2)  # <span class="b_free s_inv">무료</span>

    # 예약 회차
    if not span_tags:
        from ..const.sel.css_ep import EP_VIEW_CSS

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
    from ..const.const import EP_TYPES_NAMED_TU

    # 유형 저장
    if 'b_free' in types:
        ep.kinds.add(EP_TYPES_NAMED_TU.free)

    if 'b_19' in types:
        ep.kinds.add(EP_TYPES_NAMED_TU.adult)

    from ..const.sel.css_ep import EP_STATS_CSS

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
    from ..const.sel.css_ep import EP_VIEW_COUNT_CSS

    view_tag: Tag = stats_tag.select_one(EP_VIEW_COUNT_CSS).extract()

    from typing import Iterable

    # ("episode_count_view", "novel_count_view_7146")
    types: str | Iterable[str] = view_tag.attrs['class']
    ep_code: str = types[1].lstrip("novel_count_view_")

    # 회차 번호 및 URL 저장
    ep.code = ep_code

    viewer_url: str = urljoin(BASE_URL, "/viewer/")
    ep.url = urljoin(viewer_url, ep_code)

    ################################################################################
    # 게시/크롤링 일자 추출 및 저장
    ################################################################################
    ep_tag_gen = (ep_tag for ep_tag in [ep_tag])
    ep_up_date_gen: Generator = ep_up_date_gen_from_tags(ep_tag_gen)
    ep.ctime = next(ep_up_date_gen)

    ################################################################################
    # 소설 번호 추출
    ################################################################################
    from ..const.sel.css_ep import EP_LINK_CSS

    only_link = SoupStrainer("div", {"class": EP_LINK_CSS.lstrip(".")})
    link_soup = BeautifulSoup(list_page, PARSER, parse_only=only_link)

    page_link_tag: Tag = link_soup.select_one(EP_LINK_CSS)
    click: str = page_link_tag.attrs["onclick"]  # "localStorage['novel_page_15597'] = '1'; episode_list();"
    novel_code: str = click[click.find("page") + len("page") + 1: click.find("]") - 1]

    ################################################################################
    # 조회수 추출
    ################################################################################
    ep_code_gen = (ep_code for ep_code in [ep_code])
    view_counts: Generator = fetch_ep_view_gen_from_code_gen(novel_code, ep_code_gen, 1)

    # 조회수 저장
    try:
        ep.count_view = next(view_counts)
    except StopIteration as si:
        print_under_new_line("[오류]", f"{si = }")

    ################################################################################
    # 글자/댓글/추천 수 추출 및 저장
    ################################################################################
    from ..const.sel.css_ep import EP_LETTER_COUNT_CSS, EP_COMMENT_COUNT_CSS, EP_RECOMMEND_COUNT_CSS

    def extract_stat(cls_sel: str) -> Optional[int]:
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

    ep_list_page: str = fetch_ep_li_pg_from_code(novel_code)
    ep: Ep = ep_obj_from_page(ep_list_page)

    return not ep or ep.num == 0


def ep_page_from_lines(ep: Ep, lines: list[str]):
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

    # css_file_path = Path.cwd().joinpath("page/style.css")

    yield from contents
