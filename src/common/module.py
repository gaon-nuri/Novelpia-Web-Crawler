import os  # os.environ[]
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# Windows Chrome User-Agent String
ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'


def print_under_new_line(*msg: object) -> None:
	print()
	print(*msg)


def get_env_var(key: str) -> str | None:
	"""
	입력받은 이름의 환경 변수를 찾아서 값을 반환하는 함수

	:param key: 이름
	:return: 값
	"""
	# 환경 변수 有, 반환
	try:
		return os.environ[key]

	# 환경 변수 無, 빈 문자열 반환
	except KeyError as ke:
		print_under_new_line(f"예외 발생: {ke = }")
		print(f"환경 변수 '{key}' 을 찾지 못했어요.")
		return None


def add_login_key(headers: dict[str: str]) -> (str, dict):
	"""
	입력받은 헤더에 로그인 키를 추가해서 반환하는 함수

	:param headers: 로그인 키를 추가할 헤더
	:return: 추가한 로그인 키, 새 헤더
	"""
	login_key: str = get_env_var("LOGINKEY")

	# 로그인 키 유무 검사
	assert login_key is not None

	# 로그인 키 有
	cookie: str = "LOGINKEY=" + login_key
	headers["Cookie"] = cookie

	return login_key, headers


def ask_for_num(num_type: str) -> int:
	"""
	유효한 번호를 얻을 때까지 입력을 받는 함수

	:param num_type:
	:return: 번호 (자연수)
	"""
	while True:
		number_string: str = str(int(ask_for_str("[입력] " + num_type, int)))  # 01, 001,... > 1
		is_valid_num: bool = ask_for_permission(f"[확인] {num_type}가 {number_string}인가요?")[1]
		number = int(number_string)

		# 유효한 소설 번호 (자연수)
		if is_valid_num and number >= 0:
			return number


def chk_str_type(in_str: str, check_type: type = str) -> bool:
	"""
	문자열의 형식을 검사하는 함수

	:param in_str: 형식을 검사할 문자열
	:param check_type: 문자열에 기대하는 형식
	:return: 형식이 올바르면 참, 그렇지 않으면 거짓
	"""
	check_str = in_str.strip()

	if check_type == str:
		return check_str.isascii()
	elif check_type == int:
		return check_str.isnumeric()
	else:
		try:
			return isinstance(check_type(check_str), check_type)

		# 해당 형식으로 변환할 수 없는 문자열
		except ValueError as ve:
			print_under_new_line(f"예외 발생: {ve = }")
			return False


def ask_for_str(prompt: str = "입력", type: type = str) -> str:
	"""
	문자열을 입력받고, 그 형식이 유효하면 반환하는 함수

	:param prompt: 문자열을 입력하라는 메시지
	:param type: 입력받을 문자열이 뜻하는 타입
	:return: 유효한 입력 문자열
	"""

	# 유효한 형식의 문자열을 입력받을 때까지 반복
	while True:
		print()
		answer_str: str = input(f"{prompt}: ").strip()
		is_valid_string = chk_str_type(answer_str, type)

		# 빈 문자열
		if len(answer_str) == 0:
			print_under_new_line("[오류] 입력을 받지 못했어요. 이전 단계로 돌아갈게요.")
			continue

		# 무효한 문자열
		if not is_valid_string:
			print_under_new_line("[오류] 잘못된 입력이에요. 이전 단계로 돌아갈게요.")
			continue
		return answer_str


def ask_for_permission(question: str, condition: bool = True) -> (bool, bool):
	"""
	사용자의 의사를 묻고 동의 여부를 출력하는 함수

	:param question: 사용자에게 물어볼 질문
	:param condition: 질문 여부를 결정하는 진리값
	:return:(질문 여부 = 항상 True, 동의 여부 - True/False)
	"""
	while condition:
		# 질문을 하고 답변을 Y, y, N, n 중 하나로 받음
		user_answer: str = ask_for_str(f"{question} (Y/n)").strip().capitalize()
		if user_answer == "Y":
			return True, True  # 질문 함, 동의 함
		elif user_answer == "N":
			return True, False  # 질문 함, 동의 안 함
		else:
			print_under_new_line("[동의] 동의하면 Y나 y, 그러지 않으면 N이나 n을 눌러 주세요.")


