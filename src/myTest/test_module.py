import shutil
from os import environ
from unittest import TestCase, main, skip

from src.common.module import *

total_novel_cnt: int = 297394  # 노벨피아 소설 수 (2024-08-13 17:37 기준)


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

        from src.common.userIO import chk_str_type
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
            from src.common.userIO import print_under_new_line
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


if __name__ == '__main__':
    main()