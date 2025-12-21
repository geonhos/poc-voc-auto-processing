# 정규화 Agent 명세

## 1. 개요

### 1.1 역할
자연어 VOC를 Ticket 생성에 필요한 구조화된 데이터로 변환한다.

### 1.2 위치
```
VOC 입력 → [정규화 Agent] → Ticket 생성
```

---

## 2. 입력/출력 스키마

### 2.1 입력

```typescript
interface NormalizerInput {
  raw_voc: string;           // VOC 원문
  customer_name: string;     // 고객명
  channel: "email" | "slack"; // 접수 채널
  received_at: string;       // 접수일시 (ISO 8601)
}
```

### 2.2 출력

```typescript
interface NormalizerOutput {
  success: boolean;
  data?: {
    summary: string;
    suspected_type: {
      primary_type: "integration_error" | "code_error" | "business_improvement";
      secondary_type: "integration_error" | "code_error" | "business_improvement" | null;
    };
    affected_system: string;
    urgency: "low" | "medium" | "high";
  };
  error?: {
    code: string;
    message: string;
  };
}
```

---

## 3. 정규화 규칙

### 3.1 summary 생성 규칙

| 규칙 | 설명 |
|------|------|
| 길이 | 1~2문장, 최대 200자 |
| 내용 | 문제의 핵심을 명확히 요약 |
| 형식 | 평서문 (의문문 X) |

#### 예시

| 원문 VOC | summary |
|----------|---------|
| "어제 결제했는데 오늘 보니까 결제가 안됐다고 나와요. 확인 좀 해주세요" | "결제 완료 후 미결제로 표시되는 현상 발생" |
| "앱이 자꾸 튕겨요 진짜 너무 불편해요" | "앱 크래시가 반복적으로 발생하여 사용 불편 호소" |

### 3.2 suspected_type 추정 규칙

| 키워드/패턴 | 추정 유형 |
|-------------|-----------|
| 외부사, 카드사, PG, 연동 | integration_error |
| 오류, 에러, 버그, 튕김, 크래시 | code_error |
| 불편, 개선, 왜 이렇게, 다른 서비스는 | business_improvement |

### 3.3 urgency 판단 규칙

| 긴급도 | 조건 |
|--------|------|
| high | 결제 실패, 금전 손실, 서비스 전면 장애 |
| medium | 일부 기능 오류, 불편 호소 |
| low | 문의, 개선 요청, 단순 확인 |

### 3.4 affected_system 추출 규칙

VOC에서 언급된 시스템/서비스명을 추출한다. 명시되지 않은 경우 "미확인"으로 설정.

---

## 4. 실패 조건

### 4.1 정규화 실패 판단 기준

| 조건 | 설명 |
|------|------|
| 내용 불명확 | 문제 파악 불가 |
| 언어 미지원 | 한국어/영어 외 언어 |
| 비정상 입력 | 의미없는 문자열, 스팸 |
| 정보 부족 | 문제 상황 추론 불가 |

### 4.2 실패 시 출력

```json
{
  "success": false,
  "error": {
    "code": "NORMALIZATION_FAILED",
    "message": "VOC 내용을 분석할 수 없습니다. 수동 분류가 필요합니다."
  }
}
```

### 4.3 실패 시 처리

- Ticket 상태: `MANUAL_REQUIRED`
- raw_voc는 그대로 보존
- summary, suspected_type 등은 null

---

## 5. Prompt 구조

### 5.1 System Prompt

```
당신은 VOC(Voice of Customer)를 분석하여 구조화된 데이터로 변환하는 전문가입니다.

## 역할
- 자연어 VOC를 정해진 형식으로 변환합니다.
- 문제의 핵심을 파악하여 요약합니다.
- 문제 유형을 추정합니다.

## 문제 유형
1. integration_error: 외부 시스템(연동사, PG사, 카드사 등) 관련 오류
2. code_error: 내부 코드 버그, 앱 크래시, 시스템 오류
3. business_improvement: 정책 개선, UX 개선, 기능 요청

## 긴급도 기준
- high: 금전 손실, 서비스 장애
- medium: 기능 오류, 불편
- low: 문의, 개선 요청

## 출력 형식
반드시 JSON 형식으로 출력하세요.
```

### 5.2 User Prompt Template

```
다음 VOC를 분석하여 구조화된 데이터로 변환해주세요.

## VOC 정보
- 고객명: {customer_name}
- 접수 채널: {channel}
- 접수일시: {received_at}

## VOC 원문
{raw_voc}

## 출력 형식
{
  "summary": "문제 요약 (1-2문장)",
  "suspected_type": {
    "primary_type": "문제 유형",
    "secondary_type": "부가 문제 유형 또는 null"
  },
  "affected_system": "영향 시스템",
  "urgency": "긴급도"
}
```

---

## 6. 예시

### 6.1 성공 케이스

**입력:**
```json
{
  "raw_voc": "어제 밤에 카드 결제를 했는데 PG사에서 결제 실패 문자가 왔어요. 근데 제 카드에서는 빠져나갔거든요? 이거 확인 좀 해주세요. 김철수입니다.",
  "customer_name": "김철수",
  "channel": "email",
  "received_at": "2024-01-15T09:30:00Z"
}
```

**출력:**
```json
{
  "success": true,
  "data": {
    "summary": "PG사 결제 실패 응답에도 불구하고 실제 카드 출금이 발생한 결제 불일치 현상",
    "suspected_type": {
      "primary_type": "integration_error",
      "secondary_type": null
    },
    "affected_system": "PG결제시스템",
    "urgency": "high"
  }
}
```

### 6.2 실패 케이스

**입력:**
```json
{
  "raw_voc": "ㅋㅋㅋㅋㅋ",
  "customer_name": "익명",
  "channel": "slack",
  "received_at": "2024-01-15T10:00:00Z"
}
```

**출력:**
```json
{
  "success": false,
  "error": {
    "code": "NORMALIZATION_FAILED",
    "message": "VOC 내용을 분석할 수 없습니다. 수동 분류가 필요합니다."
  }
}
```

---

## 7. 제약사항

| 항목 | 제약 |
|------|------|
| Timeout | 60초 |
| 최대 입력 길이 | 5000자 |
| 출력 언어 | 한국어 |
