# 확장 계획서

## 1. 개요

### 1.1 목적

POC 검증 완료 후, 프로덕션 환경으로의 확장을 위한 상세 계획을 정의한다.

### 1.2 확장 원칙

1. **점진적 확장**: 핵심 기능 우선, 단계적 기능 추가
2. **하위 호환성**: 기존 인터페이스 유지
3. **모듈화**: 독립적 배포 가능한 구조 유지

---

## 2. 외부 시스템 연동

### 2.1 Jira 연동

#### 2.1.1 연동 범위

| 기능 | 설명 | 우선순위 |
|------|------|----------|
| 이슈 생성 | 승인된 티켓 → Jira 이슈 자동 생성 | P0 |
| 이슈 연결 | VOC 티켓과 Jira 이슈 양방향 링크 | P0 |
| 상태 동기화 | Jira 이슈 상태 변경 시 티켓 상태 업데이트 | P1 |
| 코멘트 동기화 | Jira 코멘트 → VOC 시스템 동기화 | P2 |

#### 2.1.2 구현 계획

```python
# app/services/jira_service.py

class JiraService:
    async def create_issue(
        self,
        ticket: Ticket,
        project_key: str,
        issue_type: str = "Bug"
    ) -> JiraIssue:
        """
        VOC 티켓으로부터 Jira 이슈 생성

        - 문제 유형에 따라 issue_type 자동 선택
        - code_error → Bug
        - integration_error → Task (외부 팀 전달용)
        - business_improvement → Story
        """
        pass

    async def sync_status(
        self,
        ticket_id: str,
        jira_issue_key: str
    ) -> None:
        """Jira 이슈 상태와 티켓 상태 동기화"""
        pass
```

#### 2.1.3 데이터 모델 확장

```python
class Ticket(Base):
    # 기존 필드...

    # Jira 연동 필드
    jira_issue_key: Optional[str] = None
    jira_project_key: Optional[str] = None
    jira_synced_at: Optional[datetime] = None
```

#### 2.1.4 설정

```python
# app/config.py

class Settings:
    # Jira 설정
    jira_base_url: str = "https://your-org.atlassian.net"
    jira_api_token: str  # 환경 변수에서 로드
    jira_email: str
    jira_default_project: str = "VOC"
```

### 2.2 실제 로그 시스템 연동

#### 2.2.1 지원 대상

| 로그 시스템 | 연동 방식 | 우선순위 |
|------------|-----------|----------|
| Elasticsearch | REST API | P0 |
| Datadog | Log Query API | P1 |
| CloudWatch | Logs Insights | P2 |
| Splunk | REST API | P2 |

#### 2.2.2 아키텍처

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   VOC 시스템 │ ──▶ │  Log Adapter     │ ──▶ │  로그 시스템      │
│             │     │  (인터페이스)     │     │  (ES/Datadog/등) │
└─────────────┘     └──────────────────┘     └─────────────────┘
```

#### 2.2.3 인터페이스 정의

```python
# app/services/log_adapter.py

from abc import ABC, abstractmethod

class LogAdapter(ABC):
    """로그 시스템 어댑터 인터페이스"""

    @abstractmethod
    async def search_logs(
        self,
        query: str,
        time_range: TimeRange,
        limit: int = 100
    ) -> List[LogEntry]:
        """로그 검색"""
        pass

    @abstractmethod
    async def get_error_context(
        self,
        error_id: str,
        context_window: int = 10
    ) -> LogContext:
        """에러 전후 컨텍스트 조회"""
        pass


class ElasticsearchAdapter(LogAdapter):
    """Elasticsearch 어댑터"""
    pass


class DatadogAdapter(LogAdapter):
    """Datadog 어댑터"""
    pass
```

#### 2.2.4 RAG 시스템 확장

```python
# 실시간 로그 검색 통합
class EnhancedRAGService:
    def __init__(
        self,
        mock_rag: RAGService,  # 기존 Mock RAG
        log_adapter: LogAdapter  # 실제 로그 시스템
    ):
        pass

    async def search(self, query: str) -> List[LogEntry]:
        """
        1. 실제 로그 시스템에서 먼저 검색
        2. 결과 없으면 Mock RAG fallback
        """
        pass
