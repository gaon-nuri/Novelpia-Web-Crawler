"""회차 관련 기능 테스트"""
from logging import getLogger
from unittest import TestCase, main, skip

from src.func.crawl import fetch_ep_li_pg_from_code, fetch_ep_view_gen_from_code_gen
from src.func.episode import ep_obj_from_page, has_prologue
from src.models import Ep
from src.novel_info import get_novel_up_dates

logger = getLogger(__name__)


@skip
class ChkMetaClass(TestCase):
    def test_inherit_user_meta_class(self):
        """Ep 클래스의 사용자 메타 클래스 상속 여부 테스트"""
        from src.models import UserMeta
        logger.info("Ep.mro():", Ep.mro())
        self.assertTrue(isinstance(Ep, UserMeta))


class TestHasPrologue(TestCase):
    """소설의 프롤로그 유무를 구하는 테스트"""

    def test_has_prologue(self):
        code_with_p: str = "145916"  # <시계탑의 페인 공작님과 마검 소녀>
        self.assertTrue(has_prologue(code_with_p))

    def test_no_prologue(self):
        code_without: str = "4"  # <숨겨진 흑막이 되었다>
        self.assertFalse(has_prologue(code_without))


@skip
class CntNovelWithPrologue(TestCase):
    def test_cnt_novel_with_prologue(self):
        """프롤로그가 있는 소설의 수를 구하는 테스트 뭉치."""
        from src.const.const import ALL_NOVEL_CNT  # 노벨피아 총 소설 수
        for num in range(1, ALL_NOVEL_CNT):
            code = str(num)
            with self.subTest(code=code):
                self.assertTrue(has_prologue(code))


class GetEpListAndInfo(TestCase):
    @staticmethod
    def get_ep(novel_code: str, ep_no: int) -> Ep:
        """소설 번호와 회차 서수를 입력받아 Ep 객체를 반환하는 메서드

        :param novel_code: 소설 번호
        :param ep_no: 회차 서수
        :return: Ep 객체
        """
        page: str = fetch_ep_li_pg_from_code(novel_code, do_plus_login=True)
        got_ep: Ep = ep_obj_from_page(page, ep_no)
        return got_ep

    def test_invalid_novel(self):
        novel_code: str = "0"
        ep_no: int = 16
        ep_code: str = "978"
        got_ep: Ep = self.get_ep(novel_code, ep_no)
        answer_ep = Ep("계월향의 꿈", ep_code, f"https://novelpia.com/viewer/{ep_code}", "2021-01-07", kinds={"자유"}, num=0,
                       letter=117, )
        self.assertEqual(*map(str, [answer_ep, got_ep]))

    def test_deleted_valid_novel(self):
        """삭제된 회차의 정보를 구하는 테스트

        :return: 두 Ep 클래스 객체의 str 값이 같으면 성공
        """
        novel_code: str = "30"
        ep_no: int = 1
        got_ep: Ep = self.get_ep(novel_code, ep_no)
        answer_ep = Ep("프롤로그 : 기사와 양들이 만나는 날", "280", "https://novelpia.com/viewer/280", "2020-11-18", count_good=1,
                       count_view=35, kinds={"자유"}, num=0, letter=2846, )
        self.assertEqual(*map(str, [answer_ep, got_ep]))

    def test_extract_ep_title(self):
        """회차의 제목을 문자열로 추출하는 테스트

        :return: 추출한 제목이 원래 제목과 같으면 성공
        """
        test_set: set[tuple[str, str, int, str]] = {("610", "DOWN", 1, "001. 능력 각성"),  # <창작물 속으로>
            ("145916", "UP", 1, "완결 후기"),  # <시계탑의 폐인 공작님과 마검 속 소녀>
        }
        for test_params in test_set:
            code, sort, ep_no, title_a = test_params
            with self.subTest(code=code, sort=sort, ep_no=ep_no, title_a=title_a):
                page: str = fetch_ep_li_pg_from_code(code, sort)
                from src.parsers import ep_tag_gen_from_page
                ep_tag_gen = ep_tag_gen_from_page(page, [ep_no])
                ep_tag = next(ep_tag_gen)
                title_q: str = ep_tag.b.i.next
                self.assertEqual(title_a, title_q)

    def test_no_ep_novel(self, code: str = "2"):
        """빈 목록에서 회차 정보를 추출하는 테스트.

        :return: 값이 None 뿐인 빈 Dict 반환 시 성공
        """
        page: str = fetch_ep_li_pg_from_code(code)
        ep: Ep = ep_obj_from_page(page)
        self.assertIsNone(ep)

    @skip
    def test_cnt_no_ep_novel(self):
        """작성된 회차가 없는 작품의 비율을 측정하는 테스트

        :return: (None, None, None) 반환 시 성공
        """
        for num in range(1, 10):
            code = str(num)
            with self.subTest(code=code):
                self.test_no_ep_novel(code)


