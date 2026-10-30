# Simple Chat bot — 그럴깡 상담톡

카카오톡처럼 생긴 모바일 채팅 앱 형태의 AI 챗봇이에요. 한국경제아카데미 UXUI·PM 부트캠프 매니저 **그럴깡**, 날씨 도우미 **하늘깡**, 합성 페르소나 데이터로 만든 **친구 5명**과 대화할 수 있어요.

- **frontend/**: 화면 (HTML · CSS · JavaScript 모듈)
- **backend/**: 파이썬 API 서버 (Starlette). AI 호출, 프롬프트, 맛집 검색, 날씨, DB를 담당해요.
- API 키는 서버의 `backend/.env`에만 있어요. 브라우저로는 전달되지 않아요.

## 실행 방법

```bash
cd "Simple Chat bot/backend"
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # .env를 열어 GROQ_API_KEY 또는 GEMINI_API_KEY 입력
python main.py
```

브라우저에서 **http://127.0.0.1:8000** 을 열면 돼요. 서버가 화면(frontend/)까지 함께 보여 줘요.

- Groq 키: https://console.groq.com/keys (`gsk_`로 시작)
- Gemini 키: https://aistudio.google.com/apikey (복사한 키 전체)
- 처음 실행하면 `backend/app.db`(SQLite)가 만들어지고 식당 664곳과 페르소나 5명이 들어가요.

## 폴더 구성

```
Simple Chat bot/
├── backend/
│   ├── main.py               # 앱 실행 및 설정 (서비스 조립, /api 라우트, 화면 파일 제공)
│   ├── config.py             # 환경 변수(.env) 읽기
│   ├── requirements.txt
│   ├── .env.example          # 키 입력 양식 (.env는 GitHub에 올라가지 않음)
│   ├── routers/              # API 요청과 응답 처리
│   │   ├── chat.py           #   POST /api/chat        AI 답변 스트리밍
│   │   ├── rooms.py          #   GET  /api/rooms, /api/health
│   │   ├── places.py         #   GET  /api/places/search
│   │   ├── weather.py        #   GET  /api/weather
│   │   └── common.py         #   공통 응답·오류 형식
│   ├── services/             # 실제 비즈니스 로직
│   │   ├── chat_service.py   #   방 확인 → 맛집·날씨 정보 붙이기 → 프롬프트 → AI
│   │   ├── llm_service.py    #   Groq·Gemini 스트리밍 호출, 오류 정리
│   │   ├── prompt_service.py #   knowledge/ 문서로 시스템 프롬프트 만들기
│   │   ├── place_service.py  #   질문에 맞는 식당 검색 (메뉴·가격·평점·거리)
│   │   ├── weather_service.py#   지역·날짜 찾기, Open-Meteo 예보 요약, 옷차림·우산
│   │   └── room_service.py   #   채팅방 목록
│   ├── repositories/         # 데이터베이스 접근
│   │   ├── db.py             #   연결, 테이블 생성, 처음 데이터 넣기
│   │   ├── place_repository.py
│   │   └── persona_repository.py
│   ├── models/
│   │   └── tables.py         # DB 테이블 구조 (places, personas)
│   ├── schemas/              # 요청·응답 데이터 형식 (pydantic)
│   │   ├── chat.py  room.py  place.py  weather.py
│   ├── knowledge/            # 프롬프트 문서 (부트캠프 정보, 맛집 메모, 캐릭터별 지침)
│   ├── data/                 # 처음 DB에 넣는 원본 (카카오맵 식당 TSV, 페르소나 JSON)
│   ├── scripts/minipq.py     # 페르소나 원본 parquet을 읽을 때 쓴 도구
│   └── tests/                # 자동화 테스트 (가짜 AI·가짜 날씨로 실행)
├── frontend/
│   ├── index.html
│   ├── css/                  # base(색·레이아웃) · chat · list · sheet
│   └── js/
│       ├── main.js           # 시작점
│       ├── api/client.js     # 백엔드 호출, 스트리밍 받기
│       ├── core/             # dom 도구, 상태, 브라우저 저장소
│       ├── ui/               # 채팅방 목록, 말풍선, 입력, 설정, 아바타
│       └── effects/          # 테마, 패럴랙스 배경, 오버스크롤, 빠른 질문 스크롤
└── standalone.html           # 서버 없이 한 파일로 도는 예전 버전 (키를 브라우저에 입력)
```

## API

| 메서드 | 주소 | 설명 |
|---|---|---|
| GET | `/api/health` | 서버 상태, 키가 설정된 AI 서비스와 모델 목록 (키 값은 보내지 않음) |
| GET | `/api/rooms` | 채팅방 7개 정보 |
| POST | `/api/chat` | `{room_id, messages, provider?, model?, notes?}` → 답변을 `text/plain`으로 흘려보냄 |
| GET | `/api/places/search?q=만원 이하 점심` | 교육장 근처 식당 검색 |
| GET | `/api/weather?q=내일 부산` | 하늘깡이 쓰는 날씨 요약 |

오류는 `{"error": "...", "code": "..."}` 형식이에요. 예: 키 없음 503 `no_provider`, 잘못된 키 401 `bad_key`, 한도 초과 429 `rate_limited`, 형식 오류 422.

## 테스트

```bash
cd "Simple Chat bot/backend"
python -m unittest discover -s tests -v
```

실제 AI·날씨 서버 대신 가짜를 넣어서, 키나 인터넷 없이 28개 테스트가 돌아가요.

## API 키 보안

- 키는 `backend/.env`에만 넣어요. `.gitignore`에 들어 있어서 GitHub에 올라가지 않아요.
- 화면은 AI 서비스에 직접 연결하지 않고 항상 이 서버를 거쳐요. 키는 브라우저에 저장되지도, 응답에 담기지도 않아요.
- 예전 한 파일 버전(standalone.html)을 쓰던 브라우저에 남은 키는 새 화면이 열릴 때 지워져요.

## API 키가 GitHub에 올라가지 않게 막는 장치

1. **`.gitignore`**: `.env` 파일은 `git add`를 해도 아예 올라가지 않아요.
2. **커밋 전 검사 (내 컴퓨터)**: 저장소를 받은 뒤 한 번만 아래 명령을 실행해 두세요. 커밋하려는 파일에 키처럼 보이는 값(`gsk_…`, `AIza…` 등)이나 `.env` 파일이 있으면 커밋을 멈추고 경고해요.
   ```bash
   git config core.hooksPath .githooks
   ```
3. **올라간 뒤 검사 (GitHub)**: push하거나 웹에서 파일을 올릴 때마다 GitHub Actions의 **API 키 검사**가 돌아요. 키가 보이면 빨간 X로 실패하고 이메일로 알려 줘요.

경고가 뜨면 키를 지우고 다시 커밋하세요. 이미 GitHub에 올라갔다면 지워도 기록에 남으니, 그 키는 바로 삭제하고 새로 발급받아야 해요.

## 대화 상대

| 이름 | 역할 | 특징 |
|---|---|---|
| 그럴깡 | 부트캠프 매니저 (AI 챗봇) | 6기·7기 과정 정보, 교육장 근처 맛집, 일상 대화 |
| 하늘깡 | 날씨 도우미 (AI 챗봇) | 지역·날짜별 예보, 옷차림·우산 추천 |
| 이지아 | 39세, 마포구청 주무관 | 문화예술 기획자로 커리어 전환을 꿈꿈 |
| 박승범 | 38세, 세온어패럴 품질관리팀 대리 | 아이 아빠, 주말 드라이브 |
| 박한솔 | 29세, 루미에르랩 뷰티 어드바이저 | 성수동 트렌드, 소금빵 |
| 최선동 | 27세, 구직 중 (전 개발 PM) | 전자책 UX에 진지함, UX 쪽 진로 고민 |
| 박윤아 | 41세, 마켓그린 리테일마케팅팀 팀장 | 매장 데이터 분석, 창업 준비 |

페르소나 5명은 AI 대화 상대예요. 진지하게 "AI야?"라고 물으면 솔직하게 답해요. 회사 이름은 마포구청을 빼면 모두 가상이에요.

## 주요 기능

**채팅 화면**
- 카카오톡 스타일 말풍선, 읽음 표시(노란 1), 날짜 구분선
- AI 답변을 문단마다 말풍선으로 나눠 실시간으로 보여 줌
- 채팅 목록, 친구 탭, 프로필 화면, 뒤로가기(브라우저 뒤로가기 포함)
- 채팅방별 안 읽은 메시지 배지, 마지막 메시지 미리보기
- 펼쳐지는 공지, 좌우로 스크롤되는 빠른 질문 버튼

**디자인**
- 라이트·다크 모드 전환 (기기 설정을 따르고, 고른 모드는 저장)
- 배경: 다크 모드는 반짝이는 행성, 라이트 모드는 떠다니는 꽃
- 스크롤보다 느리게 움직이는 패럴랙스 배경
- 채팅 목록 글라스 효과
- 오버스크롤, 러버 밴드, 스트레치, 바운스 효과 (빠른 질문 목록은 더 약하게)
- 휴대폰 터치, 트랙패드, 마우스 휠, 마우스 드래그 모두 지원
- 기기의 "동작 줄이기" 설정을 켜면 움직임 효과가 꺼짐

**정보**
- 부트캠프 6기·7기 공식 정보 (일정, 자부담금, 커리큘럼, 혜택, 문의처)
- 교육장(양평역) 반경 800m 식당·카페 664곳의 카카오맵 평점과 메뉴 가격, 질문에 맞는 가게만 골라 추천
- Open-Meteo 날씨 예보 (API 키 불필요), 전국 약 90개 지역

## 데이터 출처

- 부트캠프 정보: 한경닷컴 IT교육센터 공식 과정 페이지 (2026년 10월 27일 확인)
- 식당 정보: 카카오맵 (2026년 10월 27일 수집). 평점·메뉴·가격은 바뀔 수 있어요.
- 페르소나 5명(이지아·박승범·박한솔·최선동·박윤아): **NVIDIA Corporation**이 제작한 [Nemotron-Personas-Korea](https://huggingface.co/datasets/nvidia/Nemotron-Personas-Korea)에서 선별하고 챗봇용으로 가공했어요. 원본 데이터셋은 [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)로 제공됩니다. 회사·말투·인사·화면 표시 등 프로젝트에서 추가·변경한 설정이 있으며, 적용 파일과 가공 내역은 [출처 및 라이선스 고지](../THIRD_PARTY_NOTICES.md)를 확인하세요.
- 날씨: Open-Meteo 예보 API

## 업데이트 기록

1. Groq API로 대화하는 카카오톡 스타일 챗봇 그럴깡 제작, 키 입력·저장 화면
2. 키 확인 대기 시간 제한, 연결이 막힌 환경 안내, 설정 창 닫기 버그 수정
3. 부트캠프 6기·7기 공식 정보 추가
4. 교육장 근처 맛집 정보 추가 → 카카오맵 664곳의 평점·메뉴 가격으로 확장
5. 공지 펼치기, 라이트·다크 모드, 행성·꽃 패럴랙스 배경
6. 채팅 목록, 친구 탭, 프로필, 뒤로가기
7. 노트북 정보를 "대여 후 반납"으로 정정
8. 합성 페르소나 5명 추가, 회사 설정 추가
9. 오버스크롤·러버 밴드·스트레치·바운스 효과 (이후 바운스 약화)
10. 그럴깡·페르소나 일상 대화 허용
11. 당길 때 틈 채우기, 글라스 효과, 헤더 구분선 정리
12. 빠른 질문 좌우 스크롤 + 약한 러버 밴드
13. 날씨 도우미 하늘깡 추가 (Open-Meteo)
14. 글자 선택이 배경 클릭으로 해제되지 않던 문제 수정
15. Gemini API 지원 추가 (Groq·Gemini 선택)
16. 백엔드(routers·services·repositories·models·schemas·tests) 분리, 화면을 css·js 폴더로 분리, API 키를 서버로 이동
17. API 키 유출 경고 장치 추가 (.gitignore, 커밋 전 검사, GitHub Actions 검사)
