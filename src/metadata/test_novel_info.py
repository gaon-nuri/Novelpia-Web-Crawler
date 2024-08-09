import unittest

from src.common.test_module import total_novel_cnt
from src.metadata.novel_info import *


class GetFinalJamo(unittest.TestCase):
    def test_final_jamo(self):
        kor_str_vowel_end: str = "창작물 속으로"
        kor_str_cons_end: str = "매도당하고 싶은 엘프님"

        is_fin_vowel: bool = ends_with_vowel(kor_str_vowel_end)
        is_fin_cons: bool = ends_with_vowel(kor_str_cons_end)

        self.assertTrue(is_fin_vowel and not is_fin_cons)


class GetUploadDate(unittest.TestCase):
    def test_single_ep(self):
        code: str = "124146"  # <연중용 나데나데 소설>
        up_date: str = "2023-12-13"

        self.assertEqual(get_ep_up_date(code), up_date)

    def test_multiple_ep(self):
        code: str = "247416"  # <숨겨진 흑막이 되었다>
        fst_up_date: str = "2023-12-11"
        lst_up_date: str = "2024-04-18"

        fst_up_date_match: bool = get_ep_up_date(code, "DOWN") == fst_up_date
        lst_up_date_match: bool = get_ep_up_date(code, "UP") == lst_up_date

        self.assertTrue(fst_up_date_match and lst_up_date_match)

    def test_no_ep(self):
        code: str = "2"  # <건물주 아들>, 최초의 삭제된 소설. 동명의 9번 소설의 습작?

        self.assertIsNone(get_ep_up_date(code))


class CntNoEpNovel(unittest.TestCase):
    def test_cnt_no_ep_novel(self):
        """
        노벨피아 소설 중 작성된 회차가 없는 작품을 세는 테스트
        :return: 회차가 없으면 성공, 있으면 실패
        """
        for num in range(total_novel_cnt):
            code = str(num)
            with self.subTest(code=code):
                self.assertIsNone(get_ep_up_date(code))


class ConvertToMarkdown(unittest.TestCase):
    def test_convert_to_markdown(self):
        """
        소설 정보가 담긴 Dict 를 Markdown 형식의 문자열로 변환하는 테스트
        :return: Markdown 형식의 소설 정보
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


def chk_up_status(novel_code: str) -> str:
    """
    소설의 연재 상태를 추출하여 반환하는 함수

    :param novel_code: 소설 번호
    :return: '완결', '연재중단', '연재지연', '연재중' 중 택 1
    """
    url: str = f"https://novelpia.com/novel/{novel_code}"
    html: str = get_novel_main_page(url)

    info_dic: dict = extract_novel_info(html)
    flag_dic: dict = info_dic["badge_dic"]
    
    for key in ["완결", "연재지연", "연재중단"]
        if flag_dic[key]:
            return key
    
    return "연재중"


class GetNovelStatus(unittest.TestCase):
    def test_get_novel_status(self):
        code_on_hiatus: str = "10"  # <미대오빠의 여사친들> - 최초의 연중작
        code_completed: str = "1"  # <S드립을 잘 치는 여사친> - 최초의 완결작
        code_ongoing: str = "610"  # <창작물 속으로> - 연재중 (24.8.8 기준)

        on_hiatus: bool = chk_up_status(code_on_hiatus)
        completed: bool = chk_up_status(code_completed)
        ongoing: bool = chk_up_status(code_ongoing)

        self.assertTrue(on_hiatus and not completed or ongoing)


class CntNovelOnHiatus(unittest.TestCase):
    def test_cnt_novel_on_hiatus(self):
        for num in range(total_novel_cnt):
            code = str(num)
            with self.subTest(code=code):
                up_status: str = chk_up_status(code)
                is_on_hiatus: bool = chk_up_status(code) == "연재지연" or "연재중단"
                self.assertTrue(is_on_hiatus)


if __name__ == '__main__':
    unittest.main()
