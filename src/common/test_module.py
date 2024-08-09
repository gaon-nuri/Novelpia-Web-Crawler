import shutil
import unittest

from src.common.module import *

total_novel_cnt: int = 296271  # 노벨피아 소설 수 (2024-08-08 20:10 기준)


class TestHasPrologue(unittest.TestCase):
    """
    입력한 번호의 소설에 프롤로그가 있는 경우와 없는 경우 모두 테스트
    """
    def test_prologue_found(self):
        code_with_p: str = "145916"  # <시계탑의 페인 공작님과 마검 소녀>
        code_without: str = "247416"  # <숨겨진 흑막이 되었다>
        self.assertTrue(has_prologue(code_with_p) and not has_prologue(code_without))


class TestGetEnvVar(unittest.TestCase):
    """
    입력받은 이름의 환경 변수가 있는 경우와 없는 경우 모두 테스트
    """
    @classmethod
    def setUpClass(cls):
        os.environ["test_key"] = "test_val"

    def test_key_found(self):
        self.assertEqual(get_env_var("test_key"), "test_val")

    def test_key_not_found(self):
        self.assertIsNone(get_env_var("fake_key"))

    @classmethod
    def tearDownClass(cls):
        os.environ.pop("test_key")


class AddLoginKey(unittest.TestCase):
    def test_add_login_key(self):
        header: dict[str: str] = {"User-Agent": ua}
        new_header: dict[str: str] = add_login_key(header)
        login_key: str = new_header["LOGINKEY"].split("=")[1]

        self.assertEqual(login_key, get_env_var("LOGINKEY"))


class TestChkStrType(unittest.TestCase):
    def test_str_is_num(self):
        num: str = "1"
        num_in_tab: str = "\t12\t"

        alnum: str = "a1"
        tab_in_num: str = "1\t2"

        is_num: bool = chk_str_type(num, int) and chk_str_type(num_in_tab, int)
        is_not_num: bool = chk_str_type(alnum, int) or chk_str_type(tab_in_num, int)

        self.assertTrue(is_num and not is_not_num)


class TestAssurePathExists(unittest.TestCase):
    def test_any_path(self):
        test_path = Path("~/path/to/assure/file.ext").expanduser()
        assure_path_exists(test_path)
        parents = test_path.parents

        try:  # 생성 성공 시 제거
            for i, path in enumerate(parents):
                if path == Path(os.environ["HOME"]):
                    child = parents[i - 1]
                    shutil.rmtree(child)
                    print("[알림]", child, "폴더를 삭제했어요.")
                    break

        except FileNotFoundError:  # 생성 실패
            raise


class GetNovelMainPage(unittest.TestCase):
    def test_valid_novel_code(self):
        # code: str = "247416"
        for num in range(10):
            code = str(num)
            with self.subTest(code=code):
                url: str = f"https://novelpia.com/novel/{code}"
                html: str = get_novel_main_page(url)

                self.assertIsNotNone(html)


class GetEpListAndInfo(unittest.TestCase):
    from src.viewer.viewer import extract_ep_info

    @staticmethod
    def get_ep_info(html, ep_no, login):
        return GetEpListAndInfo.extract_ep_info(html, ep_no, login)

    def test_invalid_novel_code(self):
        code: str = "0"
        ep_no: int = 16
        answer_title: str = "계월향의 꿈"

        html: str = get_ep_list(code)
        ep_info: str = self.get_ep_info(html, ep_no, False)
        ep_title = ep_info[0]

        self.assertEqual(ep_title, answer_title)

    def test_novel_on_service(self):

        test_set: set[tuple[str, str, int, str]] = {
            ("610", "DOWN", 1, "001. 능력 각성"),
            ("145916", "UP", 1, "완결 후기"),
        }

        for test_params in test_set:
            code, sort, ep_no, title_a = test_params

            with self.subTest(code=code, sort=sort, ep_no=ep_no, title_a=title_a):
                html: str = get_ep_list(code, sort)
                ep_info: str = self.get_ep_info(html, ep_no, False)
                title_q = ep_info[0]

                self.assertEqual(title_q, title_a)

    def test_deleted_novel(self):

        code: str = "2"
        html: str = get_ep_list(code)
        ep_info: tuple = self.get_ep_info(html, 1, False)

        self.assertTupleEqual(ep_info, (None,) * 3)


class CntDeletedNovel(GetEpListAndInfo):
    """
    노벨피아 소설 중 삭제된 작품의 비율을 측정하는 테스트
    """
    def test_cnt_deleted_novel(self):
        for num in range(1, total_novel_cnt):
            code = str(num)
            with self.subTest(code=code):
                html: str = get_ep_list(code)
                ep_info: tuple = self.get_ep_info(html, 1, False)

                self.assertTupleEqual(ep_info, (None,) * 3)


if __name__ == '__main__':
    unittest.TestCase.longMessage = False
    unittest.main()
