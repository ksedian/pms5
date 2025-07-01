import { apiClient, handleApiError } from './apiClient';
import { LoginRequest, LoginResponse, User, TwoFactorSetupResponse, UserProfileResponse } from '../types/auth';

class AuthService {
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    try {
      const response = await apiClient.post<LoginResponse>('/api/auth/login', credentials);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  async register(userData: { username: string; email: string; password: string; phone_number?: string }): Promise<any> {
    try {
      const response = await apiClient.post('/api/auth/register', userData);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  async getProfile(): Promise<UserProfileResponse> {
    try {
      const response = await apiClient.get<UserProfileResponse>('/api/auth/profile');
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  async logout(): Promise<void> {
    try {
      await apiClient.post('/api/auth/logout');
    } catch (error) {
      // Игнорируем ошибки logout на backend
      console.warn('Logout error:', error);
    } finally {
      localStorage.removeItem('access_token');
    }
  }

  async setup2FA(): Promise<TwoFactorSetupResponse> {
    try {
      const response = await apiClient.post<TwoFactorSetupResponse>('/api/auth/setup-2fa');
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  async verify2FA(token: string, backup_code?: string): Promise<any> {
    try {
      const payload = backup_code ? { backup_code } : { token };
      const response = await apiClient.post('/api/auth/verify-2fa', payload);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<any> {
    try {
      const response = await apiClient.post('/api/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      });
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }
}

export const authService = new AuthService(); 