# Issue Solver Agent 명세

## 1. 개요

### 1.1 역할
Ticket을 분석하여 문제 유형을 확정하고, 판단 근거와 해결안을 제시한다.

### 1.2 위치
```
Ticket(OPEN) → [Issue Solver Agent] → Ticket(WAITING_CONFIRM 또는 MANUAL_REQUIRED)
```

### 1.3 핵심 원칙
- Agent는 **최종 결정자가 아니다**
- Agent는 **근거 있는 해결안을 제시하는 보조자** 역할을 수행한다
- 모든 판단에는 **검증 가능한 근거**가 필요하다

---

## 2. 입력/출력 스키마

### 2.1 입력

```typescript
interface SolverInput {
  ticket_id: string;
  summary: string;
  suspected_type: {
    primary_type: string;
    secondary_type: string | null;
  };
  affected_system: string;
  urgency: string;
  raw_voc: string;
  logs: LogEntry[];  // Mock 로그 데이터
}

interface LogEntry {
  timestamp: string;
  level: "DEBUG" | "INFO" | "WARN" | "ERROR";
  service: string;
  message: string;
  error_code?: string;
  stack_trace?: string;
  metadata?: Record<string, any>;
}
```

### 2.2 출력

```typescript
interface SolverOutput {
  agent_decision: {
    primary_type: "integration_error" | "code_error" | "business_improvement";
    secondary_type: "integration_error" | "code_error" | "business_improvement" | null;
  };
  decision_confidence: number;  // 0.0 ~ 1.0
  decision_reason: {
    summary: string;
    evidence: string[];
    ruled_out: string[];
  };
  action_proposal: IntegrationInquiryAction | CodeFixAction | BusinessProposalAction;
  processing_time_seconds: number;
  analyzed_log_count: number;
}
```

---

## 3. 분석 프로세스

### 3.1 단계별 처리

```
1. 로그 수집 (Tool: get_logs)
   ↓
2. 에러 패턴 분석 (Tool: analyze_error_patterns)
   ↓
3. 문제 유형 확정
   ↓
4. 신뢰도 계산
   ↓
5. 판단 근거 생성
   ↓
6. 해결안 생성
```

### 3.2 각 단계 상세

#### Step 1: 로그 수집
- affected_system 기반 관련 로그 조회
- 시간 범위: VOC 접수 시점 기준 ±24시간
- 최대 로그 수: 100건

#### Step 2: 에러 패턴 분석
- ERROR, WARN 레벨 로그 필터링
- 에러 코드 빈도 분석
- 스택 트레이스 패턴 매칭

#### Step 3: 문제 유형 확정
- 정규화 Agent의 suspected_type 검증
- 로그 분석 결과와 대조
- 필요시 유형 변경

#### Step 4: 신뢰도 계산
- 근거 명확성, 패턴 일치도 등 종합

#### Step 5: 판단 근거 생성
- 관리자가 1~2분 내 이해 가능한 수준
- 증거(evidence)와 제외 사유(ruled_out) 명시

#### Step 6: 해결안 생성
- 문제 유형별 action_proposal 생성

---

## 4. Tool 정의

### 4.1 get_logs

로그 데이터를 조회한다.

```typescript
interface GetLogsParams {
  service: string;
  start_time: string;
  end_time: string;
  level?: "DEBUG" | "INFO" | "WARN" | "ERROR";
  limit?: number;
}

interface GetLogsResult {
  logs: LogEntry[];
  total_count: number;
}
```

### 4.2 analyze_error_patterns

에러 패턴을 분석한다.

```typescript
interface AnalyzeErrorPatternsParams {
  logs: LogEntry[];
}

interface AnalyzeErrorPatternsResult {
  error_summary: {
    error_code: string;
    count: number;
    first_occurrence: string;
    last_occurrence: string;
    sample_message: string;
  }[];
  stack_trace_patterns: string[];
  external_system_errors: {
    system: string;
    error_count: number;
  }[];
}
```

### 4.3 get_system_info

시스템 정보를 조회한다.

```typescript
interface GetSystemInfoParams {
  system_name: string;
}

interface GetSystemInfoResult {
  system_name: string;
  type: "internal" | "external";
  contact_info?: string;
  recent_incidents?: string[];
}
```

---

## 5. 신뢰도 계산 기준

### 5.1 신뢰도 요소

| 요소 | 가중치 | 설명 |
|------|--------|------|
| 로그 증거 명확성 | 40% | 관련 에러 로그 존재 여부 |
| 패턴 일치도 | 30% | 알려진 패턴과의 일치 |
| VOC-로그 연관성 | 20% | VOC 내용과 로그의 상관관계 |
| 유형 일관성 | 10% | suspected_type과 분석 결과 일치 |

### 5.2 신뢰도 수준

| 범위 | 수준 | 처리 |
|------|------|------|
| 0.8 ~ 1.0 | 높음 | WAITING_CONFIRM |
| 0.6 ~ 0.8 | 중간 | WAITING_CONFIRM (근거 상세 제시) |
| 0.0 ~ 0.6 | 낮음 | MANUAL_REQUIRED |

---

## 6. 문제 유형별 출력

### 6.1 integration_error

