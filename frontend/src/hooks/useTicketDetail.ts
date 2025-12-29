/**
 * Hook for Ticket Detail Page
 * Handles fetching ticket, polling, and admin actions
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ticketService } from '../services/ticket.service';
import { Ticket } from '../types/ticket.types';
import { mockTickets } from '../mocks/mockData';

// Use mock data for design review
const USE_MOCK_DATA = true;

export const useTicketDetail = (ticketId: string) => {
  const navigate = useNavigate();
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchTicket = async () => {
    try {
      setError(null);

      if (USE_MOCK_DATA) {
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 300));
        const mockTicket = mockTickets.find(t => t.ticket_id === ticketId);
        if (mockTicket) {
          setTicket(mockTicket);
        } else {
          setError('티켓을 찾을 수 없습니다');
        }
      } else {
        const data = await ticketService.getTicket(ticketId);
        setTicket(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '티켓을 불러오는데 실패했습니다');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTicket();

    // Auto-refresh every 5 seconds
    const interval = setInterval(() => {
      fetchTicket();
    }, 5000);

    return () => clearInterval(interval);
  }, [ticketId]);

  const handleApprove = async () => {
    setActionLoading('approve');
    try {
      await ticketService.approveTicket(ticketId);
      navigate('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : '승인 처리 중 오류가 발생했습니다');
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (reason: string) => {
    setActionLoading('reject');
    try {
      await ticketService.rejectTicket(ticketId, reason);
      navigate('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : '거부 처리 중 오류가 발생했습니다');
    } finally {
      setActionLoading(null);
    }
  };

  const handleReanalyze = async () => {
    setActionLoading('reanalyze');
    try {
      await ticketService.reanalyzeTicket(ticketId);
      await fetchTicket(); // Refresh immediately
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
    handleApprove,
    handleReject,
    handleReanalyze,
    refetch: fetchTicket,
  };
};
