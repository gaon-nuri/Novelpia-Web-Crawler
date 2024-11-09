# novel_crawler/main.py
"""프로그램의 진입점을 정의합니다."""

from src.file_io import create_file_from_string, set_md_str_from_novel, set_path_from_novel_infos
from src.func.userio import get_num_from_input
from src.models import Novel
from src.user.shelf import novel_gen_from_mem


def novel_obj_from_code(novel_code: str) -> Novel:
    """소설 번호를 사용자에게 입력받아 Novel 객체를 생성하는 함수

    :return: Novel 객체
    """
    sub_mem: int = 1
    novels, novel_cnt = novel_gen_from_mem(sub_mem, novel_code)
    assert novel_cnt == 1
    novel = next(novels)
    return novel


def mk_md_file_from_novel_obj(novel: Novel) -> None:
    """Novel 객체를 Markdown 파일에 쓰는 함수"""

    md_str = set_md_str_from_novel(novel)
    path = set_path_from_novel_infos(novel.title, novel.code)
    create_file_from_string(md_str, path)


def novel_info_main() -> None:
    """직접 실행할 때만 호출되는 메인 함수"""

    novel_code = str(get_num_from_input("소설 번호"))
    novel: Novel = novel_obj_from_code(novel_code)
    mk_md_file_from_novel_obj(novel)


if __name__ == "__main__":
    novel_info_main()
