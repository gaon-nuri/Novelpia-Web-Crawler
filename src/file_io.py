# novel_crawler/file_io.py
"""파일 입출력 관련 함수들을 포함합니다."""

from logging import getLogger
from pathlib import Path
from typing import Optional

from .exceptions import WriteFileError
from .models import Novel

logger = getLogger(__name__)


def set_md_str_from_novel(novel: Novel) -> str:
    """
    Novel 객체를 Markdown 문자열로 변환하는 함수

    :param novel: Novel 객체
    :return: Markdown 문자열
    """
    lines = [
        "---",
        "aliases:\n  - (직접 적어 주세요)",
        "유입 경로: (직접 적어 주세요)",
        f"작가명: {novel.writer_nick}",
        f"소설 링크: {novel.url}",
        f"tags:{novel.tags}",
        "\n".join([f"{novel_kind}: True" for novel_kind in novel.kinds]),
        f"{novel.up_status}: True",
        "---\n"
    ]
    if novel.synopsis:
        lines.append(novel.synopsis)
    md_str = "\n".join(lines)
    return md_str


def set_path_from_novel_infos(title: str, any_digit_code: str, base_path: Optional[str] = None) -> Path:
    """소설 정보를 입력받아 Markdown 파일의 저장 경로를 반환하는 함수
    """
    from .func.common import load_env_var_from_name
    md_path = None
    if not base_path:
        with load_env_var_from_name("NOVEL_INFO_MD_DIR") as (env_md_dir, key_err):
            if not key_err:
                md_path = Path(env_md_dir, "소설 정보")
    logger.info("[알림] Markdown 파일은", md_path, "에 쓸게요.")
    safe_title: str = title.replace("/", "|")  # 제목의 "/"로 인한 폴더 생성 방지
    six_digit_code: str = any_digit_code.zfill(6)  # 노벨피아 총 소설 수는 약 30만 개 (6자리)
    file_name: str = f"{six_digit_code} - {safe_title}"

    tmp_path = Path.cwd() / "novel" / "markdown"
    base_path = base_path or md_path or tmp_path
    base_path.mkdir(parents=True, exist_ok=True)
    file_path = base_path / file_name
    return file_path


def create_file_from_string(string: str, path: Path) -> None:
    """
    파일에 문자열을 쓰는 함수

    :param string: 파일에 쓸 문자열
    :param path: 파일 경로
    """
    try:
        with path.open("w", encoding="utf-8") as f:
            f.write(string)
        logger.info(f"[알림] {path} 파일을 썼어요.")
    except IOError as e:
        logger.error(f"[오류] {path} 파일을 열지 못했어요. {e}")
        raise WriteFileError(f"파일 쓰기 오류: {e}")
