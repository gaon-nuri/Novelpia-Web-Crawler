"""회차 본문 크롤링 테스트"""
from unittest import TestCase, main

from src.viewer import fetch_ep_content


class FindEpLoc(TestCase):
    def test_find_ep_loc(self):
        from src.viewer import find_list_loc_from_ep_num

        novel_code: str = "15597"
        ep_num, real_page, real_ep_no = 1, 1, 2
        got_page, got_ep_no = find_list_loc_from_ep_num(novel_code, ep_num)

        right_page: bool = (got_page == real_page)
        right_ep_no: bool = (got_ep_no == real_ep_no)

        self.assertTrue(right_page and right_ep_no)


class GetEpListHTML(TestCase):
    def test_get_empty_list(self):
        novel_code: str = "27"  # <건물주 아들>, 최초의 삭제된 소설. 동명의 9번 소설의 습작?

        from src.func.crawl import fetch_ep_li_pg_from_code

        list_html: str = fetch_ep_li_pg_from_code(novel_code)

        from bs4 import BeautifulSoup as Soup
        from bs4.filter import SoupStrainer as Strainer
        from src.const.const import PARSER

        only_td = Strainer("td")
        soup = Soup(list_html, PARSER, parse_only=only_td)

        self.assertEqual("작성된 글을 찾을 수 없습니다.", soup.text)


class GetEpContent(TestCase):
    def test_available_ep(self):
        ep_code: str = "2333686"  # <공지 메모장>
        got_lines: list[str] | None = fetch_ep_content(ep_code)
        real_lines: list[str] = ['입니다\n', '\n', '\n']

        self.assertEqual(real_lines, got_lines)

    def test_unavailable_ep(self):
        ep_code: str = "1"
        got_lines: list[str] | None = fetch_ep_content(ep_code)

        self.assertIsNone(got_lines)


class EpContentToMd(TestCase):
    def test_ep_content_to_md(self):
        novel_code: str = "28"
        ep_code: str = "245"
        from src.models import get_datetime_by_min
        real_md: str = f"""---
링크: https://novelpia.com/viewer/{ep_code}
연재일: 2020-11-06
정보 수집일: {get_datetime_by_min()}
화수: 0
댓글 수: -1
글자 수: 3878
조회 수: 11
추천 수: 1
---
"""
        from src.func.episode import ep_obj_from_page
        from src.func.crawl import fetch_ep_li_pg_from_code
        from src.viewer import init_md_gen_from_ep

        ep_list_html: str = fetch_ep_li_pg_from_code(novel_code, do_plus_login=True)
        ep = ep_obj_from_page(ep_list_html)
        got_md_gen = init_md_gen_from_ep(ep)
        got_md: str = "".join(got_md_gen)
        self.assertEqual(real_md, got_md)


if __name__ == "__main__":
    main()
