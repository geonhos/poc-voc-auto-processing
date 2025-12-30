/**
 * Ticket List Page
 */

import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useTicketList } from '../hooks/useTicketList';
import { Loading } from '../components/atoms/Loading';
import type { TicketStatus, Urgency } from '../types/ticket.types';
import './TicketListPage.css';
import '../components/atoms/Badge.css';

const STATUS_OPTIONS: { value: TicketStatus | ''; label: string }[] = [
  { value: '', label: '전체 상태' },
  { value: 'OPEN', label: 'OPEN' },
  { value: 'ANALYZING', label: 'ANALYZING' },
  { value: 'WAITING_CONFIRM', label: 'WAITING_CONFIRM' },
  { value: 'MANUAL_REQUIRED', label: 'MANUAL_REQUIRED' },
  { value: 'DONE', label: 'DONE' },
  { value: 'REJECTED', label: 'REJECTED' },
];

const URGENCY_OPTIONS: { value: Urgency | ''; label: string }[] = [
  { value: '', label: '전체 긴급도' },
  { value: 'high', label: '긴급' },
  { value: 'medium', label: '보통' },
  { value: 'low', label: '낮음' },
];

export const TicketListPage = () => {
  const [selectedStatus, setSelectedStatus] = useState<TicketStatus | ''>('');
  const [selectedUrgency, setSelectedUrgency] = useState<Urgency | ''>('');
  const [page, setPage] = useState(1);

  const filters = useMemo(() => ({
    status: selectedStatus ? [selectedStatus] : undefined,
    urgency: selectedUrgency || undefined,
    page,
  }), [selectedStatus, selectedUrgency, page]);

  const { tickets, totalCount, totalPages, currentPage, isLoading, error } = useTicketList(filters);

  const handleStatusChange = (value: string) => {
    setSelectedStatus(value as TicketStatus | '');
    setPage(1);
  };

  const handleUrgencyChange = (value: string) => {
    setSelectedUrgency(value as Urgency | '');
    setPage(1);
  };

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

  const renderPagination = () => {
    if (totalPages <= 1) return null;

    const pages: (number | string)[] = [];
    const maxVisiblePages = 5;

    if (totalPages <= maxVisiblePages) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      if (currentPage <= 3) {
        for (let i = 1; i <= 4; i++) pages.push(i);
        pages.push('...', totalPages);
      } else if (currentPage >= totalPages - 2) {
        pages.push(1, '...');
        for (let i = totalPages - 3; i <= totalPages; i++) pages.push(i);
      } else {
        pages.push(1, '...');
        for (let i = currentPage - 1; i <= currentPage + 1; i++) pages.push(i);
        pages.push('...', totalPages);
      }
    }

    return (
      <div className="pagination">
        <button
          className="pagination-btn"
          onClick={() => setPage(currentPage - 1)}
          disabled={currentPage === 1}
        >
          &lt;
        </button>
        {pages.map((p, idx) =>
          typeof p === 'number' ? (
            <button
              key={idx}
              className={`pagination-btn ${p === currentPage ? 'active' : ''}`}
              onClick={() => setPage(p)}
            >
              {p}
            </button>
          ) : (
            <span key={idx} className="pagination-ellipsis">{p}</span>
          )
        )}
        <button
          className="pagination-btn"
          onClick={() => setPage(currentPage + 1)}
          disabled={currentPage === totalPages}
        >
          &gt;
        </button>
      </div>
    );
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Ticket 목록</h1>
        <span className="ticket-count">총 {totalCount}건</span>
      </div>

      {/* Filters */}
      <div className="filters-section">
        <select
          value={selectedStatus}
          onChange={(e) => handleStatusChange(e.target.value)}
        >
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <select
          value={selectedUrgency}
          onChange={(e) => handleUrgencyChange(e.target.value)}
        >
          {URGENCY_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      <div className="ticket-list">
        {tickets.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📭</div>
            <p className="empty-title">티켓이 없습니다</p>
            <p className="empty-subtitle">선택한 필터에 해당하는 티켓이 없습니다.</p>
          </div>
        ) : (
          tickets.map((ticket) => (
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
          ))
        )}
      </div>

      {/* Pagination */}
      {renderPagination()}
    </div>
  );
};
