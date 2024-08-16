from contextlib import contextmanager

from bs4 import BeautifulSoup
from bs4.element import Tag

from src.common.module import Path
from src.common.userIO import print_under_new_line


def get_novel_up_dates(code: str, sort: str) -> str:
    from src.common.episode import get_ep_list, extract_ep_tags, get_ep_up_dates
    page_li_html: str = get_ep_list(code, sort, 1, False)
    page_li_soup = BeautifulSoup(page_li_html, "html.parser")
    ep_tag_set: set = extract_ep_tags(page_li_soup, {1})
    up_dates: list[str] | None = get_ep_up_dates(ep_tag_set)
    up_date: str = up_dates[0]

    return up_date


@contextmanager
def chk_novel_status(info_dic: dict, soup: BeautifulSoup):
    """
    파싱된 소설 메인 페이지에서 추출한 소설 정보를 담은 Dict를 반환하는 함수

    :param info_dic: 소설 정보가 담긴 Dict
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

                info_dic["연재 상태"]["삭제"] = True

            elif alert_msg.endswith("잘못된 접근입니다."):
                alert_msg = f"<{html_title}>에 대한 {alert_msg}"

                info_dic["연재 유형"]["자유"] = True
                info_dic["연재 상태"]["연습작품"] = True

            # 오류 메시지 출력
            print_under_new_line("[노벨피아]", alert_msg)

            info_dic["연재 상태"]["연재 중"] = False

            yield html_title, info_dic, attr_err

    # 서비스 상태 정상
    else:
        # 제목 검사 후 반환
        assert_msg: str = f"[오류] 제목 불일치: 페이지 제목 '{html_title}'과 소설 제목 '{novel_title}'가 달라요."
        assert html_title == novel_title, assert_msg

        yield novel_title, info_dic, None


def extract_novel_info(html: str) -> tuple[str, dict]:
    """입력받은 소설의 메인 페이지 HTML에서 정보를 추출하여 반환하는 함수

    :param html: 소설 Metadata 를 추출할 HTML
    :return: 소설 제목, 추출한 Metadata 가 담긴 Dict
    """
    info_dic: dict[str] = {}.fromkeys(["작가명", "소설 링크", "인생픽 순위", "tags", "줄거리", "공개 일자", "갱신 일자"])
    info_dic.setdefault("완독 일자", "0000-00-00")
    info_dic["연재 상태"]: dict = {}.fromkeys(["완결", "연재지연", "연재중단", "삭제", "연습작품"], False)
    info_dic["연재 상태"].setdefault("연재 중", True)
    info_dic["연재 유형"]: dict = {}.fromkeys(["19", "자유", "독점", "챌린지"], False)
    info_dic["독자 수 비례 지표"]: dict = {}.fromkeys(["회차 수", "알람 수", "선호 수"])
    info_dic["회차 수 비례 지표"]: dict = {}.fromkeys(["추천 수", "조회 수"])

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    # 소설 메인 페이지 URL 추출
    # tag: <meta content="https://novelpia.com/novel/1" property="og:url"/>
    meta_url_tag = soup.select_one("meta[property='og:url']")
    novel_page_url: str = meta_url_tag.get("content")

    # URL 저장
    info_dic["소설 링크"] = novel_page_url

    # 소설 번호 추출
    from urllib.parse import urlparse
    code: str = urlparse(novel_page_url).path.split("/")[-1]  # "https://novelpia.com/novel/1" > "1"

    # 제목 추출 및 소설 서비스 상태 확인
    with chk_novel_status(info_dic, soup) as (title, info_dic, err):
        if err:
            return title, info_dic

    # 작가명 추출
    author: str = soup.select_one("a.writer-name").string.strip()  # '제울'
    info_dic["작가명"] = author

    print_under_new_line(f"[알림] {author} 작가의 <{title}>은 정상적으로 서비스 중인 소설이에요.")

    # 연재 유형(자유/PLUS), 청불/독점작/챌린지/연중(및 지연)/완결 여부
    flag_list: list[str] = [badge.text for badge in soup.select(".in-badge span")]

    for flag in flag_list:
        if flag in info_dic["연재 유형"].keys():  # ["19", "자유", "독점", "챌린지"]
            info_dic["연재 유형"][flag] = True

        elif flag in info_dic["연재 상태"].keys():  # ["연재 중", "삭제", "완결", "연재지연", "연재중단"] (flag 는 "연재 중"일 수 X)
            info_dic["연재 상태"][flag] = True
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
    indices = int(len(tag_set) / 2)  # 3
    hash_tags: list[str] = [i.string.lstrip("#") for i in tag_set[:indices]]  # ['판타지','현대', '하렘']

    info_dic["tags"]: str = "".join([f"\n  - {tag.lstrip('#')}" for tag in hash_tags])
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

    # 선호/알람/회차 수 추출
    novel_stats: list = [i.string.replace(",", "") for i in soup.select("span.writer-name")]
    novel_stats[2] = novel_stats[2].removesuffix("회차")  # 239회차 > 239
    novel_stats = list(map(int, novel_stats))  # [7694, 879, 239]

    keys = info_dic["독자 수 비례 지표"].keys()  # dict_keys(['회차 수', '알람 수', '선호 수'])
    novel_stats = novel_stats[::-1]  # [239, 879, 7694]

    # 회차/선호/알람 수 저장
    info_dic["독자 수 비례 지표"].update(zip(keys, novel_stats))

    # 프롤로그 존재 시 회차 수 1 가산
    # EP.0 ~ EP.10 이면 10회차로 나오니 총 회차 수는 여기에 1을 더해야 함
    from src.common.episode import has_prologue
    if has_prologue(code):
        novel_stats[2] += 1

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
    if info_dic["독자 수 비례 지표"]["회차 수"] != 0:
        info_dic["공개 일자"] = get_novel_up_dates(code, "DOWN")
        info_dic["갱신 일자"] = get_novel_up_dates(code, "UP")

    return title, info_dic


def novel_info_to_md(title: str, info_dic: dict) -> str:
    """추출한 소설 제목과 정보를 받아 Markdown 형식으로 변환하는 함수

    :param title: 소설 제목
    :param info_dic: 소설 정보
    """
    lines: list[str] = []

    print_under_new_line("[알림]", title + ".md 파일에 '유입 경로' 속성을 추가했어요. Obsidian 으로 직접 수정해 주세요.")

    # 삭제된 소설, Markdown 미작성
    if info_dic["연재 상태"]["삭제"]:
        return "삭제"

    # 소설 서비스 상태 정상, Markdown 작성
    lines = ["aliases:\n  - (직접 적어 주세요)"] + lines
    lines += ["유입 경로: (직접 적어 주세요)"]

    for k1, v1 in info_dic.items():
        assert isinstance(k1, str)

        # 빈 항목 건너뛰기
        if v1 is None:
            continue
        
        # 줄거리는 나중에 추가
        if k1 == "줄거리":
            if v1 is None:
                info_dic.pop(k1)
            continue

        # 인생픽 순위가 미공개 상태일 경우 건너뛰기
        if k1 == "인생픽 순위" and v1 is None:
            continue

        # 연재 유형, 연재 상태
        if isinstance(v1, dict):
            for k2, v2 in v1.items():
                assert isinstance(k2, str)

                if v2 is None:
                    continue

                if isinstance(v2, bool):
                    # 연재 유형/상태 값이 참인 것만 추가
                    if not v2:
                        continue
                        
                    # 연재 지연/중단의 경우 '연중(각)'으로 표시
                    if k2 == "연재지연" or k2 == "연재중단":
                        lines += ["연중(각): True"]
                        continue
                    
                # 속성 이름이 숫자인 경우 Obsidian 출력이 꼬이지 않게 따옴표 씌우기
                if k2.isnumeric():
                    if k2 == "19":
                        k2 = "성인"
                    else:
                        k2 = '"' + k2 + '"'
                lines += [k2 + ": " + str(v2)]
        else:
            # 공개/갱신/완독 일자
            if k1.endswith("일자"):
                if v1 is None:
                    v1 = "0000-00-00"

            if k1.isnumeric():
                k1 = '"' + k1 + '"'
            lines += [k1 + ": " + str(v1)]

    lines = ["---"] + lines
    lines += ["---"]

    synopsis: str = info_dic["줄거리"]
    if synopsis is not None:
        lines += [synopsis]

    md_string: str = "\n".join(lines) + "\n"

    return md_string


def novel_info_main() -> None:
    """
    모듈 대신 스크립트로 실행할 때 호출되는 함수.
    """
    base_url: str = "https://novelpia.com/novel/"
    novel_dir = Path(Path.cwd().parent, "novel")

    # 환경 변수의 Markdown 폴더 경로 사용
    from src.common.module import get_env_var_w_error
    with get_env_var_w_error("MARKDOWN_DIR") as (env_md_dir, key_err):
        if key_err:
            md_dir = Path(novel_dir, "md")
        else:
            md_dir: Path = Path(env_md_dir)

    print("Markdown 파일은", md_dir, "에 쓸게요.")

    from src.common.userIO import input_num
    code: str = str(input_num("소설 번호"))

    from urllib.parse import urljoin
    url: str = urljoin(base_url, code)  # https://novelpia.com/novel/1

    from src.common.module import get_novel_main_w_error
    with get_novel_main_w_error(url) as (html, connect_err):
        assert connect_err is None, f"{connect_err = }"

    # Metadata 추출하기
    title, info_dic = extract_novel_info(html)

    # ../novel/markdown/제목.md
    md_file_name = Path(md_dir, title).with_suffix(".md")

    # Markdown 형식으로 변환하기
    md_file_content = novel_info_to_md(title, info_dic)

    # Markdownovel_infon 폴더 확보하기
    from src.common.module import assure_path_exists
    assure_path_exists(md_file_name)

    # Markdown 파일 새로 만들기
    from src.common.module import opened_x_error
    with opened_x_error(md_file_name, "x") as (f, err):
        from io import TextIOWrapper
        assert isinstance(f, TextIOWrapper)
        f.write(md_file_content)
        print_under_new_line("[알림]", md_file_name, "작성함.")


if __name__ == "__main__":
    novel_info_main()
