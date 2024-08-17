def print_under_new_line(*msg: object) -> None:
    """빈 줄을 찍고 입력받은 문자열(들)을 출력하는 함수

    >>> print_under_new_line("Hello, World.")
    <BLANKLINE>
    Hello, World.

    :param msg: 출력할 문자열(들)
    """
    print()
    print(*msg)


def chk_str_type(in_str: str, check_type: type = str) -> bool:
    """문자열의 형식을 검사하는 함수

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
            ve.add_note("args: " + ', '.join(map(str, ve.args)))
            print_under_new_line(f"예외 발생: {ve = }")
            return False


def input_permission(question: str, condition: bool = True) -> (bool, bool):
    """사용자의 의사를 묻고 동의 여부를 출력하는 함수

    :param question: 사용자에게 물어볼 질문
    :param condition: 질문 여부를 결정하는 진리값
    :return:(질문 여부 = 항상 True, 동의 여부 - True/False)
    """
    while condition:
        # 질문을 하고 답변을 Y, y, N, n 중 하나로 받음
        user_answer: str = input_str(f"{question} (Y/n)").strip().capitalize()
        if user_answer == "Y":
            return True, True  # 질문 함, 동의 함
        elif user_answer == "N":
            return True, False  # 질문 함, 동의 안 함
        else:
            print_under_new_line("[동의] 동의하면 Y나 y, 그러지 않으면 N이나 n을 눌러 주세요.")


def input_str(prompt: str = "입력", type: type = str) -> str:
    """문자열을 입력받고, 그 형식이 유효하면 반환하는 함수

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


def input_num(num_type: str) -> int:
    """유효한 번호를 얻을 때까지 입력을 받는 함수

    :param num_type: 번호 유형
    :return: 번호 (자연수)
    """
    while True:
        number_string: str = str(int(input_str("[입력] " + num_type, int)))  # 01, 001,... > 1
        is_valid_num: bool = input_permission(f"[확인] {num_type}가 {number_string}인가요?")[1]
        number = int(number_string)

        # 유효한 소설 번호 (자연수)
        if is_valid_num and number >= 0:
            return number
