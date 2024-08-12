from unittest import TestCase, main, skip

from src.metadata.novel_info import *
from src.unittest.test_module import total_novel_cnt


class GetFinalJamo(TestCase):
    ko_word_v_end: str = "창작물 속으로"
    ko_word_c_end: str = "매도당하고 싶은 엘프님"

    v_post: list = ["가", "를", "는", "야"]
    c_post: list = ["이", "을", "은", "아"]
    q_post: list = ["이", "을", "은", "아"]

    def test_final_consonant(self):
        word: str = GetFinalJamo.ko_word_c_end
        args: list = GetFinalJamo.q_post
        a_post: list = list(map(get_postposition, [word] * 4, args))

        self.assertEqual(a_post, GetFinalJamo.c_post)

    def test_final_vowel(self):
        word: str = GetFinalJamo.ko_word_v_end
        args: list = GetFinalJamo.q_post
        a_post: list = list(map(get_postposition, [word] * 4, args))

        self.assertEqual(a_post, GetFinalJamo.v_post)


class GetUpDate(TestCase):
    def test_single_ep(self):
        code: str = "124146"  # <연중용 나데나데 소설>
        up_date: str = "2023-12-13"

        self.assertEqual(get_ep_up_date(code), up_date)

    def test_multiple_ep(self):
        code: str = "247416"  # <숨겨진 흑막이 되었다>
        fst_up_date: str = "2023-12-11"
        lst_up_date: str = "2024-04-18"

        fst_match: bool = get_ep_up_date(code, "DOWN") == fst_up_date
        lst_match: bool = get_ep_up_date(code, "UP") == lst_up_date

        self.assertTrue(fst_match and lst_match)

    def test_no_ep(self):
        code: str = "2"  # <건물주 아들>, 최초의 삭제된 소설. 동명의 9번 소설의 습작?

        self.assertIsNone(get_ep_up_date(code))


@skip
class CntNoEpNovel(TestCase):
    def test_cnt_no_ep_novel(self):
        """
        노벨피아 소설 중 작성된 회차가 없는 작품을 세는 테스트
        :return: 회차가 없으면 성공, 있으면 실패
        """
        for num in range(1, total_novel_cnt):
            code = str(num)
            with self.subTest(code=code):
                self.assertIsNone(get_ep_up_date(code))


class ConvertToMarkdown(TestCase):
    def test_convert_to_md(self):
        """
        소설 정보가 담긴 Dict 를 Markdown 형식의 문자열로 변환하는 테스트
        :return: Markdown 형식의 소설 정보
        """
        title: str = '숨겨진 흑막이 되었다'
        info_dic: dict = {
            '작가명': '미츄리',
            '소설 링크': 'https://novelpia.com/novel/247416',
            '인생픽 순위': None,
            'tags': '\n  - 현대판타지\n  - 하렘\n  - 괴담\n  - 집착',
            '공개 일자': '2023-12-11',
            '갱신 일자': '2024-04-18',
            '완독 일자': None,
            '연재 상태': {
                '연재 중': False,
                '완결': True,
                '삭제': False,
                '연재지연': False,
                '연재중단': False,
            },
            '연재 유형': {
                '19': False,
                '자유': False,
                '독점': True,
                '챌린지': False
            },
            'per_user_stats': {'회차 수': 225, '알람 수': 1139, '선호 수': 14669},
            'per_ep_stats': {'추천 수': 224039, '조회 수': 2179530},
            '줄거리': '> [!TLDR] 시놉시스\n> 괴담, 저주, 여학생 등….\n> 집착해선 안 될 것들이 내게 집착한다',
        }
        formatted_md: str = """---
aliases:
  - (직접 적어 주세요)
유입 경로: (직접 적어 주세요)
작가명: 미츄리
소설 링크: https://novelpia.com/novel/247416
tags: 
  - 현대판타지
  - 하렘
  - 괴담
  - 집착
공개 일자: 2023-12-11
갱신 일자: 2024-04-18
완독 일자: 0000-00-00
완결: True
독점: True
회차 수: 225
알람 수: 1139
선호 수: 14669
추천 수: 224039
조회 수: 2179530
---
> [!TLDR] 시놉시스
> 괴담, 저주, 여학생 등….
> 집착해선 안 될 것들이 내게 집착한다
"""
        converted_md = convert_to_md(title, info_dic)

        self.assertEqual(formatted_md, converted_md)


class GetNovelStatus(TestCase):
    """
    연중작, 완결작, 연재작의 연재 상태를 각각 추출하는 테스트.
    """

    @staticmethod
    def chk_up_status(novel_code: str) -> str:
        """
        입력받은 번호의 소설의 연재 상태를 추출하여 반환하는 함수

        :param novel_code: 소설 번호
        :return: '연재 중', '완결', '삭제', '연재중단', '연재지연' 중 택 1
        """
        url: str = f"https://novelpia.com/novel/{novel_code}"
        html: str = get_novel_main_page(url)

        title, info_dic = extract_novel_info(html)
        flag_dic: dict = info_dic["연재 상태"]
        up_status: str = [k for k, v in flag_dic.items() if v][0]

        return up_status

    def test_get_novel_status(self):
        code_deleted: str = "2"  # <건물주 아들> - 최초의 삭제작
        code_hiatus: str = "10"  # <미대오빠의 여사친들> - 최초의 연중작
        code_completed: str = "1"  # <S드립을 잘 치는 여사친> - 최초의 완결작
        code_ongoing: str = "610"  # <창작물 속으로> - 연재중 (24.8.8 기준)

        deleted: bool = (self.chk_up_status(code_deleted) == "삭제")
        hiatus: bool = (self.chk_up_status(code_hiatus) == "연재중단")
        compl: bool = (self.chk_up_status(code_completed) == "완결")
        ongoing: bool = (self.chk_up_status(code_ongoing) == "연재 중")

        self.assertTrue(deleted and hiatus and compl and ongoing)


@skip
class CntNovelInStatus(GetNovelStatus):
    """
    특정 연재 상태의 소설 비율을 재는 테스트
    """

    @staticmethod
    def chk_up_status(novel_code: str):
        return GetNovelStatus.chk_up_status(novel_code)

    def test_cnt_novel_on_hiatus(self):
        """
        연중작 비율을 재는 테스트
        """
        for num in range(1, total_novel_cnt):
            code = str(num)
            with self.subTest(code=code):
                up_status: str = self.chk_up_status(code)

                self.assertTrue(up_status == "연재지연" or up_status == "연재중단")

    def test_cnt_deleted_novel(self, status: str = "삭제"):
        """
        삭제작 비율을 재는 테스트
        """
        for num in range(1, total_novel_cnt):
            code = str(num)
            with self.subTest(code=code):
                up_status: str = self.chk_up_status(code)

                self.assertTrue(up_status == status)


if __name__ == '__main__':
    main()
