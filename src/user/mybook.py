"""내 서재 페이지의 선호작들의 정보를 크롤링하여 Markdown 파일로 쓰는 코드"""
from src.func.userio import print_under_new_line


def mybook_main():
    """직접 실행할 때만 호출되는 메인 함수"""
    from ..novel_info import Novel
    from .shelf import novel_gen_from_mem

    # Novel 객체 생성
    # 1은 일반 계정, 2는 구독 계정
    # sub_mem: int = 1
    plus_mem: int = 2
    novels, count = novel_gen_from_mem(plus_mem)

    for i in range(count):
        try:
            novel: Novel = next(novels)
        except StopIteration as si:
            raise RuntimeError(mybook_main, f"{si = }")
        else:
            from src.main import mk_md_file_from_novel_obj
            mk_md_file_from_novel_obj(novel)
            print_under_new_line(f"{i + 1}번째 소설을 Markdown 파일에 썼어요.")


if __name__ == "__main__":
    mybook_main()
