/**
 * Hook for VOC Input Page
 * Handles form state, validation, and submission
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { vocService } from '../services/voc.service';
import { Channel } from '../types/ticket.types';

interface VocFormData {
  customerName: string;
  channel: Channel;
  receivedAt: string;
  rawVoc: string;
}

interface VocFormErrors {
  customerName?: string;
  receivedAt?: string;
  rawVoc?: string;
}

export const useVocInput = () => {
  const navigate = useNavigate();

  const [formData, setFormData] = useState<VocFormData>({
    customerName: '',
    channel: 'email',
    receivedAt: new Date().toISOString().slice(0, 16),
    rawVoc: '',
  });

  const [errors, setErrors] = useState<VocFormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const validateForm = (): boolean => {
    const newErrors: VocFormErrors = {};

    // Customer name validation
    if (!formData.customerName.trim()) {
      newErrors.customerName = '고객명은 필수 입력 항목입니다';
    } else if (formData.customerName.length > 100) {
      newErrors.customerName = '고객명은 100자를 초과할 수 없습니다';
    }

    // Received at validation
    const receivedDate = new Date(formData.receivedAt);
    const now = new Date();
    if (receivedDate > now) {
      newErrors.receivedAt = '접수 일시는 현재 시점 이전이어야 합니다';
    }

    // VOC content validation
    if (!formData.rawVoc.trim()) {
      newErrors.rawVoc = 'VOC 내용은 필수 입력 항목입니다';
    } else if (formData.rawVoc.length > 5000) {
      newErrors.rawVoc = 'VOC 내용은 5000자를 초과할 수 없습니다';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    setSubmitError(null);

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      // For design review, just navigate to mock ticket
      await new Promise(resolve => setTimeout(resolve, 1000));
      navigate(`/tickets/VOC-20240115-0001`);
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : '요청 처리 중 오류가 발생했습니다');
    } finally {
      setIsSubmitting(false);
    }
  };

  const updateField = <K extends keyof VocFormData>(
    field: K,
    value: VocFormData[K]
  ) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Clear error when field is updated
    if (errors[field as keyof VocFormErrors]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  return {
    formData,
    errors,
    isSubmitting,
    submitError,
    updateField,
    handleSubmit,
  };
};
