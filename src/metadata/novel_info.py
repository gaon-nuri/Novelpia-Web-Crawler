from src.common.module import *


def get_postposition(kr_word: str, postposition: str) -> str:
    """입력받은 한글 단어의 종성에 맞는 조사의 이형태를 반환하는 함수

    :param kr_word: 한글 문자열
    :param postposition: 원래 조사
    :return: 모음 - True / 모음 외 나머지 - False
    """

    # (초성 인덱스 * 21 + 중성 인덱스) * 28 + 종성 인덱스 + 0xAC00
    # 참고: https://en.wikipedia.org/wiki/Korean_language_and_computers#Hangul_in_Unicode

    v_post: tuple = ("가", "를", "는", "야")
    c_post: tuple = ("이", "을", "은", "아")
    # post_dic = dict(zip(vowel_post, consonant_post))

    ends_with_vowel: bool = ((ord(kr_word[-1]) - 0xAC00) % 28 == 0)

    for v, c in zip(v_post, c_post):
        if postposition == v:
            if not ends_with_vowel:
                return c
            return v
        elif postposition == c:
            if ends_with_vowel:
                return v
            else:
                return c


def extract_alert_msg(soup, title: str) -> str | None:
    """소설 메인 페이지에서 알림 창의 오류 메시지를 추출하는 함수

    :param soup: BeautifulSoup 객체
    :param title: 소설 제목
    :return: 오류 메시지
    """
    try:
        msg_tag = soup.select_one("#alert_modal .mg-b-5")

    # 알림 창이 나오지 않음
    except AttributeError as ae:
        print_under_new_line(f"예외 발생: {ae = }")

        return None

    # 알림 메시지 추출
    msg: str = msg_tag.text
    """
    0: 잘못된 소설 번호 입니다. (제목, 줄거리 無)
    2: 삭제된 소설 입니다. (제목 有, 줄거리 無)
    200000: 잘못된 접근입니다. (제목 有, 줄거리 無)
    - 연습등록작품은 작가만 열람이 가능
    - 공지 참고: <2021년 01월 13일 - 노벨피아 업데이트 변경사항(https://novelpia.com/notice/20/view_4149/)>
    """
    if msg == "잘못된 소설 번호 입니다.":
        pass
    elif msg == "잘못된 접근입니다.":
        msg = f"<{title}>에 대한 {msg}"
    elif msg == "삭제된 소설 입니다.":
        postposition: str = get_postposition(title, "은")
        msg = f"<{title}>{postposition} {msg}"

    return msg


def get_ep_up_date(novel_code: str, sort: str = "DOWN") -> str | None:
    """소설의 회차 목록에서 첫/마지막 회차 게시일을 추출하여 반환하는 함수

    :param novel_code: 소설 번호
    :param sort: "DOWN", 첫화부터 / "UP", 최신화부터
    :return: 첫/마지막 회차 게시일. 작성된 회차가 없으면 None
    """
    list_html = get_ep_list(novel_code, sort, 1)
    from bs4 import BeautifulSoup
    list_soup = BeautifulSoup(list_html, "html.parser")

    # 회차 목록 표 추출
    list_table = list_soup.table

    # 작성된 회차 無
    if list_table is None:
        return None

    # 작성된 회차 有
    ep_list = list_table.select_one("tr.ep_style5")

    # ['무료', '프롤로그', 'EP.0', '0', '0', '2', '21.01.18']
    ep_info: list[str] = ep_list.text.split()
    up_date: str = ep_info[-1]  # 21.01.18 또는 '19시간전'

    # 24시간 이내에 게시된 경우 당일 날짜로 간주
    if up_date.endswith("전"):  # upload_date: '19시간전'
        from datetime import date
        up_date = str(date.today())  # 2024-07-25
    else:
        up_date = ("20" + up_date).replace(".", "-")  # 21.01.18 > 2021-01-18

    return up_date


