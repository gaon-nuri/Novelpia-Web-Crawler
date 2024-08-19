from contextlib import contextmanager
from pathlib import Path

from bs4 import BeautifulSoup
from bs4.element import Tag
from bs4.filter import SoupStrainer

from src.common.module import Page
from src.common.userIO import print_under_new_line


class Novel(Page):
    """노벨피아 소설 정보 클래스.

    :var _writer_name: 작가명
    :var _rank: 인생픽 순위
    :var _tags: 해시 태그로 된 bulleted list
    :var _mtime: 최근 (예정) 연재일
    :var _status: 연재 상태 (연재 중, 완결, 삭제, 연습작품, 연재지연, 연재중단 中 1)
    :var _types: 유형
    :var _ep: 회차 수
    :var _alarm: 일람 수
    :var _prefer: 선호 수
    :var _synopsis: 줄거리로 된 Markdown Callout
    """
    __slots__ = Page.__slots__ + (
                                    "_writer_name",
                                    "_rank",
                                    "_tags",
                                    "_status",
                                    "_types",
                                    "_ep",
                                    "_alarm",
                                    "_prefer",
                                    "_synopsis",
                                  )

    def __init__(self,
                 title: str = '',
                 code: str = '',
                 url: str = '',
                 ctime: str = '0000-00-00',
                 mtime: str = '0000-00-00',
                 got_time: str = '0000-00-00',
                 recommend: int = -1,
                 view: int = -1,
                 writer_name: str = '',
                 rank: str = '',
                 tags: str = "tags:",
                 status: str = '',
                 types: tuple[str] = ('',),
                 ep: int = -1,
                 alarm: int = -1,
                 prefer: int = -1,
                 synopsis: str = ''
                 ):

        super().__init__(title, code, url, ctime, mtime, got_time, recommend, view)

        self._writer_name = writer_name
        self._rank = rank
        self._tags = tags
        self._status = status
        self._types = types
        self._ep = ep
        self._alarm = alarm
        self._prefer = prefer
        self._synopsis = synopsis

    def __str__(self):
        return novel_info_to_md(self)

    @property
    def writer_name(self):
        return self._writer_name

    @writer_name.setter
    def writer_name(self, writer_name: str):
        if writer_name.isprintable():
            self._writer_name = writer_name

    @property
    def rank(self):
        return self._rank

    @rank.setter
    def rank(self, rank: str):
        if rank.isprintable():
            self._rank = rank

    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, tags: list[str]):
        length: int = len(tags)
        if length < 1:
            print_under_new_line("태그를 한 개 이상 입력해 주세요.")
        else:
            self._tags += "\n  - " + "\n  - ".join(tags)
            """
            태그의 각 줄 앞에 '-'를 붙여서 Markdown list (Obsidian 태그) 형식으로 변환
            tags:
              - 판타지
              - 중세
            """

    @property
    def mtime(self):
        return self._mtime

    @mtime.setter
    def mtime(self, up_date_s: str):
        try:
            from datetime import datetime
            datetime.fromisoformat(up_date_s)  # up_date_s: "2024-12-13"
        except ValueError as err:
            err.add_note(*err.args)
            print_under_new_line("예외 발생: " + f"{err = }")
            raise
        else:
            self._mtime = up_date_s

    def __pick_one_from(self, key: str, val: str, vals: frozenset):
        super().pick_one_from(key, val, vals)

    def __add_one_from(self, key: str, val: str, vals: frozenset):
        return super().add_one_from(key, val, vals)

    def __set_signed_int(self, key: str, val: int):
        super().set_signed_int(key, val)

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status: str):
        statuses = frozenset(["완결", "연재지연", "연재중단", "삭제", "연습작품"])
        self.__pick_one_from("_status", status, statuses)

    @property
    def types(self):
        return self._types

    @types.setter
    def types(self, type: str):
        types = frozenset(["성인", "자유", "PLUS", "독점", "챌린지"])
        self.__add_one_from("_types", type, types)

    @property
    def ep(self):
        return self._ep

    @ep.setter
    def ep(self, ep: int):
        self.__set_signed_int("_ep", ep)

    @property
    def alarm(self):
        return self._alarm

    @alarm.setter
    def alarm(self, alarm: int):
        self.__set_signed_int("_alarm", alarm)

    @property
    def prefer(self):
        return self._prefer

    @prefer.setter
    def prefer(self, prefer: int):
        self.__set_signed_int("_prefer", prefer)

    @property
    def synopsis(self):
        return self._synopsis

    @synopsis.setter
    def synopsis(self, synopsis: str):
        """줄거리의 각 줄 앞에 '>'를 붙여서 Markdown Callout 블록으로 변환 후 저장하는 함수

        :param synopsis: 줄거리
        :type synopsis: str
        """
        lines = [line for line in synopsis.splitlines() if line != ""]
        synopsis_lines: list[str] = ["> [!TLDR] 시놉시스"] + lines
        summary_callout = "\n> ".join(synopsis_lines)
        """
        > [!TLDR] 시놉시스
        > 괴담, 저주, 여학생 등….
        > 집착해선 안 될 것들이 내게 집착한다
        """
        self._synopsis = summary_callout


