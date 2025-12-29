/**
 * VOC Input Page
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './VocInputPage.css';

export const VocInputPage = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    customerName: '',
    channel: 'email',
    receivedAt: new Date().toISOString().slice(0, 16),
    rawVoc: '',
  });
  const [errors, setErrors] = useState<any>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const charCount = formData.rawVoc.length;
  const charCountClass =
    charCount >= 5000 ? 'error' : charCount >= 4000 ? 'warning' : '';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const newErrors: any = {};
    if (!formData.customerName.trim()) {
      newErrors.customerName = '고객명은 필수 입력 항목입니다';
    }
    if (!formData.rawVoc.trim()) {
      newErrors.rawVoc = 'VOC 내용은 필수 입력 항목입니다';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setIsSubmitting(true);
    setTimeout(() => {
      navigate('/tickets/VOC-20240115-0001');
    }, 1000);
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

      <form className="voc-form" onSubmit={handleSubmit}>
        <div className="form-field">
          <label className="required">고객명</label>
          <input
            type="text"
            placeholder="예: 홍길동"
            maxLength={100}
            value={formData.customerName}
            onChange={(e) => {
              setFormData({ ...formData, customerName: e.target.value });
              setErrors({ ...errors, customerName: undefined });
            }}
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
                onChange={(e) =>
                  setFormData({ ...formData, channel: e.target.value })
                }
              />
              Email
            </label>
            <label>
              <input
                type="radio"
                name="channel"
                value="slack"
                checked={formData.channel === 'slack'}
                onChange={(e) =>
                  setFormData({ ...formData, channel: e.target.value })
                }
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
            onChange={(e) =>
              setFormData({ ...formData, receivedAt: e.target.value })
            }
          />
        </div>

        <div className="form-field">
          <label className="required">VOC 내용</label>
          <textarea
            placeholder="고객의 문의 내용을 입력하세요..."
            maxLength={5000}
            value={formData.rawVoc}
            onChange={(e) => {
              setFormData({ ...formData, rawVoc: e.target.value });
              setErrors({ ...errors, rawVoc: undefined });
            }}
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
