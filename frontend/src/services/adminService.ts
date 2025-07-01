import { apiClient, handleApiError } from './apiClient';
import { User, Role, Permission, AuditLog } from '../types/auth';

class AdminService {
  // User Management
  async getUsers(): Promise<{ users: User[]; total: number }> {
    try {
      const response = await apiClient.get('/api/admin/users');
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  async getUser(userId: number): Promise<{ user: User }> {
    try {
      const response = await apiClient.get(`/api/admin/users/${userId}`);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  async activateUser(userId: number): Promise<any> {
    try {
      const response = await apiClient.post(`/api/admin/users/${userId}/activate`);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  async deactivateUser(userId: number): Promise<any> {
    try {
      const response = await apiClient.post(`/api/admin/users/${userId}/deactivate`);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  async unlockUser(userId: number): Promise<any> {
    try {
      const response = await apiClient.post(`/api/admin/users/${userId}/unlock`);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Role Management
  async getRoles(): Promise<{ roles: Role[]; total: number }> {
    try {
      const response = await apiClient.get('/api/admin/roles');
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  async createRole(roleData: { name: string; description?: string }): Promise<{ role: Role; message: string }> {
    try {
      const response = await apiClient.post('/api/admin/roles', roleData);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  async updateRole(roleId: number, roleData: { name?: string; description?: string }): Promise<any> {
    try {
      const response = await apiClient.put(`/api/admin/roles/${roleId}`, roleData);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  async deleteRole(roleId: number): Promise<any> {
    try {
      const response = await apiClient.delete(`/api/admin/roles/${roleId}`);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Permission Management
  async getPermissions(): Promise<{ permissions: Permission[]; total: number }> {
    try {
      const response = await apiClient.get('/api/admin/permissions');
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  async createPermission(permissionData: { 
    name: string; 
    description: string; 
    resource: string; 
    action: string 
  }): Promise<{ permission: Permission; message: string }> {
    try {
      const response = await apiClient.post('/api/admin/permissions', permissionData);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  async updatePermission(permissionId: number, permissionData: {
    name?: string;
    description?: string;
  }): Promise<any> {
    try {
      const response = await apiClient.put(`/api/admin/permissions/${permissionId}`, permissionData);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  async deletePermission(permissionId: number): Promise<any> {
    try {
      const response = await apiClient.delete(`/api/admin/permissions/${permissionId}`);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Role-User Assignments
  async assignRole(userId: number, roleId: number): Promise<any> {
    try {
      const response = await apiClient.post(`/api/admin/users/${userId}/roles`, { role_id: roleId });
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  async revokeRole(userId: number, roleId: number): Promise<any> {
    try {
      const response = await apiClient.delete(`/api/admin/users/${userId}/roles/${roleId}`);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Role-Permission Assignments
  async assignPermission(roleId: number, permissionId: number): Promise<any> {
    try {
      const response = await apiClient.post(`/api/admin/roles/${roleId}/permissions`, { permission_id: permissionId });
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  async revokePermission(roleId: number, permissionId: number): Promise<any> {
    try {
      const response = await apiClient.delete(`/api/admin/roles/${roleId}/permissions/${permissionId}`);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Audit Logs
  async getAuditLogs(filters?: {
    user_id?: number;
    event_type?: string;
    start_date?: string;
    end_date?: string;
    page?: number;
    per_page?: number;
  }): Promise<{ logs: AuditLog[]; total: number; page: number; pages: number }> {
    try {
      const params = new URLSearchParams();
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== undefined) {
            params.append(key, value.toString());
          }
        });
      }
      
      const response = await apiClient.get(`/api/admin/audit-logs?${params}`);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }
}

export const adminService = new AdminService(); 