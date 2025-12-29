/**
 * VOC Service - API calls for VOC operations
 */

import { apiClient } from './api.service';
import { CreateVocRequest, CreateVocResponse } from '../types/api.types';

export const vocService = {
  /**
   * Create a new VOC
   */
  async createVoc(data: CreateVocRequest): Promise<CreateVocResponse> {
    const response = await apiClient.post<CreateVocResponse>('/voc', data);
    return response.data;
  },
};
