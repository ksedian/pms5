import apiClient from './apiClient';
import {
  TechnologicalRoute,
  CreateRouteRequest,
  UpdateRouteRequest,
  RoutesListResponse,
  RoutesListParams,
  RouteVersion,
  RouteVersionsResponse,
  VersionDiffResponse,
  CreateVersionRequest,
  Operation
} from '../types/routes';

class RoutesService {
  private readonly baseUrl = '/api/routes';

  /**
   * Получить список технологических маршрутов
   */
  async getRoutes(params?: RoutesListParams): Promise<RoutesListResponse> {
    const response = await apiClient.get(this.baseUrl, { params });
    return response.data;
  }

  /**
   * Получить технологический маршрут по ID
   */
  async getRoute(id: number): Promise<TechnologicalRoute> {
    const response = await apiClient.get(`${this.baseUrl}/${id}`);
    return response.data;
  }

  /**
   * Создать новый технологический маршрут
   */
  async createRoute(data: CreateRouteRequest): Promise<TechnologicalRoute> {
    const response = await apiClient.post(this.baseUrl, data);
    return response.data;
  }

  /**
   * Обновить технологический маршрут
   */
  async updateRoute(id: number, data: UpdateRouteRequest): Promise<TechnologicalRoute> {
    const response = await apiClient.put(`${this.baseUrl}/${id}`, data);
    return response.data;
  }

  /**
   * Удалить технологический маршрут
   */
  async deleteRoute(id: number): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/${id}`);
  }

  /**
   * Получить операции маршрута
   */
  async getRouteOperations(routeId: number): Promise<Operation[]> {
    const response = await apiClient.get(`${this.baseUrl}/${routeId}/operations`);
    return response.data;
  }

  /**
   * Добавить операцию к маршруту
   */
  async addRouteOperation(routeId: number, operationData: {
    operation_id: number;
    sequence_number: number;
    is_parallel?: boolean;
  }): Promise<void> {
    await apiClient.post(`${this.baseUrl}/${routeId}/operations`, operationData);
  }

  /**
   * Удалить операцию из маршрута
   */
  async removeRouteOperation(routeId: number, operationId: number): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/${routeId}/operations/${operationId}`);
  }

  /**
   * Получить версии маршрута
   */
  async getRouteVersions(routeId: number, params?: { page?: number; per_page?: number }): Promise<RouteVersion[]> {
    const response = await apiClient.get(`${this.baseUrl}/${routeId}/versions`, { params });
    return response.data.versions || response.data;
  }

  /**
   * Создать новую версию маршрута
   */
  async createRouteVersion(routeId: number, data: CreateVersionRequest): Promise<RouteVersion> {
    const response = await apiClient.post(`${this.baseUrl}/${routeId}/versions`, data);
    return response.data;
  }

  /**
   * Получить конкретную версию маршрута
   */
  async getRouteVersion(routeId: number, versionId: number): Promise<RouteVersion> {
    const response = await apiClient.get(`${this.baseUrl}/${routeId}/versions/${versionId}`);
    return response.data;
  }

  /**
   * Сравнить две версии маршрута
   */
  async compareRouteVersions(routeId: number, v1: number, v2: number): Promise<VersionDiffResponse> {
    const response = await apiClient.get(`${this.baseUrl}/${routeId}/versions/diff/${v1}/${v2}`);
    return response.data;
  }

  /**
   * Восстановить маршрут из версии
   */
  async restoreRouteFromVersion(routeId: number, versionId: number): Promise<TechnologicalRoute> {
    const response = await apiClient.post(`${this.baseUrl}/${routeId}/versions/${versionId}/restore`);
    return response.data;
  }

  /**
   * Восстановить версию маршрута
   */
  async restoreRouteVersion(routeId: number, versionId: number): Promise<TechnologicalRoute> {
    return this.restoreRouteFromVersion(routeId, versionId);
  }

  /**
   * Экспортировать маршрут в различных форматах
   */
  async exportRoute(routeId: number, format: 'json' | 'pdf' | 'excel'): Promise<Blob> {
    const response = await apiClient.get(`${this.baseUrl}/${routeId}/export`, {
      params: { format },
      responseType: 'blob'
    });
    return response.data;
  }

  /**
   * Экспортировать версию маршрута
   */
  async exportRouteVersion(versionId: number, format: 'json' | 'pdf' | 'excel'): Promise<Blob> {
    const response = await apiClient.get(`${this.baseUrl}/versions/${versionId}/export`, {
      params: { format },
      responseType: 'blob'
    });
    return response.data;
  }

  /**
   * Импортировать маршрут из файла
   */
  async importRoute(file: File): Promise<TechnologicalRoute> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiClient.post(`${this.baseUrl}/import`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    
    return response.data;
  }

  /**
   * Валидировать данные маршрута
   */
  async validateRoute(data: CreateRouteRequest | UpdateRouteRequest): Promise<{ valid: boolean; errors?: string[] }> {
    const response = await apiClient.post(`${this.baseUrl}/validate`, data);
    return response.data;
  }

  /**
   * Дублировать маршрут
   */
  async duplicateRoute(routeId: number, newName?: string, newRouteCode?: string): Promise<TechnologicalRoute> {
    const response = await apiClient.post(`${this.baseUrl}/${routeId}/duplicate`, {
      name: newName,
      route_code: newRouteCode
    });
    return response.data;
  }

  /**
   * Получить статистику по маршруту
   */
  async getRouteStatistics(routeId: number): Promise<{
    total_operations: number;
    estimated_duration: number;
    complexity_score: number;
    versions_count: number;
    last_modified: string;
  }> {
    const response = await apiClient.get(`${this.baseUrl}/${routeId}/statistics`);
    return response.data;
  }

  /**
   * Поиск маршрутов
   */
  async searchRoutes(query: string, filters?: {
    status?: string;
    complexity_level?: string;
    created_by?: string;
  }): Promise<TechnologicalRoute[]> {
    const response = await apiClient.get(`${this.baseUrl}/search`, {
      params: { q: query, ...filters }
    });
    return response.data;
  }

  /**
   * Получить граф зависимостей операций
   */
  async getOperationsDependencies(routeId: number): Promise<{
    nodes: Array<{ id: string; label: string; type: string }>;
    edges: Array<{ source: string; target: string; type: string }>;
  }> {
    const response = await apiClient.get(`${this.baseUrl}/${routeId}/dependencies`);
    return response.data;
  }

  /**
   * Оптимизация маршрута
   */
  async optimizeRoute(routeId: number, criteria: 'time' | 'cost' | 'quality'): Promise<{
    optimized_route_data: any;
    improvements: Array<{
      type: string;
      description: string;
      impact: number;
    }>;
  }> {
    const response = await apiClient.post(`${this.baseUrl}/${routeId}/optimize`, { criteria });
    return response.data;
  }
}

const routesService = new RoutesService();
export { routesService };
export default routesService; 