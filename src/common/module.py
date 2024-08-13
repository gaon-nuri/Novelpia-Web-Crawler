from pathlib import Path

# Windows Chrome User-Agent String
ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'


def get_env_var(key: str) -> str | None:
    """입력받은 이름의 환경 변수를 찾아서 값을 반환하는 함수

    :param key: 이름
    :return: 값
    """
    # 환경 변수 有, 반환
    try:
        from os import environ
        return environ[key]

    # 환경 변수 無, 빈 문자열 반환
    except KeyError as ke:
        from src.common.userIO import print_under_new_line
        print_under_new_line(f"예외 발생: {ke = }")
        print(f"환경 변수 '{key}' 을 찾지 못했어요.")
        return None


def add_login_key(headers: dict[str: str]) -> (str, dict):
    """입력받은 헤더에 로그인 키를 추가해서 반환하는 함수

    :param headers: 로그인 키를 추가할 헤더
    :return: 추가한 로그인 키, 새 헤더
    """
    login_key: str = get_env_var("LOGINKEY")

    # 로그인 키 유무 검사
    assert login_key is not None, "로그인 키 無"

    # 로그인 키 有
    cookie: str = "LOGINKEY=" + login_key
    headers["Cookie"] = cookie

    return login_key, headers


def assure_path_exists(path_to_assure: Path) -> None:
    """파일/폴더의 상위 폴더가 다 있으면 넘어가고 없으면 만드는 함수.

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
    """서버에 소설의 메인 페이지를 요청하고, HTML 응답을 반환하는 함수

    :param url: 요청 URL
    :return: HTML 응답, 접속 실패 시 None
    """
    headers: dict = {'User-Agent': ua}
    from requests.exceptions import ConnectionError

    try:
        from requests import get
        # 소설 메인 페이지의 HTML 문서를 요청
        res = get(url=url, headers=headers)  # res: <Response [200]>

    # 접속 실패
    except ConnectionError as ce:
        err_msg: str = ce.args[0].args[0]
        index: int = err_msg.find("Failed")

        from src.common.userIO import print_under_new_line
        print_under_new_line(err_msg[index:-42])

        return None

    # 성공
    else:
        html: str = res.text
        assert html != "", "빈 HTML"
        return html


def open_file_if_none(file_name: Path) -> None:
    assure_path_exists(file_name)

    # 기존 파일 유무 확인, 있으면 갱신 여부 질문
    is_file: bool = file_name.exists()

    from src.common.userIO import print_under_new_line

    # 기존 파일 有
    if is_file:
        from time import ctime
        mtime: str = ctime(file_name.stat().st_mtime)
        question: str = f"[확인] {mtime} 에 수정된 파일이 있어요. 덮어 쓸까요?"

        # 사용자에게 덮어쓸 것인지 질문
        from src.common.userIO import input_permission
        asked_overwrite, can_overwrite = input_permission(question)

        # 덮어쓸 경우
        if can_overwrite:
            print_under_new_line("[알림]", file_name, "파일에 덮어 썼어요.")  # 기존 파일 有, 덮어쓰기
            print()

        # 기존 파일을 유지, 덮어쓰지 않고 종료
        else:
            exit("[알림] 기존 파일이 있으니 파일 생성은 건너 뛸게요.")

    # 기존 파일 無, 새로 내려받기
    else:
        print_under_new_line("[알림]", file_name, "에 새로 만들었어요.")


if __name__ == "__main__":
    import doctest
    doctest.testmod()
