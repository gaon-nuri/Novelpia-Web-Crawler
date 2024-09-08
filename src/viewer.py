"""회차 본문을 내려받는 코드"""
from urllib.parse import urljoin

from src.func.common import PARSER, Path
from src.func.userIO import input_num, print_under_new_line


def find_ep_location(novel_code: str, ep_num: int = -1) -> tuple[int, int]:
    """소설 번호와 회차 화수를 입력받아 해당 회차가 있는 목록 페이지의 번호와 회차의 서수를 반환하는 함수

    :param novel_code: 회차 목록을 받아올 소설의 번호
    :param ep_num: 검색할 회차의 화수
    :return: 페이지 번호, 회차 서수
    """
    while True:
        from src.func.episode import has_prologue
        has_prologue_ep: bool = has_prologue(novel_code)

        if ep_num == -1:
            ep_num = input_num("회차 화수")

        # 요청한 프롤로그가 無
        if not has_prologue_ep and ep_num == 0:
            print_under_new_line("[오류] 프롤로그가 없는 소설입니다. 다시 입력해 주세요.")
            continue
        break

    ep_cnt_in_page: int = 20  # 페이지 당 20회차씩

    # 프롤로그 有 (0화부터 시작)
    if has_prologue_ep:
        from math import floor
        page: int = floor(ep_num / ep_cnt_in_page) + 1  # EP.0 ~ 19 -> 1페이지, EP.20 ~ 39 -> 2페이지, ...
        if page == 1:
            ep_no = ep_num + 1  # EP.1 -> 1페이지 두 번째
        else:
            ep_no = ep_num % ep_cnt_in_page * (page - 1) + 1  # EP.21 -> 2페이지 두 번째

    # 프롤로그 無 (1화부터 시작)
    else:
        from math import ceil
        page: int = ceil(ep_num / ep_cnt_in_page)  # EP.1 ~ 20 -> 1페이지, EP.21 ~ 40 -> 2페이지, ...
        if page == 1:
            ep_no = ep_num  # EP.1 -> 1페이지 첫 번째
        else:
            ep_no = ep_num % (ep_cnt_in_page * (page - 1))  # EP.21 -> 2페이지 첫 번째

    return page, ep_no


def get_ep_content(ep_code: str) -> list[str] | None:
    """입력한 번호의 회차를 서버에 요청하고, 응답에서 추출한 본문 줄별 목록을 반환하는 함수

    :param ep_code: 회차 번호
    :return: 본문 줄별 목록
    """
    req_url: str = urljoin("https://novelpia.com/proc/viewer_data/", ep_code)
    form_data: dict = {"size": 14}

    from src.const.const import BASIC_HEADERS
    from src.func.common import add_login_key

    # 헤더에 로그인 키 추가
    login_key_added, headers = add_login_key(BASIC_HEADERS, True)

    from requests import post
    res = post(url=req_url, data=form_data, headers=headers)  # response: <Response [200]>

    # HTML/JSON
    ep_content: str = res.text
    '''
    \n요청 성공 시: {"s": [{"text": "~"}], "c": "{\"ct\":~\"\",\"iv\":~\"\",\"s\":\"~\"}"}
    \n요청 실패 시: <div id="alert_modal" class="modal fade" style="display:none;"> ~
    '''
    from src.func.common import load_json_w_error

    # 응답 JSON 파싱 및 본문 추출
    with load_json_w_error(ep_content) as (ep_content_dic, err):
        # 추출 실패
        if err:
            from bs4 import BeautifulSoup

            # 오류 메시지 추출
            from src.func.common import parse_alert_msg_w_error

            with parse_alert_msg_w_error(ep_content) as (alert_msg, attr_err):
                if attr_err:
                    raise RuntimeError("작업 예정")
                if alert_msg == "잘못된 소설 번호 입니다.":
                    pass
            return None

    dic_list = iter(ep_content_dic["s"])
    ep_lines: list[str] = []

    # 본문 줄별로 목록에 추가
    for dic in dic_list:
        line: str = dic["text"]
        if line.strip("\n ") == "&nbsp;":
            ep_lines.append("\n")
        else:
            ep_lines.append(line)

    return ep_lines


def viewer_main() -> None:
    """직접 실행할 때만 호출되는 메인 함수"""
    novel_num: int = input_num("소설 번호")
    novel_code = str(novel_num)
    url: str = urljoin("https://novelpia.com/novel/", novel_code)

    from src.func.common import get_novel_main_w_error

    # 메인 페이지 요청
    with get_novel_main_w_error(url) as (html, err):
        if err:
            raise err

    # 메인 페이지 파싱, 제목 추출
    from bs4 import BeautifulSoup
    from src.const.const import HTML_TITLE_PREFIX

    soup = BeautifulSoup(html, PARSER)
    novel_title: str = soup.title.text[len(HTML_TITLE_PREFIX):]  # '노벨피아 - 웹소설로 꿈꾸는 세상! - '의 22자 제거

    ep_num: int = input_num("회차 화수")

    # 회차 서수 추출
    page, ep_no = find_ep_location(novel_code, ep_num)

    # 회차 목록 HTML 요청 및 회차 정보 추출
    from src.func.episode import get_ep_list, Ep, extract_ep_info

    ep_list_html = get_ep_list(novel_code, page=page, plus_login=True)
    ep: Ep = extract_ep_info(ep_list_html, ep_no)

    # 회차 본문 추출
    ep_lines: list[str] = get_ep_content(ep.code)

    # 파일 확장자 지정
    suffix: str = ".md"
    # suffix: str = ".html"

    # 파일 경로 지정
    if suffix == ".md":
        from src.func.common import get_env_var_w_error

        with get_env_var_w_error("MARKDOWN_DIR") as (file_dir, err):
            if err:
                raise
            file_dir = Path.cwd().joinpath("novel", novel_title)  # ~/novel/제목

    elif suffix == ".html":
        raise ValueError("작업 예정")

    file_name: str = f"EP.{ep_num} - {ep.title}"  # EP.0 프롤로그.ext
    file_path = Path(file_dir).joinpath(file_name).with_suffix(suffix)  # ~/novel/제목/EP.0 프롤로그.html

    from src.func.common import assure_path_exists

    # 폴더 확보
    assure_path_exists(file_path)

    # 회차 본문 줄별 목록을 Markdown 문자열 Generator로 변환
    from typing import Generator
    from src.func.episode import ep_content_to_md

    markup_gen: Generator = ep_content_to_md(ep, ep_lines)

    # 회차 본문 줄별 목록을 HTML로 변환
    # markup: str = ep_content_to_html(ep_lines)

    from src.func.common import opened_x_error

    # Markdown 문자열 Generator를 파일에 쓰기
    with opened_x_error(file_path, mode="x") as (f, err):
        # OSError 등
        if err:
            print_under_new_line("[오류]", f"{err = }")
        else:
            from io import TextIOWrapper
            assert isinstance(f, TextIOWrapper)

            f.writelines(markup_gen)  # 속도 小, 용량 少

            # markup: str = ''.join(gen_markup)
            # f.write(markup)  # 속도 大, 용량 多


if __name__ == "__main__":
    viewer_main()
