/**
 * VOC Input Page
 */

import { useVocInput } from '../hooks/useVocInput';
import './VocInputPage.css';

export const VocInputPage = () => {
  const {
    formData,
    errors,
    isSubmitting,
    submitError,
    updateField,
    handleSubmit,
  } = useVocInput();

  const charCount = formData.rawVoc.length;
  const charCountClass =
    charCount >= 5000 ? 'error' : charCount >= 4000 ? 'warning' : '';

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await handleSubmit();
  };

  return (
    <div className="page-container">
      <h1 className="page-title">VOC 입력</h1>

      <div className="voc-info-banner">
        <p>
          💡 고객으로부터 접수된 문의 내용을 입력해주세요.
          <br />
          AI Agent가 자동으로 분석하여 처리 방안을 제시합니다.
        </p>
      </div>

      {submitError && <div className="error-banner">{submitError}</div>}

      <form className="voc-form" onSubmit={onSubmit}>
        <div className="form-field">
          <label className="required">고객명</label>
          <input
            type="text"
            placeholder="예: 홍길동"
            maxLength={100}
            value={formData.customerName}
            onChange={(e) => updateField('customerName', e.target.value)}
            className={errors.customerName ? 'error' : ''}
          />
          {errors.customerName && (
            <p className="error-message">{errors.customerName}</p>
          )}
        </div>

        <div className="form-field">
          <label className="required">접수 채널</label>
          <div className="radio-group">
            <label>
              <input
                type="radio"
                name="channel"
                value="email"
                checked={formData.channel === 'email'}
                onChange={(e) => updateField('channel', e.target.value as any)}
              />
              Email
            </label>
            <label>
              <input
                type="radio"
                name="channel"
                value="slack"
                checked={formData.channel === 'slack'}
                onChange={(e) => updateField('channel', e.target.value as any)}
              />
              Slack
            </label>
          </div>
        </div>

        <div className="form-field">
          <label className="required">접수 일시</label>
          <input
            type="datetime-local"
            value={formData.receivedAt}
            onChange={(e) => updateField('receivedAt', e.target.value)}
          />
        </div>

        <div className="form-field">
          <label className="required">VOC 내용</label>
          <textarea
            placeholder="고객의 문의 내용을 입력하세요..."
            maxLength={5000}
            value={formData.rawVoc}
            onChange={(e) => updateField('rawVoc', e.target.value)}
            className={errors.rawVoc ? 'error' : ''}
          />
          <div className={`char-count ${charCountClass}`}>
            ({charCount}/5000)
          </div>
          {errors.rawVoc && <p className="error-message">{errors.rawVoc}</p>}
        </div>

        <div className="form-actions">
          <button type="submit" className="btn-primary" disabled={isSubmitting}>
            {isSubmitting ? '처리 중...' : 'VOC 제출'}
          </button>
        </div>
      </form>
    </div>
  );
};
