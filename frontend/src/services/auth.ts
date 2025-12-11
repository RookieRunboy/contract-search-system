import api from './api';
import type { RegistrationRequestSummary, AuthUser, UserRole, UserRecord } from '../types';

export interface LoginApiResponse {
  access_token: string;
  token_type: string;
  expires_in?: number;
  user: {
    user_id: string;
    role: AuthUser['role'];
    status?: string;
    created_at?: string;
  };
}

export const login = async (userId: string, password: string): Promise<LoginApiResponse> => {
  return api.post('/auth/login', {
    user_id: userId,
    password,
  });
};

export const register = async (userId: string, password: string, confirmPassword: string) => {
  return api.post('/auth/register', {
    user_id: userId,
    password,
    confirm_password: confirmPassword,
  });
};

export interface RegistrationsResponse {
  code: number;
  message: string;
  data: RegistrationRequestSummary[];
}

export const fetchPendingRegistrations = async (): Promise<RegistrationsResponse> => {
  return api.get('/admin/registrations');
};

export const approveRegistration = async (requestId: string) => {
  return api.post(`/admin/registrations/${requestId}/approve`);
};

export const rejectRegistration = async (requestId: string, reason?: string) => {
  return api.post(`/admin/registrations/${requestId}/reject`, {
    reason,
  });
};

export interface UsersResponse {
  code: number;
  message: string;
  data: UserRecord[];
}

export const fetchAllUsers = async (): Promise<UsersResponse> => {
  return api.get('/admin/users');
};

export const updateUserRole = async (userId: string, role: UserRole) => {
  return api.put(`/admin/users/${userId}/role`, { role });
};

export const updateUserStatus = async (userId: string, status: 'active' | 'disabled') => {
  return api.put(`/admin/users/${userId}/status`, { status });
};