def extract_novel_info(main_page_html: str) -> (str, dict):
    """입력받은 소설의 메인 페이지 HTML에서 정보를 추출하여 반환하는 함수

    :param main_page_html: 소설 Metadata 를 추출할 HTML
    :return: 소설 제목, 추출한 Metadata 가 담긴 Dict
    """
    info_dic: dict[str] = {}.fromkeys(["작가명", "소설 링크", "인생픽 순위", "tags", "줄거리", "공개 일자", "갱신 일자", "완독 일자"])
    info_dic["연재 상태"]: dict = {}.fromkeys(["완결", "삭제", "연재지연", "연재중단"], False)
    info_dic["연재 유형"]: dict = {}.fromkeys(["19", "자유", "독점", "챌린지"], False)
    info_dic["독자 비례 지표"]: dict = {}.fromkeys(["회차 수", "알람 수", "선호 수"])
    info_dic["회차 수 비례 지표"]: dict = {}.fromkeys(["추천 수", "조회 수"])
    info_dic["연재 상태"]["연재 중"] = True

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(main_page_html, "html.parser")

    # 제목 추출
    html_title: str = soup.title.text[22:]  # '노벨피아 - 웹소설로 꿈꾸는 세상! - '의 22자 제거
    """
    - 브라우저 상에 제목표시줄에 페이지 위치나 소설명이 표기됨.
    - 공지 참고: <2021년 01월 13일 - 노벨피아 업데이트 변경사항(https://novelpia.com/notice/20/view_4149/)>
    """

    # 소설 메인 페이지 URL 추출
    # tag: <meta content="https://novelpia.com/novel/1" property="og:url"/>
    meta_url_tag = soup.select_one("meta[property='og:url']")
    novel_page_url: str = meta_url_tag.get("content")
    info_dic["소설 링크"] = novel_page_url

    # 소설 번호 추출
    from urllib.parse import urlparse
    novel_code: str = urlparse(novel_page_url).path.split("/")[-1]  # "https://novelpia.com/novel/1" > "1"

    # 소설 서비스 상태 확인
    from bs4.element import Tag
    novel_title_tag: Tag = soup.select_one("div.epnew-novel-title")

    # 서비스 상태 비정상, 소설 정보를 받지 못함
    if novel_title_tag is None:

        # 오류 메시지 추출
        alert_msg: str = extract_alert_msg(soup, html_title)

        if alert_msg.endswith("삭제된 소설 입니다."):
            info_dic["연재 상태"]["삭제"] = True

        # 오류 메시지 출력
        exit_code = f"[노벨피아] {alert_msg}"
        print_under_new_line(exit_code)

        return html_title, info_dic

    # 서비스 상태 정상, 제목 재추출 후 비교
    novel_title: str = novel_title_tag.text
    assert html_title == novel_title

    # 작가명 추출
    author: str = soup.select_one("a.writer-name").string.strip()  # '제울'
    info_dic["작가명"] = author

    print_under_new_line(f"[알림] {author} 작가의 <{html_title}>은 정상적으로 서비스 중인 소설이에요.")

    # 연재 유형(자유/PLUS), 청불/독점작/챌린지/연중(및 지연)/완결 여부
    flag_list: list[str] = [badge.text for badge in soup.select(".in-badge span")]

    for flag in flag_list:
        if flag in info_dic["연재 유형"].keys():  # ["19", "자유", "독점", "챌린지"]
            info_dic["연재 유형"][flag] = True

        elif flag in info_dic["연재 상태"].keys():  # ["연재 중", "삭제", "완결", "연재지연", "연재중단"]
            info_dic["연재 상태"][flag] = True

            if flag == "연재지연" or "연재중단":
                info_dic["연재 상태"]["연재 중"] = False

    # 해시태그 목록 추출 (최소 2개 - 중복 포함 4개)
    tag_set = soup.select("p.writer-tag span.tag")

    """
    - 소설 등록시 최소 2개 이상의 해시태그를 지정해야 등록, 수정이 가능.
    - 모바일/PC 페이지가 같이 들어 있어서 태그가 중복 추출됨.
    - 최소 해시태그 추가 공지: <2021년 01월 13일 - 노벨피아 업데이트 변경사항(https://novelpia.com/notice/20/view_4149/)>
    - 모바일 태그 표기 공지: <2021년 01월 14일 - 노벨피아 업데이트 변경사항(https://novelpia.com/notice/20/view_4783/)>
    """

    # PC, 모바일 중복 해시태그 제거
    indices: int = int(len(tag_set) / 2)  # 3
    tags: list[str] = [i.string.lstrip("#") for i in tag_set[:indices]]  # ['판타지','현대', '하렘']

    info_dic["tags"]: str = "".join([f"\n  - {tag.lstrip('#')}" for tag in tags])
    """
    태그의 각 줄 앞에 '-'를 붙여서 Markdown list (Obsidian 태그) 형식으로 변환
    tags:
      - 판타지
      - 중세
    """

    # 조회, 추천수 추출
    ep_stat_list: list[str] = [i.string.replace(",", "") for i in soup.select("div.counter-line-a span")]
    info_dic["회차 수 비례 지표"]["조회 수"] = int(ep_stat_list[1])  # 83,050,765 > 83050765
    info_dic["회차 수 비례 지표"]["추천 수"] = int(ep_stat_list[3])  # 4,540,540 > 4540540

    # 인생픽 순위 추출
    sole_pick_rank: str = soup.select(".counter-line-b span")[1].text

    # 인생픽 순위 공개 중, 속성 추가
    if sole_pick_rank[-1] == "위":  # 40위
        info_dic["인생픽 순위"] = sole_pick_rank  # 인생픽: 40위 (Markdown 속성 문법)

    # 비공개 상태일 시 넘어가기
    elif sole_pick_rank == "공개전":
        pass

    # 회차, 알람, 선호수 추출
    novel_stats: list = [i.string.replace(",", "") for i in soup.select("span.writer-name")]
    novel_stats[2] = novel_stats[2].removesuffix("회차")  # 2538회차 > 2538
    novel_stats = list(map(int, novel_stats))[::-1]

    info_dic["독자 비례 지표"] = dict(zip(info_dic["독자 비례 지표"].keys(), novel_stats))

    # 프롤로그 존재 시 회차 수 1 가산
    # EP.0 ~ EP.10 이면 10회차로 나오니 총 회차 수는 여기에 1을 더해야 함
    if has_prologue(novel_code):
        info_dic["독자 비례 지표"]["회차 수"] += 1

    # 줄거리 추출
    synopsis: str = soup.select_one(".synopsis").text

    # 줄거리의 각 줄 앞에 '>'를 붙여서 Markdown Callout 블록으로 변환
    synopsis_lines: list[str] = ["> [!TLDR] 시놉시스"]
    synopsis_lines += ["> " + line for line in synopsis.splitlines()]
    summary_callout = "\n".join(synopsis_lines)
    """
    > [!TLDR] 시놉시스
    > 괴담, 저주, 여학생 등….
    > 집착해선 안 될 것들이 내게 집착한다
    """

    info_dic["줄거리"] = summary_callout

    # 작성된 회차 有, 공개 일자 추출
    if info_dic["독자 비례 지표"]["회차 수"] != 0:
        info_dic["공개 일자"] = get_ep_up_date(novel_code, "DOWN")
        info_dic["갱신 일자"] = get_ep_up_date(novel_code, "UP")

    return novel_title, info_dic


