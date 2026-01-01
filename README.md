# VOC 자동 처리 POC

고객의 소리(VOC)를 AI Agent가 자동으로 분석하고 해결안을 제시하는 시스템의 Proof of Concept입니다.

**POC 상태: 완료**

## 프로젝트 목적

이 POC는 다음 질문에 대한 검증을 목표로 합니다:

1. 자연어 VOC를 구조화하여 Ticket으로 자동 전환할 수 있는가?
2. Agent가 문제 유형을 분류하고 근거 기반 해결안을 제시할 수 있는가?
3. 관리자가 Agent 판단을 신뢰하고 승인할 수 있는가?
4. 승인 이후 Ticket 종료까지 흐름이 자연스러운가?

> **핵심 목표**: 기능 완성도가 아닌 **"신뢰 가능성 검증"**

## 시스템 아키텍처

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────────────┐
│  VOC 입력   │────▶│  정규화 Agent   │────▶│  Issue Solver Agent │
└─────────────┘     └─────────────────┘     └─────────────────────┘
                            │                          │
                            ▼                          ▼
                    ┌───────────────┐         ┌───────────────────┐
                    │ Ticket 생성   │────────▶│ 관리자 승인/거부  │
                    └───────────────┘         └───────────────────┘
```

## 주요 기능

### 1. VOC 정규화
- 자연어 VOC를 구조화된 데이터로 변환
- 문제 유형 추정 (연동 오류 / 코드 오류 / 개선 요청)
- 긴급도 판단 (high / medium / low)

### 2. Issue Solver Agent
- RAG 기반 로그 분석으로 문제 원인 파악
- 판단 근거와 제외 사유 명시
- 문제 유형별 해결안 제시
  - **integration_error**: 연동사 문의 메일 초안
  - **code_error**: 코드 수정 방향 제안
  - **business_improvement**: 개선 제안서

### 3. 신뢰도 기반 처리
- 신뢰도 60% 이상: 관리자 승인 대기
- 신뢰도 60% 미만: 수동 처리로 전환

### 4. Ticket 생명주기
```
OPEN → ANALYZING → WAITING_CONFIRM → DONE
                                   → REJECTED
                 → MANUAL_REQUIRED → DONE
```

### 5. Slack 알림
- 긴급 티켓 생성 시 실시간 알림
- 분석 완료 알림

## 기술 스택

### Backend
| 항목 | 기술 |
|------|------|
| 언어 | Python 3.11+ |
| 웹 프레임워크 | FastAPI |
| Agent 프레임워크 | LangChain + Tool Use |
| LLM | Ollama (로컬 LLM) |
| 벡터 DB | ChromaDB |
| 데이터베이스 | SQLite (async) |

### Frontend
| 항목 | 기술 |
|------|------|
| 프레임워크 | React 18+ |
| 빌드 도구 | Vite |
| 언어 | TypeScript |
| HTTP 클라이언트 | Axios |

### 인프라
| 항목 | 기술 |
|------|------|
| 알림 | Slack Webhook |
| 배포 | 로컬 개발 환경 (POC) |

## 프로젝트 구조

```
poc-voc-auto-processing/
├── docs/                          # 설계 문서
│   ├── 01-requirements/           # 요구사항 정의
│   ├── 02-domain/                 # 도메인 모델
│   ├── 03-agent/                  # Agent 명세
│   ├── 04-api/                    # API 명세
│   ├── 05-ui/                     # UI 설계
│   ├── 06-test/                   # 테스트 시나리오
│   │   ├── demo-scenarios.md      # POC 시연 시나리오
│   │   ├── e2e-scenarios.md       # E2E 테스트 시나리오
│   │   └── poc-results.md         # POC 결과 보고서
│   ├── 07-expansion/              # 확장 계획
│   │   └── expansion-plan.md      # 프로덕션 확장 계획
│   └── PROJECT_PLAN.md            # 프로젝트 계획
├── backend/                       # Backend 소스
│   ├── app/
│   │   ├── agents/               # AI Agent 구현
│   │   ├── models/               # 데이터 모델
│   │   ├── routers/              # API 라우터
│   │   ├── schemas/              # Pydantic 스키마
│   │   ├── services/             # 비즈니스 로직
│   │   ├── config.py             # 설정
│   │   └── main.py               # FastAPI 앱
│   ├── tests/                    # 테스트
│   ├── requirements.txt
│   └── .env                      # 환경 변수
├── frontend/                      # Frontend 소스
│   ├── src/
│   │   ├── components/           # React 컴포넌트
│   │   ├── pages/                # 페이지 컴포넌트
│   │   ├── services/             # API 서비스
│   │   └── types/                # TypeScript 타입
│   └── package.json
├── .gitignore
└── README.md
```

## 시작하기

### 사전 요구사항

- Python 3.11+
- Node.js 18+
- Ollama (로컬 LLM 실행용)

### 1. Ollama 설정

```bash
# Ollama 설치 (macOS)
brew install ollama

