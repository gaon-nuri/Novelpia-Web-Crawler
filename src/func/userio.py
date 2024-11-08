"""사용자 입/출력 처리용 코드"""
from logging import getLogger

logger = getLogger(__name__)


def print_under_new_line(*args, sep: str = " ", end: str = "\n") -> None:
    """빈 줄을 찍고 입력받은 문자열(들)을 출력하는 함수
    >>> print_under_new_line("Hello, World.")
    <BLANKLINE>
    Hello, World.

    :param end: string appended after the last value, default a newline.
    :param sep: string inserted between values, default a space.
    :param args: 출력할 문자열(들)
    """
    print()
    print(*args, sep=sep, end=end)


def is_valid_format(input_str: str, check_type: type = str) -> bool:
    """문자열의 형식을 검사하는 함수

    :param input_str: 형식을 검사할 문자열
    :param check_type: 문자열에 기대하는 형식
    :return: 형식이 올바르면 참, 그렇지 않으면 거짓
    """
    check_str = input_str.strip()
    if check_type == str:
        return check_str.isascii()
    elif check_type == int:
        return check_str.isnumeric()
    try:
        return isinstance(check_type(check_str), check_type)

    # 해당 형식으로 변환할 수 없는 문자열
    except ValueError as ve:
        ve.add_note("args: " + ', '.join(map(str, ve.args)))
        logger.error("[오류]", ve)
        return False


def ask_consent_from_q(question: str) -> tuple[bool, bool]:
    """사용자의 의사를 묻고 동의 여부를 출력하는 함수

    :param question: 사용자에게 물어볼 질문
    :return: (질문 여부 = 항상 True, 동의 여부 - True/False)
    """
    user_answer: str = get_str_from_input(f"{question} (Y/n)").strip().capitalize()
    if user_answer == "Y":
        return True, True  # 질문 함, 동의 함
    elif user_answer == "N":
        return True, False  # 질문 함, 동의 안 함
    else:
        print_under_new_line("[동의] 동의하면 Y/y, 그러지 않으면 N/n을 눌러 주세요.")


def get_str_from_input(prompt: str = "입력", str_type: type = str) -> str:
    """문자열을 입력받고, 그 형식이 유효하면 반환하는 함수

    :param prompt: 문자열을 입력하라는 메시지
    :param str_type: 입력받을 문자열이 뜻하는 타입
    :return: 유효한 입력 문자열
    """
    # 유효한 형식의 문자열을 입력받을 때까지 반복
    while True:
        print()
        answer_str: str = input(f"{prompt}: ").strip()
        is_valid_string = is_valid_format(answer_str, str_type)

        # 빈 문자열
        if len(answer_str) == 0:
            logger.error("[오류] 입력을 받지 못했어요. 이전 단계로 돌아갈게요.")
            continue

        # 무효한 문자열
        if not is_valid_string:
            logger.error("[오류] 잘못된 입력이에요. 이전 단계로 돌아갈게요.")
            continue
        return answer_str


def get_num_from_input(num_kind: str) -> int:
    """유효한 번호를 얻을 때까지 입력을 받는 함수

    :param num_kind: 번호 유형
    :return: 번호 (자연수)
    """
    while True:
        try:  # 01, 001,... > 1
            num = int(get_str_from_input("[입력] " + num_kind, int))
            _ = str(num)
        except ValueError as ve:
            logger.error(ve, "유효한 숫자를 입력해 주세요.")
            continue
        question: str = f"[확인] {num_kind}가 {num}인가요?"
        is_asked, is_valid_num = ask_consent_from_q(question)
        if is_asked and is_valid_num and num >= 0:
            return num


if __name__ == "__main__":
    from doctest import testmod

    testmod()
