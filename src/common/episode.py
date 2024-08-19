from bs4 import BeautifulSoup
from bs4.element import ResultSet, Tag
from requests import post

from src.common.module import Page, ua
from src.common.userIO import print_under_new_line


class Ep(Page):
    __slots__ = "_ctime", "_type", "_num", "_letter", "_view", "_comment", "_recommend"

    def __init__(self):
        super().__init__()
        self._ctime = None
        self._num = None
        self._type = None
        self._comment = None
        self._letter = None

    def __pick_one_from(self, key: str, val: str, vals: frozenset):
        return super().pick_one_from(key, val, vals)

    def __set_signed_int(self, key: str, val: int):
        return super().set_signed_int(key, val)

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, type: str):
        types = frozenset(["자유", "PLUS", "성인"])
        self.__pick_one_from("_type", type, types)

    @property
    def num(self):
        return self._num

    @num.setter
    def num(self, num: str):
        # 정규 회차
        if num.startswith("EP"):
            num_i = int(num.lstrip("EP."))
            self.__set_signed_int("_num", num_i)

        # 보너스 회차
        elif isinstance(num, str) and num == "BONUS":
            self._num = num

        # 잘못된 입력
        else:
            raise ValueError(f"{num}은(는) 올바른 화수가 아니에요.")

    @property
    def letter(self):
        return self._letter

    @letter.setter
    def letter(self, letter: int):
        self.__set_signed_int("_letter", letter)

    @property
    def comment(self):
        return self._comment

    @comment.setter
    def comment(self, comment: int):
        self.__set_signed_int("_comment", comment)


def get_ep_list(code: str, sort: str = "DOWN", page: int = 1, login: bool = True) -> str:
    """서버에 회차 목록을 요청하고, 성공 시 HTML 응답을 반환하는 함수

    :param code: 소설 번호
    :param sort: "DOWN", 첫화부터 / "UP", 최신화부터
    :param page: 요청할 페이지 번호
    :param login: 로그인 키 사용 여부 (링크 추출용)
    :return: 게시일 순으로 정렬된 회차 목록의 한 페이지 (HTML)
    """
    # Chrome DevTools 에서 복사한 POST 요청 URL 및 양식 데이터
    req_url: str = "https://novelpia.com/proc/episode_list"
    form_data: dict = {"novel_no": code, "sort": sort, "page": page - 1}  # 1페이지 -> page = 0, ...
    headers: dict[str: str] = {'User-Agent': ua}

    # 요청 헤더에 로그인 키 추가
    if login:
        from src.common.module import add_login_key
        login_key, headers = add_login_key(headers)

    res = post(url=req_url, data=form_data, headers=headers)  # res: <Response [200]>
    ep_list_html: str = res.text

    return ep_list_html


def get_ep_view_counts(novel_code: str, ep_codes: frozenset[str]) -> list[int] | None:
    """입력받은 소설의 회차들의 조회수를 응답받아 반환하는 함수

    :param novel_code: 회차가 속한 소설 번호
    :param ep_codes: 조회수를 받아올 회차들의 번호
    :return: 조회수 목록
    """
    ep_count: int = len(ep_codes)
    if ep_count < 1:
        print_under_new_line("회차를 한 개 이상 선택하세요")
        return None

    url: str = "https://novelpia.com/proc/novel"
    form_data: dict = {
        "cmd": "get_episode_count_view",
        "episode_arr[]": ["episode_count_view novel_count_view_"] * ep_count,
        "novel_no": novel_code,
    }
    headers: dict = {"User-Agent": ua}

    from src.common.module import add_login_key
    login_key, headers = add_login_key(headers)

    for i, code in enumerate(ep_codes):
        form_data["episode_arr[]"][i] += code

    res = post(url, form_data, headers=headers)

    view_cnt_json = res.text
    """{
        "status": 200,  # 유효한 요청
        "code": "",
        "errmsg": "",
        "list": [{"episode_num": 3, "count_view": "1,057"}, ...]
    }"""

    # 응답에서 회차별 조회수 목록을 추출
    from src.common.module import load_json_w_error
    with load_json_w_error(view_cnt_json) as (res_dic, err):
        # 잘못된 요청 URL, 작업(cmd), 헤더
        # JSONDecodeError('Expecting value: line 1 column 1 (char 0)')
        if err:
            return None
        else:
            view_cnt_dics: list[dict] = res_dic["list"]

    view_counts: list[int] = [-1] * ep_count

    for i, dic in enumerate(view_cnt_dics):  # dic: {'count_view': '1', 'episode_no': 12606}
        view_count: str = dic["count_view"]
        view_counts[i] = int(view_count.replace(",", ""))

    # 잘못된 요청 데이터 (ep_codes > episode_arr[], novel_code > novel_no)
    if view_counts == [-1] * ep_count:
        print_under_new_line("조회수를 받지 못했어요")
        return None

    return view_counts


