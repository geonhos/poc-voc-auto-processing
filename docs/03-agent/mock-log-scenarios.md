# Mock 로그 시나리오

## 1. 개요

Issue Solver Agent가 분석에 사용할 Mock 로그 데이터의 구조와 시나리오를 정의한다.

---

## 2. 로그 데이터 구조

### 2.1 LogEntry 스키마

```typescript
interface LogEntry {
  timestamp: string;      // ISO 8601 형식
  level: "DEBUG" | "INFO" | "WARN" | "ERROR";
  service: string;        // 서비스/모듈명
  message: string;        // 로그 메시지
  error_code?: string;    // 에러 코드 (선택)
  stack_trace?: string;   // 스택 트레이스 (선택)
  metadata?: {
    transaction_id?: string;
    user_id?: string;
    request_id?: string;
    duration_ms?: number;
    [key: string]: any;
  };
}
```

### 2.2 예시

```json
{
  "timestamp": "2024-01-15T14:32:01.234Z",
  "level": "ERROR",
  "service": "PaymentService",
  "message": "External API timeout: PaymentGateway",
  "error_code": "TIMEOUT_ERROR",
  "metadata": {
    "transaction_id": "TXN-20240115-001",
    "duration_ms": 12300,
    "threshold_ms": 5000
  }
}
```

---

## 3. 시나리오 정의

### 3.1 시나리오 목록

| ID | 시나리오 | 문제 유형 | 신뢰도 예상 |
|----|----------|-----------|-------------|
| S1 | 결제 API 타임아웃 | integration_error | 높음 (0.85+) |
| S2 | NullPointerException 발생 | code_error | 높음 (0.90+) |
| S3 | 결제 취소 버튼 불편 | business_improvement | 중간 (0.70) |
| S4 | 복합 오류 (연동 + 코드) | integration_error (primary) | 중간 (0.75) |
| S5 | 로그 부족 케이스 | 불명확 | 낮음 (0.40) |

---

## 4. 시나리오 상세

### 4.1 S1: 결제 API 타임아웃 (integration_error)

#### VOC 원문
```
어제 저녁에 결제를 시도했는데 한참 기다려도 결제가 안 되더라고요.
나중에 보니까 결제 실패로 되어 있었어요. 카드는 정상인데 왜 그런 건가요?
```

#### Mock 로그

```json
[
  {
    "timestamp": "2024-01-15T18:30:00.000Z",
    "level": "INFO",
    "service": "PaymentService",
    "message": "Payment request initiated",
    "metadata": {
      "transaction_id": "TXN-20240115-001",
      "amount": 50000,
      "user_id": "USER-12345"
    }
  },
  {
    "timestamp": "2024-01-15T18:30:00.100Z",
    "level": "INFO",
    "service": "PaymentService",
    "message": "Calling external payment gateway",
    "metadata": {
      "transaction_id": "TXN-20240115-001",
      "gateway": "PaymentGateway"
    }
  },
  {
    "timestamp": "2024-01-15T18:30:12.300Z",
    "level": "ERROR",
    "service": "PaymentService",
    "message": "External API timeout: PaymentGateway did not respond within threshold",
    "error_code": "EXTERNAL_TIMEOUT",
    "metadata": {
      "transaction_id": "TXN-20240115-001",
      "duration_ms": 12300,
      "threshold_ms": 5000,
      "gateway": "PaymentGateway"
    }
  },
  {
    "timestamp": "2024-01-15T18:30:12.350Z",
    "level": "WARN",
    "service": "PaymentService",
    "message": "Payment marked as failed due to gateway timeout",
    "metadata": {
      "transaction_id": "TXN-20240115-001"
    }
  }
]
```

#### 기대 출력
- primary_type: integration_error
- confidence: 0.85+
- action_type: integration_inquiry

---

### 4.2 S2: NullPointerException 발생 (code_error)

#### VOC 원문
```
주문 상세 페이지에서 '환불 요청' 버튼을 누르면 에러가 뜹니다.
여러 번 시도해도 같은 에러가 나와요.
```

#### Mock 로그

```json
[
  {
    "timestamp": "2024-01-15T10:15:00.000Z",
    "level": "INFO",
    "service": "RefundService",
    "message": "Refund request received",
    "metadata": {
      "order_id": "ORD-20240110-999",
      "user_id": "USER-67890"
    }
  },
  {
    "timestamp": "2024-01-15T10:15:00.050Z",
    "level": "ERROR",
    "service": "RefundService",
    "message": "NullPointerException while processing refund",
    "error_code": "NPE_ERROR",
    "stack_trace": "java.lang.NullPointerException\n\tat com.example.RefundService.processRefund(RefundService.java:142)\n\tat com.example.RefundController.handleRefund(RefundController.java:58)",
    "metadata": {
      "order_id": "ORD-20240110-999"
    }
  },
  {
    "timestamp": "2024-01-15T10:20:00.000Z",
    "level": "ERROR",
    "service": "RefundService",
    "message": "NullPointerException while processing refund",
    "error_code": "NPE_ERROR",
    "stack_trace": "java.lang.NullPointerException\n\tat com.example.RefundService.processRefund(RefundService.java:142)\n\tat com.example.RefundController.handleRefund(RefundController.java:58)",
    "metadata": {
      "order_id": "ORD-20240110-999"
    }
  }
]
```

