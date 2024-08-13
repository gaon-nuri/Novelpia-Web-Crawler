import bs4
from bs4.element import ResultSet, Tag
from requests import post

from src.common.module import ua
from src.common.userIO import print_under_new_line


def get_ep_list(code: str, sort: str = "DOWN", page: int = 1, login: bool = False) -> str:
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

    return res.text


def get_ep_view_counts(novel_code: str, ep_codes: list[str]) -> list[int] | None:
    """입력받은 소설의 회차들의 조회수를 응답받아 반환하는 함수

    :param novel_code: 회차가 속한 소설 번호
    :param ep_codes: 조회수를 받아올 회차들의 번호
    :return: 조회수 목록
    """
    ep_count: int = len(ep_codes)

    url: str = "https://novelpia.com/proc/novel"
    form_data: dict = {
        "cmd": "get_episode_count_view",
        "episode_arr[]": ["episode_count_view novel_count_view_"] * ep_count,
        "novel_no": novel_code,
    }
    headers: dict = {
        "User-Agent": ua,
    }
    for i, code in enumerate(ep_codes):
        form_data["episode_arr[]"][i] += code

    res = post(url, form_data, headers=headers)

    view_cnt_json = res.text
    """{
        "status": 200,  # 유효한 요청
        "code": "",
        "errmsg": "",
        "list": [{"episode_no": 3, "count_view": "1,057"}, ...]
    }"""

    # 응답에서 회차별 조회수 목록을 추출
    from json import JSONDecodeError
    try:
        from json import loads
        view_cnt_dics: list[dict] = loads(view_cnt_json)["list"]

    # 잘못된 요청 URL, 작업(cmd), 헤더
    # JSONDecodeError('Expecting value: line 1 column 1 (char 0)')
    except JSONDecodeError as je:
        print_under_new_line("예외 발생: " + f"{je = }")

        return None

    view_counts: list[int] = [-1] * ep_count

    for i, dic in enumerate(view_cnt_dics):  # dic: {'count_view': '1', 'episode_no': 12606}
        view_count: str = dic["count_view"]
        view_counts[i] = int(view_count.replace(",", ""))

    # 잘못된 요청 데이터 (ep_codes > episode_arr[], novel_code > novel_no)
    if view_counts == [-1]:
        print_under_new_line("조회수를 받지 못했어요")
    # assert view_counts != [-1] * ep_count, "조회수를 받지 못했어요."

    return view_counts


def extract_ep_tags(list_soup: bs4.BeautifulSoup, ep_no_li: set[int]) -> list[Tag | None] | None:
    list_table: Tag | None = list_soup.table  # 회차 목록 표 추출

    # 작성된 회차 無
    if list_table is None:
        return None

    # 회차 Tag 목록 추출
    list_set: ResultSet[Tag] = list_table.select("tr.ep_style5")
    ep_tags: list[Tag | None] = []

    for ep_no in ep_no_li:
        assert ep_no > 0, "잘못된 회차 서수"
        try:  # 입력받은 서수의 회차 검색
            ep_tag: Tag = list_set[ep_no - 1]
        except IndexError:  # 회차 못 찾음
            print_under_new_line("[오류]", str(ep_no) + "번째 회차를 찾지 못했어요.")
        else:  # 회차 찾음
            ep_tags += [ep_tag]
    return ep_tags


def get_ep_up_dates(ep_tags: set[Tag]) -> list[str | None] | None:
    """목록에서 추출한 회차 Tag 들의 Set 에서 각각의 게시 일자를 추출하여 반환하는 함수

    :param ep_tags: 회차 Tag 목록
    :return: 첫/마지막 회차 게시 일자. 작성된 회차가 없으면 None
    """
    if ep_tags is None:
        return None

    ep_up_dates: list[str | None] = []

    for ep_tag in ep_tags:
        if ep_tag is None:
            ep_up_dates += [None]
            continue

        bold_tags: ResultSet[Tag] = ep_tag.select("b")
        up_date_str: str = bold_tags[1].text.strip()  # 21.01.18 또는 '19시간전'

        # 24시간 이내에 게시된 경우 게시일을 당일로 설정
        if up_date_str.endswith("전"):  # upload_date: '19시간전'
            from datetime import date
            today: date = date.today()
            up_date_str = str(today)  # 2024-07-25

        # 예약 회차
        elif up_date_str.endswith("후"):
            from datetime import datetime
            now: datetime = datetime.now()
            up_moment: datetime = now

            # 예약 회차는 공개 하루 전부터 노출
            min_index: int = up_date_str.find("분")
            if min_index != -1:
                min_left = int(up_date_str[:min_index])
                up_moment = now.replace(hour=now.minute+min_left)

            # 'N+1 시간 후'일 경우 N 시간 < 실제 잔여 시간 <= N+1 시간
            hour_index: int = up_date_str.find("시간")
            if hour_index != -1:
                hour_left = int(up_date_str[:hour_index])
                up_moment = now.replace(hour=now.hour+hour_left)

            up_date_str = up_moment.strftime("%Y-%m-%dT%H:%M:%S")
        else:
            up_date_str = ("20" + up_date_str).replace(".", "-")  # 21.01.18 > 2021-01-18

        ep_up_dates += [up_date_str]

    return ep_up_dates


