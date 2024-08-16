from unittest import TestCase, main, skip

from src.common.episode import *
from src.myTest.test_module import total_novel_cnt  # 노벨피아 총 소설 수


class TestHasPrologue(TestCase):
    """
    입력한 번호의 소설에 프롤로그가 있는 경우와 없는 경우 모두 테스트
    """
    def test_is_prologue(self):
        code_with_p: str = "145916"  # <시계탑의 페인 공작님과 마검 소녀>
        self.assertTrue(has_prologue(code_with_p))

    def test_no_prologue(self):
        code_without: str = "4"  # <숨겨진 흑막이 되었다>
        self.assertFalse(has_prologue(code_without))


class CntNovelWithPrologue(TestCase):
    @skip
    def test_cnt_novel_with_prologue(self):
        for num in range(1, total_novel_cnt):
            code = str(num)
            with self.subTest(code=code):
                self.assertTrue(has_prologue(code))


class GetEpListAndInfo(TestCase):
    def test_invalid_novel(self):
        code: str = "0"
        ep_no: int = 16
        ep_code: str = "978"

        html: str = get_ep_list(code)
        info_dic: dict = extract_ep_info(html, ep_no)
        answer_dic: dict = {
            "제목": "계월향의 꿈",
            "게시 일자": ['2021-01-07'],
            "위치": {"화수": 0, "번호": ep_code},
            "유형": {"무료": True, "성인": False},
            "통계": {
                "글자 수": 117,
                "조회수": None,
                "댓글 수": None,
                "추천 수": None,
            },
        }
        self.assertDictEqual(answer_dic, info_dic)

    def test_deleted_valid_novel(self):
        code: str = "30"
        ep_no: int = 1
        ep_code: str = "280"

        html: str = get_ep_list(code)
        info_dic: dict = extract_ep_info(html, ep_no)
        answer_dic: dict = {
            "제목": "프롤로그 : 기사와 양들이 만나는 날",
            "게시 일자": ['2020-11-18'],
            "위치": {"화수": 0, "번호": ep_code},
            "유형": {"무료": True, "성인": False},
            "통계": {
                "글자 수": 2846,
                "조회수": 35,
                "댓글 수": None,
                "추천 수": 1,
            },
        }
        self.assertDictEqual(answer_dic, info_dic)

    def test_extract_ep_title(self):
        """
        회차의 제목을 문자열로 추출.
        :return: 원 제목과 일치 시 성공
        """
        test_set: set[tuple[str, str, int, str]] = {
            ("610", "DOWN", 1, "001. 능력 각성"),  # <창작물 속으로>
            ("145916", "UP", 1, "완결 후기"),  # <시계탑의 폐인 공작님과 마검 속 소녀>
        }
        for test_params in test_set:
            code, sort, ep_no, title_a = test_params

            with self.subTest(code=code, sort=sort, ep_no=ep_no, title_a=title_a):
                html: str = get_ep_list(code, sort)

                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, "html.parser")
                ep_tags: set[Tag] | None = extract_ep_tags(soup, {ep_no})
                ep_tag: Tag = ep_tags.pop()
                title_q: str = ep_tag.b.i.next

                self.assertEqual(title_a, title_q)

    def test_no_ep_novel(self):
        """
        빈 목록에서 회차 정보를 추출하는 테스트.
        :return: 값이 None 뿐인 빈 Dict 반환 시 성공
        """
        code: str = "2"
        html: str = get_ep_list(code)
        info_dic: dict = extract_ep_info(html, 1)

        self.assertIsNone(info_dic)


@skip
class CntNoEpNovelByInfo(TestCase):
    def test_cnt_no_ep_novel(self):
        """
        작성된 회차가 없는 작품의 비율을 측정하는 테스트
        :return: (None, None, None) 반환 시 성공
        """
        for num in range(1, 10):
            code = str(num)
            with self.subTest(code=code):
                html: str = get_ep_list(code)
                info_dic: dict = extract_ep_info(html, 1)
                self.assertIsNone(info_dic)


class GetNovelUpDate(TestCase):
    @staticmethod
    def get_novel_up_date(novel_code: str, sort: str = "DOWN", ep_no: int = 1):
        from src.common.episode import extract_ep_tags, get_ep_up_dates

        list_html: str = get_ep_list(novel_code, sort)

        from bs4 import BeautifulSoup
        list_soup = BeautifulSoup(list_html, "html.parser")

        ep_tags: set[Tag] = extract_ep_tags(list_soup, {ep_no})
        if ep_tags is None:
            return None
        else:
            ep_tag: Tag = ep_tags.pop()

        up_dates: list[str] | None = get_ep_up_dates({ep_tag})
        if up_dates is None:
            return None
        else:
            return up_dates[0]

    def test_single_ep(self):
        code: str = "124146"  # <연중용 나데나데 소설>
        up_date: str = "2023-12-13"

        self.assertEqual(up_date, self .get_novel_up_date(code))

    def test_multiple_ep(self):
        code: str = "247416"  # <숨겨진 흑막이 되었다>
        fst_up_date: str = "2023-12-11"
        lst_up_date: str = "2024-04-18"

        fst_match: bool = (GetNovelUpDate.get_novel_up_date(code, "DOWN") == fst_up_date)
        lst_match: bool = (GetNovelUpDate.get_novel_up_date(code, "UP") == lst_up_date)

        self.assertTrue(fst_match and lst_match)

    def test_no_ep(self):
        code: str = "2"  # <건물주 아들>, 최초의 삭제된 소설. 동명의 9번 소설의 습작?

        self.assertIsNone(GetNovelUpDate.get_novel_up_date(code))


@skip
class CntNoEpNovelByNovelUpDate(GetNovelUpDate):
    def test_cnt_no_ep_novel(self):
        """
        노벨피아 소설 중 작성된 회차가 없는 작품을 세는 테스트
        :return: 회차가 없으면 성공, 있으면 실패
        """
        for num in range(1, 10):
            code = str(num)
            with self.subTest(code=code):
                self.assertIsNone(GetNovelUpDate.get_novel_up_date(code))


class GetEpViewCount(TestCase):
    def test_get_ep_view_cnt(self):
        novel_code: str = "30"
        ep_codes: list[str] = ["309"]
        real_view_count: int = 5

        got_view_counts: list[int] | None = get_ep_view_counts(novel_code, ep_codes)
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

        # dic: {"episode_no": 280, "count_view": "35"}
        ep_codes: list[str] = [str(dic["episode_no"]) for dic in real_view_dics]
        real_view_counts: list[int] = [int(dic["count_view"]) for dic in real_view_dics]

        got_view_counts: list[int] = get_ep_view_counts(novel_code, ep_codes)

        self.assertEqual(real_view_counts, got_view_counts)


if __name__ == "__main__":
    main()
