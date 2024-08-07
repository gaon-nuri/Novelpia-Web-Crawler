import unittest

from novel_info import *


class TestGetFstUploadDate(unittest.TestCase):
    def test_no_ep(self):
        for num in range(50):
            code = str(num)
            with self.subTest(code=code):
                self.assertIsNone(get_ep_up_date(code))
        # code: str = "247416"  #
        # fst_up_date: str = "2023-12-11"
        # self.assertEqual(get_ep_up_date(code), fst_up_date)

    def test_single_ep(self):
        code: str = "124146"  # <연중용 나데나데 소설>
        fst_up_date: str = "2023-12-13"
        self.assertEqual(get_ep_up_date(code), fst_up_date)

    def test_multiple_ep(self):
        code: str = "247416"  # <숨겨진 흑막이 되었다>
        fst_up_date: str = "2023-12-11"
        self.assertEqual(get_ep_up_date(code), fst_up_date)


class TestGetLstUploadDate(unittest.TestCase):
    def test_no_ep(self):
        self.assertEqual(get_ep_up_date("247416", "DOWN"), "2023-12-11")

    def test_single_ep(self):
        self.assertEqual(get_ep_up_date("247416", "DOWN"), "2023-12-11")

    def test_multiple_ep(self):
        self.assertEqual(get_ep_up_date("247416", "UP"), "2024-04-18")


class TestConvertToMarkdown(unittest.TestCase):
    def test_convert_to_markdown(self):
        """
        소설의 Metadata 가 담긴 Dict 를 Markdown 형식의 문자열로 변환하는 테스트
        :return: str
        """
        info_dic: dict = {
            'title': '숨겨진 흑막이 되었다',
            'author': '미츄리',
            'novel_page_url': 'https://novelpia.com/novel/247416',
            'solePick': '',
            'tagList': ['#현대판타지', '#하렘', '#괴담', '#집착'],
            'fstUploadDate': '2023-12-11',
            'lstUploadDate': '2024-04-18',
            'badge_dic': {
                '완결': True,
                '연재지연': False,
                '연재중단': False,
                '19': False,
                '자유': False,
                '독점': True,
                '챌린지': False
            },
            'user_stat_dic': {'ep': 225, 'alarm': 1139, 'prefer': 14669},
            'ep_stat_dic': {'recommend': 224039, 'view': 2179530},
            'synopsis': '괴담, 저주, 여학생 등….\r\n집착해선 안 될 것들이 내게 집착한다',
        }
        formatted_md: str = """---
aliases:
  - 
작가명: 미츄리
링크: https://novelpia.com/novel/247416
유입 경로: (직접 적어 주세요) 
tags:
  - 현대판타지
  - 하렘
  - 괴담
  - 집착
공개: 2023-12-11
갱신: 2024-04-18
완독: 0000-00-00
완결: True
연중(각): False
성인: False
무료: False
독점: True
챌린지: False
회차: 225
알람: 1139
선호: 14669
추천: 224039
조회: 2179530
---
> [!TLDR] 시놉시스
> 괴담, 저주, 여학생 등….
> 집착해선 안 될 것들이 내게 집착한다
"""
        self.assertEqual(convert_to_markdown(info_dic), formatted_md)


class Test(unittest.TestCase):
    def test_extract_metadata(self):
        self.fail()


if __name__ == '__main__':
    unittest.main()
