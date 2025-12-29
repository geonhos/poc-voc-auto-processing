/**
 * Domain Types - Ticket
 */

export type TicketStatus =
  | 'OPEN'
  | 'ANALYZING'
  | 'WAITING_CONFIRM'
  | 'DONE'
  | 'MANUAL_REQUIRED'
  | 'REJECTED';

export type Channel = 'email' | 'slack';

export type Urgency = 'low' | 'medium' | 'high';

export type ProblemType =
  | 'integration_error'
  | 'code_error'
  | 'business_improvement';

export type ActionType =
  | 'integration_inquiry'
  | 'code_fix'
  | 'business_proposal';

export interface Ticket {
  // Basic info
  ticket_id: string;
  status: TicketStatus;
  created_at: string;
  updated_at: string;
  assignee?: string;

  // VOC input
  raw_voc: string;
  customer_name: string;
  channel: Channel;
  received_at: string;

  // Normalization result
  summary?: string;
  suspected_type_primary?: string;
  suspected_type_secondary?: string;
  affected_system?: string;
  urgency?: Urgency;

  // Agent analysis result
  agent_decision_primary?: ProblemType;
  agent_decision_secondary?: string;
  decision_confidence?: number;
  decision_reason?: {
    root_cause_analysis: string;
    evidence_summary: string;
    confidence_breakdown: {
      error_pattern_clarity: number;
      log_voc_correlation: number;
      similar_case_match: number;
      system_info_availability: number;
    };
    similar_cases_used: string[];
    log_summary?: string;
  };
  action_proposal?: {
    action_type: ActionType;
    title: string;
    description: string;
    target_system?: string;
    contact_info?: string;
    code_location?: string;
    error_details?: string;
    business_impact?: string;
    suggested_improvement?: string;
  };
  analyzed_at?: string;

  // Admin action
  confirmed_at?: string;
  reject_reason?: string;
  manual_resolution?: string;
}

export interface TicketFilters {
  status?: TicketStatus[];
  urgency?: Urgency;
}

export interface TicketListResponse {
  tickets: Ticket[];
  total: number;
  page: number;
  limit: number;
}