def extract_ep_info(list_html: str, ep_no: int = 1) -> dict | None:
    """목록에 적힌 회차의 각종 정보를 추출하여 반환하는 함수

    :param list_html: 회차 목록 HTML
    :param ep_no: 추출할 회차의 목록 내 서수 (1부터 20까지)
    :return: 제목, 화수, 번호, 무료/성인 여부, 글자/댓글/조회/추천 수, 게시 일자
    """
    from bs4 import BeautifulSoup
    list_soup = BeautifulSoup(list_html, "html.parser")

    ep_tag: Tag = extract_ep_tags(list_soup, {ep_no})[0]

    # 회차 찾음
    headline: Tag = ep_tag.b  # 각종 텍스트 추출

    info_dic: dict = {}.fromkeys({"제목", "게시 일자"})
    info_dic["위치"]: dict = {}.fromkeys({"화수", "번호"})
    info_dic["유형"]: dict = {}.fromkeys({"무료", "성인"}, False)
    info_dic["통계"]: dict = {}.fromkeys({"글자 수", "조회수", "댓글 수", "추천 수"})

    # 제목 추출 및 저장
    # <i class="icon ion-bookmark" id="bookmark_978" style="display:none;"></i>계월향의 꿈
    info_dic["제목"] = headline.i.next

    # 유형 추출
    span_tags: ResultSet[Tag] | None = headline.select(".s_inv")  # <span class="b_free s_inv">무료</span>

    # 예약 회차
    if span_tags is None:
        pass

    from typing import Iterable  # Type Hint: str | Iterable[str]
    class_s: str | Iterable[str] = span_tags[0].attrs['class']  # ['b_free', 's_inv']

    # 유형 저장
    if 'b_free' in class_s:
        info_dic["유형"]["무료"] = True

    if len(span_tags) > 1:
        info_dic["유형"]["성인"] = True

    # 각종 정보 추출
    stats: Tag = ep_tag.select_one("div.ep_style2 font")

    # 회차 화수 표기 추출
    # stats.span: <span style="~">EP.0</span>
    no_string: str = stats.span.text  # 'EP.1' / 'BONUS'
    """
    - 회차 목록 내 추천, 댓글 수 표기 기능이 늦게 나와서 작품 연재 시기에 따라서 회차 화수 표기의 인덱스가 다를 수 있음
    - 추천 수 추가 공지: <2021년 01월 08일 - 노벨피아 업데이트 변경사항(https://novelpia.com/notice/20/view_1392/)>
    - 댓글, 추천, 조회수 표기 공지: <2021년 01월 12일 - 노벨피아 업데이트 변경사항(https://novelpia.com/notice/20/view_3248/)>
    """

    # 화수 저장
    if no_string.startswith("EP"):
        ep_num = int(no_string.lstrip("EP."))
        info_dic["위치"]["화수"] = ep_num

    # 보너스 회차
    else:
        info_dic["위치"]["화수"] = 'BONUS'

    # 각종 수치 추출
    stats_tag: Tag = stats.select("span")[1]

    # 회차 번호 추출
    # <span class="episode_count_view novel_count_view_7146">0</span>
    view_tag: Tag = stats_tag.select_one(".episode_count_view")

    # ("episode_count_view", "novel_count_view_7146")
    class_s: str | Iterable[str] = view_tag.attrs['class']
    ep_code: str = class_s[1].lstrip("novel_count_view_")

    # 회차 번호 저장
    info_dic["위치"]["번호"] = ep_code

    assert isinstance(int(ep_code), int), "잘못된 회차 번호"

    # 소설 번호 추출
    page_link_tag: Tag = list_soup.select_one(".page-link")
    click: str = page_link_tag.attrs["onclick"]  # "localStorage['novel_page_15597'] = '1'; episode_list();"
    novel_code: str = click[click.find("page") + 5: click.find("]") - 1]

    assert isinstance(int(novel_code), int), "잘못된 소설 번호"

    # 조회수 추출
    view_counts: list[int] = get_ep_view_counts(novel_code, [ep_code])

    # 조회수 저장
    if len(view_counts) == 1 and view_counts != [-1]:
        info_dic["통계"]["조회수"] = view_counts[0]

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

        if stat_name is None:
            stat_name = "선택한 수치"

        print_under_new_line(stat_name + "를 찾지 못했어요")

        return None

    # 글자/댓글/추천 수 저장
    info_dic["통계"]["글자 수"] = extract_stat("ion-document-text")
    """
    노벨피아 글자 수 기준은 공백 문자 및 일부 문장 부호 제외.
    공지 참고: https://novelpia.com/faq/all/view_383218/
    """
    info_dic["통계"]["댓글 수"] = extract_stat("ion-chatbox-working")
    info_dic["통계"]["추천 수"] = extract_stat("ion-thumbsup")

    # 게시 일자 추출 및 저장
    info_dic["게시 일자"] = get_ep_up_dates({ep_tag})

    return info_dic


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
    ep_list_html: str = get_ep_list(novel_code, "DOWN", 1, login=False)
    info_dic: dict = extract_ep_info(ep_list_html, 1)

    return info_dic["위치"]["화수"] == 0
