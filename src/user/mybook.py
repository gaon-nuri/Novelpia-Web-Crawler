"""내 서재 페이지의 선호작들의 정보를 크롤링하여 Markdown 파일로 쓰는 코드"""
from contextlib import contextmanager

from bs4.element import Tag

from src.func.userIO import print_under_new_line


@contextmanager
def get_mybook_page_w_err(url: str):
    """서버에 내 서재 페이지를 요청하고, HTML 응답을 반환하는 함수

    :param url: 요청 URL
    :return: HTML 응답, 접속 실패 시 None
    """
    from ..const.const import BASIC_HEADERS
    from ..func.common import add_login_key

    # 구독 계정으로 로그인
    npd_cookie, headers = add_login_key(BASIC_HEADERS, True)

    from requests.exceptions import ConnectionError
    from urllib3.exceptions import MaxRetryError

    # 소설 메인 페이지의 HTML 문서를 요청
    try:
        from requests import get

        res = get(url=url, headers=headers)  # res: <Response [200]>

    # 연결 실패, 오류 메시지 추출
    except* ConnectionError as err_group:
        ce: ConnectionError = err_group.exceptions[0]
        mre: MaxRetryError = ce.args[0]
        err_msg: str = mre.reason.args[0]

        start_index: int = err_msg.find("Failed")
        end_index: int = err_msg.find("Errno")

        re = RuntimeError(err_msg[start_index: end_index - 3])

        yield None, re
        # raise re from err_group

    # 성공
    else:
        html: str = res.text
        assert html != ""

        yield html, None


def extract_my_books(html: str):
    """내 서재 페이지에서 링크가 담긴 HTML 태그를 추출하는 함수

    :param html: 내 서재 페이지 HTML
    """
    # HTML 응답 파싱
    from ..func.common import PARSER
    from bs4 import BeautifulSoup as Soup
    from bs4.filter import SoupStrainer as Strainer
    from ..const.selector import MY_BOOK_TABLE_ROW_CSS

    only_my = Strainer("div", {"class": MY_BOOK_TABLE_ROW_CSS})
    my_soup = Soup(html, PARSER, parse_only=only_my).extract()
    # my_books = my_soup.select("div.novelbox", limit=30)
    from ..const.selector import MY_BOOK_TITLE_CSS

    only_title = Strainer("b", {"class": MY_BOOK_TITLE_CSS})
    titles = my_soup.find_all(only_title)

    yield from titles


def extract_url(div_tag: Tag):
    """HTML div 태그에서 URL을 추출하는 함수

    :param div_tag: onclick 속성을 가진 div
    :return: URL 상대 경로
    """
    click: str = div_tag.attrs["onclick"]  # click: "$('.loads').show();location = '/novel/3790123';"
    start_index: int = click.find("/novel")
    url_path: str = click[start_index: -2]

    return url_path


def mybook_main_old():
    """직접 실행할 때만 호출되는 메인 함수"""
    req_url: str = "https://novelpia.com/mybook/"
    with get_mybook_page_w_err(req_url) as (html, err):
        if err:
            raise err

    # URL 추출
    title_tags = [title_tag for title_tag in extract_my_books(html)]
    # noinspection PyTypeChecker
    url_paths = map(extract_url, title_tags)

    from urllib.parse import urljoin
    from ..const.const import HOST

    count: int = len(title_tags)
    urls = (url for url in map(urljoin, [HOST] * count, url_paths))

    from ..func.common import get_novel_main_w_error, print_under_new_line

    for i in range(count):
        with get_novel_main_w_error(next(urls)) as (html, err):
            if err:
                print_under_new_line("[오류]", f"{err = }")
            else:
                from ..novel_info import Novel, parse_novel_page, novel_to_md_file

                novel: Novel = parse_novel_page(html)
                novel_to_md_file(novel, True, True)


def mybook_main():
    """직접 실행할 때만 호출되는 메인 함수"""
    from ..novel_info import Novel, set_novel_from_likes, novel_to_md_file

    # Novel 객체 생성
    novels, count = set_novel_from_likes(2)

    for i in range(count):
        try:
            novel: Novel = next(novels)
        except StopIteration as si:
            raise RuntimeError(mybook_main, f"{si = }")
        else:
            # Markdown 파일 열기
            novel_to_md_file(novel, True, True)
            print_under_new_line(f"{i + 1}번째 소설을 Markdown 파일에 썼어요.")


if __name__ == "__main__":
    mybook_main()