def get_novel_up_dates(code: str, sort: str) -> str:
    """소설의 첫/마지막 연재일을 추출하여 반환하는 함수

    :param code: 소설 번호
    :param sort: 정렬 방식
    :return: 첫/마지막 연재일
    """
    from src.common.episode import get_ep_list, extract_ep_tags, get_ep_up_dates

    ep_li_html: str = get_ep_list(code, sort, 1, False)
    page_li_soup = BeautifulSoup(ep_li_html, "html.parser", parse_only=SoupStrainer("table"))

    ep_tags: set[Tag | None] = extract_ep_tags(page_li_soup, frozenset([1]))
    ep_tag = ep_tags.pop()

    up_dates: list[str] | None = get_ep_up_dates(frozenset([ep_tag]))
    up_date: str = up_dates[0]

    return up_date


@contextmanager
def chk_novel_status(novel: Novel, soup: BeautifulSoup):
    """
    파싱된 소설 메인 페이지에서 추출한 소설 정보를 담은 Dict를 반환하는 함수

    :param novel: 소설 정보가 담긴 Novel 클래스 객체
    :param soup: 파싱된 소설 메인 페이지
    :return: 페이지 제목, 수정된 소설 정보가 담긴 Dict
    """
    # 페이지 제목 추출
    title_tag = soup.select_one("title")
    html_title: str = title_tag.text[22:]  # '노벨피아 - 웹소설로 꿈꾸는 세상! - '의 22자 제거
    """
    - 브라우저 상에 제목표시줄에 페이지 위치나 소설명이 표기됨.
    - 공지 참고: <2021년 01월 13일 - 노벨피아 업데이트 변경사항(https://novelpia.com/notice/20/view_4149/)>
    """
    novel.title = html_title

    # 노벨피아 자체 제목 태그 추출
    novel_title_tag: Tag = soup.select_one("div.epnew-novel-title")

    # 소설 서비스 상태 확인
    try:
        novel_title: str = novel_title_tag.text

    # 서비스 상태 비정상, 소설 정보를 받지 못함
    except AttributeError as attr_err:
        print_under_new_line("예외 발생:", f"{attr_err = }")

        # 오류 메시지 추출
        from src.common.module import extract_alert_msg_w_error, get_postposition
        with extract_alert_msg_w_error(soup) as (alert_msg, err):
            if err:
                print_under_new_line("예외 발생:", f"{err = }")
                print_under_new_line("[오류] 알 수 없는 이유로 소설 정보를 추출하지 못했어요.")

            elif alert_msg.endswith("삭제된 소설 입니다."):
                postposition: str = get_postposition(html_title, "은")
                alert_msg = f"<{html_title}>{postposition} {alert_msg}"

                novel.status = "삭제"

            elif alert_msg.endswith("잘못된 접근입니다."):
                alert_msg = f"<{html_title}>에 대한 {alert_msg}"

                novel.type = "자유"
                novel.status = "연습작품"

            # 오류 메시지 출력
            print_under_new_line("[노벨피아]", alert_msg)

            yield novel, attr_err

    # 서비스 상태 정상
    else:
        # 제목 검사 후 반환
        assert_msg: str = f"[오류] 제목 불일치: 페이지 제목 '{html_title}'과 소설 제목 '{novel_title}'가 달라요."
        assert html_title == novel_title, assert_msg
        novel.title = novel_title

        yield novel, None


