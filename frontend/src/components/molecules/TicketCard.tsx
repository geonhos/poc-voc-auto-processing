/**
 * Ticket Card Component - Presentational
 */

import { Link } from 'react-router-dom';
import { Ticket } from '../../types/ticket.types';
import { Badge } from '../atoms/Badge';
import { format } from 'date-fns';
import './TicketCard.css';

interface TicketCardProps {
  ticket: Ticket;
}

export const TicketCard = ({ ticket }: TicketCardProps) => {
  const createdAt = ticket.created_at
    ? format(new Date(ticket.created_at), 'yyyy-MM-dd HH:mm')
    : '';

  const summary = ticket.decision_reason?.summary || '분석 대기 중...';
  const confidence = ticket.decision_confidence
    ? Math.round(ticket.decision_confidence * 100)
    : null;

  return (
    <Link to={`/tickets/${ticket.ticket_id}`} className="ticket-card">
      <div className="ticket-card-header">
        <span className="ticket-id">{ticket.ticket_id}</span>
        {ticket.urgency && (
          <Badge variant="urgency" value={ticket.urgency} />
        )}
      </div>

      <div className="ticket-summary">{summary}</div>

      <div className="ticket-meta">
        <Badge variant="status" value={ticket.status} />
        {confidence !== null && ticket.status === 'WAITING_CONFIRM' && (
          <span className="confidence">신뢰도: {confidence}%</span>
        )}
        <span className="customer-name">{ticket.customer_name}</span>
      </div>

      <div className="ticket-date">{createdAt}</div>
    </Link>
  );
};
