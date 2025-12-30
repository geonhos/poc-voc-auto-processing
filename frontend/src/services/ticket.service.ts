/**
 * Ticket Service - API calls for Ticket operations
 */

import { apiClient } from './api.service';
import type { Ticket, TicketStatus, Urgency } from '../types/ticket.types';
import type { ConfirmTicketRequest, RejectTicketRequest } from '../types/api.types';

export interface TicketListParams {
  status?: TicketStatus[];
  urgency?: Urgency;
  page?: number;
  limit?: number;
}

export interface TicketListResponse {
  tickets: Ticket[];
  total_count: number;
  page: number;
  limit: number;
  total_pages: number;
}

export const ticketService = {
  /**
   * Get all tickets with pagination and filters
   */
  async getTickets(params?: TicketListParams): Promise<TicketListResponse> {
    const response = await apiClient.get<TicketListResponse>('/api/v1/tickets', { params });
    return response.data;
  },

  /**
   * Get a single ticket by ID
   */
  async getTicket(ticketId: string): Promise<Ticket> {
    const response = await apiClient.get<Ticket>(`/api/v1/tickets/${ticketId}`);
    return response.data;
  },

  /**
   * Confirm a ticket (WAITING_CONFIRM → DONE)
   */
  async confirmTicket(ticketId: string, assignee?: string): Promise<Ticket> {
    const data: ConfirmTicketRequest = { assignee };
    const response = await apiClient.post<Ticket>(`/api/v1/tickets/${ticketId}/confirm`, data);
    return response.data;
  },

  /**
   * Reject a ticket (WAITING_CONFIRM → REJECTED)
   */
  async rejectTicket(ticketId: string, reject_reason: string, assignee?: string): Promise<Ticket> {
    const data: RejectTicketRequest = { reject_reason, assignee };
    const response = await apiClient.post<Ticket>(`/api/v1/tickets/${ticketId}/reject`, data);
    return response.data;
  },

  /**
   * Retry ticket analysis (WAITING_CONFIRM → ANALYZING)
   */
  async retryTicket(ticketId: string): Promise<Ticket> {
    const response = await apiClient.post<Ticket>(`/api/v1/tickets/${ticketId}/retry`);
    return response.data;
  },

  /**
   * Complete manual ticket (MANUAL_REQUIRED → DONE)
   */
  async completeManualTicket(ticketId: string, manual_resolution: string, assignee?: string): Promise<Ticket> {
    const data = { manual_resolution, assignee };
    const response = await apiClient.post<Ticket>(`/api/v1/tickets/${ticketId}/complete`, data);
    return response.data;
  },
};