def assure_path_exists(path_to_assure: Path) -> None:
	"""
	파일/폴더의 상위 폴더가 다 있으면 넘어가고 없으면 만드는 함수.

	:param path_to_assure: 상위 폴더를 확보할 파일/폴더의 경로
	"""
	parent_paths: [Path] = path_to_assure.parents
	for i, parent_path in enumerate(parent_paths):

		# 상위 폴더 유무 확인
		if parent_path.exists():
			print()

			# 상위 폴더 有, 작업 불필요
			if i == 0:
				print("[알림]", parent_path, "폴더가 이미 있으니 그대로 쓸게요.")

			# 상위 폴더 有, 재귀(?)적으로 하위 폴더 생성
			for j in range(i):
				child_path: Path = parent_paths[range(i)[i - 1 - j]]
				child_path.mkdir()
				print("[알림]", child_path, "폴더를 생성했어요.")
			break


def get_novel_main_page(url: str) -> str | None:
	"""
	서버에 소설의 메인 페이지를 요청하고, HTML 응답을 반환하는 함수

	:param url: 요청 URL
	:return: HTML 응답, 접속 실패 시 None
	"""
	headers: dict = {'User-Agent': ua}

	try:
		# 소설 메인 페이지의 HTML 문서를 요청
		response = requests.get(url=url, headers=headers)  # response: <Response [200]>

	# 접속 실패
	except requests.exceptions.ConnectionError as ce:
		err_msg: str = ce.args[0].args[0]
		index: int = err_msg.find("Failed")
		print_under_new_line(err_msg[index:-42])
		return None

	# 성공
	else:
		html: str = response.text
		assert html != ""
		return html


def open_file_if_none(file_name: Path) -> None:
	assure_path_exists(file_name)

	# 기존 파일 유무 확인, 있으면 갱신 여부 질문
	is_old_file_exist: bool = file_name.exists()

	# 기존 파일 有
	if is_old_file_exist:
		mtime: str = time.ctime(file_name.stat().st_mtime)
		question: str = f"[확인] {mtime} 에 수정된 파일이 있어요. 덮어 쓸까요?"

		# 사용자에게 덮어쓸 것인지 질문
		asked_overwrite_file, can_overwrite_file = ask_for_permission(question)

		# 덮어쓸 경우
		if can_overwrite_file:
			print_under_new_line("[알림]", file_name, "파일에 덮어 썼어요.")  # 기존 파일 有, 덮어쓰기
			print()

		# 기존 파일을 유지, 덮어쓰지 않고 종료
		else:
			exit("[알림] 기존 파일이 있으니 파일 생성은 건너 뛸게요.")

	# 기존 파일 無, 새로 내려받기
	else:
		print_under_new_line("[알림]", file_name, "에 새로 만들었어요.")


def get_ep_list(code: str, sort: str = "DOWN", page: int = 1, use_login_key: bool = False) -> str:
	"""
	서버에 회차 목록을 요청하고, 성공 시 HTML 응답을 반환하는 함수

	:param code: 소설 번호
	:param sort: "DOWN", 첫화부터 / "UP", 최신화부터
	:param page: 요청할 페이지 번호
	:param use_login_key: 로그인 키 사용 여부 (링크 추출용)
	:return: 게시일 순으로 정렬된 회차 목록의 한 페이지 (HTML)
	"""
	# Chrome DevTools 에서 복사한 POST 요청 URL 및 양식 데이터
	req_url: str = "https://novelpia.com/proc/episode_list"
	form_data: dict = {"novel_no": code, "sort": sort, "page": page - 1}  # 1페이지 -> page = 0, ...
	headers: dict[str: str] = {'User-Agent': ua}

	# 로그인 O
	if use_login_key:
		login_key_added, headers_with_login_key = add_login_key(headers)

		# 게시일 순으로 정렬된 회차 목록 요청
		response = requests.post(url=req_url, data=form_data, headers=headers_with_login_key)  # response: <Response [200]>

	# 로그인 X
	else:
		response = requests.post(url=req_url, data=form_data, headers=headers)  # response: <Response [200]>

	html: str = response.text
	return html


def has_prologue(novel_code: str) -> bool:
	"""
	소설의 회차 목록에서 프롤로그의 유무를 반환하는 함수

	:param novel_code:
	:return: 프롤로그 유무
	"""
	fst_page_ep_list_html: str = get_ep_list(novel_code, sort="DOWN", page=1)
	fst_ep_list_soup = BeautifulSoup(fst_page_ep_list_html, "html.parser")

	# 작성된 회차 無
	if fst_ep_list_soup.table is None:
		return False

	fst_page_ep_list = fst_ep_list_soup.select("tr.ep_style5 td.font12")
	fst_ep_info: list[str] = fst_page_ep_list[0].text.split()  # ['무료', '프롤로그', 'EP.0', '0', '0', '0', '24.03.03']

	# 첫 회차 서수 표기 추출
	fst_no_string: str = fst_ep_info[-5]  # 'EP.0'

	# 프롤로그 유무
	has_prologue_ep: bool = (fst_no_string == "EP.0")
	return has_prologue_ep
