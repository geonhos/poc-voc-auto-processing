# 프로젝트 진행 계획

VOC 자동 처리 POC의 단계별 구현 계획을 정의합니다.

---

## Phase 개요

| Phase | 목표 | 주요 산출물 |
|-------|------|-------------|
| Phase 0 | 프로젝트 초기화 | 설계 문서, README |
| Phase 1 | Backend 기반 구축 | FastAPI 서버, DB 스키마, 기본 API |
| Phase 2 | 정규화 Agent 구현 | VOC → 구조화 데이터 변환 |
| Phase 2.5 | RAG 기반 지식 검색 구축 | Vector DB, 유사 VOC 검색, 해결 이력 활용 |
| Phase 3 | Issue Solver Agent 구현 | 문제 분석 및 해결안 제시 (RAG 활용) |
| Phase 4 | Frontend 구현 | React UI (VOC 입력, Ticket 목록/상세) |
| Phase 5 | 통합 및 E2E 테스트 | 전체 흐름 검증, Slack 알림 |
| Phase 6 | POC 검증 및 정리 | 시연, 결과 정리, 확장 계획 |

---

## Phase 0: 프로젝트 초기화 ✅

### 목표
프로젝트 기반 설정 및 설계 문서 완성

### 작업 항목
- [x] Git 저장소 초기화
- [x] 프로젝트 구조 설정
- [x] .gitignore 설정
- [x] 요구사항 정의서 작성 (기능/비기능)
- [x] 도메인 모델 정의 (데이터 모델, 상태 다이어그램)
- [x] Agent 명세서 작성 (정규화, Solver)
- [x] API 엔드포인트 설계
- [x] UI 화면 흐름 설계
- [x] README.md 작성

### 산출물
- `docs/` 하위 설계 문서 전체
- `README.md`

---

## Phase 1: Backend 기반 구축

### 목표
FastAPI 서버 구축 및 기본 CRUD API 구현

### 작업 항목

#### 1.1 프로젝트 설정
- [ ] Python 가상환경 설정
- [ ] FastAPI 프로젝트 구조 생성
- [ ] 의존성 정의 (requirements.txt)
- [ ] 환경 변수 설정 (.env)

#### 1.2 데이터베이스 설정
- [ ] SQLite 연결 설정
- [ ] SQLAlchemy 모델 정의 (Ticket)
- [ ] Alembic 마이그레이션 설정
- [ ] 초기 스키마 생성

#### 1.3 기본 API 구현
- [ ] `/health` 헬스체크 엔드포인트
- [ ] `POST /voc` VOC 입력 (Agent 연동 제외, 기본 Ticket 생성)
- [ ] `GET /tickets` Ticket 목록 조회
- [ ] `GET /tickets/{id}` Ticket 상세 조회
- [ ] `POST /tickets/{id}/confirm` Ticket 승인
- [ ] `POST /tickets/{id}/reject` Ticket 거부
- [ ] `POST /tickets/{id}/complete` 수동 처리 완료

#### 1.4 테스트
- [ ] pytest 설정
- [ ] API 단위 테스트 작성
- [ ] 상태 전이 로직 테스트

### 산출물
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   │   └── ticket.py
│   ├── schemas/
│   │   └── ticket.py
│   ├── routers/
│   │   ├── health.py
│   │   ├── voc.py
│   │   └── tickets.py
│   └── services/
│       └── ticket_service.py
├── tests/
├── alembic/
├── requirements.txt
└── .env.example
```

---

## Phase 2: 정규화 Agent 구현

### 목표
VOC 원문을 구조화된 데이터로 변환하는 Agent 구현

### 작업 항목

#### 2.1 LLM 연동 설정
- [ ] Ollama 로컬 설정 확인
- [ ] LangChain 설정
- [ ] LLM Provider 추상화 레이어 구현

#### 2.2 정규화 Agent 구현
- [ ] Agent 기본 구조 구현
- [ ] System/User Prompt 템플릿 작성
- [ ] 입력/출력 스키마 정의 (Pydantic)
- [ ] JSON 파싱 및 검증 로직

#### 2.3 정규화 로직
- [ ] 문제 유형 추정 로직 (integration_error / code_error / business_improvement)
- [ ] 긴급도 판단 로직 (high / medium / low)
- [ ] 영향 시스템 추출 로직
- [ ] 정규화 실패 처리 (MANUAL_REQUIRED)

#### 2.4 VOC API 연동
- [ ] `POST /voc` 엔드포인트에 정규화 Agent 연동
- [ ] 비동기 처리 (Ticket 생성 후 백그라운드 분석)
- [ ] Timeout 처리 (60초)

#### 2.5 테스트
- [ ] 정규화 Agent 단위 테스트
- [ ] 다양한 VOC 케이스 테스트 (성공/실패)

### 산출물
```
backend/app/
├── agents/
│   ├── __init__.py
│   ├── base.py
│   └── normalizer/
│       ├── __init__.py
│       ├── agent.py
│       ├── prompts.py
│       └── schemas.py
└── services/
    └── llm_service.py
