# API 스키마 정의

## 1. 개요

API 요청/응답에 사용되는 JSON 스키마를 정의한다.

---

## 2. 공통 스키마

### 2.1 성공 응답 (SuccessResponse)

```typescript
interface SuccessResponse<T> {
  success: true;
  data: T;
}
```

### 2.2 에러 응답 (ErrorResponse)

```typescript
interface ErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
}
```

### 2.3 페이지네이션 (Pagination)

```typescript
interface Pagination {
  page: number;
  limit: number;
  total_count: number;
  total_pages: number;
}
```

---

## 3. Enum 타입

### 3.1 TicketStatus

```typescript
type TicketStatus =
  | "OPEN"
  | "ANALYZING"
  | "WAITING_CONFIRM"
  | "DONE"
  | "MANUAL_REQUIRED"
  | "REJECTED";
```

### 3.2 Channel

```typescript
type Channel = "email" | "slack";
```

### 3.3 Urgency

```typescript
type Urgency = "low" | "medium" | "high";
```

### 3.4 ProblemType

```typescript
type ProblemType =
  | "integration_error"
  | "code_error"
  | "business_improvement";
```

### 3.5 ActionType

```typescript
type ActionType =
  | "integration_inquiry"
  | "code_fix"
  | "business_proposal";
```

### 3.6 Severity

```typescript
type Severity = "low" | "medium" | "high" | "critical";
```

---

## 4. 요청 스키마

### 4.1 VOC 입력 요청 (CreateVocRequest)

```typescript
interface CreateVocRequest {
  raw_voc: string;         // 필수, 1~5000자
  customer_name: string;   // 필수, 1~100자
  channel: Channel;        // 필수
  received_at: string;     // 필수, ISO 8601 형식
}
```

**JSON Schema:**

```json
{
  "type": "object",
  "required": ["raw_voc", "customer_name", "channel", "received_at"],
  "properties": {
    "raw_voc": {
      "type": "string",
      "minLength": 1,
      "maxLength": 5000
    },
    "customer_name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100
    },
    "channel": {
      "type": "string",
      "enum": ["email", "slack"]
    },
    "received_at": {
      "type": "string",
      "format": "date-time"
    }
  }
}
```

### 4.2 Ticket 거부 요청 (RejectTicketRequest)

```typescript
interface RejectTicketRequest {
  reject_reason: string;   // 필수, 1~1000자
  assignee?: string;       // 선택, 1~100자
}
```

### 4.3 수동 완료 요청 (CompleteTicketRequest)

```typescript
interface CompleteTicketRequest {
  manual_resolution: string;  // 필수, 1~2000자
  assignee?: string;          // 선택, 1~100자
}
```

### 4.4 재분석 요청 (RetryTicketRequest)

```typescript
interface RetryTicketRequest {
  retry_reason?: string;   // 선택, 1~500자
}
```

### 4.5 승인 요청 (ConfirmTicketRequest)

```typescript
interface ConfirmTicketRequest {
  assignee?: string;       // 선택, 1~100자
}
```

---

## 5. 응답 스키마

### 5.1 Ticket 생성 응답 (CreateVocResponse)

```typescript
interface CreateVocResponse {
  ticket_id: string;
  status: TicketStatus;
  message: string;
}
```

### 5.2 Ticket 목록 항목 (TicketListItem)

```typescript
interface TicketListItem {
  ticket_id: string;
  status: TicketStatus;
  summary: string | null;
  urgency: Urgency | null;
  customer_name: string;
  created_at: string;
  decision_confidence: number | null;
}
```

### 5.3 Ticket 목록 응답 (TicketListResponse)

```typescript
interface TicketListResponse {
  tickets: TicketListItem[];
  pagination: Pagination;
}
```

### 5.4 VOC 입력 정보 (VocInput)

```typescript
interface VocInput {
  raw_voc: string;
  customer_name: string;
  channel: Channel;
  received_at: string;
}
```

### 5.5 정규화 결과 (NormalizationResult)

```typescript
interface NormalizationResult {
  summary: string;
  suspected_type: {
    primary_type: ProblemType;
    secondary_type: ProblemType | null;
  };
  affected_system: string;
  urgency: Urgency;
}
```

### 5.6 판단 근거 (DecisionReason)

```typescript
interface DecisionReason {
  summary: string;
  evidence: string[];
  ruled_out: string[];
}
```

### 5.7 연동 문의 액션 (IntegrationInquiryAction)

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

