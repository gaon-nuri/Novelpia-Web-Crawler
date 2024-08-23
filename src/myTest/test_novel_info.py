from unittest import TestCase, main, skip

from src.myTest.test_module import total_novel_cnt  # 노벨피아 총 소설 수


class GetFinalJamo(TestCase):
    ko_word_v_end: str = "창작물 속으로"
    ko_word_c_end: str = "매도당하고 싶은 엘프님"

    vowel_post: list = ["가", "를", "는", "야"]
    consonant_post: list = ["이", "을", "은", "아"]
    input_post: list = ["이", "을", "은", "아"]

    from src.common.module import get_postposition

    @staticmethod
    def get_josa(kr_word: str, postposition: str):
        return GetFinalJamo.get_postposition(kr_word, postposition)

    def test_final_consonant_word(self):
        word: str = GetFinalJamo.ko_word_c_end
        args: list = GetFinalJamo.input_post
        answer_post = list(map(self.get_josa, [word] * 4, args))

        self.assertEqual(answer_post, GetFinalJamo.consonant_post)

    def test_final_vowel_word(self):
        word: str = GetFinalJamo.ko_word_v_end
        args: list = GetFinalJamo.input_post

        answer_post = list(map(self.get_josa, [word] * 4, args))

        self.assertEqual(answer_post, GetFinalJamo.vowel_post)


class GetNovelStatus(TestCase):
    """연중작, 완결작, 연재작의 연재 상태를 각각 추출하는 테스트."""

    @staticmethod
    def chk_up_status(novel_code: str) -> str:
        """입력받은 번호의 소설의 연재 상태를 추출하여 반환하는 함수

        :param novel_code: 소설 번호
        :return: '연재 중', '완결', '연습작품', '삭제', '연재중단', '연재지연' 中 택 1
        """
        from urllib.parse import urljoin
        url: str = urljoin("https://novelpia.com/novel/", novel_code)

        from src.common.module import get_novel_main_w_error
        with get_novel_main_w_error(url) as (html, err):
            if err:
                raise err

        from src.metadata.novel_info import Novel, extract_novel_info
        novel: Novel = extract_novel_info(html)

        return novel.status

    def test_inaccessible_novel(self):
        code_inaccessible: str = "28"  #
        status: str = self.chk_up_status(code_inaccessible)

        self.assertEqual("연습작품", status)

    def test_deleted_novel(self):
        code_deleted: str = "2"  # <건물주 아들> - 최초의 삭제작
        status: str = self.chk_up_status(code_deleted)

        self.assertEqual("삭제", status)

    def test_novel_on_hiatus(self):
        code_hiatus: str = "10"  # <미대오빠의 여사친들> - 최초의 연중작
        status: str = self.chk_up_status(code_hiatus)

        self.assertEqual("연재중단", status)

    def test_completed_novel(self):
        code_completed: str = "1"  # <S드립을 잘 치는 여사친> - 최초의 완결작
        status: str = self.chk_up_status(code_completed)

        self.assertEqual("완결", status)

    def test_ongoing_novel(self):
        code_ongoing: str = "610"  # <창작물 속으로> - 연재중 (24.8.8 기준)
        status: str = self.chk_up_status(code_ongoing)

        self.assertEqual("연재 중", status)


@skip
class CntNovelInStatus(GetNovelStatus):
    """특정 연재 상태의 소설 비율을 재는 테스트"""

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


class NovelToMdFile(TestCase):
    from src.metadata.novel_info import Novel

    novel = Novel(
        '숨겨진 흑막이 되었다',
        '247416',
        'https://novelpia.com/novel/247416',
        '2023-12-11',
        '2024-04-18',
        224772,
        2189821,
        '미츄리',
        '공개전',
        '\n  - 현대판타지\n  - 하렘\n  - 괴담\n  - 집착',
        '완결',
        {'독점'},
        225,
        1142,
        14616,
        '> [!TLDR] 시놉시스\n> 괴담, 저주, 여학생 등….\n> 집착해선 안 될 것들이 내게 집착한다\n'
    )

    def test_novel_to_md(self):
        """소설 정보가 담긴 Dict 를 Markdown 형식의 문자열로 변환하는 테스트

        :return: Markdown 형식의 소설 정보
        """
        from src.metadata.novel_info import novel_info_to_md

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
완독일: 0000-00-00
연재 시작일: 2023-12-11
최근(예정) 연재일: 2024-04-18
정보 수집일: 0000-00-00
회차 수: 225
알람 수: 1142
선호 수: 14616
추천 수: 224772
조회 수: 2189821
---
> [!TLDR] 시놉시스
> 괴담, 저주, 여학생 등….
> 집착해선 안 될 것들이 내게 집착한다
"""
        converted_md = novel_info_to_md(NovelToMdFile.novel)

        self.assertEqual(formatted_md, converted_md)

    @skip
    def test_novel_to_md_file(self):
        from src.metadata.novel_info import novel_to_md_file

        novel_to_md_file(NovelToMdFile.novel)

        self.fail()

    def test_novels_to_md_files(self):
        from src.myTest.test_module import total_novel_cnt
        from src.common.module import get_novel_main_w_error, print_under_new_line

        from urllib.parse import urljoin

        base_url: str = "https://novelpia.com/novel/"
        urls = (urljoin(base_url, str(code)) for code in range(1, total_novel_cnt))

        for i in range(1, total_novel_cnt):
            url = next(urls)
            with self.subTest(url=url):
                with get_novel_main_w_error(url) as (html, err):
                    if err:
                        print_under_new_line("[오류]", f"{err = }")
                        self.fail()
                    else:
                        from src.metadata.novel_info import Novel, extract_novel_info, novel_to_md_file

                        novel: Novel = extract_novel_info(html)
                        if not novel:
                            self.fail()
                        novel_to_md_file(novel, True)
                self.assertTrue(True)


if __name__ == '__main__':
    main()
