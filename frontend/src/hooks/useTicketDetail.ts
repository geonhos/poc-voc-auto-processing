/**
 * Hook for Ticket Detail Page
 * Handles fetching ticket, polling, and admin actions
 */

import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { ticketService } from '../services/ticket.service';
import type { Ticket } from '../types/ticket.types';

export const useTicketDetail = (ticketId: string) => {
  const navigate = useNavigate();
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchTicket = async () => {
    try {
      setError(null);
      const data = await ticketService.getTicket(ticketId);
      setTicket(data);

      // Setup polling if status is ANALYZING
      if (data.status === 'ANALYZING') {
        startPolling();
      } else {
        stopPolling();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '티켓을 불러오는데 실패했습니다');
    } finally {
      setIsLoading(false);
    }
  };

  const startPolling = () => {
    if (pollingIntervalRef.current) return;

    pollingIntervalRef.current = setInterval(() => {
      fetchTicket();
    }, 3000); // Poll every 3 seconds
  };

  const stopPolling = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  };

  useEffect(() => {
    fetchTicket();

    return () => {
      stopPolling();
    };
  }, [ticketId]);

  const handleConfirm = async (assignee?: string) => {
    setActionLoading('confirm');
    try {
      const updatedTicket = await ticketService.confirmTicket(ticketId, assignee);
      setTicket(updatedTicket);
      navigate('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : '승인 처리 중 오류가 발생했습니다');
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (reason: string, assignee?: string) => {
    setActionLoading('reject');
    try {
      const updatedTicket = await ticketService.rejectTicket(ticketId, reason, assignee);
      setTicket(updatedTicket);
      navigate('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : '거부 처리 중 오류가 발생했습니다');
    } finally {
      setActionLoading(null);
    }
  };

  const handleRetry = async () => {
    setActionLoading('retry');
    try {
      const updatedTicket = await ticketService.retryTicket(ticketId);
      setTicket(updatedTicket);
      // Start polling since status changed to ANALYZING
      startPolling();
    } catch (err) {
      setError(err instanceof Error ? err.message : '재분석 요청 중 오류가 발생했습니다');
    } finally {
      setActionLoading(null);
    }
  };

  return {
    ticket,
    isLoading,
    error,
    actionLoading,
    handleConfirm,
    handleReject,
    handleRetry,
    refetch: fetchTicket,
  };
};
