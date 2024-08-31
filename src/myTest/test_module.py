"""공통 함수 테스트"""
import shutil
from os import environ
from unittest import TestCase, main, skip


@skip
class TestDescriptorDeco(TestCase):
    def test_descriptor_deco(self):
        from src.func.common import Descriptor

        class A:
            @Descriptor
            def sum(self, a1, a2, a3):
                return a1 + a2 + a3

        print(A.__dict__)
        a = A()
        print(a.sum(1, 2, 3))

        self.assertTrue(True)


@skip
class TestNonDataDescriptor(TestCase):
    def test_descriptor_nd(self):
        from src.func.common import DescriptorND

        class Nondata:
            mul = DescriptorND(lambda x, y: x * y)

        nd = Nondata()
        print(nd.__dict__)
        print(nd.mul)
        print(nd.mul(2, 2))


@skip
class TestDataDescriptor(TestCase):
    def test_i_mutable_attribute(self):
        from src.func.common import MutableAttribute, ImmutableAttribute

        class Circle:
            pi = 3.1415
            radius = MutableAttribute(10)
            diameter = ImmutableAttribute(lambda x: x.radius * 2)

            @ImmutableAttribute
            def circumference(self):
                return self.pi * self.radius * 2

            @ImmutableAttribute
            def area(self):
                return self.pi * self.radius ** 2

        c = Circle()
        print(c.radius, c.diameter)
        print(c.circumference, c.area)

        c.radius = 100
        print(c.radius, c.area)

        self.assertTrue(True)


class TestGetEnvVar(TestCase):
    """입력받은 이름의 환경 변수가 있는 경우와 없는 경우 모두 테스트"""
    from src.func.common import get_env_var_w_error

    @classmethod
    def get_env_var(cls, test_key: str):
        """get_env_var_w_error 함수 주석 참고"""
        return cls.get_env_var_w_error(test_key)

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
        from src.const.const import BASIC_HEADERS
        from src.func.common import add_login_key

        given_key, new_header = add_login_key(BASIC_HEADERS)
        real_key: str = new_header["Cookie"].split("=")[1]

        self.assertEqual(real_key, given_key)


class TestAssurePathExists(TestCase):
    def test_any_path(self):
        from pathlib import Path
        from src.func.common import assure_path_exists

        test_path = Path("~/path/to/assure/file.ext").expanduser()
        assure_path_exists(test_path)
        parents = test_path.parents

        for i, path in enumerate(parents):
            if path == Path(environ["HOME"]):
                child = parents[i - 1]
                try:  # 생성 성공 시 제거
                    shutil.rmtree(child)
                except FileNotFoundError as fe:  # 생성 실패
                    from src.func.userIO import print_under_new_line

                    print_under_new_line(fe.args, "폴더 생성에 실패했어요.")
                    self.fail()
                else:
                    print("[알림]", child, "폴더와 내용물을 모두 삭제했어요.")
                    break


def join_url(code: str):
    """urljoin 함수 주석 참고"""
    base = GetNovelMainPage.HOST
    return GetNovelMainPage.urljoin(base, code)


class GetNovelMainPage(TestCase):
    from src.const.const import HOST
    from urllib.parse import urljoin

    def test_valid_novel_code(self):
        from src.func.common import get_novel_main_w_error

        code: str = "247416"
        url: str = join_url(code)

        with get_novel_main_w_error(url) as (html, connect_err):
            assert connect_err is None, f"{connect_err = }"

        self.assertIsNotNone(html)

    @skip
    def test_valid_novel_codes(self):
        from src.const.const import ALL_NOVEL_COUNT
        from src.func.common import get_novel_main_w_error

        for num in range(1, ALL_NOVEL_COUNT):
            code = str(num)
            with self.subTest(code=code):
                url: str = join_url(code)
                with get_novel_main_w_error(url) as (html, connect_err):
                    assert connect_err is None, f"{connect_err = }"

                self.assertIsNotNone(html)


if __name__ == '__main__':
    main()