### 5.8 코드 수정 액션 (CodeFixAction)

```typescript
interface CodeFixAction {
  action_type: "code_fix";
  affected_files: string[];
  error_summary: string;
  fix_direction: string;
  suggested_approach: string;
  severity: Severity;
}
```

### 5.9 비즈니스 제안 액션 (BusinessProposalAction)

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

### 5.10 제안 액션 (ActionProposal)

```typescript
type ActionProposal =
  | IntegrationInquiryAction
  | CodeFixAction
  | BusinessProposalAction;
```

### 5.11 Agent 분석 결과 (AgentAnalysis)

```typescript
interface AgentAnalysis {
  agent_decision: {
    primary_type: ProblemType;
    secondary_type: ProblemType | null;
  };
  decision_confidence: number;
  decision_reason: DecisionReason;
  action_proposal: ActionProposal;
  analyzed_at: string;
  processing_time_seconds: number;
  analyzed_log_count: number;
}
```

### 5.12 관리자 처리 정보 (AdminAction)

```typescript
interface AdminAction {
  action: "confirm" | "reject" | "complete";
  action_at: string;
  assignee: string | null;
  reject_reason: string | null;
  manual_resolution: string | null;
}
```

### 5.13 Ticket 상세 응답 (TicketDetailResponse)

```typescript
interface TicketDetailResponse {
  ticket_id: string;
  status: TicketStatus;
  created_at: string;
  updated_at: string;
  assignee: string | null;

  voc_input: VocInput;
  normalization: NormalizationResult | null;
  agent_analysis: AgentAnalysis | null;
  admin_action: AdminAction | null;
}
```

### 5.14 Ticket 액션 응답 (TicketActionResponse)

```typescript
interface TicketActionResponse {
  ticket_id: string;
  status: TicketStatus;
  message: string;
  confirmed_at?: string;
  rejected_at?: string;
  completed_at?: string;
}
```

### 5.15 Health 응답 (HealthResponse)

```typescript
interface HealthResponse {
  status: "healthy" | "unhealthy";
  timestamp: string;
  components: {
    database: "healthy" | "unhealthy";
    llm: "healthy" | "unhealthy";
    slack: "healthy" | "unhealthy";
  };
}
```

---

## 6. 에러 코드

### 6.1 에러 코드 목록

| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400 | 요청 유효성 검증 실패 |
| INVALID_STATUS_TRANSITION | 400 | 잘못된 상태 전이 |
| INVALID_CHANNEL | 400 | 잘못된 채널 값 |
| INVALID_URGENCY | 400 | 잘못된 긴급도 값 |
| TICKET_NOT_FOUND | 404 | Ticket을 찾을 수 없음 |
| NORMALIZATION_FAILED | 422 | VOC 정규화 실패 |
| AGENT_TIMEOUT | 408 | Agent 처리 타임아웃 |
| INTERNAL_ERROR | 500 | 서버 내부 오류 |
| LLM_UNAVAILABLE | 503 | LLM 서비스 이용 불가 |
| SLACK_UNAVAILABLE | 503 | Slack 서비스 이용 불가 |

### 6.2 유효성 검증 에러 상세

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "요청 데이터가 유효하지 않습니다.",
    "details": {
      "raw_voc": "필수 입력 항목입니다.",
      "channel": "'twitter'는 유효한 채널이 아닙니다. (허용: email, slack)",
      "received_at": "올바른 날짜 형식이 아닙니다. (ISO 8601)"
    }
  }
}
```

---

## 7. 유효성 검증 규칙

### 7.1 필드별 규칙

| Field | Type | Validation |
|-------|------|------------|
| raw_voc | string | 1~5000자, 필수 |
| customer_name | string | 1~100자, 필수 |
| channel | enum | email, slack 중 하나, 필수 |
| received_at | datetime | ISO 8601 형식, 필수 |
| reject_reason | string | 1~1000자, 거부 시 필수 |
| manual_resolution | string | 1~2000자, 수동 완료 시 필수 |
| assignee | string | 1~100자, 선택 |

### 7.2 상태 전이 규칙

| Current Status | Allowed Transitions |
|----------------|---------------------|
| OPEN | ANALYZING |
| ANALYZING | WAITING_CONFIRM, MANUAL_REQUIRED |
| WAITING_CONFIRM | DONE (confirm), REJECTED (reject), ANALYZING (retry) |
| MANUAL_REQUIRED | DONE (complete) |
| DONE | (없음) |
| REJECTED | (없음) |
