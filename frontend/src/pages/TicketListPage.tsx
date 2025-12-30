/**
 * Ticket List Page
 */

import { Link } from 'react-router-dom';
import { useTicketList } from '../hooks/useTicketList';
import { Loading } from '../components/atoms/Loading';
import './TicketListPage.css';
import '../components/atoms/Badge.css';

export const TicketListPage = () => {
  const { tickets, totalCount, isLoading, error } = useTicketList();

  if (isLoading) {
    return (
      <div className="page-container">
        <Loading />
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container">
        <div className="error-message">{error}</div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Ticket 목록</h1>
        <span className="ticket-count">총 {totalCount}건</span>
      </div>

      <div className="ticket-list">
        {tickets.map((ticket) => (
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
