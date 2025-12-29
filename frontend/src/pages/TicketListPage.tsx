/**
 * Ticket List Page
 */

import { Link } from 'react-router-dom';
import './TicketListPage.css';
import '../components/atoms/Badge.css';

const mockTickets = [
  {
    ticket_id: 'VOC-20240115-0001',
    status: 'WAITING_CONFIRM',
    customer_name: '김철수',
    urgency: 'high',
    summary: 'PG 결제 API 타임아웃으로 인한 결제 실패',
    decision_confidence: 0.85,
  },
  {
    ticket_id: 'VOC-20240115-0002',
    status: 'ANALYZING',
    customer_name: '이영희',
    urgency: 'medium',
    summary: '로그인 실패 문제',
  },
  {
    ticket_id: 'VOC-20240115-0003',
    status: 'DONE',
    customer_name: '박민수',
    urgency: 'low',
    summary: 'UI/UX 개선 요청 - 차트 크기 조절 기능',
    decision_confidence: 0.92,
  },
];

export const TicketListPage = () => {
  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Ticket 목록</h1>
        <span className="ticket-count">총 {mockTickets.length}건</span>
      </div>

      <div className="ticket-list">
        {mockTickets.map((ticket) => (
          <Link
            key={ticket.ticket_id}
            to={`/tickets/${ticket.ticket_id}`}
            className="ticket-card"
          >
            <div className="ticket-card-header">
              <span className="ticket-id">{ticket.ticket_id}</span>
              {ticket.urgency && (
                <span className={`badge badge-urgency badge-${ticket.urgency}`}>
                  {ticket.urgency}
                </span>
              )}
            </div>
            <div className="ticket-summary">
              {ticket.summary || '분석 대기 중...'}
            </div>
            <div className="ticket-meta">
              <span className={`badge badge-status badge-${ticket.status}`}>
                {ticket.status}
              </span>
              {ticket.decision_confidence && ticket.status === 'WAITING_CONFIRM' && (
                <span className="confidence">
                  신뢰도: {Math.round(ticket.decision_confidence * 100)}%
                </span>
              )}
              <span className="customer-name">{ticket.customer_name}</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};
