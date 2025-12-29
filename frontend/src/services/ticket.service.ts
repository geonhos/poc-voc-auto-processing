/**
 * Ticket Service - API calls for Ticket operations
 */

import { apiClient } from './api.service';
import { Ticket } from '../types/ticket.types';

export interface TicketListParams {
  skip?: number;
  limit?: number;
}

export const ticketService = {
  /**
   * Get all tickets
   */
  async getTickets(params?: TicketListParams): Promise<Ticket[]> {
    const response = await apiClient.get<Ticket[]>('/tickets', { params });
    return response.data;
  },

  /**
   * Get a single ticket by ID
   */
  async getTicket(ticketId: string): Promise<Ticket> {
    const response = await apiClient.get<Ticket>(`/tickets/${ticketId}`);
    return response.data;
  },

  /**
   * Approve a ticket (WAITING_CONFIRM → DONE)
   */
  async approveTicket(ticketId: string): Promise<void> {
    await apiClient.post(`/tickets/${ticketId}/approve`);
  },

  /**
   * Reject a ticket (WAITING_CONFIRM → REJECTED)
   */
  async rejectTicket(ticketId: string, reason: string): Promise<void> {
    await apiClient.post(`/tickets/${ticketId}/reject`, { reason });
  },

  /**
   * Request re-analysis (WAITING_CONFIRM → ANALYZING)
   */
  async reanalyzeTicket(ticketId: string): Promise<void> {
    await apiClient.post(`/tickets/${ticketId}/reanalyze`);
  },
};
