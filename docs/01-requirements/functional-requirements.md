# 기능 요구사항 정의서

## 1. 개요

### 1.1 문서 목적
VOC 자동 처리 POC의 기능 요구사항을 정의한다.

### 1.2 POC 목적
- 자연어 VOC를 구조화하여 Ticket으로 자동 전환할 수 있는가
- Agent가 문제 유형을 분류하고 근거 기반 해결안을 제시할 수 있는가
- 관리자가 Agent 판단을 신뢰하고 승인할 수 있는가
- 승인 이후 Ticket 종료까지 흐름이 자연스러운가

> 본 POC는 기능 완성도가 아니라 **"신뢰 가능성 검증"**에 목적을 둔다.

---

## 2. 기능 요구사항

### 2.1 VOC 입력 (FR-001)

| 항목 | 내용 |
|------|------|
| 우선순위 | 필수 |
| 설명 | 사용자가 VOC를 시스템에 입력할 수 있다 |

#### 입력 필드

| 필드명 | 타입 | 필수 여부 | 설명 |
|--------|------|-----------|------|
| raw_voc | text | 필수 | VOC 원문 (자연어 텍스트) |
| customer_name | string | 필수 | 고객명 |
| channel | enum | 필수 | 접수 채널 (email / slack) |
| received_at | datetime | 필수 | VOC 접수일시 |

#### 제약사항
- 첨부파일은 POC 범위에서 제외
- 로그인/인증 없이 접근 가능 (POC 한정)

---

### 2.2 VOC 정규화 (FR-002)

| 항목 | 내용 |
|------|------|
| 우선순위 | 필수 |
| 설명 | 정규화 Agent가 자연어 VOC를 구조화된 데이터로 변환한다 |

#### 정규화 출력 필드

| 필드명 | 타입 | 설명 |
|--------|------|------|
| summary | string | 문제 요약 (1~2문장) |
| suspected_type | object | 문제 유형 추정 (primary/secondary) |
| affected_system | string | 영향 시스템 |
| urgency | enum | 긴급도 (low / medium / high) |

#### 정규화 실패 처리
- 해석 불가능한 VOC는 `MANUAL_REQUIRED` 상태로 Ticket 생성
- 원문(raw_voc)은 그대로 보존

---

### 2.3 Ticket 생성 (FR-003)

| 항목 | 내용 |
|------|------|
| 우선순위 | 필수 |
| 설명 | 정규화 완료 후 Ticket이 자동 생성된다 |

#### 정책
- VOC 1건 = Ticket 1건
- 생성 시 상태: `OPEN`
- ticket_id는 시스템 자동 생성

---

### 2.4 Issue Solver Agent 분석 (FR-004)

| 항목 | 내용 |
|------|------|
| 우선순위 | 필수 |
| 설명 | Agent가 Ticket을 분석하여 문제 유형, 판단 근거, 해결안을 제시한다 |

#### 분석 프로세스
1. 로그 분석 (Mock 데이터 기반)
2. 에러 패턴 매칭
3. 도메인 룰 기반 분기
4. 판단 결과 및 근거 생성

#### 출력 필드

| 필드명 | 타입 | 설명 |
|--------|------|------|
| agent_decision | object | 최종 판단 유형 (primary/secondary) |
| decision_confidence | float | 판단 신뢰도 (0.0 ~ 1.0) |
| decision_reason | object | 판단 근거 (summary, evidence, ruled_out) |
| action_proposal | object | 제안 액션 (유형별 상이) |

---

### 2.5 신뢰도 기반 Fallback (FR-005)

| 항목 | 내용 |
|------|------|
| 우선순위 | 필수 |
| 설명 | Agent 신뢰도가 낮을 경우 수동 분석으로 전환한다 |

#### 트리거 조건
- `decision_confidence < 0.6`

#### 처리
- Ticket 상태를 `MANUAL_REQUIRED`로 변경
- 추가 정보 필요 표시

---

### 2.6 Ticket 목록 조회 (FR-006)

| 항목 | 내용 |
|------|------|
| 우선순위 | 필수 |
| 설명 | 관리자가 Ticket 목록을 조회할 수 있다 |

#### 기능
- 상태별 필터링 (OPEN, ANALYZING, WAITING_CONFIRM, DONE, MANUAL_REQUIRED, REJECTED)
- 긴급도별 정렬
- Ticket 상세 페이지로 이동

---

### 2.7 Ticket 상세 조회 (FR-007)

| 항목 | 내용 |
|------|------|
| 우선순위 | 필수 |
| 설명 | 관리자가 Ticket 상세 정보와 Agent 분석 결과를 확인할 수 있다 |

#### 표시 정보
- VOC 원문
- 정규화 결과 (summary, suspected_type, urgency 등)
- Agent 판단 결과 및 신뢰도
- 판단 근거 (evidence, ruled_out)
- 제안 액션

---

### 2.8 관리자 Confirm/Reject (FR-008)

| 항목 | 내용 |
|------|------|
| 우선순위 | 필수 |
| 설명 | 관리자가 Agent 판단을 승인하거나 거부할 수 있다 |

#### 액션

| 액션 | 설명 | 상태 변경 |
|------|------|-----------|
| Approve | Agent 판단 승인 | WAITING_CONFIRM → DONE |
| Reject | VOC 자체 거부 (사유 필수) | WAITING_CONFIRM → REJECTED |
| Retry | 재분석 요청 | WAITING_CONFIRM → ANALYZING |

---

### 2.9 수동 처리 완료 (FR-009)

| 항목 | 내용 |
|------|------|
| 우선순위 | 필수 |
| 설명 | MANUAL_REQUIRED 상태의 Ticket을 수동 처리 후 종료할 수 있다 |

#### 처리
- 관리자가 수동으로 처리 결과 입력
- 상태: `MANUAL_REQUIRED → DONE`

---

### 2.10 긴급 Ticket Slack 알림 (FR-010)

| 항목 | 내용 |
|------|------|
| 우선순위 | 필수 |
| 설명 | 긴급도가 높은 Ticket 생성 시 Slack으로 알림을 발송한다 |

#### 트리거 조건
- `urgency: high`

#### 알림 내용
- ticket_id
- summary
- urgency

---

## 3. POC 범위 외 기능

다음 기능은 POC에서 수행하지 않는다:

| 기능 | 비고 |
|------|------|
| Jira 실제 연동 | 인터페이스만 분리 |
| 메일 실제 발송 | 초안만 제시 |
| MR 실제 생성 | 제안만 제시 |
| 로그인/인증 | POC에서 생략 |
| 첨부파일 처리 | POC에서 제외 |

---

## 4. 기능 우선순위 요약

| 우선순위 | 기능 |
|----------|------|
| 필수 | FR-001 ~ FR-010 전체 |
| 선택 | 해당 없음 (POC 범위 최소화) |
