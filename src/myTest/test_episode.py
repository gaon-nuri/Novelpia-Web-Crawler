from unittest import TestCase, main, skip

from src.common.episode import Ep, extract_ep_info, extract_ep_tags, get_ep_list, get_ep_view_counts, has_prologue
from src.common.module import print_under_new_line


class ChkMetaClass(TestCase):
    def test_inherit_user_meta_class(self):
        """Ep 클래스의 사용자 메타 클래스 상속 여부 테스트"""

        from src.common.module import UserMeta
        from src.common.episode import Ep

        print_under_new_line("Ep.mro():", Ep.mro())
        
        self.assertTrue(isinstance(Ep, UserMeta))


class TestHasPrologue(TestCase):
    """소설의 프롤로그 유무를 구하는 테스트"""

    def test_is_prologue(self):
        code_with_p: str = "145916"  # <시계탑의 페인 공작님과 마검 소녀>
        self.assertTrue(has_prologue(code_with_p))

    def test_no_prologue(self):
        code_without: str = "4"  # <숨겨진 흑막이 되었다>
        self.assertFalse(has_prologue(code_without))


@skip
class CntNovelWithPrologue(TestCase):
    def test_cnt_novel_with_prologue(self):
        """프롤로그가 있는 소설의 수를 구하는 테스트 뭉치.

        :return: 각각 프롤로그가 있으면 성공
        """
        from src.common.const import TOTAL_NOVEL_COUNT  # 노벨피아 총 소설 수

        for num in range(1, TOTAL_NOVEL_COUNT):
            code = str(num)
            with self.subTest(code=code):
                self.assertTrue(has_prologue(code))


class GetEpListAndInfo(TestCase):
    from src.common.const import DEFAULT_TIME

    def test_invalid_novel(self):
        novel_code: str = "0"
        ep_no: int = 16

        html: str = get_ep_list(novel_code, plus_login=True)
        got_ep: Ep = extract_ep_info(html, ep_no)
        ep_code: str = "978"

        from datetime import datetime

        got_time: str = datetime.today().isoformat(timespec='minutes')

        answer_ep = Ep(
            "계월향의 꿈",
            ep_code,
            f"https://novelpia.com/viewer/{ep_code}",
            "2021-01-07",
            self.DEFAULT_TIME,
            got_time,
            -1,
            -1,
            {"자유"},
            0,
            117,
            -1,
        )
        self.assertEqual(*map(str, [answer_ep, got_ep]))

    def test_deleted_valid_novel(self):
        """삭제된 회차의 정보를 구하는 테스트

        :return: 두 Ep 클래스 객체의 str 값이 같으면 성공
        """
        novel_code: str = "30"
        ep_no: int = 1

        html: str = get_ep_list(novel_code, plus_login=True)
        got_ep: Ep = extract_ep_info(html, ep_no)

        answer_ep = Ep(
            "프롤로그 : 기사와 양들이 만나는 날",
            "280",
            "https://novelpia.com/viewer/280",
            "2020-11-18",
            self.DEFAULT_TIME,
            self.DEFAULT_TIME,
            1,
            35,
            {"자유"},
            0,
            2846,
            -1,
        )
        self.assertEqual(*map(str, [answer_ep, got_ep]))

    def test_extract_ep_title(self):
        """회차의 제목을 문자열로 추출하는 테스트

        :return: 추출한 제목이 원래 제목과 같으면 성공
        """
        test_set: set[tuple[str, str, int, str]] = {
            ("610", "DOWN", 1, "001. 능력 각성"),  # <창작물 속으로>
            ("145916", "UP", 1, "완결 후기"),  # <시계탑의 폐인 공작님과 마검 속 소녀>
        }
        from bs4.element import Tag

        for test_params in test_set:
            code, sort, ep_no, title_a = test_params

            with self.subTest(code=code, sort=sort, ep_no=ep_no, title_a=title_a):
                html: str = get_ep_list(code, sort)
                ep_tags: list[Tag] | None = extract_ep_tags(html, frozenset({ep_no}))
                ep_tag: Tag = ep_tags.pop()
                title_q: str = ep_tag.b.i.next

                self.assertEqual(title_a, title_q)

    def test_no_ep_novel(self):
        """빈 목록에서 회차 정보를 추출하는 테스트.

        :return: 값이 None 뿐인 빈 Dict 반환 시 성공
        """
        code: str = "2"
        html: str = get_ep_list(code)
        ep: Ep = extract_ep_info(html, 1)

        self.assertIsNone(ep)


