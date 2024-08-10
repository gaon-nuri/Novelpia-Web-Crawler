import json
import os  # os.environ[]
import time
from pathlib import Path
from typing import Iterable  # Type Hint: str | Iterable[str]

import requests as req
from bs4 import BeautifulSoup
from bs4.element import ResultSet, Tag

# Windows Chrome User-Agent String
ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'


def print_under_new_line(*msg: object) -> None:
    print()
    print(*msg)


def get_env_var(key: str) -> str | None:
    """
    입력받은 이름의 환경 변수를 찾아서 값을 반환하는 함수

    :param key: 이름
    :return: 값
    """
    # 환경 변수 有, 반환
    try:
        return os.environ[key]

    # 환경 변수 無, 빈 문자열 반환
    except KeyError as ke:
        print_under_new_line(f"예외 발생: {ke = }")
        print(f"환경 변수 '{key}' 을 찾지 못했어요.")
        return None


def add_login_key(headers: dict[str: str]) -> (str, dict):
    """
    입력받은 헤더에 로그인 키를 추가해서 반환하는 함수

    :param headers: 로그인 키를 추가할 헤더
    :return: 추가한 로그인 키, 새 헤더
    """
    login_key: str = get_env_var("LOGINKEY")

    # 로그인 키 유무 검사
    assert login_key is not None, "로그인 키 無"

    # 로그인 키 有
    cookie: str = "LOGINKEY=" + login_key
    headers["Cookie"] = cookie

    return login_key, headers


def ask_for_num(num_type: str) -> int:
    """
    유효한 번호를 얻을 때까지 입력을 받는 함수

    :param num_type:
    :return: 번호 (자연수)
    """
    while True:
        number_string: str = str(int(ask_for_str("[입력] " + num_type, int)))  # 01, 001,... > 1
        is_valid_num: bool = ask_for_permission(f"[확인] {num_type}가 {number_string}인가요?")[1]
        number = int(number_string)

        # 유효한 소설 번호 (자연수)
        if is_valid_num and number >= 0:
            return number


def chk_str_type(in_str: str, check_type: type = str) -> bool:
    """
    문자열의 형식을 검사하는 함수

    :param in_str: 형식을 검사할 문자열
    :param check_type: 문자열에 기대하는 형식
    :return: 형식이 올바르면 참, 그렇지 않으면 거짓
    """
    check_str = in_str.strip()

    if check_type == str:
        return check_str.isascii()
    elif check_type == int:
        return check_str.isnumeric()
    else:
        try:
            return isinstance(check_type(check_str), check_type)

        # 해당 형식으로 변환할 수 없는 문자열
        except ValueError as ve:
            print_under_new_line(f"예외 발생: {ve = }")
            return False


def ask_for_str(prompt: str = "입력", type: type = str) -> str:
    """
    문자열을 입력받고, 그 형식이 유효하면 반환하는 함수

    :param prompt: 문자열을 입력하라는 메시지
    :param type: 입력받을 문자열이 뜻하는 타입
    :return: 유효한 입력 문자열
    """

    # 유효한 형식의 문자열을 입력받을 때까지 반복
    while True:
        print()
        answer_str: str = input(f"{prompt}: ").strip()
        is_valid_string = chk_str_type(answer_str, type)

        # 빈 문자열
        if len(answer_str) == 0:
            print_under_new_line("[오류] 입력을 받지 못했어요. 이전 단계로 돌아갈게요.")
            continue

        # 무효한 문자열
        if not is_valid_string:
            print_under_new_line("[오류] 잘못된 입력이에요. 이전 단계로 돌아갈게요.")
            continue
        return answer_str


def ask_for_permission(question: str, condition: bool = True) -> (bool, bool):
    """
    사용자의 의사를 묻고 동의 여부를 출력하는 함수

    :param question: 사용자에게 물어볼 질문
    :param condition: 질문 여부를 결정하는 진리값
    :return:(질문 여부 = 항상 True, 동의 여부 - True/False)
    """
    while condition:
        # 질문을 하고 답변을 Y, y, N, n 중 하나로 받음
        user_answer: str = ask_for_str(f"{question} (Y/n)").strip().capitalize()
        if user_answer == "Y":
            return True, True  # 질문 함, 동의 함
        elif user_answer == "N":
            return True, False  # 질문 함, 동의 안 함
        else:
            print_under_new_line("[동의] 동의하면 Y나 y, 그러지 않으면 N이나 n을 눌러 주세요.")


