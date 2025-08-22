"""소설 정보를 크롤링하는 코드"""
from logging import getLogger

from bs4.element import Tag

from models import Novel

logger = getLogger(__name__)


def get_novel_up_dates(novel_code: str, sort_order: str = "DOWN"):
    """소설의 첫/마지막 연재일을 추출하여 반환하는 함수

    :param novel_code: 소설 번호
    :param sort_order: 정렬 방식
    :return: 첫/마지막 연재일
    """
    from .func.crawl import fetch_ep_li_pg_from_code
    list_page: str = fetch_ep_li_pg_from_code(novel_code, sort_order)

    from .parsers import ep_tag_gen_from_page
    ep_no: int = 1
    ep_tag_gen = ep_tag_gen_from_page(list_page, [ep_no])
    try:
        ep_tag: Tag = next(ep_tag_gen)
    except StopIteration as si:
        logger.error(si)
        raise

    # 회차 게시 일자 추출
    ep_tag_gen = (ep_tag for ep_tag in [ep_tag])
    from .parsers import ep_up_date_gen_from_tags
    up_date_gen = ep_up_date_gen_from_tags(ep_tag_gen)
    if not up_date_gen:
        from .exceptions import NoValueError
        err_msg = "회차 게시 일자 누락"
        nve = NoValueError(err_msg)
        logger.error(nve)
        raise nve
    up_date: str = next(up_date_gen)
    return up_date


def novel_to_md_string(novel: Novel) -> str:
    """추출한 소설 정보를 Markdown 문서로 변환하는 함수
    
    :param novel: 소설 정보가 담긴 Novel 인스턴스
    :return: Markdown 문서
    """
    logger.info(f"[알림] {novel.title}.md 파일에 '유입 경로' 속성을 추가했어요. Obsidian 으로 직접 수정해 주세요.")

    from .const.const import NOVEL_STATS_NAMED_TU as STATUS_TU
    deleted: str = STATUS_TU.deleted
    if novel.up_status == deleted:
        return deleted

    # 소설 유형 추출
    kind_bools: list[str] = [kind + ": True" for kind in novel.kinds]
    kinds: str = "\n".join(kind_bools)

    ################################################################################
    # 소설 서비스 상태 정상, Markdown 작성
    ################################################################################

    # 핵심 정보
    novel_info_lines: list[str] = [
        "aliases:\n  - (직접 적어 주세요)",
        "유입 경로: (직접 적어 주세요)",
        "작가명: " + novel.writer_nick,
        "소설 링크: " + novel.url,
        "tags:" + novel.tags,
        kinds,
        novel.up_status + ": True"
    ]
    from .const.const import BASE_TIME

    # 날짜/시간 값
    dates: list[str] = [
        "완독일: " + BASE_TIME,
        "소설 등록일: " + novel.reg_date,
        "연재 시작일: " + novel.start_date,
        "최근(예정) 연재일: " + novel.last_write_date,
        "소설 갱신일: " + novel.update_dt,
        "원격 갱신일: " + novel.status_dt,
        # "로컬 갱신일: " + novel.got_time,
    ]

    # 각종 통계
    stats: list[str] = [
        f"회차 수: {novel.count_book}",
        f"알람 수: {novel.count_alarm}",
        f"선호 수: {novel.count_like}",
        f"추천 수: {novel.count_good}",
        f"조회 수: {novel.count_view}",
    ]
    novel_info_lines = ["---"] + novel_info_lines + dates + stats
    novel_info_lines.append("---\n")

    # 줄거리 (Markdown Callout - TLDR)
    summary_callout: str = novel.novel_story
    if summary_callout:
        novel_info_lines.append(summary_callout)

    md_string: str = "\n".join(novel_info_lines)

    return md_string