def convert_to_md(title: str, info_dic: dict) -> str:
    """추출한 소설 제목과 정보를 받아 Markdown 형식으로 변환하는 함수

    :param title: 소설 제목
    :param info_dic: 소설 정보
    """
    lines: list[str] = []

    print_under_new_line("[알림]", title + ".md 파일에 '유입 경로' 속성을 추가했어요. Obsidian 으로 직접 수정해 주세요.")

    # 삭제된 소설
    if info_dic["연재 상태"]["삭제"]:
        lines = ["---"] + lines + ["---"]
        md_string: str = "\n".join(lines)
        return md_string

    # 소설 서비스 상태 정상
    # 연재 지연/중단의 경우 '연중(각)'으로 표시
    # on_hiatus: bool = info_dic["연재 유형"]["연재지연"] or info_dic["연재 유형"]["연재중단"]

    lines = ["aliases:\n  - (직접 적어 주세요)"] + lines
    lines += ["유입 경로: (직접 적어 주세요)"]

    for k1, v1 in info_dic.items():
        assert isinstance(k1, str)
        if k1 == "줄거리":
            continue
        if k1 == "인생픽 순위" and v1 is None:
            continue

        # 연재 유형, 연재 상태
        if isinstance(v1, dict):
            for k2, v2 in v1.items():
                assert isinstance(k2, str)
                if isinstance(v2, bool) and not v2:
                    continue
                if k2.isnumeric():
                    if k2 == "19":
                        k2 = "성인"
                    else:
                        k2 = '"' + k2 + '"'
                lines += [k2 + ": " + str(v2)]
        else:
            # 공개/갱신/완독 일자
            if k1.endswith("일자") and v1 is None:
                v1 = "0000-00-00"

            if k1.isnumeric():
                k1 = '"' + k1 + '"'
            lines += [k1 + ": " + str(v1)]

    lines = ["---"] + lines
    lines += ["---"]
    lines += [info_dic["줄거리"]]

    md_string: str = "\n".join(lines) + "\n"

    return md_string


def novel_info_main() -> None:
    base_url: str = "https://novelpia.com/novel/"
    novel_dir: Path = Path.cwd().parent / "novel"
    env_var_name: str = "MARKDOWN_DIR"

    # 환경 변수의 Markdown 폴더 경로 사용
    try:
        from os import environ
        env_md_dir: str = environ[env_var_name]
        novel_md_dir: Path = Path(env_md_dir)

    # 환경 변수 無, 기본 값으로
    except KeyError as ke:
        novel_md_dir = novel_dir / "md"
        print_under_new_line(f"`예외 발생: {ke = }")
        print(f"환경 변수 '{env_var_name}' 을 찾지 못했어요. Markdown 파일은 {novel_md_dir} 에 쓸게요.")

    code: str = str(ask_for_num("소설 번호"))

    from urllib.parse import urljoin
    url: str = urljoin(base_url, code)  # https://novelpia.com/novel/1
    html: str = get_novel_main_page(url)

    # Metadata 추출하기
    title, info_dic = extract_novel_info(html)

    # ../novel/markdown/제목.md
    novel_md_name = Path(novel_md_dir, title).with_suffix(".md")

    # Markdown 형식으로 변환하기
    novel_md_content = convert_to_md(title, info_dic)

    # Markdown 폴더 확보하기
    assure_path_exists(novel_md_name)

    # Markdown 파일 새로 쓰기
    with (open(novel_md_name, "w") as file):
        file.write(novel_md_content)
        print_under_new_line("[알림]", novel_md_name, "작성함.")


if __name__ == "__main__":
    novel_info_main()
