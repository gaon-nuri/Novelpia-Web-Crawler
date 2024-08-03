import os  # os.environ[]
from datetime import date  # date.today()
from pathlib import Path
from urllib.parse import urljoin  # urljoin(base_url, novel_code)

import requests
from bs4 import BeautifulSoup

# Windows Chrome User-Agent String
ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'


def ask_for_string(ask_prompt: str = "입력", ask_type: type = str) -> str:
    """
    문자열을 입력받고, 그 형식이 유효하면 반환하는 함수

    :param ask_prompt: 문자열을 입력하라는 메시지
    :param ask_type: 입력받을 문자열이 뜻하는 타입
    :return: 유효한 입력 문자열
    """

    def check_string_validity(check_str: str, check_type: type = str) -> bool:
        """
        문자열의 형식을 검사하는 함수

        :param check_str: 형식을 검사할 문자열
        :param check_type: 문자열에 기대하는 형식
        :return: 형식이 올바르면 참, 그렇지 않으면 거짓
        """
        try:
            return isinstance(check_type(check_str), check_type)

        # 해당 형식으로 변환할 수 없는 문자열
        except ValueError as ve:
            print(f"예외 발생: {ve}")
            return False

    # 유효한 형식의 문자열을 입력받을 때까지 반복
    while True:
        print()
        answer_str: str = input(f"{ask_prompt}: ").strip()
        is_valid_string = check_string_validity(answer_str, ask_type)

        # 빈 문자열
        if len(answer_str) == 0:
            print("[오류] 입력을 받지 못했어요. 이전 단계로 돌아갈게요.")
            continue

        # 무효한 문자열
        if not is_valid_string:
            print()
            print("[오류] 잘못된 입력이에요. 이전 단계로 돌아갈게요.")
            continue
        return answer_str


def ask_for_permission(question_to_ask: str, ask_condition: bool = True) -> (bool, bool):
    """
    사용자의 의사를 묻고 동의 여부를 출력하는 함수

    :param question_to_ask: 사용자에게 물어볼 질문
    :param ask_condition: 질문 여부를 결정하는 진리값
    :return:(질문 여부 = 항상 True, 동의 여부 - True/False)
    """
    while ask_condition:
        # 질문을 하고 답변을 Y, y, N, n 중 하나로 받음
        user_answer: str = ask_for_string(f"{question_to_ask} (Y/n)").strip().capitalize()
        if user_answer == "Y":
            return True, True  # 질문 함, 동의 함
        elif user_answer == "N":
            return True, False  # 질문 함, 동의 안 함
        else:
            print("[동의] 동의하면 Y나 y, 그러지 않으면 N이나 n을 눌러 주세요.")


def request_novel_main_page(url: str) -> str:
    """
    서버에 소설의 Main Webpage 를 요청하고, 성공 시 HTML 응답을 반환하는 함수

    :param url: 소설 Main Webpage URL
    :return: 소설 Main Webpage HTML
    """
    headers: dict = {'User-Agent': ua}

    # 소설 Main Webpage 의 HTML 문서를 요청
    response = requests.get(url=url, headers=headers)  # response: <Response [200]>
    html: str = response.text
    return html


def request_novel_ep_list(code: str, sort: str, page: int = 0) -> str:
    """
    서버에 회차 목록을 요청하고, 성공 시 HTML 응답을 반환하는 함수

    :param code: 소설 번호
    :param sort: "DOWN", 첫화부터 / "UP", 최신화부터
    :param page: 요청할 페이지 번호
    :return: 게시일 순으로 정렬된 회차 목록의 한 페이지 (HTML)
    """
    # Chrome DevTools 에서 복사한 POST 요청 URL 및 양식 데이터
    req_url: str = "https://novelpia.com/proc/episode_list"
    form_data: dict = {"novel_no": code, "sort": sort, "page": page}
    headers: dict = {'User-Agent': ua}

    # 게시일 순으로 정렬된 회차 목록 요청
    response = requests.post(url=req_url, data=form_data, headers=headers)  # response: <Response [200]>
    html = response.text

    return html


def get_upload_date(novel_code: str, sort_method: str = "DOWN") -> str:
    """
    소설의 회차 목록에서 첫/마지막 회차 게시일을 추출하여 반환하는 함수

    :param novel_code: 소설 번호
    :param sort_method: "DOWN", 첫화부터 / "UP", 최신화부터
    :return: 첫/마지막 회차 게시일
    """
    ep_list_html = request_novel_ep_list(novel_code, sort_method)
    ep_list_soup = BeautifulSoup(ep_list_html, "html.parser")

    # 회차 게시일 추출
    upload_date: str = ep_list_soup.select_one(".ep_style2 b").text.strip()  # 21.01.18 또는 '19시간전'

    # 24시간 이내에 게시된 경우 당일 날짜로 간주
    if upload_date.endswith("전"):  # upload_date: '19시간전'
        upload_date = str(date.today())  # 2024-07-25
    else:
        upload_date = "20" + upload_date  # 21.01.18 > 2021.01.18
        upload_date = "-".join(upload_date.split("."))  # 2021.01.18 > 2021-01-18

    return upload_date


