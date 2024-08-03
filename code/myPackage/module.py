from pathlib import Path

import requests

# Windows Chrome User-Agent String
ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'


def ask_for_number(number_type: str) -> int:
    """
    유효한 번호를 얻을 때까지 입력을 받는 함수

    :param number_type:
    :return: 번호 (자연수)
    """
    while True:
        number_string: str = str(int(ask_for_string("[입력] " + number_type, int)))  # 01, 001,... > 1
        is_valid_num: bool = ask_for_permission(f"[확인] {number_type}가 {number_string}인가요?")[1]
        number: int = int(number_string)

        # 유효한 소설 번호 (자연수)
        if is_valid_num and number >= 0:
            return number


def ask_for_string(prompt: str = "입력", type: type = str) -> str:
    """
    문자열을 입력받고, 그 형식이 유효하면 반환하는 함수

    :param prompt: 문자열을 입력하라는 메시지
    :param type: 입력받을 문자열이 뜻하는 타입
    :return: 유효한 입력 문자열
    """

    def check_string_validity(check_str: str, check_type: type = str) -> bool:
        """
        문자열의 형식을 검사하는 함수

        :param check_str: 형식을 검사할 문자열
        :param check_type: 문자열에 기대하는 형식
        :return: 형식이 올바르면 참, 그렇지 않으면 거짓
        """
        try:
            return isinstance(check_type(check_str), check_type)

        # 해당 형식으로 변환할 수 없는 문자열
        except ValueError as ve:
            print(f"예외 발생: {ve}")
            return False

    # 유효한 형식의 문자열을 입력받을 때까지 반복
    while True:
        print()
        answer_str: str = input(f"{prompt}: ").strip()
        is_valid_string = check_string_validity(answer_str, type)

        # 빈 문자열
        if len(answer_str) == 0:
            print("[오류] 입력을 받지 못했어요. 이전 단계로 돌아갈게요.")
            continue

        # 무효한 문자열
        if not is_valid_string:
            print()
            print("[오류] 잘못된 입력이에요. 이전 단계로 돌아갈게요.")
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
        user_answer: str = ask_for_string(f"{question} (Y/n)").strip().capitalize()
        if user_answer == "Y":
            return True, True  # 질문 함, 동의 함
        elif user_answer == "N":
            return True, False  # 질문 함, 동의 안 함
        else:
            print("[동의] 동의하면 Y나 y, 그러지 않으면 N이나 n을 눌러 주세요.")


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


def request_novel_main_page(url: str) -> str:
    """
    서버에 소설의 Main Webpage 를 요청하고, 성공 시 HTML 응답을 반환하는 함수

    :param url: 소설 Main Webpage URL
    :return: 소설 Main Webpage HTML
    """
    headers: dict = {'User-Agent': ua}

    # 소설 Main Webpage 의 HTML 문서를 요청
    response = requests.get(url=url, headers=headers)  # response: <Response [200]>
    html: str = response.text
    return html


def request_novel_ep_list(code: str, sort: str = "DOWN", page: int = 0) -> str:
    """
    서버에 회차 목록을 요청하고, 성공 시 HTML 응답을 반환하는 함수

    :param code: 소설 번호
    :param sort: "DOWN", 첫화부터 / "UP", 최신화부터
    :param page: 요청할 페이지 번호
    :return: 게시일 순으로 정렬된 회차 목록의 한 페이지 (HTML)
    """
    # Chrome DevTools 에서 복사한 POST 요청 URL 및 양식 데이터
    req_url: str = "https://novelpia.com/proc/episode_list"
    form_data: dict = {"novel_no": code, "sort": sort, "page": page}
    headers: dict = {'User-Agent': ua}

    # 게시일 순으로 정렬된 회차 목록 요청
    response = requests.post(url=req_url, data=form_data, headers=headers)  # response: <Response [200]>
    html = response.text

    return html
