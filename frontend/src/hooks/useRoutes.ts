import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import routesService from '../services/routesService';
import {
  TechnologicalRoute,
  CreateRouteRequest,
  UpdateRouteRequest,
  RoutesListParams,
  ConflictError,
  ReactFlowData
} from '../types/routes';

interface UseRoutesReturn {
  // Состояние
  routes: TechnologicalRoute[];
  currentRoute: TechnologicalRoute | null;
  isLoading: boolean;
  isSaving: boolean;
  error: string | null;
  hasUnsavedChanges: boolean;
  
  // Конфликты версий
  versionConflict: {
    hasConflict: boolean;
    currentVersion: number;
    serverVersion: number;
    conflictDetails?: {
      lastModifiedBy?: string;
      lastModifiedAt?: string;
      changes?: string[];
    };
  };
  
  // Методы
  fetchRoutes: (params?: RoutesListParams) => Promise<void>;
  createRoute: (data: CreateRouteRequest) => Promise<TechnologicalRoute | null>;
  updateRoute: (id: number, data: UpdateRouteRequest, force?: boolean) => Promise<TechnologicalRoute | null>;
  deleteRoute: (id: number) => Promise<boolean>;
  loadRoute: (id: number) => Promise<void>;
  refreshRoute: (id: number) => Promise<void>;
  setCurrentRoute: (route: TechnologicalRoute | null) => void;
  setUnsavedChanges: (hasChanges: boolean) => void;
  clearError: () => void;
  clearVersionConflict: () => void;
  
  // Специфичные для маршрутов методы
  updateRouteData: (routeData: ReactFlowData) => void;
  exportRoute: (id: number, format: 'json' | 'pdf' | 'excel') => Promise<void>;
  duplicateRoute: (id: number, newName?: string) => Promise<TechnologicalRoute | null>;
}

