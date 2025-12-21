# VOC 자동 처리 POC

고객의 소리(VOC)를 AI Agent가 자동으로 분석하고 해결안을 제시하는 시스템의 Proof of Concept입니다.

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
- 로그 분석 기반 문제 원인 파악
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

## 기술 스택

### Backend
| 항목 | 기술 |
|------|------|
| 언어 | Python 3.11+ |
| 웹 프레임워크 | FastAPI |
| Agent 프레임워크 | LangChain + Tool Use |
| LLM | Ollama (gpt-oss:20b) |
| 데이터베이스 | SQLite |

### Frontend
| 항목 | 기술 |
|------|------|
| 프레임워크 | React 18+ |
| 빌드 도구 | Vite |
| 언어 | TypeScript |

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
│   │   ├── functional-requirements.md
│   │   ├── non-functional-requirements.md
│   │   └── glossary.md
│   ├── 02-domain/                 # 도메인 모델
│   │   ├── ticket-state-diagram.md
│   │   ├── problem-type-taxonomy.md
│   │   └── data-model.md
│   ├── 03-agent/                  # Agent 명세
│   │   ├── normalizer-spec.md
│   │   ├── solver-spec.md
│   │   ├── confidence-criteria.md
│   │   └── mock-log-scenarios.md
│   ├── 04-api/                    # API 명세
│   │   ├── api-endpoints.md
│   │   └── schemas.md
│   ├── 05-ui/                     # UI 설계
│   │   ├── screen-flow.md
│   │   └── wireframes.md
│   └── 06-test/                   # 테스트 시나리오
│       └── e2e-scenarios.md
├── backend/                       # Backend 소스 (구현 예정)
├── frontend/                      # Frontend 소스 (구현 예정)
├── .gitignore
└── README.md
```

## 시작하기

### 사전 요구사항
- Python 3.11+
- Node.js 18+
- Ollama (로컬 LLM 실행용)

### Backend 설정

```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
uvicorn main:app --reload
```

### Frontend 설정

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

### Ollama 설정

```bash
# Ollama 설치 후
ollama pull gpt-oss:20b
```

## API 개요

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | /api/v1/voc | VOC 입력 및 Ticket 생성 |
| GET | /api/v1/tickets | Ticket 목록 조회 |
| GET | /api/v1/tickets/{id} | Ticket 상세 조회 |
| POST | /api/v1/tickets/{id}/confirm | Ticket 승인 |
| POST | /api/v1/tickets/{id}/reject | Ticket 거부 |
| POST | /api/v1/tickets/{id}/retry | 재분석 요청 |
| POST | /api/v1/tickets/{id}/complete | 수동 처리 완료 |

자세한 API 명세는 [docs/04-api/api-endpoints.md](docs/04-api/api-endpoints.md)를 참조하세요.

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

## POC 범위 외

다음 기능은 POC에서 구현하지 않습니다:

- Jira 실제 연동 (인터페이스만 분리)
- 메일 실제 발송 (초안만 제시)
- MR 실제 생성 (제안만 제시)
- 로그인/인증
- 첨부파일 처리
- 모바일 반응형

## 라이선스

Internal Use Only - POC 프로젝트