def extract_novel_info(html: str) -> Novel:
    """입력받은 소설의 메인 페이지 HTML에서 정보를 추출하여 반환하는 함수

    :param html: 소설 Metadata 를 추출할 HTML
    :return: 소설 제목, 추출한 Metadata 가 담긴 Dict
    """
    novel = Novel()
    # print_under_new_line(novel)

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    # 소설 메인 페이지 URL 추출
    # tag: <meta content="w1" property="og:url"/>
    meta_url_tag = soup.select_one("meta[property='og:url']")
    url: str = meta_url_tag.get("content")

    # URL 저장
    novel.url = url

    # 소설 번호 추출
    from urllib.parse import urlparse
    novel_code: str = urlparse(url).path.split("/")[-1]  # "https://novelpia.com/novel/1" > "1"

    # 제목 추출 및 소설 서비스 상태 확인
    with chk_novel_status(novel, soup) as (novel, err):
        if err:
            return novel

    # 작가명 추출
    author: str = soup.select_one("a.writer-name").string.strip()  # '제울'
    novel.writer_name = author

    print_under_new_line(f"[알림] {author} 작가의 <{novel.title}>은 정상적으로 서비스 중인 소설이에요.")

    # 연재 유형(자유/PLUS), 청불/독점작/챌린지/연중(및 지연)/완결 여부
    flag_list: list[str] = [badge.text for badge in soup.select(".in-badge span")]

    for flag in flag_list:
        if flag in ["19", "자유", "독점", "챌린지"]:
            if flag == "19":
                flag = "성인"
            novel.type = flag

        # elif flag in novel.status.keys():  # ["연재 중", "삭제", "완결", "연재지연", "연재중단"] (flag 는 "연재 중"일 수 X)
        #     novel.status[flag] = True

    # 해시태그 목록 추출 (최소 2개 - 중복 포함 4개)
    tag_set = soup.select("p.writer-tag span.tag")
    """
    - 소설 등록시 최소 2개 이상의 해시태그를 지정해야 등록, 수정이 가능.
    - 모바일/PC 페이지가 같이 들어 있어서 태그가 중복 추출됨.
    - 최소 해시태그 추가 공지: <2021년 01월 13일 - 노벨피아 업데이트 변경사항(https://novelpia.com/notice/20/view_4149/)>
    - 모바일 태그 표기 공지: <2021년 01월 14일 - 노벨피아 업데이트 변경사항(https://novelpia.com/notice/20/view_4783/)>
    """

    # PC, 모바일 중복 해시태그 제거
    indices = int(len(tag_set) / 2)  # 3
    hash_tags: list[str] = [i.string.lstrip("#") for i in tag_set[:indices]]  # ['판타지','현대', '하렘']

    novel.tags = hash_tags

    # 조회, 추천수 추출
    ep_stat_list: list[str] = [i.text.replace(",", "") for i in soup.select(".counter-line-a span")]

    novel.view = int(ep_stat_list[1])  # 83,050,765 > 83050765
    novel.recommend = int(ep_stat_list[3])  # 4,540,540 > 4540540

    # 인생픽 순위 추출
    sole_pick_rank: str = soup.select(".counter-line-b span")[1].text

    # 인생픽 순위 공개 중, 속성 추가
    if sole_pick_rank.endswith("위"):  # 40위
        novel.rank = sole_pick_rank  # 인생픽: 40위 (Markdown 속성 문법)

    # 비공개 상태일 시 넘어가기
    elif sole_pick_rank == "공개전":
        pass

    # 선호/알람/회차 수 추출
    novel_stats: list = [i.string.replace(",", "") for i in soup.select("span.writer-name")]
    novel_stats[2] = novel_stats[2].removesuffix("회차")  # 239회차 > 239
    novel_stats = list(map(int, novel_stats))  # [7694, 879, 239]

    novel_stats = novel_stats[::-1]  # [239, 879, 7694]

    # 회차/선호/알람 수 저장
    novel.ep, novel.alarm, novel.prefer = novel_stats

    # 프롤로그 존재 시 회차 수 1 가산
    # EP.0 ~ EP.10 이면 10회차로 나오니 총 회차 수는 여기에 1을 더해야 함
    from src.common.episode import has_prologue
    if has_prologue(novel_code):
        novel_stats[2] += 1

    # 줄거리 추출 및 저장
    novel.synopsis = soup.select_one("div.synopsis").text

    # 첫/마지막 연재 일자 추출 및 저장
    novel.ctime, novel.mtime = map(get_novel_up_dates, [novel_code] * 2, ["DOWN", "UP"])

    # 크롤링 일자 저장
    from datetime import datetime
    novel.got_time = datetime.today()

    return novel


