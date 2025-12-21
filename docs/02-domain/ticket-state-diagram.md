# Ticket 상태 다이어그램

## 1. 개요

Ticket의 생명주기와 상태 전이 규칙을 정의한다.

---

## 2. 상태 정의

| 상태 | 코드 | 설명 | 종료 여부 |
|------|------|------|-----------|
| 생성됨 | OPEN | Ticket 생성 직후 초기 상태 | X |
| 분석 중 | ANALYZING | Issue Solver Agent가 분석 수행 중 | X |
| 승인 대기 | WAITING_CONFIRM | Agent 분석 완료, 관리자 확인 대기 | X |
| 완료 | DONE | 처리 완료 | O |
| 수동 처리 필요 | MANUAL_REQUIRED | 자동 처리 불가, 수동 개입 필요 | X |
| 거부됨 | REJECTED | VOC 자체 거부 | O |

---

## 3. 상태 전이 다이어그램

```
                    ┌─────────────────────────────────────┐
                    │                                     │
                    ▼                                     │
┌──────┐       ┌───────────┐       ┌─────────────────┐   │
│ OPEN │──────▶│ ANALYZING │──────▶│ WAITING_CONFIRM │───┤
└──────┘       └───────────┘       └─────────────────┘   │
                    │                      │             │
                    │                      ├─────────────┼───▶ DONE
                    │                      │             │
                    │                      └─────────────┼───▶ REJECTED
                    │                                    │
                    └────────────────────────────────────┼───▶ MANUAL_REQUIRED
                                                         │           │
                                                         │           │
                                                         │           ▼
                                                         └────────  DONE
```

---

## 4. 상태 전이 규칙

### 4.1 정상 흐름

| 전이 | From | To | 트리거 | 조건 |
|------|------|----|--------|------|
| T1 | OPEN | ANALYZING | 시스템 자동 | Ticket 생성 완료 |
| T2 | ANALYZING | WAITING_CONFIRM | Agent 완료 | confidence >= 0.6 |
| T3 | WAITING_CONFIRM | DONE | 관리자 Approve | - |

### 4.2 예외 흐름

| 전이 | From | To | 트리거 | 조건 |
|------|------|----|--------|------|
| T4 | ANALYZING | MANUAL_REQUIRED | Agent 완료 | confidence < 0.6 |
| T5 | ANALYZING | MANUAL_REQUIRED | 시스템 | Agent timeout (60초) |
| T6 | WAITING_CONFIRM | REJECTED | 관리자 Reject | 사유 입력 필수 |
| T7 | WAITING_CONFIRM | ANALYZING | 관리자 Retry | 재분석 요청 |
| T8 | MANUAL_REQUIRED | DONE | 관리자 수동 완료 | 처리 결과 입력 |

### 4.3 정규화 실패 흐름

| 전이 | From | To | 트리거 | 조건 |
|------|------|----|--------|------|
| T9 | (생성 시) | MANUAL_REQUIRED | 정규화 Agent | 정규화 실패 |

---

## 5. 상태별 허용 액션

| 상태 | 허용 액션 |
|------|-----------|
| OPEN | 없음 (자동 전이) |
| ANALYZING | 없음 (Agent 처리 중) |
| WAITING_CONFIRM | Approve, Reject, Retry |
| DONE | 없음 (종료 상태) |
| MANUAL_REQUIRED | 수동 완료 |
| REJECTED | 없음 (종료 상태) |

---

## 6. 상태 전이 유효성 검증

시스템은 다음 전이만 허용한다:

```python
VALID_TRANSITIONS = {
    "OPEN": ["ANALYZING"],
    "ANALYZING": ["WAITING_CONFIRM", "MANUAL_REQUIRED"],
    "WAITING_CONFIRM": ["DONE", "REJECTED", "ANALYZING"],
    "MANUAL_REQUIRED": ["DONE"],
    "DONE": [],
    "REJECTED": [],
}
```

유효하지 않은 상태 전이 요청 시 에러를 반환한다.

---

## 7. 종료 상태 정책

| 종료 상태 | 재오픈 가능 여부 | 비고 |
|-----------|------------------|------|
| DONE | 불가 | 정상 종료 |
| REJECTED | 불가 | VOC 거부 종료 |

종료된 Ticket은 수정할 수 없으며, 새로운 VOC로 재입력해야 한다.
