import shutil
import unittest

from module import *


class TestHasPrologue(unittest.TestCase):
    """
    입력한 번호의 소설에 프롤로그가 있는 경우와 없는 경우 모두 테스트
    """
    def test_prologue_found(self):
        self.assertTrue(has_prologue("145916"))  # <시계탑의 페인 공작님과 마검 소녀>

    def test_prologue_not_found(self):
        self.assertFalse(has_prologue("247416"))  # <숨겨진 흑막이 되었다>


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


class TestGetNovelMainPage(unittest.TestCase):
    def test_valid_novel_code(self):
        # code: str = "247416"
        for num in range(10):
            code = str(num)
            with self.subTest(code=code):
                url: str = f"https://novelpia.com/novel/{code}"
                try:
                    html: str = get_novel_main_page(url)

                # 접속 실패
                except requests.exceptions.ConnectionError as ce:
                    err_msg: str = ce.args[0].args[0]
                    index: int = err_msg.find("Failed")
                    print_under_new_line(err_msg[index:-42])

                # 성공
                else:
                    self.assertNotEqual(html, "")


class TestGetEpListAndInfo(unittest.TestCase):
    def test_invalid_novel_code(self):
        from src.viewer.viewer import extract_ep_info

        code: str = "0"
        ep_no: int = 16
        answer_title: str = "계월향의 꿈"

        html: str = get_ep_list(code)
        ep_info: str = extract_ep_info(html, ep_no, False)
        ep_title = ep_info[0]

        self.assertEqual(ep_title, answer_title)

    def test_novel_on_service(self):
        from src.viewer.viewer import extract_ep_info

        test_set: set[tuple[str, str, int, str]] = {
            ("610", "DOWN", 1, "001. 능력 각성"),
            ("145916", "UP", 1, "완결 후기"),
        }

        for test_params in test_set:
            code, sort, ep_no, title_a = test_params

            with self.subTest(code=code, sort=sort, ep_no=ep_no, title_a=title_a):
                html: str = get_ep_list(code, sort)
                ep_info: str = extract_ep_info(html, ep_no, False)
                title_q = ep_info[0]

                self.assertEqual(title_q, title_a)

    def test_deleted_novel(self):
        from src.viewer.viewer import extract_ep_info

        # code: str = "2"
        ep_no: int = 1

        # html: str = get_ep_list(code)
        # ep_info: tuple = extract_ep_info(html, ep_no, False)

        # self.assertTupleEqual(ep_info, (None,) * 3)

        for num in range(296079):  # 노벨피아 소설 수 (24.8.7 22.32 기준)
            code = str(num)
            with self.subTest(code=code, ep_no=ep_no):
                html: str = get_ep_list(code)
                ep_info: tuple = extract_ep_info(html, ep_no, False)

                self.assertTupleEqual(ep_info, (None,) * 3)


class Test(unittest.TestCase):
    def test_add_login_key(self):
        # header: dict[str: str] = {"User-Agent": ua}
        # header_with_login_key = {"User-Agent": ua, "Cookie": "LOGINKEY="}
        # self.assertEqual()
        self.fail()

    def test_open_file_if_none(self):
        self.fail()


if __name__ == '__main__':
    unittest.main()
