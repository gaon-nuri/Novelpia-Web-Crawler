"""공통 함수들"""
from logging import getLogger
from pathlib import Path
from typing import Optional

logger = getLogger(__name__)


def mk_path_if_none(path_to_assure: Path) -> None:
    """파일/폴더의 상위 폴더가 다 있으면 넘어가고 없으면 만드는 함수.

    :param path_to_assure: 상위 폴더를 확보할 파일/폴더의 경로
    """
    parent_paths: [Path] = path_to_assure.parents
    for i, parent_path in enumerate(parent_paths):
        if parent_path.exists():
            print()

            # 상위 폴더 有, 작업 불필요
            if i == 0:
                print("[알림]", parent_path, "폴더가 이미 있으니 그대로 쓸게요.")

            # 상위 폴더 有, 재귀적으로 하위 폴더 생성
            for j in range(i):
                child_path: Path = parent_paths[range(i)[i - 1 - j]]
                child_path.mkdir()
                print("[알림]", child_path, "폴더를 생성했어요.")
            break


def parse_err_msg_from_err(err_group: ExceptionGroup) -> str:
    """예외에서 메시지를 추출하는 함수

    :param err_group: 예외
    :return: 예외 메시지
    """
    from requests.exceptions import ConnectionError
    from urllib3.exceptions import MaxRetryError

    ce: ConnectionError = err_group.exceptions[0]
    mre: MaxRetryError = ce.args[0]
    err_msg: str = mre.reason.args[0]

    start_index: int = err_msg.find("Failed")
    end_index: int = err_msg.find("Errno")
    err_msg: str = err_msg[start_index: end_index - 3]

    return err_msg


def suffix_from_words(kr_word: str, suffix: str) -> str:
    """입력받은 한글 단어의 종성에 맞는 조사의 이형태를 반환하는 함수

    :param kr_word: 한글 문자열
    :param suffix: 원래 조사
    :return: 모음 - True / 모음 외 나머지 - False
    """
    ends_with_vowel: bool = ((ord(kr_word[-1]) - 0xAC00) % 28 == 0)
    """
    한글 글자 인덱스 = (초성 인덱스 * 21 + 중성 인덱스) * 28 + 종성 인덱스 + 0xAC00\n
    참고: https://en.wikipedia.org/wiki/Korean_language_and_computers#Hangul_in_Unicode
    """
    from const.const import SUFFIX_NAMED_TU
    for v, c in zip(*SUFFIX_NAMED_TU):
        if suffix in (v, c):
            if ends_with_vowel:
                return v
            return c


def load_mem_no_from_env(log_kind) -> int:
    env_var_name: Optional[str] = None
    sub_mem: int = 1
    plus_mem: int = 2
    if log_kind == sub_mem:
        env_var_name: str = "MEM_NO_SUB"
    elif log_kind == plus_mem:
        env_var_name: str = "MEM_NO_PLUS"
    assert env_var_name
    mem_code = load_env_var_from_name(env_var_name)
    mem_no = int(mem_code)
    return mem_no


def load_env_var_from_name(var_name: str) -> str:
    """입력받은 이름의 환경 변수를 찾고 값과 오류를 반환하는 제너레이터 함수

    :param var_name: 환경 변수의 이름
    :return: 환경 변수의 값과 오류 (각각 없으면 None)
    """
    try:
        from dotenv import dotenv_values
        config = dotenv_values()
        env_var: str = config[var_name]
        return env_var
    except KeyError as ke:
        ke.add_note(f"환경 변수 '{var_name}' 을 찾지 못했어요.")
        logger.error(ke)
        raise ke


def load_dic_from_json(res_json: str):
    """입력받은 JSON을 dict로 가져오고 해당 dict와 오류 내역을 반환하는 함수

    :param res_json: 응답 JSON
    """
    from json import JSONDecodeError
    from json import loads as load_obj_from_json
    try:
        res_dic: dict = load_obj_from_json(res_json)
        dic, err = res_dic, None
        return dic, err
    except JSONDecodeError as je:
        je.add_note("응답 JSON: " + res_json)
        logger.error(je)
        raise


def mk_file_from_path(path: Path, mode: str = "xt", enc: str = "utf-8", can_skip: bool = False,
                      can_rewrite: bool = False):
    """입력받은 대로 파일을 열고 파일을 반환하는 함수

    :param path: 파일 경로
    :param mode: 파일 모드 (읽기, 쓰기, 붙이기, ..)
    :param enc: 파일의 인코딩 (기본 UTF-8)
    :param can_skip: 동명의 파일 존재 시 건너뛸 지 여부
    :param can_rewrite: 덮어 쓰기 여부
    """
    assert mode.find("b") == -1
    mk_path_if_none(path)
    try:
        with open(path, mode, encoding='utf-8') as f:
            logger.info("[알림]", path, "파일을 열었어요.")
        logger.info("[알림]", path, "파일을 닫았어요.")
        return f
    except FileExistsError:
        file_exists_err_handler(enc, path, can_rewrite, can_skip)
    except OSError as os_err:
        err = os_err
        logger.error(err)
        raise err
    except Exception as ue:
        err = ue
        logger.error(err)
        raise err


def file_exists_err_handler(encoding, path, force_rewrite, skip):
    mtime_secs: float = path.stat().st_mtime
    from time import ctime as time_str_from_time_secs
    mtime_str: str = time_str_from_time_secs(mtime_secs)
    asked_rewrite, do_rewrite = False, False

    if not (skip or force_rewrite):
        q_str: str = "[확인] " + mtime_str + "에 수정된 파일이 있어요. 덮어 쓸까요?"
        from ..func.userio import ask_consent_from_q
        asked_rewrite, do_rewrite = ask_consent_from_q(q_str)
    if force_rewrite or (asked_rewrite and do_rewrite):
        logger.info("[알림]", path, "파일에 덮어 쓸게요.")
        with mk_file_from_path(path, "wt", encoding, True, True) as (f, wrt_f_err):
            file, err = f, wrt_f_err
    else:
        err_msg = "이미 동명의 파일이 있어요."
        fee = FileExistsError(err_msg)
        logger.error(fee)
        raise fee
    if err:
        logger.error(err)
        raise err
