# API 엔드포인트 목록

## 1. 개요

VOC 자동 처리 시스템의 REST API 엔드포인트를 정의한다.

### 1.1 Base URL

```
http://localhost:8000/api/v1
```

### 1.2 공통 헤더

```
Content-Type: application/json
```

---

## 2. 엔드포인트 목록

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | /voc | VOC 입력 및 Ticket 생성 |
| GET | /tickets | Ticket 목록 조회 |
| GET | /tickets/{ticket_id} | Ticket 상세 조회 |
| POST | /tickets/{ticket_id}/confirm | Ticket 승인 |
| POST | /tickets/{ticket_id}/reject | Ticket 거부 |
| POST | /tickets/{ticket_id}/retry | Ticket 재분석 요청 |
| POST | /tickets/{ticket_id}/complete | 수동 처리 완료 |
| GET | /health | 시스템 상태 확인 |

---

## 3. 엔드포인트 상세

### 3.1 VOC 입력 및 Ticket 생성

VOC를 입력하고 정규화 후 Ticket을 생성한다.

```
POST /voc
```

#### Request Body

```json
{
  "raw_voc": "string (required)",
  "customer_name": "string (required)",
  "channel": "email | slack (required)",
  "received_at": "string (ISO 8601, required)"
}
```

#### Response

**성공 (201 Created)**

```json
{
  "success": true,
  "data": {
    "ticket_id": "VOC-20240115-0001",
    "status": "OPEN",
    "message": "Ticket이 생성되었습니다. 분석이 시작됩니다."
  }
}
```

**정규화 실패 (201 Created, 수동 분류 필요)**

```json
{
  "success": true,
  "data": {
    "ticket_id": "VOC-20240115-0002",
    "status": "MANUAL_REQUIRED",
    "message": "VOC 정규화에 실패했습니다. 수동 분류가 필요합니다."
  }
}
```

**유효성 검증 실패 (400 Bad Request)**

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "필수 필드가 누락되었습니다.",
    "details": {
      "raw_voc": "필수 입력 항목입니다."
    }
  }
}
```

---

### 3.2 Ticket 목록 조회

Ticket 목록을 조회한다.

```
GET /tickets
```

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| status | string | N | - | 상태 필터 (쉼표 구분 가능) |
| urgency | string | N | - | 긴급도 필터 |
| sort | string | N | created_at | 정렬 기준 (created_at, urgency) |
| order | string | N | desc | 정렬 순서 (asc, desc) |
| page | integer | N | 1 | 페이지 번호 |
| limit | integer | N | 20 | 페이지당 항목 수 (최대 100) |

#### Example

```
GET /tickets?status=WAITING_CONFIRM,ANALYZING&urgency=high&sort=created_at&order=desc
```

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "tickets": [
      {
        "ticket_id": "VOC-20240115-0001",
        "status": "WAITING_CONFIRM",
        "summary": "결제 API 타임아웃으로 인한 결제 실패",
        "urgency": "high",
        "customer_name": "김철수",
        "created_at": "2024-01-15T09:30:00Z",
        "decision_confidence": 0.85
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total_count": 45,
      "total_pages": 3
    }
  }
}
```

---

### 3.3 Ticket 상세 조회

특정 Ticket의 상세 정보를 조회한다.

```
GET /tickets/{ticket_id}
```

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| ticket_id | string | Y | Ticket ID |

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "ticket_id": "VOC-20240115-0001",
    "status": "WAITING_CONFIRM",
    "created_at": "2024-01-15T09:30:00Z",
    "updated_at": "2024-01-15T09:31:30Z",
    "assignee": null,

    "voc_input": {
      "raw_voc": "어제 밤에 카드 결제를 했는데...",
      "customer_name": "김철수",
      "channel": "email",
      "received_at": "2024-01-15T09:30:00Z"
    },

    "normalization": {
      "summary": "PG사 결제 실패 응답에도 불구하고 실제 카드 출금 발생",
      "suspected_type": {
        "primary_type": "integration_error",
        "secondary_type": null
      },
      "affected_system": "PG결제시스템",
      "urgency": "high"
    },

    "agent_analysis": {
      "agent_decision": {
        "primary_type": "integration_error",
        "secondary_type": null
      },
      "decision_confidence": 0.85,
      "decision_reason": {
        "summary": "외부 결제 API 타임아웃으로 인한 결제 실패",
        "evidence": [
          "2024-01-15 14:32:01 - PaymentGateway 응답 시간 12.3초",
          "내부 로직 정상 완료 후 외부 호출 단계에서 실패"
        ],
        "ruled_out": [
          "내부 코드 오류: Exception 없음"
        ]
      },
      "action_proposal": {
        "action_type": "integration_inquiry",
        "target_system": "PaymentGateway",
        "contact_info": "partner-support@pg.com",
        "email_draft": {
          "subject": "[문의] 결제 API 타임아웃 증가 현상",
          "body": "..."
        }
      },
      "analyzed_at": "2024-01-15T09:31:30Z",
      "processing_time_seconds": 8.5,
      "analyzed_log_count": 47
    },

    "admin_action": null
  }
}
```

#### Response (404 Not Found)

```json
{
  "success": false,
  "error": {
    "code": "TICKET_NOT_FOUND",
    "message": "Ticket을 찾을 수 없습니다."
  }
}
```

---

### 3.4 Ticket 승인

Agent 판단을 승인하고 Ticket을 완료 처리한다.

```
POST /tickets/{ticket_id}/confirm
```

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| ticket_id | string | Y | Ticket ID |

#### Request Body

```json
{
  "assignee": "string (optional)"
}
```

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "ticket_id": "VOC-20240115-0001",
    "status": "DONE",
    "confirmed_at": "2024-01-15T10:00:00Z",
    "message": "Ticket이 승인되어 완료 처리되었습니다."
  }
}
```