def novel_info_to_md(novel: Novel) -> str:
    """추출한 소설 정보를 Markdown 문서로 변환하는 함수
    
    :param novel: 소설 정보가 담긴 객체
    :return: Markdown 문서
    """
    lines: list[str] = []

    print_under_new_line(f"[알림] {novel.title}.md 파일에 '유입 경로' 속성을 추가했어요. Obsidian 으로 직접 수정해 주세요.")

    # 삭제된 소설, Markdown 미작성
    if novel.status == "삭제":
        return "삭제"

    # 소설 서비스 상태 정상, Markdown 작성
    lines = ["aliases:\n  - (직접 적어 주세요)"] + lines
    lines.append("유입 경로: (직접 적어 주세요)")

    lines: list[str] = ["작가명: " + novel.writer_name,
                        "소설 링크: " + novel.url, novel.tags,
                        "유입 경로: ",
                        "연재 시작일: " + novel.ctime,
                        "최근(예정) 연재일: " + novel.mtime,
                        "완독일: ",
                        "정보 수집일: " + novel.got_time,
                        "회차 수: " + str(novel.ep),
                        "알람 수: " + str(novel.alarm),
                        "선호 수: " + str(novel.prefer),
                        "추천 수: " + str(novel.recommend),
                        "조회 수: " + str(novel.view)]

    lines = ["---"] + lines
    lines.append("---")

    summary_callout: str = novel.synopsis
    if summary_callout is not None:
        lines.append(summary_callout)

    md_string: str = "\n".join(lines)

    return md_string


def novel_info_main() -> None:
    """
    모듈 대신 스크립트로 실행할 때 호출되는 함수.
    """
    base_url: str = "https://novelpia.com/novel/"
    novel_dir = Path(Path.cwd(), "novel")

    # 환경 변수의 Markdown 폴더 경로 사용
    from src.common.module import get_env_var_w_error
    with get_env_var_w_error("MARKDOWN_DIR") as (env_md_dir, key_err):
        if key_err:
            md_dir = Path(novel_dir, "markdown")
        else:
            md_dir: Path = Path(env_md_dir)

    print_under_new_line("[알림] Markdown 파일은", md_dir, "에 쓸게요.")

    # 소설 번호 입력 받기
    from src.common.userIO import input_num
    code: str = str(input_num("소설 번호"))

    from urllib.parse import urljoin
    url: str = urljoin(base_url, code)  # https://novelpia.com/novel/1

    # 소설 페이지 응답 받기
    from src.common.module import get_novel_main_w_error
    with get_novel_main_w_error(url) as (html, err):
        if err is not None:
            print_under_new_line(f"{err = }")

    # 소설 정보 추출하기
    novel: Novel = extract_novel_info(html)

    # 기본 경로: ../novel/markdown/제목.md
    md_file_name = Path(md_dir, novel.title).with_suffix(".md")

    # Markdown 형식으로 변환하기
    md_file_content = novel_info_to_md(novel)

    # Markdown 폴더 확보 및 새 파일 열기
    from src.common.module import opened_x_error
    with opened_x_error(md_file_name, "x") as (f, err):
        assert f is not None
        # print(md_file_content, file=f)
        f.write(md_file_content)
        print_under_new_line("[알림]", md_file_name, "파일을 작성했어요.")


if __name__ == "__main__":
    novel_info_main()
