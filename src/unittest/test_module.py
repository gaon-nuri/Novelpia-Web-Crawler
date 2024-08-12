import shutil
from os import environ
from unittest import TestCase, main, skip

from src.common.module import *

total_novel_cnt: int = 296271  # 노벨피아 소설 수 (2024-08-08 20:10 기준)


class TestHasPrologue(TestCase):
    """
    입력한 번호의 소설에 프롤로그가 있는 경우와 없는 경우 모두 테스트
    """
    def test_prologue_found(self):
        code_with_p: str = "145916"  # <시계탑의 페인 공작님과 마검 소녀>
        code_without: str = "4"  # <숨겨진 흑막이 되었다>
        self.assertTrue(has_prologue(code_with_p) and not has_prologue(code_without))


class CntNovelWithPrologue(TestCase):
    @skip
    def test_cnt_novel_with_prologue(self):
        for num in range(1, total_novel_cnt):
            code = str(num)
            with self.subTest(code=code):
                self.assertTrue(has_prologue(code))


class TestGetEnvVar(TestCase):
    """
    입력받은 이름의 환경 변수가 있는 경우와 없는 경우 모두 테스트
    """
    @classmethod
    def setUpClass(cls):
        environ["test_key"] = "test_val"

    def test_key_found(self):
        self.assertEqual(get_env_var("test_key"), "test_val")

    def test_key_not_found(self):
        self.assertIsNone(get_env_var("fake_key"))

    @classmethod
    def tearDownClass(cls):
        environ.pop("test_key")


class AddLoginKey(TestCase):
    def test_add_login_key(self):
        header: dict[str: str] = {"User-Agent": ua}
        given_key, new_header = add_login_key(header)
        real_key: str = new_header["Cookie"].split("=")[1]

        self.assertEqual(given_key, real_key)


class TestChkStrType(TestCase):
    def test_str_is_num(self):
        num: str = "1"
        num_in_tab: str = "\t12\t"

        alnum: str = "a1"
        tab_in_num: str = "1\t2"

        is_num: bool = chk_str_type(num, int) and chk_str_type(num_in_tab, int)
        is_not_num: bool = chk_str_type(alnum, int) or chk_str_type(tab_in_num, int)

        self.assertTrue(is_num and not is_not_num)


class TestAssurePathExists(TestCase):
    def test_any_path(self):
        test_path = Path("~/path/to/assure/file.ext").expanduser()
        assure_path_exists(test_path)
        parents = test_path.parents

        try:  # 생성 성공 시 제거
            for i, path in enumerate(parents):
                if path == Path(environ["HOME"]):
                    child = parents[i - 1]
                    shutil.rmtree(child)
                    print("[알림]", child, "폴더와 내용물을 모두 삭제했어요.")
                    break

        except FileNotFoundError as fe:  # 생성 실패
            print_under_new_line(fe.args, "폴더 생성에 실패했어요.")
            self.fail()


class GetNovelMainPage(TestCase):
    def test_valid_novel_code(self):
        code: str = "247416"
        url: str = "https://novelpia.com/novel/" + code
        html: str = get_novel_main_page(url)

        self.assertIsNotNone(html)

    @skip
    def test_valid_novel_codes(self):
        for num in range(total_novel_cnt):
            code = str(num)

            with self.subTest(code=code):
                url: str = "https://novelpia.com/novel/" + code
                html: str = get_novel_main_page(url)

                self.assertIsNotNone(html)


class GetEpViewCount(TestCase):
    def test_get_ep_view_cnt(self):
        novel_code: str = "30"
        ep_codes: list[str] = ["309"]
        real_view_cnt: int = 5

        got_view_cnts: list[int] | None = get_ep_view_cnts(novel_code, ep_codes)
        assert got_view_cnts is not None, "조회수를 받지 못했어요."

        got_view_cnt = got_view_cnts[0]

        self.assertEqual(got_view_cnt, real_view_cnt)

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

        # dic = {"episode_no": 280, "count_view": "35"}
        ep_codes: list[str] = [str(dic["episode_no"]) for dic in real_view_dics]
        real_view_cnts: list[int] = [int(dic["count_view"]) for dic in real_view_dics]

        got_view_cnts: list[int] = get_ep_view_cnts(novel_code, ep_codes)

        self.assertEqual(got_view_cnts, real_view_cnts)


class GetEpListAndInfo(TestCase):
    def test_invalid_novel_code(self):
        code: str = "0"
        ep_no: int = 16

        html: str = get_ep_list(code)
        info_dic: dict = extract_ep_info(html, ep_no)
        answer_dic: dict = {
            "제목": "계월향의 꿈",
            "위치": {"화수": 0, "번호": '978'},
            "유형": {"무료": True, "성인": False},
            "통계": {
                "글자 수": 117,
                "조회수": None,
                "댓글 수": None,
                "추천 수": None,
            },
        }
        self.assertDictEqual(info_dic, answer_dic)

    @skip
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
                ep_info: dict = extract_ep_info(html, ep_no)
                title_q = ep_info["제목"]

                self.assertEqual(title_q, title_a)

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
class CntNoEpNovel(TestCase):
    def test_cnt_no_ep_novel(self):
        """
        작성된 회차가 없는 작품의 비율을 측정하는 테스트
        :return: (None, None, None) 반환 시 성공
        """
        for num in range(1, total_novel_cnt):
            code = str(num)
            with self.subTest(code=code):
                html: str = get_ep_list(code)
                info_dic: dict = extract_ep_info(html, 1)
                self.assertIsNone(info_dic)


if __name__ == '__main__':
    main()
