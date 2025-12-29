/**
 * Ticket Detail Page
 */

import { useParams, Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import '../components/atoms/Badge.css';
import './TicketDetailPage.css';

const mockTicket = {
  ticket_id: 'VOC-20240115-0001',
  status: 'WAITING_CONFIRM',
  customer_name: '김철수',
  channel: 'email',
  raw_voc: '어제 밤에 카드 결제를 했는데 PG사에서 결제 실패 문자가 왔어요. 근데 제 카드에서는 빠져나갔거든요? 이거 확인 좀 해주세요.',
  created_at: '2024-01-15T09:30:00',
  analyzed_at: '2024-01-15T09:31:00',
  urgency: 'high',
  summary: 'PG 결제 API 타임아웃으로 인한 결제 실패',
  affected_system: 'PG결제시스템',
  decision_confidence: 0.85,
  root_cause: '외부 결제 API 타임아웃으로 인한 결제 실패. PaymentGateway 응답 시간 12.3초 (임계값 5초 초과). 내부 로직 정상 완료 후 외부 호출 단계에서 실패. 최근 7일간 동일 패턴 3건 발생.',
  action_title: '연동사 문의',
  action_description: 'PaymentGateway 담당자에게 API 타임아웃 증가 현상에 대한 문의가 필요합니다.',
};

export const TicketDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [rejectModalOpen, setRejectModalOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState('');

  const confidence = Math.round((mockTicket.decision_confidence || 0) * 100);

  const handleApprove = () => {
    alert('승인되었습니다');
    navigate('/');
  };

  const handleReject = () => {
    if (rejectReason.trim().length === 0) {
      alert('거부 사유를 입력해주세요');
      return;
    }
    alert('거부되었습니다');
    setRejectModalOpen(false);
    navigate('/');
  };

  return (
    <div className="page-container">
      <Link to="/" className="breadcrumb">
        ← 목록으로
      </Link>

      {/* Ticket Header Card */}
      <div className="ticket-header-card">
        <h2 className="ticket-id-large">{mockTicket.ticket_id}</h2>
        <div className="ticket-header-meta">
          <span className={`badge badge-status badge-${mockTicket.status}`}>
            {mockTicket.status}
          </span>
          {mockTicket.urgency && (
            <span className={`badge badge-urgency badge-${mockTicket.urgency}`}>
              {mockTicket.urgency}
            </span>
          )}
        </div>
        <div className="ticket-timestamps">
          생성: {new Date(mockTicket.created_at).toLocaleString('ko-KR')}
          {mockTicket.analyzed_at && ` | 분석: ${new Date(mockTicket.analyzed_at).toLocaleString('ko-KR')}`}
        </div>
      </div>

      {/* VOC 원문 Section */}
      <section className="voc-section">
        <h3>📝 VOC 원문</h3>
        <div className="voc-meta">
          <span>고객명: {mockTicket.customer_name}</span>
          <span>|</span>
          <span>채널: {mockTicket.channel}</span>
        </div>
        <div className="voc-meta">
          <span>접수: {new Date(mockTicket.created_at).toLocaleString('ko-KR')}</span>
        </div>
        <div className="voc-content">{mockTicket.raw_voc}</div>
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

        {mockTicket.affected_system && (
          <div className="affected-system">
            영향 시스템: <span>{mockTicket.affected_system}</span>
          </div>
        )}
      </section>

      {/* 판단 요약 */}
      <section className="summary-section">
        <h3>📋 판단 요약</h3>
        <p>{mockTicket.summary}</p>
      </section>

      {/* 판단 근거 */}
      <section className="evidence-section">
        <h3>✅ 판단 근거</h3>
        <p>{mockTicket.root_cause}</p>
      </section>

      {/* 제안 액션 */}
      <section className="action-section">
        <h3>💡 제안 액션: {mockTicket.action_title}</h3>
        <p>{mockTicket.action_description}</p>
      </section>

      {/* Admin Actions */}
      {mockTicket.status === 'WAITING_CONFIRM' && (
        <div className="admin-actions">
          <h3>관리자 액션</h3>
          <div className="action-buttons">
            <button className="btn-approve" onClick={handleApprove}>
              ✓ 승인
            </button>
            <button className="btn-reject" onClick={() => setRejectModalOpen(true)}>
              ✗ 거부
            </button>
            <button className="btn-reanalyze" onClick={() => alert('재분석 요청')}>
              ↻ 재분석
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
              <button className="btn-danger" onClick={handleReject}>
                거부 확인
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
