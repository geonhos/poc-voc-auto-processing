/**
 * Hook for Ticket List Page
 * Handles fetching, filtering, and auto-refresh
 */

import { useState, useEffect } from 'react';
import { ticketService, type TicketListParams } from '../services/ticket.service';
import type { Ticket } from '../types/ticket.types';

export const useTicketList = (filters?: TicketListParams) => {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [currentPage, setCurrentPage] = useState(filters?.page || 1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTickets = async (params?: TicketListParams) => {
    try {
      setError(null);
      const response = await ticketService.getTickets(params);
      setTickets(response.tickets);
      setTotalCount(response.total_count);
      setTotalPages(response.total_pages);
      setCurrentPage(response.page);
    } catch (err) {
      setError(err instanceof Error ? err.message : '티켓 목록을 불러오는데 실패했습니다');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTickets(filters);

    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchTickets(filters);
    }, 30000);

    return () => clearInterval(interval);
  }, [filters?.page, filters?.status, filters?.urgency]);

  return {
    tickets,
    totalCount,
    totalPages,
    currentPage,
    isLoading,
    error,
    refetch: fetchTickets,
  };
};
