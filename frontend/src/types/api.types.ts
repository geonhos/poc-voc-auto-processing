/**
 * API Request/Response Types
 */

import type { Channel } from './ticket.types';

export interface CreateVocRequest {
  raw_voc: string;
  customer_name: string;
  channel: Channel;
  received_at: string;
}

export interface CreateVocResponse {
  ticket_id: string;
  status: string;
  message: string;
}

export interface ConfirmTicketRequest {
  assignee?: string;
}

export interface RejectTicketRequest {
  reject_reason: string;
  assignee?: string;
}

export interface CompleteManualTicketRequest {
  manual_resolution: string;
  assignee?: string;
}

export interface ApiError {
  detail: string;
}
