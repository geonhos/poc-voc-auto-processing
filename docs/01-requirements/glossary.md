# 용어 정의서

## 1. 개요

VOC 자동 처리 POC에서 사용하는 용어를 정의한다. 모든 문서와 코드에서 동일한 용어를 사용한다.

---

## 2. 핵심 용어

### VOC (Voice of Customer)

| 항목 | 설명 |
|------|------|
| 정의 | 고객의 문의, 불만, 요청 등을 담은 자연어 텍스트 |
| 입력 주체 | VOC 전담 팀 |
| 입력 형태 | 메일, 슬랙, CS 이관 문구 등 |
| 시스템 내 표현 | `raw_voc` 필드 |

### Ticket

| 항목 | 설명 |
|------|------|
| 정의 | VOC를 구조화하여 처리 상태를 추적하는 단위 |
| 생성 조건 | VOC 정규화 완료 시 자동 생성 |
| 정책 | VOC 1건 = Ticket 1건 |
| 식별자 | `ticket_id` (시스템 자동 생성) |

### Agent

| 항목 | 설명 |
|------|------|
| 정의 | LLM 기반으로 특정 작업을 수행하는 자동화 모듈 |
| 역할 | 최종 결정자가 아닌 **보조자** |
| 종류 | 정규화 Agent, Issue Solver Agent |

---

## 3. Agent 관련 용어

### 정규화 Agent (Normalizer Agent)

| 항목 | 설명 |
|------|------|
| 정의 | 자연어 VOC를 구조화된 데이터로 변환하는 Agent |
| 입력 | raw_voc (자연어 텍스트) |
| 출력 | summary, suspected_type, affected_system, urgency |

### Issue Solver Agent

| 항목 | 설명 |
|------|------|
| 정의 | Ticket을 분석하여 문제 유형, 판단 근거, 해결안을 제시하는 Agent |
| 입력 | 정규화된 Ticket 정보 + Mock 로그 데이터 |
| 출력 | agent_decision, decision_confidence, decision_reason, action_proposal |

### Tool Use

| 항목 | 설명 |
|------|------|
| 정의 | Agent가 외부 도구(함수)를 호출하여 정보를 수집하거나 액션을 수행하는 방식 |
| 예시 | 로그 조회 Tool, 에러 패턴 매칭 Tool |

---

## 4. 상태 관련 용어

### Ticket 상태 (Status)

| 상태 | 설명 |
|------|------|
| OPEN | Ticket 생성 직후 초기 상태 |
| ANALYZING | Issue Solver Agent가 분석 중 |
| WAITING_CONFIRM | Agent 분석 완료, 관리자 승인 대기 |
| DONE | 처리 완료 (종료 상태) |
| MANUAL_REQUIRED | 수동 처리 필요 (정규화 실패 또는 저신뢰도) |
| REJECTED | VOC 자체 거부 (종료 상태) |

### 종료 상태 (Terminal Status)

| 항목 | 설명 |
|------|------|
| 정의 | 더 이상 상태 전이가 불가능한 최종 상태 |
| 해당 상태 | DONE, REJECTED |

---

## 5. 문제 유형 관련 용어

### 문제 유형 (Problem Type)

| 유형 | 설명 |
|------|------|
| integration_error | 외부 연동 시스템 오류 |
| code_error | 내부 코드 오류 |
| business_improvement | 비즈니스 정책 또는 UX 개선 필요 |

### Primary / Secondary Type

| 항목 | 설명 |
|------|------|
| primary_type | 주요 문제 유형 (필수) |
| secondary_type | 부가 문제 유형 (선택, null 가능) |

---

## 6. 판단 관련 용어

### 판단 신뢰도 (Decision Confidence)

| 항목 | 설명 |
|------|------|
| 정의 | Agent가 자신의 판단에 대해 가지는 확신도 |
| 범위 | 0.0 ~ 1.0 (0: 확신 없음, 1: 완전한 확신) |
| 임계값 | 0.6 미만 시 MANUAL_REQUIRED로 전환 |

### 판단 근거 (Decision Reason)

| 항목 | 설명 |
|------|------|
| 정의 | Agent가 해당 판단에 도달한 이유와 증거 |
| 구성 요소 | summary (요약), evidence (근거), ruled_out (제외된 가능성) |

### 제안 액션 (Action Proposal)

| 항목 | 설명 |
|------|------|
| 정의 | Agent가 제안하는 해결 방안 |
| 유형별 예시 | 연동사 문의 메일 초안, 코드 수정 방향, 비즈니스 개선 제안 |

---

## 7. 긴급도 관련 용어

### 긴급도 (Urgency)

| 레벨 | 설명 | 알림 |
|------|------|------|
| low | 낮은 긴급도 | 없음 |
| medium | 중간 긴급도 | 없음 |
| high | 높은 긴급도 | Slack 알림 발송 |

---

## 8. 관리자 액션 용어

### Approve

| 항목 | 설명 |
|------|------|
| 정의 | Agent 판단을 승인하고 Ticket을 종료 |
| 상태 변경 | WAITING_CONFIRM → DONE |

### Reject

| 항목 | 설명 |
|------|------|
| 정의 | VOC 자체를 거부하고 Ticket을 종료 |
| 상태 변경 | WAITING_CONFIRM → REJECTED |
| 필수 조건 | 거부 사유 입력 필수 |

### Retry

| 항목 | 설명 |
|------|------|
| 정의 | Agent 재분석 요청 |
| 상태 변경 | WAITING_CONFIRM → ANALYZING |

---

## 9. 채널 관련 용어

### 접수 채널 (Channel)

| 채널 | 설명 |
|------|------|
| email | 이메일을 통해 접수된 VOC |
| slack | Slack 메시지를 통해 접수된 VOC |
