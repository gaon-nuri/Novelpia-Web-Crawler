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


class GetLikeNovelInfo(TestCase):
    @staticmethod
    def toggle_novel_alarm(novel_code: str):
        """원 함수 주석 참조"""
        from src.novel_info import toggle_novel_action

        success, alarms = toggle_novel_action(novel_code, login=1)
        print("해당 소설의 현재 알람 수:", alarms)

        return success

    def test_toggle_novel_alarm(self):
        novel_code: str = "2"  # <건물주 아들>

        self.toggle_novel_alarm(novel_code)
        status_code: int = self.toggle_novel_alarm(novel_code)

        self.assertTrue(status_code in [1, 2])

    @staticmethod
    def toggle_novel_like(novel_code: str):
        """원 함수 주석 참조"""
        from dotenv import dotenv_values
        from src.novel_info import toggle_novel_action

        config = dotenv_values()
        csrf: str = config["CSRF"]
        success, likes = toggle_novel_action(novel_code, 1, True, csrf)
        print("해당 소설의 현재 선호 수:", likes)

        return success

    def test_toggle_novel_like(self):
        novel_code: str = "2"  # <건물주 아들>

        self.toggle_novel_like(novel_code)
        status_code: int = self.toggle_novel_like(novel_code)

        self.assertTrue(status_code in [1, 2])

    from dotenv import dotenv_values

    config = dotenv_values()
    mem_no = int(config["SUB_MEM_NO"])

    @classmethod
    def get_like_novel_info_dics(cls):
        """get_like_novel_info_dics 함수 주석 참고"""
        from src.novel_info import get_like_novel_info_dics

        return get_like_novel_info_dics(cls.mem_no)

    def test_get_like_novel_info_dic(self):
        novel_code: str = "99"  # <눈송아리>

        self.toggle_novel_like(novel_code)
        count, dics = self.get_like_novel_info_dics()
        self.toggle_novel_like(novel_code)

        try:
            got_dic: dict = next(dics)

        # 선호작 X
        except StopIteration as si:
            print(self, f"{si = }")

            self.fail()
        else:
            answer_dic: dict = {
                'novel_no': 99,
                'novel_name': "눈송아리",
                'novel_search': "ㄴㅜㄴㅅㅗㅇㅇㅏㄹㅣ|ㄴㅜㅅㅗㅇㅏㄹㅣ|ㄴㅅㅇㄹ",
                'novel_subtitle': "눈송아리",
                'novel_age': 0,
                'mem_no': 1516,
                'novel_thumb': None,
                'novel_img': None,
                'novel_thumb_all': '',
                'novel_img_all': '',
                'novel_count': 0,
                'novel_type': 2,
                'novel_genre': None,
                'novel_story': "이것은...\r\n\r\n잔혹한 운명의 흐름속에 놓인 두 괴물의 사랑 이야기.",
                'novel_status': 1,
                'novel_weekly': 0,
                'novel_notice': '',
                'novel_plus_want': 0,
                'count_view': 12,
                'count_good': 0,
                'count_book': 1,
                'count_pick': 0,
                'writer_nick': "삭제",
                'writer_original': None,
                'isbn': None,
                'last_viewdate': "2021-01-07 10:38:08",
                'is_monopoly': 0,
                'is_del': 0,
                'is_complete': 0,
                'is_donation_refusal': 0,
                'is_secondary_creation': 0,
                'is_contest': 0,
                'start_date': "2021-01-07 10:38:08",
                'status_date': '2024-09-07 19:00:29',
                'del_date': None,
                'complete_date': None,
                'plus_date': None,
                'plus_call_date': None,
                'plus_check_admin_no': None,
                'last_write_date': "2021-01-07 10:38:08",
                'novel_live': 0,
                'live_stop_end_date': None,
                'is_indent': 0,
                'main_genre': 0,
                'is_osmu': None,
                'flag_collect': 0,
                'local_code': "KR",
                'monopoly_date': None,
                'flag_img_policy': 0,
                'flag_translate': 0,
                'reg_date': None,
                'update_dt': None,
                'plus_start_date': None,
            }

            self.assertEqual(answer_dic, got_dic)


