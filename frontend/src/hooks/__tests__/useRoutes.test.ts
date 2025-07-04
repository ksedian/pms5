import { renderHook, act, waitFor } from '@testing-library/react';
import { useRoutes } from '../useRoutes';
import routesService from '../../services/routesService';
import { TechnologicalRoute, CreateRouteRequest } from '../../types/routes';

// Mock the services
jest.mock('../../services/routesService');
jest.mock('react-router-dom', () => ({
  useNavigate: () => jest.fn(),
}));

const mockRoutesService = routesService as jest.Mocked<typeof routesService>;

const mockRoute: TechnologicalRoute = {
  id: 1,
  name: 'Тестовый маршрут',
  description: 'Описание тестового маршрута',
  route_number: 'RT-001',
  status: 'active',
  version: 1,
  complexity_level: 'medium',
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
  operations: [],
  route_data: {
    nodes: [],
    edges: [],
  },
};

const mockCreateRequest: CreateRouteRequest = {
  name: 'Новый маршрут',
  route_number: 'RT-002',
  description: 'Описание нового маршрута',
  complexity_level: 'low',
};

describe('useRoutes', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('инициализируется с пустым состоянием', () => {
    const { result } = renderHook(() => useRoutes());

    expect(result.current.routes).toEqual([]);
    expect(result.current.currentRoute).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isSaving).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.hasUnsavedChanges).toBe(false);
    expect(result.current.versionConflict.hasConflict).toBe(false);
  });

  it('загружает маршруты успешно', async () => {
    const mockResponse = {
      data: [mockRoute],
      pagination: {
        total: 1,
        pages: 1,
        current_page: 1,
        per_page: 10,
        has_next: false,
        has_prev: false,
      },
    };

    mockRoutesService.getRoutes.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useRoutes());

    await act(async () => {
      await result.current.fetchRoutes();
    });

    expect(result.current.routes).toEqual([mockRoute]);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(mockRoutesService.getRoutes).toHaveBeenCalledTimes(1);
  });

  it('обрабатывает ошибки при загрузке маршрутов', async () => {
    const mockError = new Error('Ошибка сети');
    mockRoutesService.getRoutes.mockRejectedValue(mockError);

    const { result } = renderHook(() => useRoutes());

    await act(async () => {
      await result.current.fetchRoutes();
    });

    expect(result.current.routes).toEqual([]);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBe('Ошибка сети');
  });

  it('создает новый маршрут успешно', async () => {
    mockRoutesService.createRoute.mockResolvedValue(mockRoute);

    const { result } = renderHook(() => useRoutes());

    let createdRoute: TechnologicalRoute | null = null;

    await act(async () => {
      createdRoute = await result.current.createRoute(mockCreateRequest);
    });

    expect(createdRoute).toEqual(mockRoute);
    expect(result.current.routes).toEqual([mockRoute]);
    expect(result.current.currentRoute).toEqual(mockRoute);
    expect(result.current.hasUnsavedChanges).toBe(false);
    expect(result.current.isSaving).toBe(false);
    expect(mockRoutesService.createRoute).toHaveBeenCalledWith(mockCreateRequest);
  });

  it('обрабатывает ошибки при создании маршрута', async () => {
    const mockError = new Error('Ошибка создания');
    mockRoutesService.createRoute.mockRejectedValue(mockError);

    const { result } = renderHook(() => useRoutes());

    let createdRoute: TechnologicalRoute | null = null;

    await act(async () => {
      createdRoute = await result.current.createRoute(mockCreateRequest);
    });

    expect(createdRoute).toBeNull();
    expect(result.current.routes).toEqual([]);
    expect(result.current.error).toBe('Ошибка создания');
    expect(result.current.isSaving).toBe(false);
  });

  it('обновляет маршрут успешно', async () => {
    const updatedRoute = { ...mockRoute, name: 'Обновленный маршрут' };
    mockRoutesService.updateRoute.mockResolvedValue(updatedRoute);

    const { result } = renderHook(() => useRoutes());

    // Устанавливаем начальное состояние
    act(() => {
      result.current.setCurrentRoute(mockRoute);
    });

    let updatedResult: TechnologicalRoute | null = null;

    await act(async () => {
      updatedResult = await result.current.updateRoute(1, { name: 'Обновленный маршрут' });
    });

    expect(updatedResult).toEqual(updatedRoute);
    expect(result.current.currentRoute).toEqual(updatedRoute);
    expect(result.current.hasUnsavedChanges).toBe(false);
    expect(result.current.isSaving).toBe(false);
  });

  it('обрабатывает конфликт версий', async () => {
    const conflictError = {
      response: {
        status: 409,
        data: {
          error: 'Конфликт версий',
          current_version: 2,
          provided_version: 1,
          details: {
            lastModifiedBy: 'admin',
            lastModifiedAt: '2023-01-02T00:00:00Z',
            changes: ['Изменено название'],
          },
        },
      },
    };

    mockRoutesService.updateRoute.mockRejectedValue(conflictError);

    const { result } = renderHook(() => useRoutes());

    // Устанавливаем начальное состояние
    act(() => {
      result.current.setCurrentRoute(mockRoute);
    });

    await act(async () => {
      await result.current.updateRoute(1, { name: 'Обновленный маршрут' });
    });

    expect(result.current.versionConflict.hasConflict).toBe(true);
    expect(result.current.versionConflict.currentVersion).toBe(1);
    expect(result.current.versionConflict.serverVersion).toBe(2);
    expect(result.current.error).toBe('Конфликт версий: маршрут был изменен другим пользователем');
  });

  it('удаляет маршрут успешно', async () => {
    mockRoutesService.deleteRoute.mockResolvedValue(undefined);

    const { result } = renderHook(() => useRoutes());

    // Устанавливаем начальное состояние
    act(() => {
      result.current.setCurrentRoute(mockRoute);
    });

    let deleteResult: boolean = false;

    await act(async () => {
      deleteResult = await result.current.deleteRoute(1);
    });

    expect(deleteResult).toBe(true);
    expect(result.current.currentRoute).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(mockRoutesService.deleteRoute).toHaveBeenCalledWith(1);
  });

  it('загружает конкретный маршрут', async () => {
    mockRoutesService.getRoute.mockResolvedValue(mockRoute);

    const { result } = renderHook(() => useRoutes());

    await act(async () => {
      await result.current.loadRoute(1);
    });

    expect(result.current.currentRoute).toEqual(mockRoute);
    expect(result.current.hasUnsavedChanges).toBe(false);
    expect(result.current.isLoading).toBe(false);
    expect(mockRoutesService.getRoute).toHaveBeenCalledWith(1);
  });

  it('обновляет данные маршрута', () => {
    const { result } = renderHook(() => useRoutes());

    // Устанавливаем начальное состояние
    act(() => {
      result.current.setCurrentRoute(mockRoute);
    });

    const newRouteData = {
      nodes: [{ id: 'node-1', type: 'operation' as const, position: { x: 0, y: 0 }, data: { label: 'Test' } }],
      edges: [],
    };

    act(() => {
      result.current.updateRouteData(newRouteData);
    });

    expect(result.current.currentRoute?.route_data).toEqual(newRouteData);
    expect(result.current.hasUnsavedChanges).toBe(true);
  });

  it('очищает ошибки', () => {
    const { result } = renderHook(() => useRoutes());

    // Устанавливаем ошибку
    act(() => {
      result.current.clearError();
    });

    expect(result.current.error).toBeNull();
  });

  it('очищает конфликт версий', () => {
    const { result } = renderHook(() => useRoutes());

    act(() => {
      result.current.clearVersionConflict();
    });

    expect(result.current.versionConflict.hasConflict).toBe(false);
  });

  it('устанавливает флаг несохраненных изменений', () => {
    const { result } = renderHook(() => useRoutes());

    act(() => {
      result.current.setUnsavedChanges(true);
    });

    expect(result.current.hasUnsavedChanges).toBe(true);

    act(() => {
      result.current.setUnsavedChanges(false);
    });

    expect(result.current.hasUnsavedChanges).toBe(false);
  });
}); 