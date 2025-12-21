# 문제 유형 분류 체계

## 1. 개요

Agent가 VOC를 분석하여 분류하는 문제 유형 체계를 정의한다.

---

## 2. 문제 유형 구조

### 2.1 Primary / Secondary 구조

| 구분 | 설명 | 필수 여부 |
|------|------|-----------|
| primary_type | 주요 문제 유형 | 필수 |
| secondary_type | 부가 문제 유형 | 선택 (null 가능) |

하나의 VOC에 복수의 문제 유형이 존재할 수 있으며, 이 경우 가장 핵심적인 유형을 primary로, 부가적인 유형을 secondary로 지정한다.

---

## 3. 문제 유형 정의

### 3.1 integration_error (연동사 오류)

| 항목 | 설명 |
|------|------|
| 정의 | 외부 연동 시스템에서 발생한 오류 |
| 책임 소재 | 외부 시스템 (연동사) |

#### 판단 기준

| 조건 | 가중치 |
|------|--------|
| 외부 시스템 에러 응답 코드 존재 | 높음 |
| 내부 로직은 정상 동작 확인 | 높음 |
| 외부 API 타임아웃 발생 | 중간 |
| 동일 외부 시스템 관련 VOC 반복 | 중간 |

#### 예시 로그 패턴

```
[ERROR] PaymentGateway response: 503 Service Unavailable
[ERROR] External API timeout after 30000ms
[WARN] Retry exhausted for partner API: CardCompany
```

#### 제안 액션

- 연동사 문의 메일 초안 생성
- 장애 이력 확인 제안

---

### 3.2 code_error (코드 오류)

| 항목 | 설명 |
|------|------|
| 정의 | 내부 코드에서 발생한 버그 또는 예외 |
| 책임 소재 | 내부 개발팀 |

#### 판단 기준

| 조건 | 가중치 |
|------|--------|
| 내부 Exception/StackTrace 존재 | 높음 |
| NullPointerException, TypeError 등 코드 오류 | 높음 |
| 동일 코드 경로에서 반복 발생 | 중간 |
| 특정 입력값에서만 재현 | 중간 |

#### 예시 로그 패턴

```
[ERROR] NullPointerException at PaymentService.java:142
[ERROR] TypeError: Cannot read property 'amount' of undefined
[ERROR] IndexOutOfBoundsException in OrderProcessor.process()
```

#### 제안 액션

- 수정 방향 요약
- 영향 파일 목록 제시
- 심각도 평가

---

### 3.3 business_improvement (비즈니스 개선)

| 항목 | 설명 |
|------|------|
| 정의 | 명확한 오류가 아닌 정책/UX 개선 필요 사항 |
| 책임 소재 | 기획팀 / 프로덕트팀 |

#### 판단 기준

| 조건 | 가중치 |
|------|--------|
| 명확한 에러 로그 없음 | 높음 |
| 사용자 불편/혼란 호소 | 높음 |
| 동일 유형 VOC 반복 발생 | 중간 |
| 기능 요청 성격 | 중간 |

#### 예시 VOC 패턴

```
"결제 취소 버튼을 찾기 어려워요"
"왜 이렇게 처리되는지 이해가 안 돼요"
"다른 서비스는 이런 기능이 있던데요"
```

#### 제안 액션

- 개선 제안서 작성
- 관련 이해관계자 목록
- 예상 효과 제시

---

## 4. 유형 간 경계 판단

### 4.1 복합 유형 처리

| 상황 | 처리 방법 |
|------|-----------|
| 연동 오류 + 코드 오류 | 근본 원인을 primary로 지정 |
| 코드 오류 + 비즈니스 개선 | 오류 해결이 primary, 개선은 secondary |
| 연동 오류 + 비즈니스 개선 | 오류 해결이 primary |

### 4.2 판단 우선순위

1. 명확한 에러가 있으면 오류 유형 우선
2. 오류 중에서는 근본 원인(root cause)이 primary
3. 에러 없으면 business_improvement

---

## 5. 신뢰도와 유형 판단

| 신뢰도 범위 | 의미 | 처리 |
|-------------|------|------|
| 0.8 ~ 1.0 | 높은 확신 | 정상 처리 |
| 0.6 ~ 0.8 | 중간 확신 | 정상 처리 (근거 상세 제시) |
| 0.0 ~ 0.6 | 낮은 확신 | MANUAL_REQUIRED 전환 |

---

## 6. 유형별 출력 스키마

### 6.1 agent_decision 구조

```json
{
  "agent_decision": {
    "primary_type": "integration_error",
    "secondary_type": "code_error"
  }
}
```

### 6.2 유효한 조합 예시

| primary_type | secondary_type | 설명 |
|--------------|----------------|------|
| integration_error | null | 순수 연동 오류 |
| integration_error | code_error | 연동 오류 + 내부 예외 처리 미흡 |
| code_error | null | 순수 코드 오류 |
| code_error | business_improvement | 코드 오류 + UX 개선 필요 |
| business_improvement | null | 순수 개선 요청 |