class GetNovelStatus(TestCase):
    """연중작, 완결작, 연재작의 연재 상태를 각각 추출하는 테스트."""

    @staticmethod
    def chk_up_status(novel_code: str) -> str:
        """입력받은 번호의 소설의 연재 상태를 추출하여 반환하는 함수

        :param novel_code: 소설 번호
        :return: '연재 중', '완결', '연습작품', '삭제', '연재중단', '연재지연' 中 택 1
        """
        from src.novel_info import Novel, set_novel_from_likes

        novels, count = set_novel_from_likes(1, novel_code)
        novel: Novel = next(novels)

        return novel.up_status

    def test_inaccessible_novel(self):
        code_inaccessible: str = "28"  #
        up_status: str = self.chk_up_status(code_inaccessible)

        self.assertEqual(STATUSES.draft, up_status)

    def test_deleted_novel(self):
        code_deleted: str = "2"  # <건물주 아들> - 최초의 삭제작
        up_status: str = self.chk_up_status(code_deleted)

        self.assertEqual(STATUSES.deleted, up_status)

    def test_novel_on_hiatus(self):
        code_hiatus: str = "10"  # <미대오빠의 여사친들> - 최초의 연중작
        up_status: str = self.chk_up_status(code_hiatus)

        self.assertEqual(STATUSES.hiatus, up_status)

    def test_completed_novel(self):
        code_completed: str = "1"  # <S드립을 잘 치는 여사친> - 최초의 완결작
        up_status: str = self.chk_up_status(code_completed)

        self.assertEqual(STATUSES.complete, up_status)

    def test_ongoing_novel(self):
        code_ongoing: str = "610"  # <창작물 속으로> - 연재중 (24.8.8 기준)
        up_status: str = self.chk_up_status(code_ongoing)

        self.assertEqual(STATUSES.ongoing, up_status)


class CntNovelInStatus(GetNovelStatus):
    """특정 연재 상태의 소설 비율을 재는 테스트"""
    from src.const.const import ALL_NOVEL_COUNT  # 노벨피아 총 소설 수

    @staticmethod
    def chk_up_status(novel_code: str):
        return GetNovelStatus.chk_up_status(novel_code)

    @skip
    def test_cnt_novel_on_hiatus(self):
        """연중작 비율을 재는 테스트"""

        for num in range(1, self.ALL_NOVEL_COUNT):
            code = str(num)
            with self.subTest(code=code):
                up_status: str = self.chk_up_status(code)

                self.assertTrue(up_status == STATUSES.delayed or up_status == STATUSES.hiatus)

    @skip
    def test_cnt_deleted_novel(self, real_up_status: str = "삭제"):
        """삭제작 비율을 재는 테스트"""

        for num in range(1, self.ALL_NOVEL_COUNT):
            code = str(num)
            with self.subTest(code=code):
                got_up_status: str = self.chk_up_status(code)

                self.assertTrue(real_up_status == got_up_status)


