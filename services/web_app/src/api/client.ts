import axios from 'axios';
import type { LoanApplicationData, PredictApiResponse, SaveEnrichedRecordPayload } from '../types/loan';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

export const predictCreditRisk = async (
  application: LoanApplicationData,
  task: string = 'credit_risk'
): Promise<PredictApiResponse> => {
  const response = await apiClient.post<PredictApiResponse>(`/api/v1/predict?task=${task}`, application);
  return response.data;
};

// [C] Create
export const saveEnrichedRecord = async (data: SaveEnrichedRecordPayload) => {
  const response = await apiClient.post('/api/v1/enrich', data);
  return response.data;
};

export const getPortfolioSummary = async () => {
  const response = await apiClient.get('/api/v1/analytics/portfolio-summary');
  return response.data;
};

export interface EnrichedRecordsQuery {
  page?: number;
  pageSize?: number;
  source?: 'all' | 'live' | 'backlog';
  grade?: string;
  search?: string;
}

// [R] Read List
export const getEnrichedRecords = async (params: EnrichedRecordsQuery = {}) => {
  const { page = 1, pageSize = 20, source = 'all', grade, search } = params;
  const queryParams = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
    source,
  });
  if (grade && grade !== 'ALL') queryParams.append('grade', grade);
  if (search && search.trim()) queryParams.append('search', search.trim());

  const response = await apiClient.get(`/api/v1/enrich/records?${queryParams.toString()}`);
  return response.data;
};

// [R] Read Single
export const getSingleRecord = async (clientId: string) => {
  const response = await apiClient.get(`/api/v1/enrich/records/${clientId}`);
  return response.data;
};

// [U] Update Details
export const updateLoanRecord = async (clientId: string, updates: Record<string, any>) => {
  const response = await apiClient.put(`/api/v1/enrich/records/${clientId}`, updates);
  return response.data;
};

// [U] Update Decision / Label
export const updateRecordLabel = async (clientId: string, loanStatus: number) => {
  const response = await apiClient.patch(`/api/v1/enrich/records/${clientId}/label?loan_status=${loanStatus}`);
  return response.data;
};

// [D] Delete
export const deleteLoanRecord = async (clientId: string) => {
  const response = await apiClient.delete(`/api/v1/enrich/records/${clientId}`);
  return response.data;
};

export const getEnrichedStats = async () => {
  const response = await apiClient.get('/api/v1/enrich/stats');
  return response.data;
};