def extract_ep_tags(list_soup: BeautifulSoup, ep_num_queue: frozenset[int]):
    """입력받은 회차 목록에서 선택한 회차들의 태그를 추출하여 하나씩 반환하는 제너레이터 함수

    :param list_soup: 회차 목록
    :param ep_num_queue: 태그를 추출할 회차 서수의 집합
    :return: 회차 태그의 집합
    """
    list_table: Tag | None = list_soup.table  # 회차 목록 표 추출

    # 작성된 회차 無
    if list_table is None:
        print_under_new_line("[노벨피아] 작성된 글을 찾을 수 없습니다.")
        return None

    # 회차 Tag 목록 추출
    list_set: ResultSet[Tag] = list_table.select("tr.ep_style5")

    ep_tags: list[Tag] = []

    for ep_num in ep_num_queue:
        assert ep_num > 0, "잘못된 회차 서수"
        try:  # 입력받은 서수의 회차 검색
            ep_tag: Tag = list_set[ep_num - 1]
        except IndexError:  # 회차 못 찾음
            print_under_new_line("[오류]", str(ep_num) + "번째 회차를 찾지 못했어요.")
        else:  # 회차 찾음
            ep_tags.append(ep_tag)

    return ep_tags


def get_ep_up_dates(ep_tags: frozenset[Tag]) -> list[str | None] | None:
    """목록에서 추출한 회차 Tag 들의 Set 에서 각각의 게시 일자를 추출하여 반환하는 함수

    :param ep_tags: 회차 Tag 목록
    :return: 입력받은 회차들의 게시 일자. 작성된 회차가 없으면 None, 입력된 회차가 없으면 list[None]
    """
    if not any(ep_tags):
        return None

    ep_up_dates: list[str | None] = []

    for ep_tag in ep_tags:
        if ep_tag is None:
            ep_up_dates.append(None)
            continue

        bold_tags: ResultSet[Tag] = ep_tag.select("b")
        up_date_str: str = bold_tags[1].text.strip()  # 21.01.18 또는 '19시간전'

        from datetime import datetime

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
            from datetime import timedelta
            today: datetime = datetime.today()

            # 예약 회차는 공개 하루 전부터 노출
            if up_date_str[1].isnumeric():
                end_index: int = 1
            else:
                end_index: int = 0

            assert end_index != -1

            # 남은 시간이 1시간 미만
            if up_date_str[end_index + 1] == "분":
                min_left = int(up_date_str[:end_index + 1])
                up_datetime = today + timedelta(minutes=min_left)

                up_date_str = up_datetime.isoformat(timespec="minutes")

            # 남은 시간이 1시간 이상 하루 미만
            elif up_date_str[end_index + 1] == "시":
                hour_left = int(up_date_str[:end_index + 1])
                if hour_left == 24:
                    up_datetime = today + timedelta(days=1)
                else:
                    up_datetime = today + timedelta(hours=hour_left)

                # 'N+1 시간 후'일 경우 N 시간 < 실제 잔여 시간 <= N+1 시간
                up_date_str = up_datetime.isoformat(timespec="hours")
            else:
                raise ValueError("잘못된 예약 시간: " + up_date_str)

        # 연재 일자가 과거의 날짜
        else:
            from datetime import date
            ctime: date = datetime.strptime(up_date_str, "%y.%m.%d").date()  # 21.01.18 > 2021-01-18
            up_date_str = ctime.isoformat()

        ep_up_dates.append(up_date_str)

    return ep_up_dates