@skip
class CntNoEpNovelByInfo(TestCase):
    def test_cnt_no_ep_novel(self):
        """작성된 회차가 없는 작품의 비율을 측정하는 테스트

        :return: (None, None, None) 반환 시 성공
        """
        for num in range(1, 10):
            code = str(num)
            with self.subTest(code=code):
                html: str = get_ep_list(code)
                info_dic: dict = extract_ep_info(html, 1)
                self.assertIsNone(info_dic)


class GetNovelUpDate(TestCase):
    """소설의 연재 시작일과 최근 (예정) 연재일을 구하는 테스트"""

    from src.novel_info import get_novel_up_dates

    def test_single_ep(self):
        """단편 소설의 회차 게시 일자 추출 테스트"""
        
        code: str = "124146"  # <연중용 나데나데 소설>
        up_date: str = "2023-12-13"

        self.assertEqual(up_date, self.get_novel_up_dates(code))

    def test_multiple_ep(self):
        """장편 소설의 회차 게시 일자 추출 테스트"""
        
        code: str = "247416"  # <숨겨진 흑막이 되었다>
        fst_up_date: str = "2023-12-11"
        lst_up_date: str = "2024-04-18"

        fst_match: bool = (GetNovelUpDate.get_novel_up_dates(code, "DOWN") == fst_up_date)
        lst_match: bool = (GetNovelUpDate.get_novel_up_dates(code, "UP") == lst_up_date)

        self.assertTrue(fst_match and lst_match)

    def test_no_ep(self):
        """회차가 없는 소설의 회차 게시 일자 추출 테스트"""
        
        code: str = "2"  # <건물주 아들>, 최초의 삭제된 소설. 동명의 9번 소설의 습작?

        self.assertIsNone(GetNovelUpDate.get_novel_up_dates(code))

    @skip
    def test_scheduled_ep(self):
        """예약 회차 게시 일자 추출 테스트"""
        
        code: str = "610"
        up_date: str = "2024-08-19T04:25:29"

        self.assertEqual(up_date, self.get_novel_up_dates(code))


@skip
class CntNoEpNovelByNovelUpDate(GetNovelUpDate):
    def test_cnt_no_ep_novel(self):
        """노벨피아 소설 중 작성된 회차가 없는 작품을 세는 테스트

        :return: 회차가 없으면 성공, 있으면 실패
        """
        for num in range(1, 10):
            code = str(num)
            with self.subTest(code=code):
                self.assertIsNone(GetNovelUpDate.get_novel_up_dates(code))


class GetEpViewCount(TestCase):
    def test_get_ep_view_cnt(self):
        """회차의 조회 수를 추출하는 테스트

        :return: 추출한 조회 수가 실제 조회수와 같으면 성공
        """
        novel_code: str = "30"
        from typing import Generator

        ep_codes: Generator = (s for s in ["309"])
        real_view_count: int = 5

        got_view_counts: list[int] | None = get_ep_view_counts(novel_code, ep_codes, 1)
        assert got_view_counts is not None, "조회수를 받지 못했어요."

        got_view_count = got_view_counts[0]

        self.assertEqual(real_view_count, got_view_count)

    def test_get_ep_view_cnt_list(self):
        novel_code: str = "30"
        real_view_json: dict[str: list[dict]] = {
            "list": [
                {
                    "episode_no": 280,
                    "count_view": "35"
                },
                {
                    "episode_no": 286,
                    "count_view": "13"
                },
                {
                    "episode_no": 294,
                    "count_view": "11"
                },
                {
                    "episode_no": 301,
                    "count_view": "8"
                },
                {
                    "episode_no": 309,
                    "count_view": "5"
                },
                {
                    "episode_no": 310,
                    "count_view": "4"
                },
                {
                    "episode_no": 318,
                    "count_view": "3"
                },
                {
                    "episode_no": 319,
                    "count_view": "3"
                },
                {
                    "episode_no": 326,
                    "count_view": "3"
                },
                {
                    "episode_no": 327,
                    "count_view": "6"
                },
                {
                    "episode_no": 10730,
                    "count_view": "2"
                },
                {
                    "episode_no": 12604,
                    "count_view": "2"
                },
                {
                    "episode_no": 12605,
                    "count_view": "1"
                },
                {
                    "episode_no": 12606,
                    "count_view": "1"
                }
            ]
        }
        real_view_dics: list[dict] = real_view_json["list"]
        ep_count: int = len(real_view_dics)

        # dic: {"episode_no": 280, "count_view": "35"}
        ep_codes = (str(dic["episode_no"]) for dic in real_view_dics)
        real_view_counts: list[int] = [int(dic["count_view"]) for dic in real_view_dics]

        got_view_counts: list[int] = get_ep_view_counts(novel_code, ep_codes, ep_count)

        self.assertEqual(real_view_counts, got_view_counts)


if __name__ == "__main__":
    main()