```

---

## Phase 2.5: RAG 기반 지식 검색 구축

### 목표
과거 VOC 이력과 해결 사례를 검색하여 Agent 판단 품질 향상

### RAG 활용 시나리오

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   새 VOC 입력   │────▶│   유사 VOC 검색  │────▶│  해결 이력 참조 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │                         │
                               ▼                         ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │ 문제 유형 참고   │     │ 해결안 템플릿   │
                        └──────────────────┘     └─────────────────┘
```

### 작업 항목

#### 2.5.1 Vector Database 설정
- [ ] ChromaDB 설치 및 설정
- [ ] 임베딩 모델 선택 (sentence-transformers)
- [ ] Collection 스키마 설계

#### 2.5.2 VOC 임베딩 및 저장
- [ ] VOC 텍스트 임베딩 생성
- [ ] Ticket 완료 시 Vector DB에 저장
- [ ] 메타데이터 저장 (문제 유형, 해결 방법, 신뢰도 등)

#### 2.5.3 유사 VOC 검색 구현
- [ ] 유사도 검색 인터페이스 구현
- [ ] Top-K 유사 케이스 조회
- [ ] 검색 결과 필터링 (상태: DONE만, 신뢰도 임계값)

#### 2.5.4 해결 이력 활용
- [ ] 유사 케이스의 해결 방법 추출
- [ ] 문제 유형 분포 분석
- [ ] 성공적인 해결안 패턴 추출

#### 2.5.5 RAG Retriever 구현
- [ ] LangChain VectorStore Retriever 통합
- [ ] 검색 결과 포맷팅
- [ ] Agent Prompt에 컨텍스트 주입

#### 2.5.6 시드 데이터 구축
- [ ] 초기 VOC 샘플 데이터 생성 (10~20건)
- [ ] 해결 이력 포함한 완료 Ticket 데이터
- [ ] 다양한 문제 유형 커버

#### 2.5.7 테스트
- [ ] 임베딩 생성 테스트
- [ ] 유사도 검색 정확도 테스트
- [ ] 검색 성능 테스트 (응답 시간)

### 산출물
```
backend/app/
├── rag/
│   ├── __init__.py
│   ├── embeddings.py          # 임베딩 생성
│   ├── vector_store.py        # ChromaDB 연동
│   ├── retriever.py           # 검색 인터페이스
│   └── schemas.py             # RAG 관련 스키마
├── data/
│   ├── seed/                  # 시드 데이터
│   │   └── sample_vocs.json
│   └── chroma/                # Vector DB 저장소
└── services/
    └── rag_service.py         # RAG 서비스 레이어
```

### RAG 데이터 스키마

```python
class VocEmbeddingDocument:
    """Vector DB에 저장되는 VOC 문서"""
    ticket_id: str           # Ticket ID
    raw_voc: str             # VOC 원문
    summary: str             # 정규화된 요약
    problem_type: str        # 확정된 문제 유형
    resolution: str          # 해결 방법 요약
    action_proposal: dict    # 제안된 액션
    confidence: float        # 최종 신뢰도
    resolved_at: datetime    # 해결 일시
```

### 검색 파라미터