#### Response (400 Bad Request) - 잘못된 상태

```json
{
  "success": false,
  "error": {
    "code": "INVALID_STATUS_TRANSITION",
    "message": "현재 상태(DONE)에서는 승인할 수 없습니다."
  }
}
```

---

### 3.5 Ticket 거부

VOC를 거부하고 Ticket을 종료한다.

```
POST /tickets/{ticket_id}/reject
```

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| ticket_id | string | Y | Ticket ID |

#### Request Body

```json
{
  "reject_reason": "string (required)",
  "assignee": "string (optional)"
}
```

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "ticket_id": "VOC-20240115-0001",
    "status": "REJECTED",
    "rejected_at": "2024-01-15T10:00:00Z",
    "message": "Ticket이 거부되었습니다."
  }
}
```

#### Response (400 Bad Request) - 사유 누락

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "거부 사유는 필수 입력 항목입니다."
  }
}
```

---

### 3.6 Ticket 재분석 요청

Agent에게 재분석을 요청한다.

```
POST /tickets/{ticket_id}/retry
```

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| ticket_id | string | Y | Ticket ID |

#### Request Body

```json
{
  "retry_reason": "string (optional)"
}
```

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "ticket_id": "VOC-20240115-0001",
    "status": "ANALYZING",
    "message": "재분석이 시작되었습니다."
  }
}
```

---

### 3.7 수동 처리 완료

MANUAL_REQUIRED 상태의 Ticket을 수동 완료 처리한다.

```
POST /tickets/{ticket_id}/complete
```

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| ticket_id | string | Y | Ticket ID |

#### Request Body

```json
{
  "manual_resolution": "string (required)",
  "assignee": "string (optional)"
}
```

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "ticket_id": "VOC-20240115-0001",
    "status": "DONE",
    "completed_at": "2024-01-15T10:00:00Z",
    "message": "수동 처리가 완료되었습니다."
  }
}
```

#### Response (400 Bad Request) - 잘못된 상태

```json
{
  "success": false,
  "error": {
    "code": "INVALID_STATUS_TRANSITION",
    "message": "수동 완료는 MANUAL_REQUIRED 상태에서만 가능합니다."
  }
}
```

---

### 3.8 시스템 상태 확인

시스템 상태를 확인한다.

```
GET /health
```

#### Response (200 OK)

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:00:00Z",
  "components": {
    "database": "healthy",
    "llm": "healthy",
    "slack": "healthy"
  }
}
```

---

## 4. 공통 에러 응답

### 4.1 에러 응답 형식

```json
{
  "success": false,
  "error": {
    "code": "string",
    "message": "string",
    "details": {}
  }
}
```

### 4.2 공통 에러 코드

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | VALIDATION_ERROR | 요청 유효성 검증 실패 |
| 400 | INVALID_STATUS_TRANSITION | 잘못된 상태 전이 시도 |
| 404 | TICKET_NOT_FOUND | Ticket을 찾을 수 없음 |
| 500 | INTERNAL_ERROR | 서버 내부 오류 |
| 503 | LLM_UNAVAILABLE | LLM 서비스 이용 불가 |

---

## 5. 비동기 처리

### 5.1 Agent 처리

VOC 입력 후 Agent 분석은 비동기로 처리된다.

```
POST /voc → 즉시 응답 (Ticket 생성)
         → 백그라운드에서 정규화 Agent 실행
         → 백그라운드에서 Issue Solver Agent 실행
         → 완료 시 상태 업데이트
```

### 5.2 상태 폴링

클라이언트는 Ticket 상태를 주기적으로 폴링하여 진행 상황을 확인한다.

```
GET /tickets/{ticket_id}  (5초 간격 권장)
```

---

## 6. Slack 알림 (내부 처리)

긴급 Ticket 생성 시 Slack 알림은 서버에서 자동 처리된다. 별도 API 노출 없음.

### 6.1 트리거 조건

- Ticket 생성 시 `urgency: high`

### 6.2 알림 내용

```json
{
  "text": "🚨 긴급 VOC Ticket 생성",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Ticket ID:* VOC-20240115-0001\n*요약:* 결제 실패 문의\n*긴급도:* 🔴 High"
      }
    }
  ]
}
```
