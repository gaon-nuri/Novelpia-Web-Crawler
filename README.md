![1  노벨피아 소설 페이지](https://github.com/user-attachments/assets/12e80855-b3f5-41eb-bd34-95e72c6b05f1)

# Novelpia-Web-Crawler

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Stars](https://img.shields.io/github/stars/gaon-nuri/Novelpia-Web-Crawler.svg)
![Forks](https://img.shields.io/github/forks/gaon-nuri/Novelpia-Web-Crawler.svg)
![Language](https://img.shields.io/github/languages/top/gaon-nuri/Novelpia-Web-Crawler.svg)

**Novelpia-Web-Crawler**는 노벨피아 소설 페이지에서 메타데이터를 추출하여 Obsidian에 최적화된 Markdown 파일로 저장하는 웹 크롤러입니다.

---

# 📖 개요

노벨피아(Novelpia)에서 소설의 주요 정보를 자동으로 수집하고, 이를 Obsidian에서 손쉽게 활용할 수 있는 Markdown 파일로 변환합니다. 이 도구는 소설 관리 및 분석을 보다 효율적으로 수행할 수 있도록 도와줍니다.

---

# 🚀 주요 기능

- **메타데이터 크롤링**: 소설의 제목, 작가명, 링크, 시놉시스, 태그, 연재 일자 등 다양한 정보를 자동으로 수집합니다.
- **Obsidian 최적화**: 수집된 데이터를 Obsidian에서 쉽게 활용할 수 있도록 Markdown 문법에 맞춰 저장합니다.
- **환경 변수 지원**: 파일 저장 위치를 `.env` 파일을 통해 유연하게 설정할 수 있습니다.
- **단위 테스트 지원**: 안정적인 크롤링 및 데이터 처리 기능을 보장하기 위해 단위 테스트를 제공합니다.

---

# 🛠️ 설치 및 설정

## 1. 저장소 클론

```bash
git clone https://github.com/gaon-nuri/Novelpia-Web-Crawler.git
cd Novelpia-Web-Crawler
```

## 2. 가상 환경 설정 (선택 사항)

Python 가상 환경을 사용하는 것이 권장됩니다.

```bash
python -m venv venv
source venv/bin/activate  # Unix/macOS
venv\Scripts\activate     # Windows
```

## 3. 의존성 설치

```bash
pip install -r requirements.txt
```

## 4. 환경 변수 설정

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고, 다음과 같이 설정합니다. `MARKDOWN_DIR`은 Markdown 파일이 저장될 디렉토리 경로입니다.

```env
MARKDOWN_DIR=/path/to/your/markdown/directory
```

환경 변수가 설정되지 않은 경우, 기본적으로 `NWC/novel/markdown/` 디렉토리에 저장됩니다.

---

# 📝 사용법

터미널에서 다음 명령어를 실행하여 소설 번호를 입력받고, 해당 소설의 정보를 크롤링하여 Markdown 파일로 저장합니다.

```bash
python main.py
```

## 입력 예시

```bash
소설 번호를 입력하세요: 12345
```

## 🖼️ 출력 예시

### 1. 터미널

  ```
  [알림] 1 - 내가 쓰다 만 소설의 등장하지도 않는 성녀가 되어버렸다.md 파일을 썼어요.
  ```

### 2. 생성된 Markdown 파일

  ```markdown
  ---
    aliases:
    - (직접 적어 주세요)
      작가명: 십삼중수소
      링크: https://novelpia.com/novel/15597
      유입 경로: (직접 적어 주세요)
      tags:
    - 현대판타지
    - 판타지
    - 라이트노벨
    - 아카데미
    - TS
    - 착각
    - 노맨스
    - 연중성녀
      공개: 2021-05-02
      갱신: 2021-12-22
      완독: 0000-00-00
      완결: true
      연중(각): false
      성인: false
      무료: true
      독점: true
      챌린지: false
      회차: 7654
      알람: 878
      선호: 239
      추천: 123151
      조회: 1147258
    ---
    > [!TLDR] 시놉시스
    > 트럭에 치였더니 뜬금없이 내가 십대시절 혼자 히히덕거리며 끄적인 중2병 먼치킨 소설 속에 소환되었다. 여신의 부탁을 받고 떨어지긴 했는데... 앞이 막막하다.
  ```

[내가 쓰다 만 소설의 등장하지도 않는 성녀가 되어버렸다.md](https://github.com/user-attachments/files/16478359/default.md)

### 3. Obsidian 스크린샷

  ![Obsidian 스크린샷](https://github.com/user-attachments/assets/911b366d-2ad0-4e1f-baf5-835bb35ef280)

---

# 🔍 크롤링 정보 목록

크롤링하는 소설 정보는 다음과 같습니다:

- **기본 정보**
    - 제목
    - 작가명
    - 링크
    - 시놉시스
    - 태그

- **연재 정보**
    - 연재 일자
    - 연재 시작일
    - 최근(예정) 연재일
    - 연재 유형
        - 완결
        - 연습작품
        - 삭제
        - 연재중단
        - 연재지연
    - 작품 유형
        - 성인
        - 자유/PLUS
        - 독점
        - 챌린지

- **통계 정보**
    - 회차수
    - 알람수
    - 선호수
    - 조회수
    - 추천수
    - 인생픽 순위

---

# 🧪 단위 테스트

프로젝트는 단위 테스트를 지원하여 크롤링 기능의 안정성을 보장합니다. 테스트를 실행하려면 다음 명령어를 사용하세요.

```bash
python -m unittest discover tests
```

---

# 💡 구현 세부 사항

- **언어 및 라이브러리**
    - Python 3.x
    - `requests`: HTTP 요청을 보내기 위해 사용
    - `BeautifulSoup`: HTML 파싱을 위해 사용

- **크롤링 방식**
    - HTTP Client 방식 (Headless Browser 방식 미사용)
    - 노벨피아 공식 API만 호출, 비공식 API 사용 금지

---

# 🚧 주의 사항

- **환경 변수**: `.env` 파일에 `MARKDOWN_DIR`이 설정되지 않은 경우, 기본적으로 `NWC/novel/markdown/` 디렉토리에 파일이 저장됩니다.
- **API 사용**: 노벨피아의 공식 API만을 사용하며, 비공식 API는 사용하지 않습니다.
- **HTTP Client 방식**: Headless Browser 방식은 사용하지 않고, 단순한 HTTP 요청으로 데이터를 수집합니다.

---

# 🔗 관련 링크

- [노벨피아 웹사이트](https://novelpia.com)
- [Obsidian 공식 웹사이트](https://obsidian.md)

---

# 📄 라이선스

이 프로젝트는 [MIT 라이선스](LICENSE)를 따릅니다.

---

# 🛠️ 기여 방법

기여를 환영합니다! 버그 보고, 기능 요청, 풀 리퀘스트 등 모든 형태의 기여가 환영됩니다. 자세한 사항은 향후 추가 예정인 [CONTRIBUTING.md](CONTRIBUTING.md)를 참고해주세요.

---

# 📫 연락처

문의 사항이나 제안이 있으시면 [Issues](https://github.com/gaon-nuri/Novelpia-Web-Crawler/issues)로 남겨주세요.

---

# 📈 활동 현황

- **Stars**: 1
- **Forks**: 0
- **Watchers**: 1

---

© 2024 GitHub, Inc.

---
