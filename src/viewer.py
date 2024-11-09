"""회차 본문을 내려받는 코드"""
from logging import getLogger
from typing import Optional
from urllib.parse import urljoin

from src.const.const import EP_CNT_IN_PAGE
from src.func.crawl import init_default_header, log_header_from_default_header
from src.main import novel_obj_from_code
from src.models import Ep
from src.novel_info import Novel
from .func.common import Path, load_dic_from_json, load_env_var_from_name, mk_file_from_path
from .func.userio import get_num_from_input, print_under_new_line

logger = getLogger(__name__)


def find_list_loc_from_ep_num(novel_code: str, ep_num: int = -1) -> tuple[int, int]:
    """소설 번호와 회차 화수를 입력받아 해당 회차가 있는 목록 페이지의 번호와 회차의 서수를 반환하는 함수

    :param novel_code: 회차 목록을 받아올 소설의 번호
    :param ep_num: 검색할 회차의 화수
    :return: 페이지 번호, 회차 서수
    """
    while True:
        from .func.episode import has_prologue

        has_prologue_ep: bool = has_prologue(novel_code)

        if ep_num == -1:
            ep_num = get_num_from_input("회차 화수")

        # 요청한 프롤로그가 無
        if not has_prologue_ep and ep_num == 0:
            print_under_new_line("[오류] 프롤로그가 없는 소설입니다. 다시 입력해 주세요.")
            continue
        break

    from .const.const import EP_CNT_IN_PAGE as EP_COUNT

    # 프롤로그 有 (0화부터 시작)
    if has_prologue_ep:
        from math import floor

        page: int = floor(ep_num / EP_COUNT) + 1  # EP.0 ~ 19 -> 1페이지, EP.20 ~ 39 -> 2페이지, ...
        if page == 1:
            ep_no = ep_num + 1  # EP.1 -> 1페이지 두 번째
        else:
            ep_no = ep_num % EP_COUNT * (page - 1) + 1  # EP.21 -> 2페이지 두 번째

    # 프롤로그 無 (1화부터 시작)
    else:
        from math import ceil

        page: int = ceil(ep_num / EP_COUNT)  # EP.1 ~ 20 -> 1페이지, EP.21 ~ 40 -> 2페이지, ...
        if page == 1:
            ep_no = ep_num  # EP.1 -> 1페이지 첫 번째
        else:
            ep_no = ep_num % (EP_COUNT * (page - 1))  # EP.21 -> 2페이지 첫 번째

    return page, ep_no


def fetch_ep_content(ep_code: str) -> Optional[list[str]]:
    """입력한 번호의 회차를 서버에 요청하고, 응답에서 추출한 본문 줄별 목록을 반환하는 함수

    :param ep_code: 회차 번호
    :return: 본문 줄별 목록
    """
    req_url: str = urljoin("https://novelpia.com/proc/viewer_data/", ep_code)
    form_data: dict = {"size": 14}

    rand_header = init_default_header()
    log_key, header = log_header_from_default_header(rand_header, True)

    from requests import post
    res = post(url=req_url, data=form_data, headers=header)  # response: <Response [200]>

    # HTML/JSON
    ep_json_or_page: str = res.text
    """
    \n요청 성공 시: {"s": [{"text": "~"}], "c": "{\"ct\":~\"\",\"iv\":~\"\",\"s\":\"~\"}"}
    \n요청 실패 시: <div id="alert_modal" class="modal fade" style="display:none;"> ~
    """

    # 응답 JSON 파싱 및 본문 추출
    with load_dic_from_json(ep_json_or_page) as (ep_dic, err):
        if err:
            # 본문 추출 실패, 오류 메시지 추출
            from src.parsers import alert_msg_and_err_from_page
            with alert_msg_and_err_from_page(ep_json_or_page) as (alert_msg, attr_err):
                if attr_err:
                    raise NotImplementedError("작업 예정")
                if alert_msg == "잘못된 소설 번호 입니다.":
                    pass
            return None

    dic_list = iter(ep_dic["s"])
    ep_lines: list[str] = []

    # 본문 줄별로 목록에 추가
    for dic in dic_list:
        line: str = dic["text"]
        if line.strip("\n ") == "&nbsp;":
            ep_lines.append("\n")
        else:
            ep_lines.append(line)
    return ep_lines


def set_ep_path_from_ep_ins(novel: Novel, ep: Ep) -> Path:
    """파일을 생성할 경로를 반환하는 함수

    :return: 생성할 파일의 경로
    """
    # 파일 확장자 지정
    suffix: str = ".md"
    # suffix: str = ".page"

    # 파일 경로 지정
    f_path = Path.cwd()

    if suffix == ".md":
        f_path = set_md_novel_path_from_novel_ins(novel)

    elif suffix == ".page":
        # TODO: 완성
        raise ValueError("작업 예정")

    base, exponent = 1, 0
    count_book = novel.count_book
    while True:
        if base <= count_book < base * 10:
            break
        base *= 10
        exponent += 1

    ep_num = str(ep.num).zfill(exponent + 1)
    file_name: str = f"EP:{ep_num} - {ep.title}"  # EP.0 프롤로그.ext
    f_path = Path(f_path).joinpath(file_name).with_suffix(suffix)  # ~/novel/제목/EP.0 -프롤로그.page

    return f_path


def set_md_novel_path_from_novel_ins(novel):
    with load_env_var_from_name("NOVEL_INFO_MD_DIR") as (value, err):
        if err:
            base_path = Path.cwd()
        else:
            base_path = Path(value)
    f_path = base_path.joinpath("소장함", f"{novel.title}")  # ~/회차 목록/제목
    return f_path


