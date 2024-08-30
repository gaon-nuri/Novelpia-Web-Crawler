"""소설 정보 크롤링 테스트"""
from unittest import TestCase, main, skip

from src.const.const import NOVEL_STATUSES_NAMED_TUPLE as STATUSES


class ChkMetaClass(TestCase):
    def test_inherit_user_meta_class(self):
        """Novel 클래스의 사용자 메타 클래스 상속 여부 테스트"""

        from src.func.common import UserMeta, print_under_new_line
        from src.novel_info import Novel

        print_under_new_line("Novel.mro():", Novel.mro())

        self.assertTrue(isinstance(Novel, UserMeta))


class GetFinalJamo(TestCase):
    from src.const.const import POSTPOSITIONS_NAMED_TUPLE

    ko_word_v_end: str = "창작물 속으로"
    ko_word_c_end: str = "매도당하고 싶은 엘프님"

    input_post: tuple = POSTPOSITIONS_NAMED_TUPLE.consonant

    from src.func.common import get_postposition

    @staticmethod
    def get_josa(kr_word: str, postposition: str):
        """get_postposition 함수 주석 참고"""
        return GetFinalJamo.get_postposition(kr_word, postposition)

    def test_final_consonant_word(self):
        word: str = self.ko_word_c_end
        args: tuple = self.input_post
        answer_post = tuple(map(GetFinalJamo.get_josa, [word] * 4, args))

        self.assertEqual(answer_post, GetFinalJamo.POSTPOSITIONS_NAMED_TUPLE.consonant)

    def test_final_vowel_word(self):
        word: str = self.ko_word_v_end
        args: tuple = self.input_post

        answer_post = tuple(map(self.get_josa, [word] * 4, args))

        self.assertEqual(answer_post, self.POSTPOSITIONS_NAMED_TUPLE.vowel)


class GetFavoriteNovelInfo(TestCase):
    from src.func.common import get_env_var_w_error

    mem_no: int
    novel_no: int

    with get_env_var_w_error("SUB_MEM_NO") as (mem_no, err):
        if err:
            raise err

    with get_env_var_w_error("FAVORITE_NOVEL_NO") as (novel_no, err):
        if err:
            raise err

    @classmethod
    def get_favorite_novel_info_dics(cls):
        """get_favorite_novel_info_dics 함수 주석 참고"""
        from src.novel_info import get_favorite_novel_info_dics

        return get_favorite_novel_info_dics(cls.mem_no)

    def test_get_novel_info_dic(self):
        count, dics = self.get_favorite_novel_info_dics()
        got_dic: dict = dics[0]
        answer_dic: dict = {
            'novel_no': self.novel_no,
            'novel_name': "test14",
            'novel_search': "test14|test14|test14",
            'novel_subtitle': None,
            'novel_age': 0,
            'mem_no': self.mem_no,
            'novel_thumb': "",
            'novel_img': None,
            'novel_thumb_all': None,
            'novel_img_all': None,
            'novel_count': 0,
            'novel_status': 1,
            'novel_type': 2,
            'novel_genre': '["판타지","라이트노벨"]',
            'novel_story': ".",
            'novel_weekly': 1,
            'novel_notice': None,
            'novel_plus_want': 0,
            'count_view': 1,
            'count_good': 0,
            'count_book': 1,
            'count_pick': None,
            'writer_nick': "test14",
            'writer_original': "",
            'isbn': "",
            'last_viewdate': "2024-08-17 20:43:00",
            'is_monopoly': 0,
            'is_del': 0,
            'is_complete': 0,
            'is_donation_refusal': 0,
            'is_secondary_creation': 0,
            'is_contest': 0,
            'start_date': "2024-08-17 20:43:00",
            'status_date': "2024-08-28 11:18:22",
            'del_date': None,
            'complete_date': None,
            'plus_date': None,
            'plus_call_date': None,
            'plus_check_admin_no': None,
            'last_write_date': None,
            'novel_live': 0,
            'live_stop_end_date': None,
            'is_indent': 0,
            'main_genre': 1,
            'is_osmu': None,
            'flag_collect': 0,
            'local_code': "ko",
            'monopoly_date': None,
            'flag_img_policy': 0,
            'flag_translate': 0,
            'reg_date': '2024-08-16 19:56:20',
            'update_dt': "2024-08-28 11:57:52",
            'plus_start_date': None,
        }

        # keys = [*got_dic]
        # print("*got_dic:", keys)

        self.assertEqual(answer_dic, got_dic)

    @classmethod
    def chk_favorite_novel_statuses(cls):
        """chk_favorite_novel_statuses 함수 주석 참고"""
        from src.novel_info import chk_favorite_novel_statuses

        return chk_favorite_novel_statuses()

    def test_chk_favorite_novel_statuses(self):
        got_dic: dict[int, str] = self.chk_favorite_novel_statuses()
        answer_dic: dict[int, str] = {
            298052: "연재 중",
            258784: "연재 지연",
            84: "연재 중단",
            38191: "완결",
            610: "연재 중"
        }
        self.assertEqual(answer_dic, got_dic)


