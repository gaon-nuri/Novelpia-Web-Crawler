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
					print_with_new_line(err_msg[index:-42])

				# 성공
				else:
					self.assertNotEqual(html, "")


class Test(unittest.TestCase):
	def test_add_login_key(self):
		# header: dict[str: str] = {"User-Agent": ua}
		# header_with_login_key = {"User-Agent": ua, "Cookie": "LOGINKEY="}
		# self.assertEqual()
		self.fail()

	def test_open_file_if_none(self):
		self.fail()

	def test_get_ep_list(self):
		self.fail()


if __name__ == '__main__':
	unittest.main()
