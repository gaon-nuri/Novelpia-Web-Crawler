"""공통 함수 테스트"""
from logging import getLogger
from os import environ
from shutil import rmtree
from unittest import TestCase, main, skip

import src.func.common
from src.func.crawl import init_default_header, log_header_from_default_header

logger = getLogger(__name__)


class TestGetEnvVar(TestCase):
    """입력받은 이름의 환경 변수가 있는 경우와 없는 경우 모두 테스트"""

    @classmethod
    def get_env_var(cls, test_key: str):
        """load_env_var_from_name 함수 주석 참고"""
        return src.func.common.load_env_var_from_name(test_key)

    @classmethod
    def setUpClass(cls):
        """테스트 준비 메서드"""
        environ["test_key"] = "test_val"

    def test_key_found(self):
        test_key: str = "test_key"
        with self.get_env_var(test_key) as (test_val, ke):
            self.assertTrue(test_val == "test_val" and ke is None)

    def test_key_not_found(self):
        test_key: str = "fake_key"
        with self.get_env_var(test_key) as (test_val, ke):
            self.assertTrue(test_val is None and isinstance(ke, KeyError))

    @classmethod
    def tearDownClass(cls):
        """테스트 뒷정리 메서드"""
        environ.pop("test_key")


class AddLoginKey(TestCase):
    def test_add_login_key(self):
        rand_header: dict[str:str] = init_default_header()
        given_key, new_header = log_header_from_default_header(rand_header)
        real_key: str = new_header["Cookie"].split("=")[1]
        self.assertEqual(real_key, given_key)


class TestAssurePathExists(TestCase):
    def test_any_path(self):
        from pathlib import Path
        from src.func.common import mk_path_if_none
        test_path = Path("~/path/to/assure/file.ext").expanduser()
        mk_path_if_none(test_path)
        parents = test_path.parents

        for i, path in enumerate(parents):
            if path == Path(environ["HOME"]):
                child = parents[i - 1]
                try:  # 생성 성공 시 제거
                    rmtree(child)
                except FileNotFoundError as fe:  # 생성 실패
                    from src.func.userio import print_under_new_line
                    logger.info(fe.args, "폴더 생성에 실패했어요.")
                    self.fail()
                logger.info("[알림]", child, "폴더와 내용물을 모두 삭제했어요.")
                break


def join_url(rel_url: str):
    """urljoin 함수 주석 참고"""
    base = GetNovelMainPage.BASE_URL
    abs_url: str = GetNovelMainPage.urljoin(base, rel_url)
    return abs_url


class GetNovelMainPage(TestCase):
    from src.const.const import BASE_URL
    from urllib.parse import urljoin

    def test_valid_novel_code(self, code: str = "247416"):
        from src.func.crawl import fetch_page_from_url

        url: str = join_url(code)

        with fetch_page_from_url(url) as (page, connect_err):
            assert connect_err is None, f"{connect_err = }"

        self.assertIsNotNone(page)

    @skip
    def test_valid_novel_codes(self):
        from src.const.const import ALL_NOVEL_CNT

        for num in range(1, ALL_NOVEL_CNT):
            code = str(num)
            with self.subTest(code=code):
                self.test_valid_novel_code(code)


if __name__ == '__main__':
    main()
