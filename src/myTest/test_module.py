import shutil
from os import environ
from unittest import TestCase, main, skip

from src.common.module import *


class TestGetEnvVar(TestCase):
    """
    입력받은 이름의 환경 변수가 있는 경우와 없는 경우 모두 테스트
    """

    @classmethod
    def setUpClass(cls):
        environ["test_key"] = "test_val"

    def test_key_found(self):
        test_key: str = "test_key"
        with get_env_var_w_error(test_key) as (test_val, ke):
            self.assertTrue(test_val == "test_val" and ke is None)

    def test_key_not_found(self):
        test_key: str = "fake_key"
        with get_env_var_w_error(test_key) as (test_val, ke):
            self.assertTrue(test_val is None and isinstance(ke, KeyError))

    @classmethod
    def tearDownClass(cls):
        environ.pop("test_key")


class AddLoginKey(TestCase):
    def test_add_login_key(self):
        header: dict[str: str] = {"User-Agent": UA}
        given_key, new_header = add_login_key(header)
        real_key: str = new_header["Cookie"].split("=")[1]

        self.assertEqual(real_key, given_key)


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

        for i, path in enumerate(parents):
            if path == Path(environ["HOME"]):
                child = parents[i - 1]
                try:  # 생성 성공 시 제거
                    shutil.rmtree(child)
                except FileNotFoundError as fe:  # 생성 실패
                    from src.common.userIO import print_under_new_line
                    print_under_new_line(fe.args, "폴더 생성에 실패했어요.")
                    self.fail()
                else:
                    print("[알림]", child, "폴더와 내용물을 모두 삭제했어요.")
                    break


class GetNovelMainPage(TestCase):
    def test_valid_novel_code(self):
        code: str = "247416"
        url: str = "https://novelpia.com/novel/" + code
        with get_novel_main_w_error(url) as (html, connect_err):
            assert connect_err is None, f"{connect_err = }"

        self.assertIsNotNone(html)

    @skip
    def test_valid_novel_codes(self):
        from src.common.const import TOTAL_NOVEL_COUNT

        for num in range(1, TOTAL_NOVEL_COUNT):
            code = str(num)
            with self.subTest(code=code):
                url: str = "https://novelpia.com/novel/" + code
                with get_novel_main_w_error(url) as (html, connect_err):
                    assert connect_err is None, f"{connect_err = }"

                self.assertIsNotNone(html)


if __name__ == '__main__':
    main()