| 파라미터 | 기본값 | 설명 |
|----------|--------|------|
| top_k | 5 | 반환할 유사 케이스 수 |
| min_similarity | 0.7 | 최소 유사도 임계값 |
| filter_status | ["DONE"] | 필터링할 Ticket 상태 |
| min_confidence | 0.6 | 참조할 케이스의 최소 신뢰도 |

---

## Phase 3: Issue Solver Agent 구현

### 목표
Ticket을 분석하여 문제 유형 확정 및 해결안 제시

### 작업 항목

#### 3.1 Mock 로그 시스템
- [ ] Mock 로그 데이터 생성
- [ ] 로그 조회 인터페이스 구현
- [ ] 시나리오별 로그 패턴 정의

#### 3.2 Agent Tool 구현
- [ ] `get_logs` Tool 구현
- [ ] `analyze_error_patterns` Tool 구현
- [ ] `get_system_info` Tool 구현
- [ ] `search_similar_vocs` Tool 구현 (RAG 연동)

#### 3.3 Issue Solver Agent 구현
- [ ] Agent 기본 구조 (Tool Use 기반)
- [ ] System/User Prompt 템플릿
- [ ] 분석 프로세스 구현 (로그 수집 → 패턴 분석 → 유형 확정)

#### 3.4 RAG 기반 의사결정 지원
- [ ] 유사 VOC 검색 결과를 Agent 컨텍스트에 추가
- [ ] 과거 해결 사례 기반 해결안 추천
- [ ] 유사 케이스 신뢰도 가중치 적용
- [ ] 참조한 케이스 정보 decision_reason에 포함

#### 3.5 신뢰도 계산
- [ ] 신뢰도 계산 로직 구현
- [ ] 신뢰도 기반 상태 전이 (WAITING_CONFIRM / MANUAL_REQUIRED)
- [ ] RAG 유사 케이스 일치 시 신뢰도 보정

#### 3.6 해결안 생성
- [ ] integration_error: 연동사 문의 메일 초안 생성
- [ ] code_error: 코드 수정 방향 제안
- [ ] business_improvement: 개선 제안서 생성
- [ ] 유사 케이스의 해결안 템플릿 활용

#### 3.7 API 연동
- [ ] 정규화 완료 후 자동 Solver Agent 실행
- [ ] Ticket 상태 업데이트
- [ ] `POST /tickets/{id}/retry` 재분석 구현
- [ ] Ticket 완료 시 Vector DB에 해결 이력 저장

#### 3.8 테스트
- [ ] Solver Agent 단위 테스트
- [ ] Tool 동작 테스트
- [ ] RAG 검색 및 컨텍스트 주입 테스트
- [ ] 시나리오별 통합 테스트

### 산출물
```
backend/app/
├── agents/
│   └── solver/
│       ├── __init__.py
│       ├── agent.py
│       ├── prompts.py
│       ├── schemas.py
│       └── tools/
│           ├── get_logs.py
│           ├── analyze_patterns.py
│           ├── get_system_info.py
│           └── search_similar_vocs.py  # RAG 연동
└── mock/
    └── logs/
        ├── __init__.py
        ├── generator.py
        └── scenarios/
```

### RAG 활용 프로세스 (Phase 3)

```
┌─────────────────┐
│  새 VOC/Ticket  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────────┐
│  search_similar │────▶│  Vector DB 검색      │
│  _vocs Tool     │     │  (유사 케이스 5건)   │
└────────┬────────┘     └──────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  Agent Prompt에 유사 케이스 컨텍스트 추가   │
│  - 과거 문제 유형                           │
│  - 성공한 해결 방법                         │
│  - 관리자 승인된 케이스 우선                │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  Agent 분석 (로그 + RAG 컨텍스트 결합)      │
│  - 로그 기반 증거 수집                      │
│  - 유사 케이스 패턴 참조                    │
│  - 신뢰도 보정 (유사 케이스 일치 시 +0.1)   │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  해결안 생성                                │
│  - 유사 케이스 해결안 템플릿 활용           │
│  - decision_reason에 참조 케이스 명시       │
└─────────────────────────────────────────────┘
```

---

## Phase 4: Frontend 구현

### 목표
React 기반 관리자 UI 구현

### 작업 항목