export const useRoutes = (): UseRoutesReturn => {
  const [routes, setRoutes] = useState<TechnologicalRoute[]>([]);
  const [currentRoute, setCurrentRoute] = useState<TechnologicalRoute | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [versionConflict, setVersionConflict] = useState({
    hasConflict: false,
    currentVersion: 0,
    serverVersion: 0,
    conflictDetails: undefined as any
  });

  const navigate = useNavigate();

  // Обработка ошибок
  const handleError = useCallback((err: any) => {
    console.error('Routes error:', err);
    
    if (err.response?.status === 409) {
      // Конфликт версий
      const conflictError = err.response.data as ConflictError;
      setVersionConflict({
        hasConflict: true,
        currentVersion: conflictError.provided_version,
        serverVersion: conflictError.current_version,
        conflictDetails: conflictError.details
      });
      setError('Конфликт версий: маршрут был изменен другим пользователем');
    } else if (err.response?.status === 403) {
      setError('Недостаточно прав для выполнения операции');
    } else if (err.response?.status === 404) {
      setError('Маршрут не найден');
    } else {
      setError(err.response?.data?.error || err.message || 'Произошла ошибка');
    }
  }, []);

  // Получение списка маршрутов
  const fetchRoutes = useCallback(async (params?: RoutesListParams) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await routesService.getRoutes(params);
      setRoutes(response.routes);
    } catch (err) {
      handleError(err);
    } finally {
      setIsLoading(false);
    }
  }, [handleError]);

  // Создание нового маршрута
  const createRoute = useCallback(async (data: CreateRouteRequest): Promise<TechnologicalRoute | null> => {
    setIsSaving(true);
    setError(null);
    
    try {
      const newRoute = await routesService.createRoute(data);
      setRoutes(prev => [newRoute, ...prev]);
      setCurrentRoute(newRoute);
      setHasUnsavedChanges(false);
      return newRoute;
    } catch (err) {
      handleError(err);
      return null;
    } finally {
      setIsSaving(false);
    }
  }, [handleError]);

  // Обновление маршрута
  const updateRoute = useCallback(async (
    id: number, 
    data: UpdateRouteRequest, 
    force = false
  ): Promise<TechnologicalRoute | null> => {
    setIsSaving(true);
    setError(null);
    
    try {
      // Добавляем текущую версию для контроля конкурентности
      const updateData = {
        ...data,
        version_number: currentRoute?.version_number,
        force_update: force
      };
      
      const updatedRoute = await routesService.updateRoute(id, updateData);
      
      // Обновляем состояние
      setRoutes(prev => prev.map(route => 
        route.id === id ? updatedRoute : route
      ));
      setCurrentRoute(updatedRoute);
      setHasUnsavedChanges(false);
      setVersionConflict(prev => ({ ...prev, hasConflict: false }));
      
      return updatedRoute;
    } catch (err) {
      handleError(err);
      return null;
    } finally {
      setIsSaving(false);
    }
  }, [currentRoute?.version_number, handleError]);

  // Удаление маршрута
  const deleteRoute = useCallback(async (id: number): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    
    try {
      await routesService.deleteRoute(id);
      setRoutes(prev => prev.filter(route => route.id !== id));
      
      if (currentRoute?.id === id) {
        setCurrentRoute(null);
      }
      
      return true;
    } catch (err) {
      handleError(err);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [currentRoute?.id, handleError]);

  // Загрузка конкретного маршрута
  const loadRoute = useCallback(async (id: number) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const route = await routesService.getRoute(id);
      setCurrentRoute(route);
      setHasUnsavedChanges(false);
    } catch (err) {
      handleError(err);
    } finally {
      setIsLoading(false);
    }
  }, [handleError]);

  // Обновление маршрута с сервера
  const refreshRoute = useCallback(async (id: number) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const route = await routesService.getRoute(id);
      setCurrentRoute(route);
      setHasUnsavedChanges(false);
      setVersionConflict(prev => ({ ...prev, hasConflict: false }));
    } catch (err) {
      handleError(err);
    } finally {
      setIsLoading(false);
    }
  }, [handleError]);

  // Обновление данных маршрута (для React Flow)
  const updateRouteData = useCallback((routeData: ReactFlowData) => {
    if (currentRoute) {
      const updatedRoute = {
        ...currentRoute,
        route_data: routeData
      };
      setCurrentRoute(updatedRoute);
      setHasUnsavedChanges(true);
    }
  }, [currentRoute]);

  // Экспорт маршрута
  const exportRoute = useCallback(async (id: number, format: 'json' | 'pdf' | 'excel') => {
    setIsLoading(true);
    setError(null);
    
    try {
      const blob = await routesService.exportRoute(id, format);
      
      // Создаем ссылку для скачивания
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `route_${id}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      handleError(err);
    } finally {
      setIsLoading(false);
    }
  }, [handleError]);

  // Дублирование маршрута
  const duplicateRoute = useCallback(async (
    id: number, 
    newName?: string
  ): Promise<TechnologicalRoute | null> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const duplicatedRoute = await routesService.duplicateRoute(id, newName);
      setRoutes(prev => [duplicatedRoute, ...prev]);
      return duplicatedRoute;
    } catch (err) {
      handleError(err);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [handleError]);

  // Очистка ошибок
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Очистка конфликта версий
  const clearVersionConflict = useCallback(() => {
    setVersionConflict(prev => ({ ...prev, hasConflict: false }));
  }, []);

  // Установка флага несохраненных изменений
  const setUnsavedChanges = useCallback((hasChanges: boolean) => {
    setHasUnsavedChanges(hasChanges);
  }, []);

  // Предупреждение о несохраненных изменениях при уходе со страницы
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = '';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasUnsavedChanges]);

  return {
    // Состояние
    routes,
    currentRoute,
    isLoading,
    isSaving,
    error,
    hasUnsavedChanges,
    versionConflict,
    
    // Методы
    fetchRoutes,
    createRoute,
    updateRoute,
    deleteRoute,
    loadRoute,
    refreshRoute,
    setCurrentRoute,
    setUnsavedChanges,
    clearError,
    clearVersionConflict,
    
    // Специфичные методы
    updateRouteData,
    exportRoute,
    duplicateRoute
  };
};

export default useRoutes; 