# Ollama 서비스 시작
ollama serve

# 모델 다운로드 (별도 터미널)
ollama pull qwen2.5:14b
```

### 2. Backend 설정

```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env  # 필요시 .env 파일 수정

# 서버 실행
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend 설정

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

### 4. 접속

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API 문서 (Swagger)**: http://localhost:8000/docs

## 테스트 실행

### Backend 테스트

```bash
cd backend
source .venv/bin/activate

# 전체 테스트
python -m pytest tests/ -v

# 커버리지 포함
python -m pytest tests/ -v --cov=app --cov-report=html

# 특정 테스트만
python -m pytest tests/test_e2e.py -v
python -m pytest tests/test_performance.py -v
```

### 테스트 결과

| 테스트 유형 | 테스트 수 | 커버리지 |
|------------|-----------|----------|
| 단위 테스트 | 40+ | - |
| 통합 테스트 | 20+ | - |
| E2E 테스트 | 16 | - |
| 성능 테스트 | 11 | - |
| **총계** | **89+** | **85.58%** |

## API 개요

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | /api/v1/voc | VOC 입력 및 Ticket 생성 |
| GET | /api/v1/tickets | Ticket 목록 조회 |
| GET | /api/v1/tickets/{id} | Ticket 상세 조회 |
| POST | /api/v1/tickets/{id}/analyze | 분석 시작 |
| POST | /api/v1/tickets/{id}/confirm | Ticket 승인 |
| POST | /api/v1/tickets/{id}/reject | Ticket 거부 |
| POST | /api/v1/tickets/{id}/complete | 수동 처리 완료 |
| GET | /health | 헬스체크 |

자세한 API 명세는 [docs/04-api/api-endpoints.md](docs/04-api/api-endpoints.md)를 참조하세요.

## 데모 시나리오

POC 시연을 위한 시나리오는 [docs/06-test/demo-scenarios.md](docs/06-test/demo-scenarios.md)를 참조하세요.

### 주요 시나리오

1. **연동사 오류**: 결제 API 타임아웃 VOC → 연동사 문의 메일 초안 생성
2. **코드 오류**: 환불 버튼 에러 VOC → 코드 수정 방향 제안
3. **비즈니스 개선**: UX 개선 요청 → 개선 제안서 생성
4. **관리자 거부**: Agent 판단 거부 및 사유 기록
5. **수동 처리**: 정규화 실패 시 수동 처리 흐름

## 문서

| 문서 | 설명 |
|------|------|
| [기능 요구사항](docs/01-requirements/functional-requirements.md) | 시스템 기능 정의 |
| [비기능 요구사항](docs/01-requirements/non-functional-requirements.md) | 성능, 제약사항, 기술 스택 |
| [데이터 모델](docs/02-domain/data-model.md) | Ticket 데이터 구조 |
| [Ticket 상태도](docs/02-domain/ticket-state-diagram.md) | 상태 전이 규칙 |
| [정규화 Agent 명세](docs/03-agent/normalizer-spec.md) | VOC 정규화 Agent 설계 |
| [Solver Agent 명세](docs/03-agent/solver-spec.md) | Issue Solver Agent 설계 |
| [화면 흐름도](docs/05-ui/screen-flow.md) | UI 설계 및 와이어프레임 |
| [POC 결과 보고서](docs/06-test/poc-results.md) | POC 검증 결과 |
| [확장 계획](docs/07-expansion/expansion-plan.md) | 프로덕션 확장 계획 |

## POC 결과

### 목표 달성 현황

| 기능 | 상태 |
|------|------|
| VOC 정규화 (LLM 기반) | 완료 |
| 문제 유형 분류 (3종) | 완료 |
| RAG 기반 로그 검색 | 완료 |
| 해결안 자동 생성 | 완료 |
| 관리자 승인 워크플로우 | 완료 |
| Slack 알림 연동 | 완료 |
| 웹 UI | 완료 |

### 성능

| 항목 | 목표 | 실측 |
|------|------|------|
| API 응답 시간 | 1초 이내 | 평균 50ms |
| Agent 처리 시간 | 60초 이내 | 30-50초 |
| 테스트 커버리지 | 70% 이상 | 85.58% |

자세한 결과는 [POC 결과 보고서](docs/06-test/poc-results.md)를 참조하세요.

## POC 범위 외

다음 기능은 POC에서 구현하지 않습니다:

- Jira 실제 연동 (인터페이스만 분리)
- 메일 실제 발송 (초안만 제시)
- MR 실제 생성 (제안만 제시)
- 로그인/인증
- 첨부파일 처리
- 모바일 반응형

확장 계획은 [확장 계획서](docs/07-expansion/expansion-plan.md)를 참조하세요.

## 라이선스

Internal Use Only - POC 프로젝트