#### 4.1 프로젝트 설정
- [ ] Vite + React + TypeScript 프로젝트 생성
- [ ] 의존성 설치 (React Router, Axios, etc.)
- [ ] 프로젝트 구조 설정

#### 4.2 공통 컴포넌트
- [ ] Layout (Header, Navigation)
- [ ] 상태 Badge 컴포넌트
- [ ] 긴급도 표시 컴포넌트
- [ ] 로딩/에러 상태 컴포넌트

#### 4.3 VOC 입력 화면 (`/voc/new`)
- [ ] VOC 입력 폼 구현
- [ ] 폼 유효성 검증
- [ ] API 연동 (POST /voc)
- [ ] 성공 시 Ticket 상세로 이동

#### 4.4 Ticket 목록 화면 (`/tickets`)
- [ ] Ticket 목록 표시
- [ ] 상태별 필터링
- [ ] 긴급도별 정렬
- [ ] 페이지네이션
- [ ] API 연동 (GET /tickets)

#### 4.5 Ticket 상세 화면 (`/tickets/:id`)
- [ ] VOC 원문 표시
- [ ] 정규화 결과 표시
- [ ] Agent 분석 결과 표시 (판단 근거, 제외 사유)
- [ ] 해결안 표시 (유형별)
- [ ] 관리자 액션 버튼 (승인/거부/재분석)
- [ ] 거부 사유 모달
- [ ] 수동 처리 완료 폼 (MANUAL_REQUIRED)
- [ ] 상태별 화면 분기

#### 4.6 상태 폴링
- [ ] ANALYZING 상태에서 자동 새로고침
- [ ] 분석 완료 시 UI 갱신

#### 4.7 테스트
- [ ] 컴포넌트 단위 테스트
- [ ] 화면 통합 테스트

### 산출물
```
frontend/
├── src/
│   ├── components/
│   │   ├── common/
│   │   ├── ticket/
│   │   └── voc/
│   ├── pages/
│   │   ├── VocInputPage.tsx
│   │   ├── TicketListPage.tsx
│   │   └── TicketDetailPage.tsx
│   ├── hooks/
│   ├── services/
│   │   └── api.ts
│   ├── types/
│   └── App.tsx
├── package.json
└── vite.config.ts
```

---

## Phase 5: 통합 및 E2E 테스트

### 목표
전체 시스템 통합 및 End-to-End 테스트

### 작업 항목

#### 5.1 Slack 알림 연동
- [ ] Slack Webhook 설정
- [ ] 긴급 Ticket 알림 구현 (urgency: high)
- [ ] 알림 테스트

#### 5.2 E2E 테스트
- [ ] 정상 흐름 테스트 (VOC 입력 → 분석 → 승인 → 완료)
- [ ] 예외 흐름 테스트 (정규화 실패, 낮은 신뢰도)
- [ ] 거부 흐름 테스트
- [ ] 재분석 흐름 테스트
- [ ] 수동 처리 흐름 테스트

#### 5.3 성능 테스트
- [ ] Agent 응답 시간 측정 (60초 이내 확인)
- [ ] API 응답 시간 측정 (1초 이내)
- [ ] UI 로딩 시간 측정 (3초 이내)

#### 5.4 버그 수정 및 안정화
- [ ] 발견된 버그 수정
- [ ] 에러 핸들링 보완
- [ ] 로깅 추가

### 산출물
- E2E 테스트 리포트
- 성능 측정 결과
- 버그 수정 목록

---

## Phase 6: POC 검증 및 정리

### 목표
POC 결과 정리 및 확장 계획 수립

### 작업 항목

#### 6.1 POC 시연
- [ ] 시연 시나리오 준비
- [ ] 데모 데이터 준비
- [ ] 시연 진행

#### 6.2 결과 정리
- [ ] POC 목표 달성 여부 검토
  - 자연어 VOC → Ticket 자동 전환 가능 여부
  - Agent 문제 분류 및 해결안 제시 품질
  - 관리자 신뢰 가능성
  - 전체 흐름 자연스러움
- [ ] 한계점 및 개선점 정리
- [ ] 기술적 이슈 정리

