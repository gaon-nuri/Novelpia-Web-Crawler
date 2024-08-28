"""공용 상수 모음

"""
from collections import namedtuple

# Windows Chrome User-Agent String
UA: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
BASIC_HEADERS: dict = {"User-Agent": UA}

# bs4 용 파이썬 내장 파서
PARSER: str = "html.parser"

HOST: str = "https://novelpia.com"

DEFAULT_TIME: str = "0000-00-00"

################################################################################
# src.common.module
################################################################################
LOGIN_KEY_NAME: str = "LOGINKEY"

POSTPOSITIONS_NAMED_TUPLE_CLS = namedtuple("KoPostpositions", "vowel consonant")
POSTPOSITIONS_NAMED_TUPLE = POSTPOSITIONS_NAMED_TUPLE_CLS(("가", "를", "는", "야"), ("이", "을", "은", "아"))

################################################################################
# src.novel_info
################################################################################
HTML_TITLE_PREFIX: str = '노벨피아 - 웹소설로 꿈꾸는 세상! - '

NOVEL_TYPES_NAMED_TUPLE_CLS = namedtuple("NovelTypes", "adult free exclusive challenge")
NOVEL_STATUSES_NAMED_TUPLE_CLS = namedtuple("NovelStatuses", "ongoing deleted draft complete delayed hiatus")

NOVEL_TYPES_NAMED_TUPLE = NOVEL_TYPES_NAMED_TUPLE_CLS("19", "자유", "독점", "챌린지")
NOVEL_STATUSES_NAMED_TUPLE = NOVEL_STATUSES_NAMED_TUPLE_CLS("연재 중", "삭제", "연습작품", "완결", "연재지연", "연재중단")

RANK_PLACE_HOLDER: str = "공개전"

################################################################################
# src.common.episode
################################################################################
EP_TYPES_NAMED_TUPLE_CLS = namedtuple("EpTypes", "free plus adult")
EP_TYPES_NAMED_TUPLE = EP_TYPES_NAMED_TUPLE_CLS("자유", "PLUS", "성인")

################################################################################
# src.myTest
################################################################################
ALL_NOVEL_COUNT: int = 299487  # 노벨피아 소설 수 (2024-08-23 21:36 기준)
