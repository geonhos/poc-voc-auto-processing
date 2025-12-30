/**
 * VOC Service - API calls for VOC operations
 */

import { apiClient } from './api.service';
import type { CreateVocRequest, CreateVocResponse } from '../types/api.types';

export const vocService = {
  /**
   * Create a new VOC
   */
  async createVoc(data: CreateVocRequest): Promise<CreateVocResponse> {
    const response = await apiClient.post<CreateVocResponse>('/api/v1/voc', data);
    return response.data;
  },
};
