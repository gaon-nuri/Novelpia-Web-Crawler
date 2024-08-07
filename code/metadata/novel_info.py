0from datetime import date  # date.today()
from urllib.parse import urljoin, urlparse

from code.common.module import *


def get_upload_date(novel_code: str, sort_method: str = "DOWN") -> str:
    """
    소설의 회차 목록에서 첫/마지막 회차 게시일을 추출하여 반환하는 함수

    :param novel_code: 소설 번호
    :param sort_method: "DOWN", 첫화부터 / "UP", 최신화부터
    :return: 첫/마지막 회차 게시일
    """
    ep_list_html = get_ep_list(novel_code, sort_method, 1)
    ep_list_soup = BeautifulSoup(ep_list_html, "html.parser")

    # 회차 게시일 추출
    # ['무료', '프롤로그', 'EP.0', '0', '0', '2', '21.01.18']
    ep_info: list[str] = ep_list_soup.select_one("tr.ep_style5").text.split()
    upload_date: str = ep_info[-1]  # 21.01.18 또는 '19시간전'

    # 24시간 이내에 게시된 경우 당일 날짜로 간주
    if upload_date.endswith("전"):  # upload_date: '19시간전'
        upload_date = str(date.today())  # 2024-07-25
    else:
        upload_date = "20" + upload_date  # 21.01.18 > 2021.01.18
        upload_date = upload_date.replace(".", "-")  # 2021.01.18 > 2021-01-18

    return upload_date