#### 6.3 확장 계획
- [ ] Jira 연동 계획
- [ ] 실제 로그 시스템 연동 계획
- [ ] 메일/MR 자동화 계획
- [ ] 인증/인가 추가 계획
- [ ] 확장 시 아키텍처 변경 사항

#### 6.4 문서 정리
- [ ] 최종 README 업데이트
- [ ] 설치 및 실행 가이드 정리
- [ ] 코드 정리 및 주석 추가

### 산출물
- POC 결과 보고서
- 확장 계획서
- 최종 코드 및 문서

---

## 의존성 관계

```
Phase 0 (완료)
    │
    ▼
Phase 1 (Backend 기반)
    │
    ├────────────────────────────────┐
    ▼                                ▼
Phase 2 (정규화 Agent)            Phase 4 (Frontend - 병렬 가능)
    │                                │
    ▼                                │
Phase 2.5 (RAG 지식 검색)           │
    │                                │
    ▼                                │
Phase 3 (Solver Agent + RAG)        │
    │                                │
    └───────────────┬────────────────┘
                    ▼
              Phase 5 (통합 테스트)
                    │
                    ▼
              Phase 6 (검증 및 정리)
```

### 병렬 작업 가능 영역
- Phase 2 + Phase 4: 정규화 Agent와 Frontend 동시 진행 가능
- Phase 2.5는 Phase 2 완료 후 시작 (완료된 Ticket 데이터 필요)

---

## 리스크 및 대응

| 리스크 | 영향도 | 대응 방안 |
|--------|--------|-----------|
| LLM 응답 품질 불안정 | 높음 | 프롬프트 튜닝, Fallback 처리 |
| Agent 응답 시간 초과 | 중간 | Timeout 처리, 비동기 처리 |
| 신뢰도 계산 정확도 | 중간 | 기준 조정, 수동 검토 케이스 분석 |
| Mock 로그 다양성 부족 | 낮음 | 시나리오 추가, 실제 로그 패턴 참고 |
| RAG 검색 정확도 낮음 | 중간 | 임베딩 모델 교체, 유사도 임계값 조정 |
| RAG 시드 데이터 부족 | 중간 | 다양한 문제 유형 커버하는 샘플 데이터 추가 |
| Vector DB 성능 이슈 | 낮음 | 인덱스 최적화, 검색 결과 캐싱 |

---

## 기술 부채 관리

### Phase별 허용 가능한 기술 부채

| Phase | 허용 범위 | 해결 시점 |
|-------|-----------|-----------|
| Phase 1-3 | 테스트 커버리지 60% | Phase 5 |
| Phase 4 | 반응형 미지원 | POC 범위 외 |
| Phase 1-5 | 에러 핸들링 최소화 | Phase 5 |
| 전체 | 인증/인가 미구현 | POC 범위 외 |

---

## 체크포인트

### Phase 1 완료 기준
- [ ] Backend 서버 실행 가능
- [ ] 기본 CRUD API 동작
- [ ] 단위 테스트 통과

### Phase 2 완료 기준
- [ ] VOC 입력 시 정규화 동작
- [ ] 정규화 실패 시 MANUAL_REQUIRED 전환
- [ ] 성공/실패 케이스 테스트 통과

### Phase 2.5 완료 기준
- [ ] Vector DB 설정 및 연결 완료
- [ ] VOC 임베딩 생성 및 저장 동작
- [ ] 유사 VOC 검색 동작 (Top-5)
- [ ] 시드 데이터 10건 이상 구축
- [ ] 검색 정확도 테스트 통과

### Phase 3 완료 기준
- [ ] Solver Agent가 로그 분석 수행
- [ ] RAG 기반 유사 케이스 검색 동작
- [ ] 신뢰도 기반 상태 전이 동작
- [ ] 해결안 생성 확인 (유사 케이스 참조 포함)

### Phase 4 완료 기준
- [ ] 3개 화면 모두 동작
- [ ] API 연동 완료
- [ ] 관리자 액션 동작

### Phase 5 완료 기준
- [ ] E2E 시나리오 전체 통과
- [ ] Slack 알림 동작
- [ ] 성능 요구사항 충족

### Phase 6 완료 기준
- [ ] 시연 완료
- [ ] 결과 보고서 작성
- [ ] 문서 정리 완료