class GetNovelUpDate(TestCase):
    """소설의 연재 시작일과 최근 (예정) 연재일을 구하는 테스트"""

    def test_single_ep(self):
        """단편 소설의 회차 게시 일자 추출 테스트"""
        code: str = "124146"  # <연중용 나데나데 소설>
        up_date: str = "2023-12-13"
        self.assertEqual(up_date, get_novel_up_dates(code))

    def test_multiple_ep(self):
        """장편 소설의 회차 게시 일자 추출 테스트"""
        code: str = "247416"  # <숨겨진 흑막이 되었다>
        fst_up_date: str = "2023-12-11"
        lst_up_date: str = "2024-04-18"
        fst_match: bool = (get_novel_up_dates(code) == fst_up_date)
        lst_match: bool = (get_novel_up_dates(code, "UP") == lst_up_date)
        self.assertTrue(fst_match and lst_match)

    def test_no_ep(self):
        """회차가 없는 소설의 회차 게시 일자 추출 테스트"""
        code: str = "2"  # <건물주 아들>, 최초의 삭제된 소설. 동명의 9번 소설의 습작?
        self.assertIsNone(get_novel_up_dates(code))

    @skip
    def test_scheduled_ep(self):
        """예약 회차 게시 일자 추출 테스트"""
        code: str = "610"
        up_date: str = "2024-08-19T04:25:29"
        self.assertEqual(up_date, get_novel_up_dates(code))


@skip
class CntNoEpNovelByNovelUpDate(GetNovelUpDate):
    def test_cnt_no_ep_novel(self):
        """노벨피아 소설 중 작성된 회차가 없는 작품을 세는 테스트

        :return: 회차가 없으면 성공, 있으면 실패
        """
        for num in range(1, 10):
            code = str(num)
            with self.subTest(code=code):
                self.assertIsNone(get_novel_up_dates(code))


class GetEpViewCount(TestCase):
    def test_get_ep_view_cnt(self):
        """회차의 조회 수를 추출하는 테스트

        :return: 추출한 조회 수가 실제 조회수와 같으면 성공
        """
        novel_code: str = "30"
        ep_code_gen = (s for s in ["309"])
        real_view_cnt: int = 5
        got_view_cnt_gen = fetch_ep_view_gen_from_code_gen(novel_code, ep_code_gen, 1)
        assert got_view_cnt_gen is not None, "조회수를 받지 못했어요."
        got_view_cnt = next(got_view_cnt_gen)
        self.assertEqual(real_view_cnt, got_view_cnt)

    def test_get_ep_view_cnt_list(self):
        novel_code: str = "30"
        real_view_dic: dict[str: list[dict]] = {
            "list": [{"episode_no": 280, "cnt_view": "35"}, {"episode_no": 286, "cnt_view": "13"},
                     {"episode_no": 294, "cnt_view": "11"}, {"episode_no": 301, "cnt_view": "8"},
                     {"episode_no": 309, "cnt_view": "5"}, {"episode_no": 310, "cnt_view": "4"},
                     {"episode_no": 318, "cnt_view": "3"}, {"episode_no": 319, "cnt_view": "3"},
                     {"episode_no": 326, "cnt_view": "3"}, {"episode_no": 327, "cnt_view": "6"},
                     {"episode_no": 10730, "cnt_view": "2"}, {"episode_no": 12604, "cnt_view": "2"},
                     {"episode_no": 12605, "cnt_view": "1"}, {"episode_no": 12606, "cnt_view": "1"}]}
        real_view_dic_li: list[dict] = real_view_dic["list"]
        ep_cnt: int = len(real_view_dic_li)

        # dic: {"episode_no": 280, "cnt_view": "35"}
        ep_codes = (str(dic["episode_no"]) for dic in real_view_dic_li)
        real_view_cnts: list[int] = [int(dic["cnt_view"]) for dic in real_view_dic_li]
        got_view_cnt_gen = fetch_ep_view_gen_from_code_gen(novel_code, ep_codes, ep_cnt)
        self.assertEqual(real_view_cnts, [*got_view_cnt_gen])


if __name__ == "__main__":
    main()