def extract_metadata(main_page_html: str) -> dict:
    """
    소설 Main Weppage HTML 문자열을 입력받아 Metadata 를 반환하는 함수

    :param main_page_html: 소설 Metadata 를 추출할 HTML
    :return: 추출한 Metadata 가 담긴 Dict
    """
    info_dic: dict = {
        "title": "",
        "author": "",
        "novel_page_url": "",
        "solePick": "",
        "tagList": ["",],
        "badge_dic": {x: False for x in [
                "완결",
                "연재지연",
                "연재중단",
                "19",
                "자유",
                "독점",
                "챌린지",
            ]
        },
        "user_stat_dic": {user_stat: 0 for user_stat in [
                "ep",
                "alarm",
                "prefer",
            ]
        },
        "ep_stat_dic": {ep_stat: 0 for ep_stat in [
                "recommend",
                "view",
            ]
        },
        "synopsis": ""
    }
    soup = BeautifulSoup(main_page_html, "html.parser")

    # 제목 추출
    title = soup.title.text[22:]  # '노벨피아 - 웹소설로 꿈꾸는 세상! - '의 22자 제거

    # 소설 Main Webpage URL 추출
    # tag: <meta content="https://novelpia.com/novel/1" property="og:url"/>
    meta_url_tag = soup.select_one("meta[property='og:url']")
    novel_page_url: str = meta_url_tag.get("content")
    info_dic["novel_page_url"] = novel_page_url

    # 소설 번호 추출
    novel_code: str = urlparse(novel_page_url).path.split("/")[-1]  # "https://novelpia.com/novel/1" > "1"

    # 소설 서비스 상태 확인
    try:
        # 제목 추출, 검사, 등록
        if title == soup.select_one("div.epnew-novel-title").string:  # '창작물 속으로'
            info_dic["title"] = title

    # 서비스 상태 비정상, 소설 정보를 받지 못함
    except AttributeError as ae:
        print_with_new_line(f"[오류] 예외 발생: {ae = }")

        # 알림 창 추출
        try:
            msg_tag = soup.select_one("#alert_modal .mg-b-5")

        # 알림 창이 나오지 않음
        except AttributeError as ae:
            print(f"예외 발생: {ae = }")

        # 알림 메시지 추출
        else:
            msg: str = msg_tag.text
            """
            0: 잘못된 소설 번호 입니다. (제목, 줄거리 無)
            4: 삭제된 소설 입니다. (제목 有, 줄거리 無)
            200000: 잘못된 접근입니다. (제목 有, 줄거리 無)
            """
            if msg == "잘못된 소설 번호 입니다.":
                pass
            elif msg == "잘못된 접근입니다.":
                msg = f"<{title}> 에 대한 {msg}"
            elif msg == "삭제된 소설 입니다.":
                msg = f"<{title}> 은(는) {msg}"

            # 오류 메시지 출력 후 종료
            print()
            exit_code = f"[노벨피아] {msg}"
            exit(exit_code)

    # 서비스 상태 정상, 계속 진행
    else:
        # 작가명 추출
        info_dic["author"]: str = soup.select_one("a.writer-name").string.strip()  # '제울'

        print_with_new_line(f"[알림] {info_dic['author']} 작가의 <{info_dic['title']}>은 정상적으로 서비스 중인 소설이에요.")

        # 연재 유형(자유/PLUS), 청불/독점작/챌린지/연중(및 지연)/완결 여부
        badge_list: list[str] = [badge.text for badge in soup.select(".in-badge span")]

        for flag in badge_list:
            if flag in info_dic["badge_dic"].keys():
                info_dic["badge_dic"][flag] = True

        # 해시태그 목록 추출 (최소 2개 - 중복 포함 4개)
        tag_set = soup.select("p.writer-tag span.tag")

        # PC, 모바일 중복 해시태그 제거
        indices: int = int(len(tag_set) / 2)  # 3
        info_dic["tagList"]: list[str] = [i.string for i in tag_set[:indices]]  # ['판타지','#현대', '#하렘']

        # 조회, 추천수 추출
        ep_stat_list: list[str] = [i.string.replace(",", "") for i in soup.select("div.counter-line-a span")]
        info_dic["ep_stat_dic"]["view"] = int(ep_stat_list[1])  # 83,050,765 > 83050765
        info_dic["ep_stat_dic"]["recommend"] = int(ep_stat_list[3])  # 4,540,540 > 4540540

        # 인생픽 순위 추출
        sole_pick_rank: str = soup.select(".counter-line-b span")[1].text

        # 인생픽 순위 공개 중, 속성 추가
        if sole_pick_rank[-1] == "위":  # 40위
            info_dic["solePick"] = "\n인생픽: " + sole_pick_rank  # 인생픽: 40위 (Markdown 속성 문법)

        # 비공개 상태일 시 넘어가기
        elif sole_pick_rank == "공개전":
            pass

        # 회차, 알람, 선호수 추출
        user_stat_li: list[str] = [i.string.replace(",", "") for i in soup.select("span.writer-name")]
        user_stat_li[2] = user_stat_li[2].removesuffix("회차")  # 2538회차 > 2538
        user_stat_li_int: list[int] = [int(user_stat) for user_stat in user_stat_li][::-1]

        info_dic["user_stat_dic"] = dict(zip(info_dic["user_stat_dic"].keys(), user_stat_li_int))

        # 프롤로그 존재 시 회차 수 1 가산
        # EP.0 ~ EP.10 이면 10회차로 나오니 총 회차 수는 여기에 1을 더해야 함
        if has_prologue(novel_code):
            info_dic["user_stat_dic"]["ep"] += 1

        # 줄거리 추출
        info_dic["synopsis"]: str = soup.select_one(".synopsis").text

        # 공개 일자 추출
        info_dic["fstUploadDate"] = get_upload_date(novel_code, "DOWN")
        info_dic["lstUploadDate"] = get_upload_date(novel_code, "UP")

    return info_dic


