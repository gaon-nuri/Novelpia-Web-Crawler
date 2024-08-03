![1  노벨피아 소설 페이지](https://github.com/user-attachments/assets/6de46560-f34c-4ccf-b348-f8190cdc12df)

# 개요
노벨피아 소설의 번호를 입력받아 소설의 Metadata 를 크롤링한 뒤 Obsidian용 Markdown 파일로 출력합니다.

# 특징
- Python 100%. requests, BeautifulSoup 사용.
- HTTP Client 방식 (Headless Browser 방식 X)
- 제목, 작가명, 태그 등을 크롤링. 전체 목록 아래에.
- 노벨피아 공식 API만 호출함. 비공식 API 사용 X.
- 반자동. 소설 번호와 별칭 유무를 수동으로 입력받음.
- Obsidian에 최적화된 문법의 Markdown 파일을 출력.

# 크롤링하는 정보의 목록
- 제목
- 작가명
- 링크
- 시놉시스
- 태그
- 첫 연재일
- 마지막 연재일
- 완결 여부
- 성인 작품 여부
- 연재 유형 (자유/PLUS)
- 독점작 여부
- 신작 챌린지 참여작 여부
- 연재중단, 연재지연 여부
- 회차수
- 알람수
- 선호수
- 조회수
- 추천수

# 출력 예시

## 터미널 스크린샷
![2  코드 실행 결과](https://github.com/user-attachments/assets/1d2a355a-bc8c-4152-9ea0-149f8222edc0)

## Markdown 파일
[내가 쓰다 만 소설의 등장하지도 않는 성녀가 되어버렸다.md](https://github.com/user-attachments/files/16432711/default.md)

## Obsidian 스크린샷
![3  Obsidan에서 연 Markdown 출력 파일](https://github.com/user-attachments/assets/3a0cc87f-7d33-4c8c-bb1d-0934293e132d)

