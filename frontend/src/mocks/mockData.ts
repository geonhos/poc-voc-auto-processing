/**
 * Mock Data for Design Review
 */

import type { Ticket } from '../types/ticket.types';

export const mockTickets: Ticket[] = [
  {
    ticket_id: 'VOC-20240115-0001',
    status: 'WAITING_CONFIRM',
    raw_voc: '어제 밤에 카드 결제를 했는데 PG사에서 결제 실패 문자가 왔어요. 근데 제 카드에서는 빠져나갔거든요? 이거 확인 좀 해주세요.',
    customer_name: '김철수',
    channel: 'email',
    received_at: '2024-01-15T09:30:00',
    created_at: '2024-01-15T09:30:00',
    updated_at: '2024-01-15T09:31:00',
    analyzed_at: '2024-01-15T09:31:00',
    urgency: 'high',
    summary: 'PG 결제 API 타임아웃으로 인한 결제 실패',
    suspected_type_primary: 'integration_error',
    affected_system: 'PG결제시스템',
    agent_decision_primary: 'integration_error',
    decision_confidence: 0.85,
    decision_reason: {
      root_cause_analysis: '외부 결제 API 타임아웃으로 인한 결제 실패. 2024-01-15 14:32:01 - PaymentGateway 응답 시간 12.3초 (임계값 5초 초과). 내부 로직 정상 완료 후 외부 호출 단계에서 실패. 최근 7일간 동일 패턴 3건 발생.',
      evidence_summary: '타임아웃 로그 확인',
      confidence_breakdown: {
        error_pattern_clarity: 0.9,
        log_voc_correlation: 0.85,
        similar_case_match: 0.8,
        system_info_availability: 0.85,
      },
      similar_cases_used: ['VOC-001', 'VOC-002'],
    },
    action_proposal: {
      action_type: 'integration_inquiry',
      title: '연동사 문의',
      description: 'PaymentGateway 담당자에게 API 타임아웃 증가 현상에 대한 문의가 필요합니다.',
      contact_info: 'partner-support@pg.com',
    },
  },
  {
    ticket_id: 'VOC-20240115-0002',
    status: 'ANALYZING',
    raw_voc: '로그인이 안 돼요. 비밀번호 재설정도 해봤는데 계속 로그인 실패라고 나와요.',
    customer_name: '이영희',
    channel: 'slack',
    received_at: '2024-01-15T10:15:00',
    created_at: '2024-01-15T10:15:00',
    updated_at: '2024-01-15T10:15:00',
    urgency: 'medium',
  },
  {
    ticket_id: 'VOC-20240115-0003',
    status: 'DONE',
    raw_voc: '대시보드에서 차트가 너무 작아서 보기 힘들어요. 크게 할 수 있는 방법이 있나요?',
    customer_name: '박민수',
    channel: 'email',
    received_at: '2024-01-14T14:20:00',
    created_at: '2024-01-14T14:20:00',
    updated_at: '2024-01-14T14:21:00',
    analyzed_at: '2024-01-14T14:21:00',
    urgency: 'low',
    summary: 'UI/UX 개선 요청 - 차트 크기 조절 기능',
    suspected_type_primary: 'business_improvement',
    agent_decision_primary: 'business_improvement',
    decision_confidence: 0.92,
    decision_reason: {
      root_cause_analysis: '사용자 경험 개선을 위한 차트 확대 기능 요청',
      evidence_summary: '유사 요청 최근 30일간 15건',
      confidence_breakdown: {
        error_pattern_clarity: 0.95,
        log_voc_correlation: 0.9,
        similar_case_match: 0.92,
        system_info_availability: 0.9,
      },
      similar_cases_used: ['VOC-100', 'VOC-101'],
    },
  },
];