```

### 2.3 알림 채널 확장

#### 2.3.1 지원 채널

| 채널 | 현재 상태 | 확장 계획 |
|------|-----------|-----------|
| Slack | ✅ 구현됨 | 스레드 지원 추가 |
| Email | ❌ | SMTP/SES 연동 |
| MS Teams | ❌ | Webhook 연동 |
| PagerDuty | ❌ | 긴급 알림 연동 |

#### 2.3.2 알림 서비스 추상화

```python
# app/services/notification_service.py

class NotificationService:
    def __init__(
        self,
        slack: SlackService,
        email: Optional[EmailService] = None,
        teams: Optional[TeamsService] = None
    ):
        self.channels = {
            "slack": slack,
            "email": email,
            "teams": teams
        }

    async def send(
        self,
        channel: str,
        message: NotificationMessage
    ) -> None:
        """채널별 알림 전송"""
        pass

    async def broadcast(
        self,
        message: NotificationMessage,
        channels: List[str] = ["slack"]
    ) -> None:
        """다중 채널 동시 알림"""
        pass
```

---

## 3. LLM 확장

### 3.1 상용 LLM 연동

#### 3.1.1 지원 모델

| Provider | Model | 용도 |
|----------|-------|------|
| OpenAI | GPT-4 | 고품질 분석 |
| OpenAI | GPT-4 Turbo | 비용 최적화 |
| Anthropic | Claude 3 | 긴 컨텍스트 처리 |
| Ollama | Mistral/Llama | 로컬 개발/테스트 |

#### 3.1.2 LLM 라우터

```python
# app/services/llm_router.py

class LLMRouter:
    """
    요청 특성에 따라 적절한 LLM 선택
    """

    def select_model(
        self,
        task: str,
        urgency: Urgency,
        context_length: int
    ) -> str:
        """
        - 긴급 + 짧은 컨텍스트 → GPT-4 Turbo (빠른 응답)
        - 비긴급 + 긴 컨텍스트 → Claude 3 (긴 컨텍스트)
        - 개발/테스트 → Ollama (비용 절감)
        """
        pass
```

### 3.2 프롬프트 관리

#### 3.2.1 프롬프트 버전 관리

```python
# app/prompts/prompt_manager.py

class PromptManager:
    def __init__(self, prompt_dir: str = "prompts"):
        self.prompts = self._load_prompts(prompt_dir)

    def get_prompt(
        self,
        name: str,
        version: str = "latest"
    ) -> str:
        """버전별 프롬프트 조회"""
        pass

    def render_prompt(
        self,
        name: str,
        variables: Dict[str, Any]
    ) -> str:
        """변수 바인딩된 프롬프트 생성"""
        pass
```

#### 3.2.2 프롬프트 디렉토리 구조

```
prompts/
├── normalizer/
│   ├── v1.0.0.md
│   └── v1.1.0.md
├── solver/
│   ├── v1.0.0.md
│   └── v1.1.0.md
└── manifest.yaml
```

---

## 4. 인증/권한 시스템

### 4.1 인증 방식

| 방식 | 용도 | 우선순위 |
|------|------|----------|
| JWT | API 인증 | P0 |
| OAuth 2.0 | SSO 연동 | P1 |
| API Key | 외부 시스템 연동 | P1 |

### 4.2 역할 기반 접근 제어 (RBAC)

```python
# app/auth/roles.py

class Role(Enum):
    ADMIN = "admin"           # 전체 권한
    MANAGER = "manager"       # 승인/거부 권한
    VIEWER = "viewer"         # 조회 권한
    SUBMITTER = "submitter"   # VOC 제출 권한

# 권한 매핑
PERMISSIONS = {
    Role.ADMIN: ["*"],
    Role.MANAGER: [
        "ticket:read",
        "ticket:confirm",
        "ticket:reject",
        "ticket:analyze"
    ],
    Role.VIEWER: ["ticket:read"],
    Role.SUBMITTER: ["voc:submit", "ticket:read"]
}
```

### 4.3 API 보호

```python
# app/auth/dependencies.py

async def get_current_user(
    token: str = Depends(oauth2_scheme)
) -> User:
    """현재 사용자 조회"""
    pass

def require_permission(permission: str):
    """권한 검증 데코레이터"""
    pass

# 사용 예시
@router.post("/tickets/{ticket_id}/confirm")
@require_permission("ticket:confirm")
async def confirm_ticket(
    ticket_id: str,
    current_user: User = Depends(get_current_user)
):
    pass