def extract_ep_info(list_html: str, ep_no: int = 1):
    """목록에 적힌 회차의 각종 정보를 추출하여 반환하는 함수

    :param list_html: 회차 목록 HTML
    :param ep_no: 추출할 회차의 목록 내 서수 (1부터 20까지)
    :return: 제목, 화수, 번호, 무료/성인 여부, 글자/댓글/조회/추천 수, 게시 일자
    """
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(list_html, "html.parser")

    ep_tags = extract_ep_tags(soup, frozenset({ep_no}))

    if ep_tags is None or ep_tags == [None]:
        return None

    ep_tag: Tag = ep_tags[0]

    # 회차 찾음
    # Ep 클래스 객체 생성
    ep = Ep()

    headline: Tag = ep_tag.b  # 각종 텍스트 추출

    # 제목 추출 및 저장
    # <i class="icon ion-bookmark" id="bookmark_978" style="display:none;"></i>계월향의 꿈
    ep.title = headline.i.next

    # 유형 추출
    span_tags: ResultSet[Tag] | None = headline.select("span.s_inv")  # <span class="b_free s_inv">무료</span>

    # 예약 회차
    if span_tags is None:
        # 회차 번호 추출
        view_tag: Tag = ep_tag.select_one("td.font12")
        click: str = view_tag.attrs["onclick"]  # click: "$('.loads').show();location = '/viewer/3790123';"
        start_index: int = click.find("viewer") + 7
        ep_code: str = click[start_index: -2]

        # 회차 번호 저장
        ep.code = ep_code

        return ep

    from typing import Iterable  # Type Hint: str | Iterable[str]
    types: list[str] = [tag.attrs['class'][0] for tag in span_tags]  # ['b_free', 's_inv']

    # 유형 저장
    if 'b_free' in types:
        ep.type = "자유"

    if 'b_19' in types:
        ep.type = "성인"

    # 각종 정보 추출
    stats: Tag = ep_tag.select_one("div.ep_style2 font")

    # 회차 화수 표기 추출
    # stats.span: <span style="~">EP.0</span>
    ep_no: str = stats.span.text  # 'EP.1' / 'BONUS'
    """
    - 회차 목록 내 추천, 댓글 수 표기 기능이 늦게 나와서 작품 연재 시기에 따라서 회차 화수 표기의 인덱스가 다를 수 있음
    - 추천 수 추가 공지: <2021년 01월 08일 - 노벨피아 업데이트 변경사항(https://novelpia.com/notice/20/view_1392/)>
    - 댓글, 추천, 조회수 표기 공지: <2021년 01월 12일 - 노벨피아 업데이트 변경사항(https://novelpia.com/notice/20/view_3248/)>
    """
    # 화수 저장
    ep.num = ep_no

    # 각종 수치 추출
    stats_tag: Tag = stats.select("span")[1]

    # 회차 번호 추출
    # <span class="episode_count_view novel_count_view_7146">0</span>
    view_tag: Tag = stats_tag.select_one(".episode_count_view")

    # ("episode_count_view", "novel_count_view_7146")
    types: str | Iterable[str] = view_tag.attrs['class']
    ep_code: str = types[1].lstrip("novel_count_view_")

    # 회차 번호 저장
    ep.code = ep_code

    assert isinstance(int(ep_code), int), "잘못된 회차 번호"

    # 소설 번호 추출
    page_link_tag: Tag = soup.select_one(".page-link")
    click: str = page_link_tag.attrs["onclick"]  # "localStorage['novel_page_15597'] = '1'; episode_list();"
    novel_code: str = click[click.find("page") + 5: click.find("]") - 1]

    assert isinstance(int(novel_code), int), "잘못된 소설 번호"

    # 조회수 추출
    view_counts: list[int] | None = get_ep_view_counts(novel_code, frozenset([ep_code]))

    # 조회수 저장
    if view_counts is not None:
        ep.view = view_counts[0]

    def flatten(tag: Tag) -> int:
        return int(tag.next.strip().replace(",", ""))

    def extract_stat(cls_sel: str) -> int | None:
        """
        CSS 클래스 선택자를 입력받아 수치를 추출하여 반환하는 함수

        :param cls_sel: 추출할 태그의 CSS 클래스 선택자
        :return: 추출한 수치
        """
        stat_tag: Tag = stats_tag.select_one("i." + cls_sel)

        if stat_tag is not None:
            return flatten(stat_tag)

        stat_type: str = cls_sel.lstrip("ion-")
        stat_name: str | None = None

        if stat_type.startswith("doc"):
            stat_name = "글자 수"
        elif stat_type.startswith("chat"):
            stat_name = "댓글 수"
        elif stat_type.startswith("thumb"):
            stat_name = "추천 수"
        elif stat_name is None:
            stat_name = "선택한 수치"

        print_under_new_line(stat_name + "를 찾지 못했어요")
        return None

    # 글자/댓글/추천 수 저장
    ep.letter = extract_stat("ion-document-text")
    """
    노벨피아 글자 수 기준은 공백 문자 및 일부 문장 부호 제외.
    공지 참고: https://novelpia.com/faq/all/view_383218/
    """
    ep.comment = extract_stat("ion-chatbox-working")
    ep.recommend = extract_stat("ion-thumbsup")

    # 게시 일자 추출 및 저장
    ep.ctime = get_ep_up_dates(frozenset({ep_tag}))[0]

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
    ep_list_html: str = get_ep_list(novel_code, "DOWN", 1)
    ep = extract_ep_info(ep_list_html, 1)

    return ep.num == 0


def ep_content_to_md(ep: Ep, ep_lines: list[str]):
    """추출한 회차 정보와 본문 줄별 목록을 받아 Markdown 제너레이터를 반환하는 함수

    :param ep: Ep 클래스의 객체
    :param ep_lines: 회차 본문 줄별 목록
    :type: list[str]
    :rtype: Generator
    """
    property_lines: list[str] = ["공개 일자: " + ep.ctime, "회차 링크: " + ep.url, "화수: " + str(ep.num),
                                 "댓글 수: " + str(ep.comment), "글자 수: " + str(ep.letter), "조회 수: " + str(ep.view),
                                 "추천 수: " + str(ep.recommend)]

    property_lines = ["---"] + property_lines
    property_lines.append("---")

    property_str: str = "\n".join(property_lines) + "\n"
    md_lines: list[str] = [property_str] + ep_lines

    yield from md_lines


def ep_content_to_html(lines: list[str]):
    """회차 제목과 본문을 입력받아 HTML 문서 제너레이터를 반환하는 함수

    :param lines: 회차 본문 줄 목록
    :type: list[str]
    :return: HTML 문서를 한 줄씩 반환하는 제너레이터
    :rtype: Generator
    """
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
