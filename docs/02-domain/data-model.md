# 데이터 모델 정의

## 1. 개요

VOC 자동 처리 시스템의 데이터 모델을 정의한다.

---

## 2. Ticket 모델

### 2.1 전체 필드 정의

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| ticket_id | string | O | Ticket 고유 식별자 (시스템 생성) |
| status | enum | O | 현재 상태 |
| created_at | datetime | O | 생성일시 |
| updated_at | datetime | O | 최종 수정일시 |
| assignee | string | X | 담당 관리자 |

#### VOC 입력 정보

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| raw_voc | text | O | VOC 원문 |
| customer_name | string | O | 고객명 |
| channel | enum | O | 접수 채널 (email / slack) |
| received_at | datetime | O | VOC 접수일시 |

#### 정규화 결과

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| summary | string | O | 문제 요약 |
| suspected_type | object | O | 추정 문제 유형 |
| affected_system | string | O | 영향 시스템 |
| urgency | enum | O | 긴급도 (low / medium / high) |

#### Agent 분석 결과

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| agent_decision | object | X | Agent 최종 판단 유형 |
| decision_confidence | float | X | 판단 신뢰도 (0.0 ~ 1.0) |
| decision_reason | object | X | 판단 근거 |
| action_proposal | object | X | 제안 액션 |
| analyzed_at | datetime | X | 분석 완료일시 |

#### 관리자 처리 정보

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| confirmed_at | datetime | X | 승인/거부 일시 |
| reject_reason | string | X | 거부 사유 (REJECTED 시 필수) |
| manual_resolution | string | X | 수동 처리 결과 (MANUAL_REQUIRED → DONE 시) |

---

## 3. 상세 타입 정의

### 3.1 status (Ticket 상태)

```typescript
enum TicketStatus {
  OPEN = "OPEN",
  ANALYZING = "ANALYZING",
  WAITING_CONFIRM = "WAITING_CONFIRM",
  DONE = "DONE",
  MANUAL_REQUIRED = "MANUAL_REQUIRED",
  REJECTED = "REJECTED"
}
```

### 3.2 channel (접수 채널)

```typescript
enum Channel {
  EMAIL = "email",
  SLACK = "slack"
}
```

### 3.3 urgency (긴급도)

```typescript
enum Urgency {
  LOW = "low",
  MEDIUM = "medium",
  HIGH = "high"
}
```

### 3.4 suspected_type / agent_decision (문제 유형)

```typescript
interface ProblemType {
  primary_type: "integration_error" | "code_error" | "business_improvement";
  secondary_type: "integration_error" | "code_error" | "business_improvement" | null;
}
```

### 3.5 decision_reason (판단 근거)

```typescript
interface DecisionReason {
  summary: string;           // 1문장 요약
  evidence: string[];        // 판단 근거 목록
  ruled_out: string[];       // 제외된 가능성 목록
}
```

### 3.6 action_proposal (제안 액션)

#### integration_error 유형

```typescript
interface IntegrationInquiryAction {
  action_type: "integration_inquiry";
  target_system: string;
  contact_info: string;
  email_draft: {
    subject: string;
    body: string;
  };
}
```

#### code_error 유형

```typescript
interface CodeFixAction {
  action_type: "code_fix";
  affected_files: string[];
  error_summary: string;
  fix_direction: string;
  suggested_approach: string;
  severity: "low" | "medium" | "high" | "critical";
}
```

#### business_improvement 유형

```typescript
interface BusinessProposalAction {
  action_type: "business_proposal";
  category: string;
  problem_pattern: string;
  proposal: string;
  expected_impact: string;
  stakeholders: string[];
}
```

---

## 4. SQLite 테이블 스키마

```sql
CREATE TABLE tickets (
    -- 기본 정보
    ticket_id TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'OPEN',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    assignee TEXT,

    -- VOC 입력 정보
    raw_voc TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    channel TEXT NOT NULL,
    received_at DATETIME NOT NULL,

    -- 정규화 결과
    summary TEXT,
    suspected_type_primary TEXT,
    suspected_type_secondary TEXT,
    affected_system TEXT,
    urgency TEXT,

    -- Agent 분석 결과
    agent_decision_primary TEXT,
    agent_decision_secondary TEXT,
    decision_confidence REAL,
    decision_reason TEXT,  -- JSON string
    action_proposal TEXT,  -- JSON string
    analyzed_at DATETIME,

    -- 관리자 처리 정보
    confirmed_at DATETIME,
    reject_reason TEXT,
    manual_resolution TEXT
);

-- 인덱스
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_urgency ON tickets(urgency);
CREATE INDEX idx_tickets_created_at ON tickets(created_at);
```

---

## 5. ticket_id 생성 규칙

| 항목 | 규칙 |
|------|------|
| 형식 | `VOC-YYYYMMDD-XXXX` |
| 예시 | `VOC-20240115-0001` |
| XXXX | 해당 날짜의 일련번호 (0001부터 시작) |

---

## 6. JSON 필드 저장 형식

`decision_reason`과 `action_proposal`은 JSON 문자열로 저장한다.

### 예시: decision_reason

```json
{
  "summary": "외부 결제 API 타임아웃으로 인한 결제 실패",
  "evidence": [
    "2024-01-15 14:32:01 - PaymentGateway 응답 시간 12.3초",
    "내부 로직 정상 완료 후 외부 호출 단계에서 실패"
  ],
  "ruled_out": [
    "내부 코드 오류: Exception 없음"
  ]
}
```

### 예시: action_proposal (integration_error)

```json
{
  "action_type": "integration_inquiry",
  "target_system": "PaymentGateway",
  "contact_info": "partner-support@pg.com",
  "email_draft": {
    "subject": "[문의] 결제 API 타임아웃 증가 현상",
    "body": "안녕하세요,\n\n귀사 결제 API 호출 시 타임아웃이 발생하고 있습니다..."
  }
}
```

---

## 7. 데이터 무결성 규칙

| 규칙 | 설명 |
|------|------|
| status 유효성 | 정의된 6개 상태만 허용 |
| channel 유효성 | email, slack만 허용 |
| urgency 유효성 | low, medium, high만 허용 |
| reject_reason 필수 | status가 REJECTED일 때 필수 |
| decision_confidence 범위 | 0.0 ~ 1.0 |
