/**
 * Hook for Ticket List Page
 * Handles fetching, filtering, and auto-refresh
 */

import { useState, useEffect } from 'react';
import { ticketService } from '../services/ticket.service';
import { Ticket } from '../types/ticket.types';
import { mockTickets } from '../mocks/mockData';

// Use mock data for design review
const USE_MOCK_DATA = true;

export const useTicketList = () => {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTickets = async () => {
    try {
      setError(null);

      if (USE_MOCK_DATA) {
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 500));
        setTickets(mockTickets);
      } else {
        const data = await ticketService.getTickets();
        setTickets(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '티켓 목록을 불러오는데 실패했습니다');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTickets();

    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchTickets();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  return {
    tickets,
    isLoading,
    error,
    refetch: fetchTickets,
  };
};