def extract_metadata(main_page_html: str) -> dict:
    """
    소설 Main Weppage HTML 문자열을 입력받아 Metadata 를 반환하는 함수

    :param main_page_html: 소설 Metadata 를 추출할 HTML
    :return: 추출한 Metadata 가 담긴 Dict
    """
    metadata_dic: dict = {
        "title": "",
        "author": "",
        "novel_page_url": "",
        "solePick": "",
        "tagList": ["",],
        "fstUploadDate": "0000-00-00",
        "lstUploadDate": "0000-00-00",
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
    metadata_dic["novel_page_url"] = meta_url_tag.get("content")

    # 소설 서비스 상태 확인
    # novel_info = soup.select_one(".epnew-novel-info")
    try:
        # 제목 추출, 검사, 등록
        if title == soup.select_one("div.epnew-novel-title").string:  # '창작물 속으로'
            metadata_dic["title"] = title

    except AttributeError as ae:
        print()
        print(f"[오류] 예외 발생: {ae}")

        try:
            # if not novel_info is None:
            msg_tag = soup.select_one("#alert_modal .mg-b-5")
            msg: str = msg_tag.text
            """
            0: 잘못된 소설 번호 입니다. (제목, 줄거리 無)
            4: 삭제된 소설 입니다. (제목 有, 줄거리 無)
            200000: 잘못된 접근입니다. (제목 有, 줄거리 無)
            """

        except AttributeError as ae:
            print(f"예외 발생: {ae}")

        else:
            if msg == "잘못된 소설 번호 입니다.":
                pass
            elif msg == "잘못된 접근입니다.":
                msg = f"<{title}> 에 대한 {msg}"
            elif msg == "삭제된 소설 입니다.":
                msg = f"<{title}> 은(는) {msg}"

            # 오류 메시지를 출력하며 종료
            print()
            exit_code = f"[노벨피아] {msg}"
            exit(exit_code)

    # 소설 서비스 상태 정상, 계속 진행
    else:
        # 작가명 추출
        metadata_dic["author"]: str = soup.select_one("a.writer-name").string.strip()  # '제울'

        print()
        print(f"[알림] {metadata_dic['author']} 작가의 <{metadata_dic['title']}>은 정상적으로 서비스 중인 소설이에요.")

        # 연재 유형(자유/PLUS), 청불/독점작/챌린지/연중(및 지연)/완결 여부
        badge_list: list[str] = [badge.text for badge in soup.select(".in-badge span")]

        for flag in badge_list:
            if flag in metadata_dic["badge_dic"].keys():
                metadata_dic["badge_dic"][flag] = True

        # 해시태그 목록 추출 (최소 2개 - 중복 포함 4개)
        tag_set = soup.select("p.writer-tag span.tag")

        # PC, 모바일 중복 해시태그 제거
        indices: int = int(len(tag_set) / 2)  # 3
        metadata_dic["tagList"]: list[str] = [i.string for i in tag_set[:indices]]  # ['판타지','#현대', '#하렘']

        # 조회, 추천수 추출
        ep_stat_list: list[str] = [i.string.replace(",", "") for i in soup.select("div.counter-line-a span")]
        metadata_dic["ep_stat_dic"]["view"] = int(ep_stat_list[1])  # 83,050,765 > 83050765
        metadata_dic["ep_stat_dic"]["recommend"] = int(ep_stat_list[3])  # 4,540,540 > 4540540

        # 인생픽 순위 추출
        sole_pick_rank: str = soup.select(".counter-line-b span")[1].text

        if sole_pick_rank[-1] == "위":  # 40위
            metadata_dic["solePick"] = "\n인생픽: " + sole_pick_rank  # 인생픽: 40위 (Markdown 속성 문법)

            # 선호, 알람, 회차수 추출
        user_stat_li: list[str] = [i.string.replace(",", "") for i in soup.select("span.writer-name")]
        user_stat_li[2] = user_stat_li[2].replace("회차", "")  # 2538회차 > 2538
        user_stat_li_int: list[int] = [int(user_stat) for user_stat in user_stat_li]

        metadata_dic["user_stat_dic"] = dict(zip(metadata_dic["user_stat_dic"].keys(), user_stat_li_int))

        # 줄거리 추출
        metadata_dic["synopsis"]: str = soup.select_one(".synopsis").text

        novel_code: str = metadata_dic["novel_page_url"].split("/")[-1]  # "https://novelpia.com/novel/1" > "1"

        metadata_dic["fstUploadDate"] = get_upload_date(novel_code, "DOWN")
        metadata_dic["lstUploadDate"] = get_upload_date(novel_code, "UP")

    return metadata_dic


def assure_path_exists(path_to_assure: Path) -> None:
    """
    파일/폴더의 상위 폴더가 다 있으면 넘어가고 없으면 만드는 함수.

    :param path_to_assure: 상위 폴더를 확보할 파일/폴더의 경로
    """
    parent_paths: [Path] = path_to_assure.parents
    for i, parent_path in enumerate(parent_paths):

        # 상위 폴더 유무 확인
        if parent_path.exists():
            print()

            # 상위 폴더 有, 작업 불필요
            if i == 0:
                print("[알림]", parent_path, "폴더가 이미 있으니 그대로 쓸게요.")

            # 상위 폴더 有, 재귀(?)적으로 하위 폴더 생성
            for j in range(i):
                child_path: Path = parent_paths[range(i)[i - 1 - j]]
                child_path.mkdir()
                print("[알림]", child_path, "폴더를 생성했어요.")
            break


def write_markdown(metadata_dic: dict, novel_markdown_name: Path) -> None:
    """
    Markdown 파일을 새로 열고 추출한 소설 정보를 쓰는 함수

    :param metadata_dic: 파일에 쓸 Metadata 가 담긴 Dict
    :param novel_markdown_name: 생성할 파일의 경로
    """

    # Markdown 폴더 확보하기
    assure_path_exists(novel_markdown_name)

    # Markdown 파일 열기
    with (open(novel_markdown_name, "w") as novelMarkDownFile):
        aliases: str = ""
        aliases_q: str = f"[확인] {metadata_dic['title']}.md 파일에 '별칭(aliases)' 속성을 추가할까요?"
        asked_add_alias, will_add_alias = ask_for_permission(aliases_q)

        # 별칭을 추가할 경우
        if will_add_alias:
            aliases = "\naliases: \n  - (직접 적어 주세요)"  # Markdown 속성 문법
            print()
            print(f"[알림] {metadata_dic['title']}.md 파일에 '별칭(aliases)' 속성을 추가했어요. Obsidian 으로 직접 수정해 주세요.")
            print()

        print(f"[알림] {metadata_dic['title']}.md 파일에 '유입 경로' 속성을 추가했어요. Obsidian 으로 직접 수정해 주세요.")

        # 태그의 각 줄 앞에 '-'를 붙여서 Markdown list (Obsidian 태그) 형식으로 변환
        tag_ul: str = "".join(f"\n  - {tag.lstrip('#')}" for tag in metadata_dic["tagList"])
        """
        tags:
          - 판타지
          - 중세
        """
        # 줄거리의 각 줄 앞에 '>'를 붙여서 Markdown Callout 블록으로 변환
        synopsis_lines: list[str] = metadata_dic["synopsis"].splitlines()
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
        on_hiatus: bool = (metadata_dic["badge_dic"]["연재지연"] != metadata_dic["badge_dic"]["연재중단"])

        # 최종 Markdown
        novel_markdown_content: str = f"""---{aliases}
작가명: {metadata_dic["author"]}
링크: {metadata_dic["novel_page_url"]}
유입 경로: (직접 적어 주세요) {metadata_dic["solePick"]}
tags:{tag_ul}
공개: {metadata_dic["fstUploadDate"]}
갱신: {metadata_dic["lstUploadDate"]}
완독: 0000-00-00
완결: {metadata_dic["badge_dic"]["완결"]}
연중(각): {on_hiatus}
성인: {metadata_dic["badge_dic"]["19"]}
무료: {metadata_dic["badge_dic"]["자유"]}
독점: {metadata_dic["badge_dic"]["독점"]}
챌린지: {metadata_dic["badge_dic"]["챌린지"]}
회차: {metadata_dic["user_stat_dic"]["ep"]}
알람: {metadata_dic["user_stat_dic"]["alarm"]}
선호: {metadata_dic["user_stat_dic"]["prefer"]}
추천: {metadata_dic["ep_stat_dic"]["recommend"]}
조회: {metadata_dic["ep_stat_dic"]["view"]}
---
{synopsis_callout}"""

        # MarkDown 파일 쓰기
        novelMarkDownFile.write(novel_markdown_content)
        print()
        print(novel_markdown_name, "작성함.")


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
        print()
        print(f"예외 발생: {ke = }")
        print(f"환경 변수 '{env_var_name}' 을 찾지 못했어요. Markdown 파일은 {novel_markdown_dir} 에 쓸게요.")

    # 유효한 소설 번호를 얻을 때까지 입력을 받음
    while True:
        novel_code: str = str(int(ask_for_string("[입력] 소설 번호를 입력해 주세요", int)))  # 01, 001,... > 1
        is_valid_code: bool = ask_for_permission(f"[확인] 소설 번호가 {novel_code}인가요?")[1]

        # 유효한 소설 번호 (자연수)
        if is_valid_code:
            break

    novel_main_page_url: str = urljoin(base_url, novel_code)  # https://novelpia.com/novel/1
    novel_main_page_html: str = request_novel_main_page(novel_main_page_url)

    # Metadata 추출하기
    metadata_dic: dict = extract_metadata(novel_main_page_html)

    # ../novel/markdown/제목.md
    novel_markdown_name: Path = (novel_markdown_dir / metadata_dic['title']).with_suffix(".md")

    # Markdown 파일 생성하기
    write_markdown(metadata_dic, novel_markdown_name)


if __name__ == "__main__":
    main()