class GetNovelStatus(TestCase):
    """연중작, 완결작, 연재작의 연재 상태를 각각 추출하는 테스트."""

    @staticmethod
    def chk_up_status(novel_code: str) -> int:
        """입력받은 번호의 소설의 연재 상태를 추출하여 반환하는 함수

        :param novel_code: 소설 번호
        :return: '연재 중', '완결', '연습작품', '삭제', '연재중단', '연재지연' 中 택 1
        """
        from urllib.parse import urljoin
        url: str = urljoin("https://novelpia.com/novel/", novel_code)

        from src.func.common import get_novel_main_w_error
        with get_novel_main_w_error(url) as (html, err):
            if err:
                raise err

        from src.novel_info import Novel, extract_novel_info
        novel: Novel = extract_novel_info(html)

        return novel.novel_live

    def test_inaccessible_novel(self):
        code_inaccessible: str = "28"  #
        status: int = self.chk_up_status(code_inaccessible)

        self.assertEqual(STATUSES.draft, status)

    def test_deleted_novel(self):
        code_deleted: str = "2"  # <건물주 아들> - 최초의 삭제작
        status: int = self.chk_up_status(code_deleted)

        self.assertEqual(STATUSES.deleted, status)

    def test_novel_on_hiatus(self):
        code_hiatus: str = "10"  # <미대오빠의 여사친들> - 최초의 연중작
        status: int = self.chk_up_status(code_hiatus)

        self.assertEqual(STATUSES.hiatus, status)

    def test_completed_novel(self):
        code_completed: str = "1"  # <S드립을 잘 치는 여사친> - 최초의 완결작
        status: int = self.chk_up_status(code_completed)

        self.assertEqual(STATUSES.complete, status)

    def test_ongoing_novel(self):
        code_ongoing: str = "610"  # <창작물 속으로> - 연재중 (24.8.8 기준)
        status: int = self.chk_up_status(code_ongoing)

        self.assertEqual(STATUSES.ongoing, status)


@skip
class CntNovelInStatus(GetNovelStatus):
    """특정 연재 상태의 소설 비율을 재는 테스트"""

    from src.const.const import ALL_NOVEL_COUNT  # 노벨피아 총 소설 수

    @staticmethod
    def chk_up_status(novel_code: str):
        return GetNovelStatus.chk_up_status(novel_code)

    def test_cnt_novel_on_hiatus(self):
        """연중작 비율을 재는 테스트"""

        for num in range(1, self.ALL_NOVEL_COUNT):
            code = str(num)
            with self.subTest(code=code):
                up_status: int = self.chk_up_status(code)

                self.assertTrue(up_status == STATUSES.delayed or up_status == STATUSES.hiatus)

    def test_cnt_deleted_novel(self, status: str = "삭제"):
        """삭제작 비율을 재는 테스트"""

        for num in range(1, self.ALL_NOVEL_COUNT):
            code = str(num)
            with self.subTest(code=code):
                up_status: int = self.chk_up_status(code)

                self.assertTrue(up_status == status)


class NovelToMdFile(TestCase):
    from src.novel_info import Novel

    novel_code: str = '247416'
    novel = Novel(
        novel_code,
        f'https://novelpia.com/novel/{novel_code}',
        '미츄리',
        896,
        '숨겨진 흑막이 되었다',
        {'독점'},
        12,
        '\n  - 현대판타지\n  - 하렘\n  - 괴담\n  - 집착',
        '> [!TLDR] 시놉시스\n> 괴담, 저주, 여학생 등….\n> 집착해선 안 될 것들이 내게 집착한다\n',
        # '완결',
        "2023-12-11 15:19:55",
        "2024-04-17 20:00:00",
        "2023-12-11 14:12:08",
        "2024-08-29 15:45:30",
        1142,
        14616,
        225,
        224772,
        2189821,
    )

    def test_novel_to_md(self):
        """소설 정보가 담긴 Dict 를 Markdown 형식의 문자열로 변환하는 테스트

        :return: Markdown 형식의 소설 정보
        """
        from datetime import datetime
        from src.novel_info import novel_info_to_md

        formatted_md: str = f"""---
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
독점: True
완독일: 0000-00-00
연재 시작일: 2023-12-11 14:12:08
최근(예정) 연재일: 2024-04-17 20:00:00
정보 수집일: {datetime.today().isoformat(timespec='minutes')}
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
        converted_md = novel_info_to_md(self.novel)

        self.assertEqual(formatted_md, converted_md)

    @skip
    def test_novel_to_md_file(self):
        from src.novel_info import novel_to_md_file

        novel_to_md_file(NovelToMdFile.novel)

        # self.assertRaises(FileExistsError, open())
        self.fail()

    @skip
    def test_novels_to_md_files(self):
        from src.func.common import get_novel_main_w_error, print_under_new_line
        from src.const.const import HOST, ALL_NOVEL_COUNT

        from urllib.parse import urljoin

        base_url: str = urljoin(HOST, "/novel/")
        urls = (urljoin(base_url, str(code)) for code in range(1, ALL_NOVEL_COUNT))
        from time import sleep

        while True:
            url = next(urls)
            with self.subTest(url=url):
                with get_novel_main_w_error(url) as (html, err):
                    if err:
                        print_under_new_line("[오류]", f"{err = }")
                        self.fail()
                    else:
                        from src.novel_info import Novel, extract_novel_info, novel_to_md_file

                        novel: Novel = extract_novel_info(html)
                        if not novel:
                            continue
                        novel_to_md_file(novel, True)
                sleep(0.1)
                self.assertTrue(True)


if __name__ == '__main__':
    main()
