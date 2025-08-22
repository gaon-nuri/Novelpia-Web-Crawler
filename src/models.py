# novel_crawler/models.py
# Novel 클래스를 정의합니다. 데이터 클래스(dataclasses.dataclass)를 활용하여 클래스 정의를 간결하게 만들 수 있습니다.
from dataclasses import InitVar, dataclass
from datetime import datetime
from logging import getLogger
from typing import Optional

from const.const import BASE_TIME

logger = getLogger(__name__)


def get_datetime_by_min() -> str:
    return datetime.today().isoformat(timespec='minutes')


class UserMeta(type):
    """아무 것도 하지 않는 사용자 메타 클래스."""
    pass


@dataclass(slots=True)
class Page(metaclass=UserMeta):
    """노벨피아 웹 페이지 클래스.

    :var title: 제목
    :var code: 고유 번호
    :var url: URL
    :var ctime: 공개 시각
    :var mtime: 갱신 시각
    :var got_time: 크롤링 시각
    :var count_good: 추천 수
    :var count_view: 조회 수
    """
    got_time = get_datetime_by_min()

    title: Optional[str] = None
    code: Optional[str] = None
    url: Optional[str] = None
    ctime: Optional[str] = None
    mtime: Optional[str] = None
    count_good: Optional[int] = None
    count_view: Optional[int] = None

    page_dic: InitVar[Optional[dict]] = None

    def init_class_attr(self, dic):
        if dic is None:
            return
        for dic_key, dic_val in dic.items():
            attr_name: str = dic_key
            attr_val = dic_val
            if attr_name in self.__dict__:
                self.__setattr__(attr_name, attr_val)

    def __post_init__(self, page_dic):
        self.init_class_attr(page_dic)


@dataclass(slots=True)
class Novel(Page):
    """노벨피아 소설 정보 클래스.

    :var writer_nick: 작가 닉네임
    :var novel_live: 연재 상태 (연재 중, 완결: 0, 연재지연: 1, 연재중단: 2 中 1)
    :var up_status: 연재 상태 (연재 중, 완결, 삭제, 연습작품, 연재지연, 연재중단 中 1)
    :var tags: 해시 태그로 된 Bulleted List
    :var novel_story: 줄거리로 된 Markdown Callout
    :var start_date: 연재 시작일
    :var last_write_date: 최근 (예정) 일반 회차 연재일
    :var count_book: 회차 수
    :var count_pick: 인생픽 순위
    """
    writer_nick: Optional[str] = None
    mem_no: Optional[int] = None
    up_status: Optional[str] = None
    main_genre: Optional[str] = None
    novel_genre: Optional[str] = None
    novel_type: Optional[str] = None
    novel_story: Optional[str] = None
    tags: Optional[str] = None
    start_date: Optional[str] = None
    last_view_date: Optional[str] = None
    last_write_date: Optional[str] = None
    reg_date: Optional[str] = None
    status_dt: Optional[str] = None
    del_date: Optional[str] = None
    complete_date: Optional[str] = None
    update_dt: Optional[str] = None
    alarm: Optional[int] = None
    count_book: Optional[int] = None
    count_pick: Optional[int] = None
    count_like: Optional[int] = None
    count_alarm: Optional[int] = None
    novel_age: Optional[int] = None
    novel_live: Optional[int] = None
    is_del: Optional[bool] = None
    is_complete: Optional[bool] = None
    is_contest: Optional[bool] = None
    is_osmu: Optional[bool] = None
    synopsis: Optional[str] = None
    kinds: Optional[list[str]] = None

    novel_dic: InitVar[Optional[dict]] = None

    def __post_init__(self, page_dic, novel_dic):
        alias_dic: dict = {
            "novel_no": "code",
            "novel_name": "title",
        }
        for dic_key, dic_val in novel_dic.items():
            attr_name: str = dic_key
            attr_val = dic_val
            if attr_name in self.__dict__:
                if attr_name == "novel_type":
                    if attr_val == 1:
                        self.kinds.append("PLUS")
                    elif attr_val == 2:
                        self.kinds.append("자유")
                elif attr_name == "novel_genre":
                    self.novel_genre = attr_val
                elif attr_name == "novel_story":
                    self.novel_story = attr_val
                elif attr_name == "novel_live":
                    up_status_dic: dict[int: str] = {
                        0: "연재 중",
                        1: "연재 지연",
                        2: "연재 중단"
                    }
                    if attr_val in up_status_dic:
                        self.up_status = up_status_dic[attr_val]
                elif attr_name == "is_del" and attr_val == 1:
                    self.up_status = "삭제"
                elif attr_name == "is_complete" and attr_val == 1:
                    self.up_status = "완결"
                else:
                    self.__setattr__(attr_name, attr_val)
                continue
            if attr_name in alias_dic:
                if attr_name == "novel_no":
                    from .const.const import BASE_URL
                    self.code = attr_val
                    from urllib.parse import urljoin
                    rel_url: str = f"/novel/{attr_val}"
                    self.url = urljoin(BASE_URL, rel_url)
                else:
                    alias = alias_dic[attr_name]
                    self.__setattr__(alias, attr_val)


@dataclass(slots=True)
class Ep(Page):
    """노벨피아 회차 정보 클래스.

    :var kinds: 유형 (자유/PLUS, 19금 여부)
    :var num: 화수
    :var letter: 글자 수
    :var comment: 댓글 수
    """
    title: Optional[str] = None
    code: Optional[str] = None
    url: Optional[str] = None
    count_good: Optional[int] = None
    count_view: Optional[int] = None
    num: Optional[int] = None
    letter: Optional[int] = None
    comment: Optional[int] = None
    kinds: Optional[set[str]] = None
    ctime: str = BASE_TIME
    mtime: str = BASE_TIME

    ep_dic: InitVar[Optional[dict]] = None

    def __str__(self):
        from typing import Generator
        from .viewer import init_md_gen_from_ep

        md_gen: Generator = init_md_gen_from_ep(self)
        return "".join(md_gen)

    def __post_init__(self, page_dic, ep_dic):
        self.init_class_attr(ep_dic)