class NovelToMdFile(TestCase):
    from src.novel_info import Novel

    novel_code: str = '247416'
    info_dic: dict = {
        "novel_no": novel_code,
        "novel_name": "숨겨진 흑막이 되었다",
        "novel_search": "ㅅㅜㅁㄱㅕㅈㅣㄴ ㅎㅡㄱㅁㅏㄱㅇㅣ ㄷㅚㅇㅓㅆㄷㅏ|ㅅㅜㄱㅕㅈㅣ ㅎㅡㅁㅏㅇㅣ ㄷㅚㅇㅓㄷㅏ|ㅅㄱㅈ ㅎㅁㅇ ㄷㅇㄷ",
        "novel_subtitle": None,
        "novel_age": 0,
        "mem_no": 896,
        "novel_thumb": "",
        "novel_img": None,
        "novel_thumb_all": "/imagebox/cover/3ff0030a8af5ee6a2facf697c2976e11_56852_ori.file",
        "novel_img_all": "/imagebox/cover/0ec297a59a49a6db56922fff3b47a3c1_4587281_q_ori.file",
        "novel_count": 0,
        "novel_status": 1,
        "novel_type": 1,
        "novel_genre": "[\"현대판타지\",\"하렘\",\"괴담\",\"집착\"]",
        "novel_story": "괴담, 저주, 여학생 등….\r\n집착해선 안 될 것들이 내게 집착한다",
        "novel_weekly": 127,
        "novel_notice": None,
        "novel_plus_want": 2,
        "count_view": 2198153,
        "count_good": 225713,
        "count_book": 225,
        "count_pick": 53,
        "writer_nick": "미츄리",
        "writer_original": "",
        "isbn": "",
        "last_viewdate": "2024-04-18 20:00:00",
        "is_monopoly": 1,
        "is_del": 0,
        "is_complete": 1,
        "is_donation_refusal": 0,
        "is_secondary_creation": 0,
        "is_contest": 0,
        "start_date": "2023-12-11 15:19:55",
        "status_date": "2024-08-31 17:45:30",
        "del_date": None,
        "complete_date": "2024-04-18 17:58:21",
        "plus_date": "2023-12-18 09:12:15",
        "plus_call_date": "2024-01-01 14:42:58",
        "plus_check_admin_no": 1227680,
        "last_write_date": "2024-04-17 20:00:00",
        "novel_live": 0,
        "live_stop_end_date": None,
        "is_indent": 0,
        "main_genre": 12,
        "is_osmu": None,
        "flag_collect": 0,
        "local_code": "ko",
        "monopoly_date": "2024-01-02 14:55:09",
        "flag_img_policy": 1,
        "flag_translate": 0,
        "reg_date": "2023-12-11 14:12:08",
        "update_dt": "2024-08-29 17:29:15",
        "plus_start_date": None
    }
    novel = Novel(
        info_dic,
        '완결',
        {'독점'},
        '\n  - 현대판타지\n  - 하렘\n  - 괴담\n  - 집착',
        '> [!TLDR] 시놉시스\n> 괴담, 저주, 여학생 등….\n> 집착해선 안 될 것들이 내게 집착한다\n',
    )

    def test_novel_to_md(self):
        """Novel 클래스 객체를 Markdown 형식의 문자열로 변환하는 테스트"""
        from datetime import datetime
        from src.novel_info import novel_info_to_md

        formatted_md: str = f"""---
aliases:
  - (직접 적어 주세요)
유입 경로: (직접 적어 주세요)
작가명: 미츄리
소설 링크: https://novelpia.com/novel/247416
tags:
  - "현대판타지"
  - "하렘"
  - "괴담"
  - "집착"
PLUS: True
독점: True
완결: True
완독일: 0000-00-00T00:00
연재 시작일: 2023-12-11 15:19:55
최근(예정) 연재일: 2024-04-17 20:00:00
소설 등록일: 2023-12-11 14:12:08
소설 갱신일: 2024-08-29 17:29:15
원격 갱신일: 2024-08-31 17:45:30
로컬 갱신일: {datetime.today().isoformat(timespec='minutes')}
회차 수: 225
알람 수: None
선호 수: None
추천 수: 225713
조회 수: 2198153
---

> [!TLDR] 시놉시스
> 괴담, 저주, 여학생 등….
> 집착해선 안 될 것들이 내게 집착한다
"""
        converted_md = novel_info_to_md(self.novel)

        self.assertEqual(formatted_md, converted_md)

    @skip
    def test_novel_to_md_file(self):
        """Novel 클래스 객체를 Markdown 파일로 쓰는 테스트"""
        from src.novel_info import novel_to_md_file

        novel_to_md_file(self.novel)

        self.assertTrue(True)

    @skip
    def test_novels_to_md_files(self):
        """모든 노벨피아 소설의 정보를 Markdown 파일로 추출하는 테스트"""
        from urllib.parse import urljoin
        from time import sleep

        from src.const.const import HOST, ALL_NOVEL_COUNT
        from src.novel_info import Novel, set_novel_from_likes, novel_to_md_file

        base_url: str = urljoin(HOST, "/novel/")

        for i in range(1, ALL_NOVEL_COUNT):
            code = str(i)
            with self.subTest(url=urljoin(base_url, code)):
                novels, count = set_novel_from_likes(1, code)
                novel: Novel = next(novels)
                if not novel:
                    continue
                novel_to_md_file(novel, True)
                sleep(0.1)

                self.assertTrue(True)


if __name__ == '__main__':
    main()