def init_md_gen_from_ep(ep: Ep):
    """Ep 객체를 받아서 Markdown 제너레이터를 반환하는 함수

    :param ep: Ep 클래스의 객체
    """
    property_lines: list[str] = [
        "링크: " + ep.url,
        "연재일: " + ep.ctime,
        "정보 수집일: " + ep.got_time,
        "화수: " + str(ep.num),
        "댓글 수: " + str(ep.comment),
        "글자 수: " + str(ep.letter),
        "조회 수: " + str(ep.count_view),
        "추천 수: " + str(ep.count_good)
    ]
    property_lines = ["---"] + property_lines
    property_lines.append("---")

    property_str: str = "\n".join(property_lines) + "\n"
    ep_lines: list[str] | None = fetch_ep_content(ep.code)
    ep_lines = ep_lines if ep_lines else []
    md_lines: list[str] = [property_str] + ep_lines

    yield from md_lines


def create_f_from_ep(path: Path, ep: Ep) -> None:
    """회차 본문을 파일에 쓰는 함수

    :param path: 파일을 생성할 경로
    :param ep: Ep 객체
    """
    # 폴더 확보
    from .func.common import mk_path_if_none

    mk_path_if_none(path)

    # Ep 객체를 Markdown 문자열 제너레이터로 변환
    from typing import Generator

    md_gen: Generator = init_md_gen_from_ep(ep)

    # 회차 본문 줄별 목록을 HTML로 변환
    # markup: str = ep_content_to_html(ep_lines)

    # Markdown 문자열 제너레이터를 파일에 쓰기

    with mk_file_from_path(path, mode="xt") as (f, err):
        # OSError 등
        if err:
            print_under_new_line("[오류]", f"{err = }")
        else:
            from io import TextIOWrapper
            assert isinstance(f, TextIOWrapper)

            f.writelines(md_gen)  # 속도 小, 용량 少

            # markup: str = ''.join(gen_markup)
            # f.write(markup)  # 속도 大, 용량 多


def append_list_file(path: Path, f_name: str, novel=None) -> None:
    """

    :param novel:
    :param path:
    :param f_name:
    """
    list_f_path: Path = path.parent.joinpath(f"!회차 목록_{novel.title}.md")  # ~/novel/'제목'/회차 목록.md
    in_link: str = f"[[{f_name}]]\n\n"
    from .func.common import mk_file_from_path
    with mk_file_from_path(list_f_path, mode="at") as (f, err):
        # OSError 등
        if err:
            logger.error("[오류]", err)
            raise err
        from io import TextIOWrapper
        assert isinstance(f, TextIOWrapper)
        f.write(in_link)  # 속도 小, 용량 少


def write_all_ep_text(fst_ep_num: int, lst_ep_num: int, novel: Novel) -> None:
    """선택한 회차들의 본문을 파일에 쓰는 함수

    :param fst_ep_num: 첫 회차 화수
    :param lst_ep_num: 마지막 회차 화수
    :param novel: Novel 객체
    :return: Ep 객체
    """
    # 페이지 번호, 회차 서수 추출
    code: str = novel.code
    fst_page, fst_ep_no = find_list_loc_from_ep_num(code, fst_ep_num)
    lst_page, lst_ep_no = find_list_loc_from_ep_num(code, lst_ep_num)

    # 회차 목록 HTML 요청 및 회차 정보 추출
    from .func.episode import Ep, ep_obj_from_page
    from src.func.crawl import fetch_ep_li_pg_from_code

    def write_ep_text_in_list(a_page: int, a_ep_no: int, a_novel: Novel) -> None:
        """목록의 회차들의 본문을 Markdown 파일에 쓰는 함수

        :param a_page: 페이지 번호
        :param a_ep_no: 회차 번호
        :param a_novel: Novel 객체
        """
        ep_list_html = fetch_ep_li_pg_from_code(a_novel.code, page=a_page, do_plus_login=True)
        ep: Ep = ep_obj_from_page(ep_list_html, a_ep_no)  # 파일 경로 설정
        file_path: Path = set_ep_path_from_ep_ins(a_novel, ep)
        append_list_file(file_path, file_path.with_suffix("").name)
        create_f_from_ep(file_path, ep)

    fst: int = fst_ep_no
    for page in range(fst_page, lst_page + 1):
        lst = lst_ep_no + 1 if page == lst_page else EP_CNT_IN_PAGE + 1
        for ep_no in range(fst, lst):
            write_ep_text_in_list(page, ep_no, novel)
        fst = 1


def viewer_main() -> None:
    """직접 실행할 때만 호출되는 메인 함수"""
    # Novel 객체 생성
    novel_num: int = get_num_from_input("소설 번호")
    novel_code = str(novel_num)
    novel: Novel = novel_obj_from_code(novel_code)

    # 회차 화수 입력받기
    while True:
        fst_ep_num: int = get_num_from_input("첫 회차 화수")
        lst_ep_num: int = get_num_from_input("마지막 회차 화수")
        if fst_ep_num <= lst_ep_num <= novel.count_book:
            break
        else:
            err_msg: str = write_all_ep_text.__str__() + "잘못된 회차 화수에요."
            ve = ValueError()
            ve.add_note(err_msg)
            logger.error(ve)
    write_all_ep_text(fst_ep_num, lst_ep_num, novel)


if __name__ == "__main__":
    viewer_main()
