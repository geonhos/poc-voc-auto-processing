/**
 * Ticket Detail Page
 */

import { useParams, Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import '../components/atoms/Badge.css';
import { useTicketDetail } from '../hooks/useTicketDetail';
import { Badge } from '../components/atoms/Badge';
import { Loading } from '../components/atoms/Loading';
import { format } from 'date-fns';
import { useState } from 'react';
import './TicketDetailPage.css';

export const TicketDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const {
    ticket,
    isLoading,
    error,
    actionLoading,
    handleApprove,
    handleReject,
    handleReanalyze,
  } = useTicketDetail(id!);

  const [rejectModalOpen, setRejectModalOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState('');

  if (isLoading) {
    return (
      <div className="page-container">
        <Loading />
      </div>
    );
  }

  if (error || !ticket) {
    return (
      <div className="page-container">
        <div className="error-state">
          <p>{error || '티켓을 찾을 수 없습니다'}</p>
        </div>
      </div>
    );
  }

  const createdAt = ticket.created_at
    ? format(new Date(ticket.created_at), 'yyyy-MM-dd HH:mm')
    : '';
  const analyzedAt = ticket.analyzed_at
    ? format(new Date(ticket.analyzed_at), 'yyyy-MM-dd HH:mm')
    : '';

  const confidence = ticket.decision_confidence
    ? Math.round(ticket.decision_confidence * 100)
    : null;

  const onReject = () => {
    if (rejectReason.trim().length === 0) {
      alert('거부 사유를 입력해주세요');
      return;
    }
    handleReject(rejectReason);
    setRejectModalOpen(false);
  };

  return (
    <div className="page-container">
      <Link to="/" className="breadcrumb">
        ← 목록으로
      </Link>

      {/* Ticket Header Card */}
      <div className="ticket-header-card">
        <h2 className="ticket-id-large">{ticket.ticket_id}</h2>
        <div className="ticket-header-meta">
          <Badge variant="status" value={ticket.status} />
          {ticket.urgency && <Badge variant="urgency" value={ticket.urgency} />}
        </div>
        <div className="ticket-timestamps">
          생성: {createdAt}
          {analyzedAt && ` | 분석: ${analyzedAt}`}
        </div>
      </div>

      {/* VOC 원문 Section */}
      <section className="voc-section">
        <h3>📝 VOC 원문</h3>
        <div className="voc-meta">
          <span>고객명: {ticket.customer_name}</span>
          <span>|</span>
          <span>채널: {ticket.channel}</span>
        </div>
        <div className="voc-meta">
          <span>접수: {createdAt}</span>
        </div>
        <div className="voc-content">{ticket.raw_voc}</div>
      </section>

      {/* Agent 분석 결과 */}
      {ticket.status === 'ANALYZING' && (
        <section className="analysis-section analyzing">
          <h3>🤖 Agent 분석 결과</h3>
          <div className="analyzing-state">
            <div className="spinner"></div>
            <p>Agent가 분석 중입니다...</p>
            <p className="analyzing-hint">예상 소요 시간: 약 30초</p>
          </div>
        </section>
      )}

      {ticket.status === 'WAITING_CONFIRM' && ticket.decision_reason && (
        <>
          <section className="analysis-section">
            <h3>🤖 Agent 분석 결과</h3>
            {confidence !== null && (
              <div className="confidence-bar">
                <span>신뢰도:</span>
                <div className="progress-bar">
                  <div
                    className={`progress ${
                      confidence >= 80
                        ? 'high'
                        : confidence >= 60
                        ? 'medium'
                        : 'low'
                    }`}
                    style={{ width: `${confidence}%` }}
                  ></div>
                </div>
                <span>
                  {confidence}% (
                  {confidence >= 80 ? '높음' : confidence >= 60 ? '중간' : '낮음'}
                  )
                </span>
              </div>
            )}

            {ticket.problem_type_primary && (
              <div className="problem-types">
                <div className="problem-type-card">
                  <strong>문제 유형</strong>
                  <p>{ticket.problem_type_primary}</p>
                </div>
                {ticket.problem_type_secondary && (
                  <div className="problem-type-card">
                    <strong>Secondary</strong>
                    <p>{ticket.problem_type_secondary}</p>
                  </div>
                )}
              </div>
            )}

            {ticket.affected_system && (
              <div className="affected-system">
                영향 시스템: <span>{ticket.affected_system}</span>
              </div>
            )}
          </section>

          {ticket.decision_reason.summary && (
            <section className="summary-section">
              <h3>📋 판단 요약</h3>
              <p>{ticket.decision_reason.summary}</p>
            </section>
          )}

          {ticket.decision_reason.root_cause_analysis && (
            <section className="evidence-section">
              <h3>✅ 판단 근거</h3>
              <p>{ticket.decision_reason.root_cause_analysis}</p>
            </section>
          )}

          {ticket.action_proposal && (
            <section className="action-section">
              <h3>💡 제안 액션: {ticket.action_proposal.title}</h3>
              <p>{ticket.action_proposal.description}</p>
            </section>
          )}
        </>
      )}

      {/* Admin Actions */}
      {ticket.status === 'WAITING_CONFIRM' && (
        <div className="admin-actions">
          <h3>관리자 액션</h3>
          <div className="action-buttons">
            <button
              className="btn-approve"
              onClick={handleApprove}
              disabled={actionLoading !== null}
            >
              {actionLoading === 'approve' ? '처리 중...' : '✓ 승인'}
            </button>
            <button
              className="btn-reject"
              onClick={() => setRejectModalOpen(true)}
              disabled={actionLoading !== null}
            >
              {actionLoading === 'reject' ? '처리 중...' : '✗ 거부'}
            </button>
            <button
              className="btn-reanalyze"
              onClick={handleReanalyze}
              disabled={actionLoading !== null}
            >
              {actionLoading === 'reanalyze' ? '처리 중...' : '↻ 재분석'}
            </button>
          </div>
        </div>
      )}

      {/* Reject Modal */}
      {rejectModalOpen && (
        <div className="modal-overlay" onClick={() => setRejectModalOpen(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>VOC 거부</h3>
              <button
                className="modal-close"
                onClick={() => setRejectModalOpen(false)}
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              <p>이 VOC를 거부하시겠습니까?</p>
              <p className="modal-warning">
                거부 시 Ticket이 종료되며, 재오픈할 수 없습니다.
              </p>
              <label>
                거부 사유 <span className="required-mark">*</span>
              </label>
              <textarea
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="거부 사유를 입력하세요..."
                maxLength={1000}
              />
              <div className="char-count">({rejectReason.length}/1000)</div>
            </div>
            <div className="modal-footer">
              <button
                className="btn-secondary"
                onClick={() => setRejectModalOpen(false)}
              >
                취소
              </button>
              <button className="btn-danger" onClick={onReject}>
                거부 확인
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