#### 기대 출력
- primary_type: code_error
- confidence: 0.90+
- action_type: code_fix
- affected_files: ["RefundService.java"]

---

### 4.3 S3: 결제 취소 버튼 불편 (business_improvement)

#### VOC 원문
```
결제 취소하려고 하는데 버튼이 어디 있는지 모르겠어요.
주문 상세에서 한참 찾아봤는데 없고, 결국 고객센터에 전화했습니다.
```

#### Mock 로그

```json
[
  {
    "timestamp": "2024-01-15T11:00:00.000Z",
    "level": "INFO",
    "service": "OrderService",
    "message": "Order detail page accessed",
    "metadata": {
      "order_id": "ORD-20240114-123",
      "user_id": "USER-11111"
    }
  },
  {
    "timestamp": "2024-01-15T11:00:30.000Z",
    "level": "INFO",
    "service": "OrderService",
    "message": "Order detail page accessed",
    "metadata": {
      "order_id": "ORD-20240114-123",
      "user_id": "USER-11111"
    }
  },
  {
    "timestamp": "2024-01-15T11:01:00.000Z",
    "level": "INFO",
    "service": "OrderService",
    "message": "Order detail page accessed",
    "metadata": {
      "order_id": "ORD-20240114-123",
      "user_id": "USER-11111"
    }
  }
]
```

#### 기대 출력
- primary_type: business_improvement
- confidence: 0.70 (에러 없음, VOC 패턴 기반)
- action_type: business_proposal
- category: "UX 개선"

---

### 4.4 S4: 복합 오류 (integration_error + code_error)

#### VOC 원문
```
결제하다가 에러가 났어요. 화면에 "시스템 오류"라고만 나와서 뭔지 모르겠습니다.
```

#### Mock 로그

```json
[
  {
    "timestamp": "2024-01-15T15:00:00.000Z",
    "level": "INFO",
    "service": "PaymentService",
    "message": "Payment request initiated",
    "metadata": {
      "transaction_id": "TXN-20240115-002"
    }
  },
  {
    "timestamp": "2024-01-15T15:00:05.000Z",
    "level": "ERROR",
    "service": "PaymentService",
    "message": "External payment gateway returned error",
    "error_code": "GATEWAY_ERROR",
    "metadata": {
      "transaction_id": "TXN-20240115-002",
      "gateway_response_code": "500",
      "gateway": "PaymentGateway"
    }
  },
  {
    "timestamp": "2024-01-15T15:00:05.100Z",
    "level": "ERROR",
    "service": "PaymentService",
    "message": "Unhandled exception while processing gateway error",
    "error_code": "UNHANDLED_EXCEPTION",
    "stack_trace": "java.lang.IllegalStateException: Unexpected response format\n\tat com.example.PaymentService.handleGatewayResponse(PaymentService.java:200)",
    "metadata": {
      "transaction_id": "TXN-20240115-002"
    }
  }
]
```

#### 기대 출력
- primary_type: integration_error (근본 원인)
- secondary_type: code_error (예외 처리 미흡)
- confidence: 0.75
- action_type: integration_inquiry (우선)

---

### 4.5 S5: 로그 부족 케이스 (MANUAL_REQUIRED)

#### VOC 원문
```
뭔가 이상해요. 자세히는 모르겠는데 예전이랑 다른 것 같아요.
```

#### Mock 로그

```json
[
  {
    "timestamp": "2024-01-15T09:00:00.000Z",
    "level": "INFO",
    "service": "MainService",
    "message": "User session started",
    "metadata": {
      "user_id": "USER-99999"
    }
  }
]
```

#### 기대 출력
- primary_type: 판단 불가
- confidence: 0.40 (로그 부족)
- 상태: MANUAL_REQUIRED

---

## 5. Mock 데이터 파일 구조

```
data/
└── mock_logs/
    ├── scenario_s1_integration_timeout.json
    ├── scenario_s2_code_npe.json
    ├── scenario_s3_business_ux.json
    ├── scenario_s4_complex_error.json
    └── scenario_s5_insufficient_logs.json
```

---

## 6. 로그 조회 시뮬레이션

### 6.1 시스템별 로그 매핑

| affected_system | 조회할 시나리오 |
|-----------------|-----------------|
| 결제시스템 | S1, S4 |
| 환불시스템 | S2 |
| 주문시스템 | S3 |
| 기타/미확인 | S5 |

### 6.2 시간 기반 필터링

```python
def get_mock_logs(service: str, start_time: str, end_time: str) -> list:
    """
    Mock 로그 조회
    - 시나리오 파일에서 로그 로드
    - 시간 범위로 필터링
    - 최대 100건 반환
    """
    pass
```
