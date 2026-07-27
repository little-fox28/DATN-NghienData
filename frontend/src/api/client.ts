import axios from 'axios';
import type { LoanApplicationData, PredictApiResponse } from '../types/loan';

const API_BASE_URL = 'http://127.0.0.1:8000';

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