def convert_to_markdown(info_dic: dict) -> str:
    """
    추출한 소설 정보를 받아 Markdown 형식으로 변환하는 함수

    :param info_dic: 추출한 소설 정보
    """
    print(f"[알림] {info_dic['title']}.md 파일에 '유입 경로' 속성을 추가했어요. Obsidian 으로 직접 수정해 주세요.")

    # 태그의 각 줄 앞에 '-'를 붙여서 Markdown list (Obsidian 태그) 형식으로 변환
    tag_ul: str = "".join(f"\n  - {tag.lstrip('#')}" for tag in info_dic["tagList"])
    """
    tags:
      - 판타지
      - 중세
    """
    # 줄거리의 각 줄 앞에 '>'를 붙여서 Markdown Callout 블록으로 변환
    synopsis_lines: list[str] = info_dic["synopsis"].splitlines()
    synopsis_callout: str = "> [!TLDR] 시놉시스\n> "

    if len(synopsis_lines) > 1:
        synopsis_callout += "\n> ".join(line for line in synopsis_lines)
    else:
        synopsis_callout += synopsis_lines[0]

    """
    > [!TLDR] 시놉시스
    > 몰살 엔딩 보려고 세상을 멸망시켰다.
    > 
    > 그리고 게임 속에 빙의당했다.
    > - ai로 제작한 이미지입니다.
    > - 상업적 이용이 가능합니다.
    """

    # 연재 지연/중단의 경우 '연중(각)'으로 표시
    on_hiatus: bool = (info_dic["badge_dic"]["연재지연"] != info_dic["badge_dic"]["연재중단"])

    # 최종 Markdown
    novel_markdown_content: str = f"""---
aliases:
  - 
작가명: {info_dic["author"]}
링크: {info_dic["novel_page_url"]}
유입 경로: (직접 적어 주세요) {info_dic["solePick"]}
tags:{tag_ul}
공개: {info_dic.setdefault("fstUploadDate", "0000-00-00")}
갱신: {info_dic.setdefault("lstUploadDate", "0000-00-00")}
완독: 0000-00-00
완결: {info_dic["badge_dic"]["완결"]}
연중(각): {on_hiatus}
성인: {info_dic["badge_dic"]["19"]}
무료: {info_dic["badge_dic"]["자유"]}
독점: {info_dic["badge_dic"]["독점"]}
챌린지: {info_dic["badge_dic"]["챌린지"]}
회차: {info_dic["user_stat_dic"]["ep"]}
알람: {info_dic["user_stat_dic"]["alarm"]}
선호: {info_dic["user_stat_dic"]["prefer"]}
추천: {info_dic["ep_stat_dic"]["recommend"]}
조회: {info_dic["ep_stat_dic"]["view"]}
---
{synopsis_callout}
"""

    return novel_markdown_content


def main() -> None:
    base_url: str = "https://novelpia.com/novel/"
    novel_dir: Path = Path.cwd().parent / "novel"
    env_var_name: str = "MARKDOWN_DIR"

    # 환경 변수의 Markdown 폴더 경로 사용
    try:
        env_markdown_dir: str = os.environ[env_var_name]
        novel_markdown_dir: Path = Path(env_markdown_dir)

    # 환경 변수 無, 기본 값으로
    except KeyError as ke:
        novel_markdown_dir = novel_dir / "markdown"
        print_with_new_line(f"`예외 발생: {ke = }")
        print(f"환경 변수 '{env_var_name}' 을 찾지 못했어요. Markdown 파일은 {novel_markdown_dir} 에 쓸게요.")

    novel_code: str = str(ask_for_number("소설 번호"))

    novel_main_page_url: str = urljoin(base_url, novel_code)  # https://novelpia.com/novel/1
    novel_main_page_html: str = get_novel_main_page(novel_main_page_url)

    # Metadata 추출하기
    metadata_dic: dict = extract_metadata(novel_main_page_html)

    # ../novel/markdown/제목.md
    novel_markdown_name: Path = (novel_markdown_dir / metadata_dic['title']).with_suffix(".md")

    # Markdown 형식으로 변환하기
    novel_markdown_content = convert_to_markdown(metadata_dic)

    # Markdown 폴더 확보하기
    assure_path_exists(novel_markdown_name)

    # Markdown 파일 새로 쓰기
    with (open(novel_markdown_name, "w") as novelMarkDownFile):
        novelMarkDownFile.write(novel_markdown_content)
        print()
        print(novel_markdown_name, "작성함.")


if __name__ == "__main__":
    main()
