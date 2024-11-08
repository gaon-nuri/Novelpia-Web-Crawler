# tests/test_parsers.py

from unittest import TestCase, main

from src.exceptions import TagNotFoundError
from src.parsers import NovelPageParser


class TestNovelPageParser(TestCase):
    def setUp(self):
        # 예시 HTML 콘텐츠
        self.valid_html = """
        <page>
            <head>
                <meta property="og:out_url" content="https://novelpia.com/novel/1">
                <title>노벨피아 - 웹소설로 꿈꾸는 세상! - 예시 소설</title>
            </head>
            <body>
                <div class="novel-info">...</div>
                <div class="novel-title">예시 소설</div>
                <a class="writer-name">작가명</a>
            </body>
        </page>
        """

        self.invalid_html = """
        <page>
            <head>
                <title>노벨피아 - 웹소설로 꿈꾸는 세상! - </title>
            </head>
            <body>
                <div class="novel-info">...</div>
                <!-- 소설 제목 누락 -->
                <a class="writer-name">작가명</a>
            </body>
        </page>
        """

    def test_parse_valid_html(self):
        parser = NovelPageParser(self.valid_html)
        novel = parser.parse()
        self.assertIsNotNone(novel)
        self.assertEqual(novel.title, "예시 소설")
        self.assertEqual(novel.code, "1")
        self.assertEqual(novel.url, "https://novelpia.com/novel/1")
        self.assertEqual(novel.writer_nick, "작가명")

    def test_parse_invalid_html_missing_title_nsoup(self):
        parser = NovelPageParser(self.invalid_html)
        with self.assertRaises(TagNotFoundError) as context:
            parser.parse()
        self.assertIn("타이틀 태그 누락", str(context.exception))

    # 추가적인 테스트 케이스...


if __name__ == '__main__':
    main()