```

---

## 5. 인프라 확장

### 5.1 데이터베이스 마이그레이션

| 현재 | 목표 | 이점 |
|------|------|------|
| SQLite | PostgreSQL | 동시성, 확장성, 안정성 |

#### 5.1.1 마이그레이션 단계

1. **스키마 변환**: SQLite → PostgreSQL DDL
2. **데이터 마이그레이션**: 기존 데이터 이관
3. **연결 풀 설정**: asyncpg + connection pooling
4. **읽기 복제본**: 읽기 성능 최적화 (선택)

### 5.2 컨테이너화

```yaml
# docker-compose.prod.yml

version: '3.8'

services:
  backend:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

  frontend:
    build: ./frontend
    ports:
      - "80:80"

  postgres:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
```

### 5.3 모니터링 스택

```yaml
# monitoring/docker-compose.yml

services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    volumes:
      - grafana_data:/var/lib/grafana

  loki:
    image: grafana/loki
```

---

## 6. 학습 기반 개선

### 6.1 피드백 루프

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Agent 판단  │ ──▶ │  관리자 피드백    │ ──▶ │  학습 데이터     │
│             │     │  (승인/거부)      │     │  (Fine-tuning)  │
└─────────────┘     └──────────────────┘     └─────────────────┘
                           │
                           ▼
                    ┌──────────────────┐
                    │  신뢰도 보정      │
                    │  (Confidence     │
                    │   Calibration)   │
                    └──────────────────┘
```

### 6.2 거부 패턴 분석

```python
# app/services/feedback_analyzer.py

class FeedbackAnalyzer:
    async def analyze_rejections(
        self,
        time_range: TimeRange
    ) -> List[RejectionPattern]:
        """
        반복 거부 패턴 분석
        - 특정 유형 오분류 패턴
        - 신뢰도 임계값 조정 필요성
        - 프롬프트 개선 포인트
        """
        pass

    async def suggest_rules(
        self,
        patterns: List[RejectionPattern]
    ) -> List[AutomationRule]:
        """
        패턴 기반 자동화 규칙 제안
        - 특정 키워드 → 특정 유형
        - 반복 오분류 케이스 룰화
        """
        pass
```

---

## 7. 확장 로드맵

### Phase 7: 프로덕션 준비 (2주)

| 작업 | 설명 | 우선순위 |
|------|------|----------|
| PostgreSQL 마이그레이션 | 데이터베이스 교체 | P0 |
| JWT 인증 구현 | API 보안 | P0 |
| Docker 환경 구성 | 컨테이너화 | P0 |
| CI/CD 파이프라인 | 자동 배포 | P1 |

### Phase 8: 외부 연동 (3주)

| 작업 | 설명 | 우선순위 |
|------|------|----------|
| Jira 연동 | 이슈 생성 자동화 | P0 |
| 실제 로그 연동 | Elasticsearch 연동 | P0 |
| 상용 LLM 연동 | GPT-4/Claude 연동 | P1 |
| Email 알림 | SMTP 연동 | P2 |

### Phase 9: 운영 고도화 (4주)

| 작업 | 설명 | 우선순위 |
|------|------|----------|
| 모니터링 구축 | Prometheus/Grafana | P0 |
| 로그 중앙화 | Loki/ELK | P1 |
| 알림 고도화 | PagerDuty 연동 | P2 |
| 피드백 분석 | 학습 기반 개선 | P2 |

---

## 8. 리스크 및 대응

| 리스크 | 영향도 | 대응 방안 |
|--------|--------|-----------|
| LLM API 비용 증가 | 높음 | 캐싱, 모델 최적화, 비용 모니터링 |
| 외부 시스템 장애 | 중간 | Circuit Breaker, Fallback |
| 데이터 마이그레이션 실패 | 높음 | 롤백 계획, 단계적 마이그레이션 |
| 보안 취약점 | 높음 | 보안 감사, 정기 점검 |

---

## 9. 참고

### 9.1 관련 문서

- [POC 결과 보고서](./poc-results.md)
- [비기능 요구사항](../01-requirements/non-functional-requirements.md)
- [API 명세서](../04-api/api-endpoints.md)

### 9.2 외부 리소스

- [Jira REST API Documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [Elasticsearch Python Client](https://elasticsearch-py.readthedocs.io/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
