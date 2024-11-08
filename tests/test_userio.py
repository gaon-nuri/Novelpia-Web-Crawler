"""사용자 입출력 기능 테스트"""


class TestChkStrType:
    def test_str_is_num(self):
        num: str = "1"
        num_in_tab: str = "\t12\t"

        alnum: str = "a1"
        tab_in_num: str = "1\t2"

        from src.func.userio import is_valid_format

        is_num: bool = is_valid_format(num, int) and is_valid_format(num_in_tab, int)
        is_not_num: bool = is_valid_format(alnum, int) or is_valid_format(tab_in_num, int)

        assert is_num and not is_not_num