```json
{
  "agent_decision": {
    "primary_type": "integration_error",
    "secondary_type": null
  },
  "decision_confidence": 0.85,
  "decision_reason": {
    "summary": "외부 결제 API 타임아웃으로 인한 결제 실패",
    "evidence": [
      "2024-01-15 14:32:01 - PaymentGateway 응답 시간 12.3초 (임계값 5초 초과)",
      "2024-01-15 14:32:01 - 내부 로직 정상 완료 후 외부 호출 단계에서 실패",
      "최근 7일간 동일 패턴 3건 발생"
    ],
    "ruled_out": [
      "내부 코드 오류: Exception 없음, 정상 흐름 확인",
      "비즈니스 로직 문제: 요청 파라미터 유효성 통과"
    ]
  },
  "action_proposal": {
    "action_type": "integration_inquiry",
    "target_system": "PaymentGateway",
    "contact_info": "partner-support@pg.com",
    "email_draft": {
      "subject": "[문의] 결제 API 타임아웃 증가 현상 (2024-01-15)",
      "body": "안녕하세요,\n\n귀사 결제 API 호출 시 타임아웃이 발생하고 있어 문의드립니다.\n\n[현상]\n- 발생 시간: 2024-01-15 14:32:01\n- 응답 시간: 12.3초 (정상: 5초 이내)\n- 트랜잭션 ID: TXN-12345\n\n확인 부탁드립니다.\n\n감사합니다."
    }
  },
  "processing_time_seconds": 8.5,
  "analyzed_log_count": 47
}
```

### 6.2 code_error

```json
{
  "agent_decision": {
    "primary_type": "code_error",
    "secondary_type": null
  },
  "decision_confidence": 0.92,
  "decision_reason": {
    "summary": "결제 응답 처리 시 null 체크 누락으로 인한 NullPointerException 발생",
    "evidence": [
      "2024-01-15 14:30:00 - NullPointerException at PaymentService.java:142",
      "payment_response 객체가 null인 상태에서 getStatus() 호출",
      "동일 에러 최근 24시간 내 5건 발생"
    ],
    "ruled_out": [
      "연동사 오류: 외부 API 응답 정상 수신 확인",
      "비즈니스 로직: 입력값 유효성 통과"
    ]
  },
  "action_proposal": {
    "action_type": "code_fix",
    "affected_files": ["src/services/PaymentService.java"],
    "error_summary": "NullPointerException at line 142",
    "fix_direction": "payment_response null 체크 추가 필요",
    "suggested_approach": "payment_response가 null인 경우 조기 반환 또는 기본값 처리",
    "severity": "high"
  },
  "processing_time_seconds": 6.2,
  "analyzed_log_count": 32
}
```

### 6.3 business_improvement

```json
{
  "agent_decision": {
    "primary_type": "business_improvement",
    "secondary_type": null
  },
  "decision_confidence": 0.75,
  "decision_reason": {
    "summary": "결제 취소 버튼 위치에 대한 반복적인 사용자 불편 호소",
    "evidence": [
      "관련 에러 로그 없음 - 시스템 정상 동작",
      "동일 유형 VOC 최근 30일간 12건 접수",
      "VOC 키워드: '찾기 어려움', '버튼 위치', 'UI'"
    ],
    "ruled_out": [
      "시스템 오류: 관련 에러 로그 없음",
      "연동 오류: 외부 시스템 관련 내용 없음"
    ]
  },
  "action_proposal": {
    "action_type": "business_proposal",
    "category": "UX 개선",
    "problem_pattern": "결제 취소 버튼 위치 관련 VOC 월 12건 이상 반복",
    "proposal": "결제 상세 페이지 상단에 '결제 취소' 버튼 추가 또는 기존 버튼 강조 처리",
    "expected_impact": "관련 VOC 50% 이상 감소 예상",
    "stakeholders": ["프론트엔드팀", "UX팀", "기획팀"]
  },
  "processing_time_seconds": 5.1,
  "analyzed_log_count": 15
}
```

---

## 7. Prompt 구조

### 7.1 System Prompt

```
당신은 VOC Ticket을 분석하여 문제 유형을 확정하고 해결안을 제시하는 Issue Solver Agent입니다.

## 핵심 원칙
1. 당신은 최종 결정자가 아닙니다. 근거 있는 해결안을 제시하는 보조자입니다.
2. 모든 판단에는 검증 가능한 증거가 필요합니다.
3. 확신이 없으면 솔직히 신뢰도를 낮게 보고하세요.

## 문제 유형
1. integration_error: 외부 연동 시스템 오류 (증거: 외부 API 에러 응답)
2. code_error: 내부 코드 버그 (증거: Exception, StackTrace)
3. business_improvement: 정책/UX 개선 필요 (증거: 에러 없음 + 반복 VOC)

## 신뢰도 기준
- 0.8 이상: 명확한 로그 증거 + 패턴 일치
- 0.6~0.8: 부분적 증거 또는 추론 포함
- 0.6 미만: 증거 부족, 수동 분석 필요

## 출력 형식
반드시 정해진 JSON 형식으로 출력하세요.
Tool을 활용하여 로그를 분석하세요.
```

### 7.2 User Prompt Template

```
다음 Ticket을 분석하여 문제 유형을 확정하고 해결안을 제시해주세요.

## Ticket 정보
- Ticket ID: {ticket_id}
- 요약: {summary}
- 추정 유형: {suspected_type}
- 영향 시스템: {affected_system}
- 긴급도: {urgency}

## VOC 원문
{raw_voc}

## 지시사항
1. get_logs Tool을 사용하여 관련 로그를 조회하세요.
2. analyze_error_patterns Tool을 사용하여 에러 패턴을 분석하세요.
3. 분석 결과를 바탕으로 문제 유형을 확정하세요.
4. 판단 근거와 해결안을 JSON 형식으로 출력하세요.
```

---

## 8. 제약사항

| 항목 | 제약 |
|------|------|
| Timeout | 60초 |
| 최대 로그 분석 수 | 100건 |
| Timeout 발생 시 | MANUAL_REQUIRED로 전환 |
