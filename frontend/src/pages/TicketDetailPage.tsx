/**
 * Ticket Detail Page
 */

import { useParams, Link } from 'react-router-dom';
import { useState } from 'react';
import { useTicketDetail } from '../hooks/useTicketDetail';
import { Loading } from '../components/atoms/Loading';
import '../components/atoms/Badge.css';
import './TicketDetailPage.css';

export const TicketDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const [rejectModalOpen, setRejectModalOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [manualResolution, setManualResolution] = useState('');

  const {
    ticket,
    isLoading,
    error,
    actionLoading,
    handleConfirm,
    handleReject,
    handleRetry,
    handleCompleteManual,
  } = useTicketDetail(id || '');

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
        <div className="error-message">{error || '티켓을 찾을 수 없습니다'}</div>
      </div>
    );
  }

  const confidence = Math.round((ticket.decision_confidence || 0) * 100);

  const onConfirmClick = () => {
    handleConfirm();
  };

  const onRejectClick = () => {
    if (rejectReason.trim().length === 0) {
      alert('거부 사유를 입력해주세요');
      return;
    }
    handleReject(rejectReason);
    setRejectModalOpen(false);
  };

  const onRetryClick = () => {
    handleRetry();
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
          <span className={`badge badge-status badge-${ticket.status}`}>
            {ticket.status}
          </span>
          {ticket.urgency && (
            <span className={`badge badge-urgency badge-${ticket.urgency}`}>
              {ticket.urgency}
            </span>
          )}
        </div>
        <div className="ticket-timestamps">
          생성: {new Date(ticket.created_at).toLocaleString('ko-KR')}
          {ticket.analyzed_at && ` | 분석: ${new Date(ticket.analyzed_at).toLocaleString('ko-KR')}`}
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
          <span>접수: {new Date(ticket.created_at).toLocaleString('ko-KR')}</span>
        </div>
        <div className="voc-content">{ticket.raw_voc}</div>
      </section>

      {/* Agent 분석 결과 */}
      <section className="analysis-section">
        <h3>🤖 Agent 분석 결과</h3>
        <div className="confidence-bar">
          <span>신뢰도:</span>
          <div className="progress-bar">
            <div
              className={`progress ${confidence >= 80 ? 'high' : confidence >= 60 ? 'medium' : 'low'}`}
              style={{ width: `${confidence}%` }}
            ></div>
          </div>
          <span>
            {confidence}% ({confidence >= 80 ? '높음' : confidence >= 60 ? '중간' : '낮음'})
          </span>
        </div>

        {ticket.affected_system && (
          <div className="affected-system">
            영향 시스템: <span>{ticket.affected_system}</span>
          </div>
        )}
      </section>

      {/* 판단 요약 */}
      <section className="summary-section">
        <h3>📋 판단 요약</h3>
        <p>{ticket.summary}</p>
      </section>

      {/* 판단 근거 */}
      {ticket.decision_reason && (
        <section className="evidence-section">
          <h3>✅ 판단 근거</h3>
          <p>{ticket.decision_reason.root_cause_analysis || ticket.decision_reason.evidence_summary || JSON.stringify(ticket.decision_reason)}</p>
        </section>
      )}

      {/* 제안 액션 */}
      {ticket.action_proposal && (
        <section className="action-section">
          <h3>💡 제안 액션: {ticket.action_proposal.title}</h3>
          <p>{ticket.action_proposal.description}</p>
        </section>
      )}

      {/* Admin Actions */}
      {ticket.status === 'WAITING_CONFIRM' && (
        <div className="admin-actions">
          <h3>관리자 액션</h3>
          <div className="action-buttons">
            <button
              className="btn-approve"
              onClick={onConfirmClick}
              disabled={actionLoading !== null}
            >
              ✓ 승인
            </button>
            <button
              className="btn-reject"
              onClick={() => setRejectModalOpen(true)}
              disabled={actionLoading !== null}
            >
              ✗ 거부
            </button>
            <button
              className="btn-reanalyze"
              onClick={onRetryClick}
              disabled={actionLoading !== null}
            >
              ↻ 재분석
            </button>
          </div>
        </div>
      )}

      {/* Manual Resolution Section */}
      {ticket.status === 'MANUAL_REQUIRED' && (
        <div className="manual-resolution-section">
          <div className="manual-resolution-header">
            <span className="warning-icon">⚠️</span>
            <div>
              <h3>수동 처리 필요</h3>
              <p>자동 분석이 불가하여 수동 처리가 필요합니다.</p>
            </div>
          </div>
          <div className="manual-resolution-form">
            <label>
              해결 내용 <span className="required-mark">*</span>
            </label>
            <textarea
              value={manualResolution}
              onChange={(e) => setManualResolution(e.target.value)}
              placeholder="수동으로 처리한 내용을 입력하세요..."
              maxLength={2000}
            />
            <div className="char-count">({manualResolution.length}/2000)</div>
            <button
              className="btn-complete"
              onClick={() => {
                if (manualResolution.trim().length === 0) {
                  alert('해결 내용을 입력해주세요');
                  return;
                }
                handleCompleteManual(manualResolution);
              }}
              disabled={actionLoading !== null || manualResolution.trim().length === 0}
            >
              {actionLoading === 'complete' ? '처리 중...' : '처리 완료'}
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
              <button className="modal-close" onClick={() => setRejectModalOpen(false)}>
                ×
              </button>
            </div>
            <div className="modal-body">
              <p>이 VOC를 거부하시겠습니까?</p>
              <p className="modal-warning">
                거부 시 Ticket이 종료되며, 재오픈할 수 없습니다.
              </p>
              <label>
                거부 사유 <span style={{ color: 'var(--error)' }}>*</span>
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
              <button className="btn-secondary" onClick={() => setRejectModalOpen(false)}>
                취소
              </button>
              <button className="btn-danger" onClick={onRejectClick}>
                거부 확인
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
