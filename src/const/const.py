# novel_crawler/const/const.py
"""공용 상수 모음"""
from collections import namedtuple

################################################################################
# 공통
################################################################################
PARSER: str = "page.parser"  # bs4 용 파이썬 내장 파서
BASE_URL: str = "https://novelpia.com"
BASE_TIME: str = "0000-00-00T00:00"

################################################################################
# src.func.common
################################################################################
LOG_KEY_NAME: str = "LOGINKEY"

SUFFIX_NAMED_TU_CLS = namedtuple("KoSuffixes", "vowel cons")
SUFFIX_NAMED_TU = SUFFIX_NAMED_TU_CLS(("가", "를", "는", "야"), ("이", "을", "은", "아"))

################################################################################
# src.func.episode
################################################################################
EP_TYPES_NAMED_TU_CLS = namedtuple("EpTypes", "free plus adult")
EP_TYPES_NAMED_TU = EP_TYPES_NAMED_TU_CLS("자유", "PLUS", "성인")

################################################################################
# src.tests.*
################################################################################
ALL_NOVEL_CNT: int = 302663  # 노벨피아 소설 수 (2024-09-08 14:17 기준)

################################################################################
# src.novel_info
################################################################################
PAGE_TITLE_PREFIX: str = '노벨피아 - 웹소설로 꿈꾸는 세상! - '

NOVEL_TYPES_NAMED_TU_CLS = namedtuple("NovelTypes", "adult free exclusive challenge")
NOVEL_STATS_NAMED_TU_CLS = namedtuple("NovelStats", "ongoing deleted draft complete delayed hiatus")

NOVEL_TYPES_NAMED_TU = NOVEL_TYPES_NAMED_TU_CLS("19", "자유", "독점", "챌린지")
NOVEL_STATS_NAMED_TU = NOVEL_STATS_NAMED_TU_CLS("연재 중", "삭제", "연습작품", "완결", "연재 지연", "연재 중단")

RANK_PLACE_HOLDER: str = "공개전"

################################################################################
# src.viewer
################################################################################
EP_CNT_IN_PAGE: int = 20  # 페이지 당 20회차씩