def assure_path_exists(path_to_assure: Path) -> None:
    """
    파일/폴더의 상위 폴더가 다 있으면 넘어가고 없으면 만드는 함수.

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


def get_novel_main_page(url: str) -> str | None:
    """
    서버에 소설의 메인 페이지를 요청하고, HTML 응답을 반환하는 함수

    :param url: 요청 URL
    :return: HTML 응답, 접속 실패 시 None
    """
    headers: dict = {'User-Agent': ua}

    try:
        # 소설 메인 페이지의 HTML 문서를 요청
        res = req.get(url=url, headers=headers)  # res: <Response [200]>

    # 접속 실패
    except req.exceptions.ConnectionError as ce:
        err_msg: str = ce.args[0].args[0]
        index: int = err_msg.find("Failed")
        print_under_new_line(err_msg[index:-42])
        return None

    # 성공
    else:
        html: str = res.text
        assert html != "", "빈 HTML"
        return html


def open_file_if_none(file_name: Path) -> None:
    assure_path_exists(file_name)

    # 기존 파일 유무 확인, 있으면 갱신 여부 질문
    is_old_file_exist: bool = file_name.exists()

    # 기존 파일 有
    if is_old_file_exist:
        mtime: str = time.ctime(file_name.stat().st_mtime)
        question: str = f"[확인] {mtime} 에 수정된 파일이 있어요. 덮어 쓸까요?"

        # 사용자에게 덮어쓸 것인지 질문
        asked_overwrite_file, can_overwrite_file = ask_for_permission(question)

        # 덮어쓸 경우
        if can_overwrite_file:
            print_under_new_line("[알림]", file_name, "파일에 덮어 썼어요.")  # 기존 파일 有, 덮어쓰기
            print()

        # 기존 파일을 유지, 덮어쓰지 않고 종료
        else:
            exit("[알림] 기존 파일이 있으니 파일 생성은 건너 뛸게요.")

    # 기존 파일 無, 새로 내려받기
    else:
        print_under_new_line("[알림]", file_name, "에 새로 만들었어요.")


def get_ep_list(code: str, sort: str = "DOWN", page: int = 1, use_login_key: bool = False) -> str:
    """
    서버에 회차 목록을 요청하고, 성공 시 HTML 응답을 반환하는 함수

    :param code: 소설 번호
    :param sort: "DOWN", 첫화부터 / "UP", 최신화부터
    :param page: 요청할 페이지 번호
    :param use_login_key: 로그인 키 사용 여부 (링크 추출용)
    :return: 게시일 순으로 정렬된 회차 목록의 한 페이지 (HTML)
    """
    # Chrome DevTools 에서 복사한 POST 요청 URL 및 양식 데이터
    req_url: str = "https://novelpia.com/proc/episode_list"
    form_data: dict = {"novel_no": code, "sort": sort, "page": page - 1}  # 1페이지 -> page = 0, ...
    headers: dict[str: str] = {'User-Agent': ua}

    # 로그인 O
    if use_login_key:
        login_key_added, headers_with_login_key = add_login_key(headers)

        # 게시일 순으로 정렬된 회차 목록 요청
        res = req.post(url=req_url, data=form_data, headers=headers_with_login_key)  # res: <Response [200]>

    # 로그인 X
    else:
        res = req.post(url=req_url, data=form_data, headers=headers)  # res: <Response [200]>

    html: str = res.text
    return html


def extract_ep_info(list_html: str, ep_no: int = 1) -> dict:
    """
    회차 목록에서 특정 회차의 제목, 화수, URL 을 추출하여 반환하는 함수

    :param list_html: 회차 목록 HTML
    :param ep_no: 추출할 회차의 목록 내 서수 (1부터 20까지)
    :return: 제목, 화수, 번호, 무료/성인 여부, 글자/댓글/조회/추천수
    """
    list_soup = BeautifulSoup(list_html, "html.parser")
    list_set: ResultSet[Tag] = list_soup.select("tr.ep_style5")

    info_dic: dict = {
        "제목": None,
        "위치": {}.fromkeys(["화수", "번호"]),
        "유형": {}.fromkeys(["무료", "성인"]),
        "통계": {}.fromkeys(["글자수", "조회수", "댓글수", "추천수"])
    }

    try:
        ep_tag: Tag = list_set[ep_no - 1]
    except IndexError as ie:
        print_under_new_line(f"예외 발생: {ie = }")
        return info_dic

    else:
        # info_li: list[str] = ep_tag.text
        """
        회차 정보 목록 추출
        예시 1. ['무료', '프롤로그', 'EP.0', '21', '21.01.07']
        예시 2. ['무료', 'ㅇ', 'EP.1', '10', '6', '21.01.07']
        예시 3. ['무료', '프롤로그', 'EP.0', '509', '3', '1', '21.01.07']
        예시 4. ['무료', '19', '봉인해제', 'EP.1', '2,732', '21.01.07']
        """
        # 각종 텍스트 추출
        headline: Tag = ep_tag.b

        # 제목 추출
        title: str = headline.i.next
        info_dic["제목"] = title

        # 유형 추출
        tags: ResultSet[Tag] = headline.select(".s_inv")
        price_tag: Tag = tags[0]
        class_li: str | Iterable[str] = price_tag.attrs['class']

        if 'b_free' in class_li:
            info_dic["유형"]["무료"] = True
        elif 'b_plus' in class_li:
            info_dic["유형"]["무료"] = False

        if len(tags) > 1:
            info_dic["유형"]["성인"] = True
        else:
            info_dic["유형"]["성인"] = False

        # 각종 정보 추출
        stats: Tag = ep_tag.select_one("div.ep_style2 font")

        # 회차 화수 표기 추출
        no_string: str = stats.span.text  # 'EP.1' / 'BONUS'
        """
        - 회차 목록 내 추천, 댓글수 표기 기능이 늦게 나와서 작품 연재 시기에 따라서 회차 화수 표기의 인덱스가 다를 수 있음
        - 추천수 추가 공지: <2021년 01월 08일 - 노벨피아 업데이트 변경사항(https://novelpia.com/notice/20/view_1392/)>
        - 댓글, 추천, 조회수 표기 공지: <2021년 01월 12일 - 노벨피아 업데이트 변경사항(https://novelpia.com/notice/20/view_3248/)>
        """

        if no_string.startswith("EP"):
            ep_num = int(no_string.lstrip("EP."))
            info_dic["위치"]["화수"] = ep_num

        else:
            info_dic["위치"]["화수"] = 'BONUS'

        # 각종 수치 추출
        stat_tag: Tag = stats.select("span")[1]

        # 회차 번호 추출
        # <span class="episode_count_view novel_count_view_7146">0</span>
        view_tag: Tag = stat_tag.select_one(".episode_count_view")

        # ("episode_count_view", "novel_count_view_7146")
        class_li: str | Iterable[str] = view_tag.attrs['class']
        ep_code: str = class_li[1].lstrip("novel_count_view_")
        info_dic["위치"]["번호"] = ep_code

        assert isinstance(int(ep_code), int), "잘못된 회차 번호"

        # 소설 번호 추출
        page_link_tag: Tag = list_soup.select_one(".page-link")
        onclick: str = page_link_tag.attrs["onclick"]  # "localStorage['novel_page_15597'] = '1'; episode_list();"
        s_index: int = onclick.find("page")
        e_index: int = onclick.find("]")
        novel_code: str = onclick[s_index + 5: e_index - 1]

        assert isinstance(int(novel_code), int), "잘못된 소설 번호"

        # 조회수 추출
        url: str = "https://novelpia.com/proc/novel"
        form_data: dict = {
            "cmd": "get_episode_count_view",
            "episode_arr[]": f"episode_count_view {class_li[1]}",
            "novel_no": novel_code,
        }
        headers: dict = {
            "User-Agent": ua,
            "Content-Type":
            "application/x-www-form-urlencoded; charset=UTF-8"
        }
        res = req.post(url, form_data, headers=headers)

        view_counts: list[dict] = json.loads(res.text)["list"]
        view_count: int | None = None
        view_s: str = "-1"

        for dic in view_counts:
            if dic["episode_no"] == int(ep_code):
                view_s = dic["count_view"].replace(",", "")

        if view_count is not None:
            info_dic["통계"]["조회수"] = int(view_s)

        def flatten(tag: Tag) -> int:
            return int(tag.next.strip().replace(",", ""))

        letter_cnt_tag: Tag = stat_tag.select_one("i.ion-document-text")
        letter_cnt: int = flatten(letter_cnt_tag)
        """
        노벨피아 글자수 기준은 공백 문자 및 일부 문장 부호 제외.
        공지 참고: https://novelpia.com/faq/all/view_383218/
        """
        info_dic["통계"]["글자수"] = letter_cnt

        chat_tag: Tag = stat_tag.select_one("i.ion-chatbox-working")
        if chat_tag is not None:
            comments: int = flatten(chat_tag)
            info_dic["통계"]["댓글수"] = comments

        thumb_tag: Tag = stat_tag.select_one("i.ion-thumbsup")
        if thumb_tag is not None:
            thumbs_up: int = flatten(thumb_tag)
            info_dic["통계"]["추천수"] = thumbs_up

        return info_dic


def has_prologue(novel_code: str) -> bool:
    """
    소설의 회차 목록에서 프롤로그의 유무를 반환하는 함수.

    :param novel_code: 확인할 소설 번호
    :return: 프롤로그 유무 (참/거짓)
    """

    """
    에필로그 기능은 노벨피아에서 2022년 5월 16일 부로 삭제함.
    공지 참고: https://novelpia.com/notice/all/view_1274648/
    """

    ep_list_html: str = get_ep_list(novel_code)
    info_dic: dict = extract_ep_info(ep_list_html)
    ep_num: int = info_dic["위치"]["화수"]

    return ep_num == 0
