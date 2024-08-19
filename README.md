![1  노벨피아 소설 페이지](https://github.com/user-attachments/assets/12e80855-b3f5-41eb-bd34-95e72c6b05f1)

# 개요
노벨피아 소설의 번호를 입력받아 소설 정보를 크롤링한 뒤 Obsidian용 Markdown 파일로 저장합니다.

# 기능
- 제목, 작가명, 태그 등을 크롤링. 전체 목록 아래에.
- Obsidian에 최적화된 문법의 Markdown 파일을 저장.

# 주의
- 파일 저장 위치는 프로젝트 폴더의 .env 파일의 MARKDOWN_DIR 값을 사용.
- 문제의 환경 변수가 없을 시 기본값 NWC/novel/markdown/ 에 저장.

# 구현
- Python 100%. requests, BeautifulSoup 사용.
- HTTP Client 방식 (Headless Browser 방식 X)
- 노벨피아 공식 API만 호출함. 비공식 API 사용 X.
- 단위 테스트 지원 (연중작 비율 측정 등에 응용 가능)

# 크롤링하는 정보의 목록
- 제목
- 작가명
- 링크
- 시놉시스
- 태그
## 연재 일자
- 연재 시작일
- 최근(예정) 연재일
## 연재 유형
- 완결
- 연습작품
- 삭제
- 연재중단, 연재지연
## 작품 유형
- 성인
- 자유/PLUS
- 독점
- 챌린지
## 통계
- 회차수
- 알람수
- 선호수
- 조회수
- 추천수
- 인생픽 순위

# 출력 예시

## 터미널 스크린샷
![2  코드 실행 결과](https://github.com/user-attachments/assets/5929ee77-7120-48b4-be33-fe079afeb009)

## Markdown 파일
[내가 쓰다 만 소설의 등장하지도 않는 성녀가 되어버렸다.md](https://github.com/user-attachments/files/16478359/default.md)

## Obsidian 스크린샷
![3  Obsidan에서 연 Markdown 출력 파일](https://github.com/user-attachments/assets/911b366d-2ad0-4e1f-baf5-835bb35ef280)

