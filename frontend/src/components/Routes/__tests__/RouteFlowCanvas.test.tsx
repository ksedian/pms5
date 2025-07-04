import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { lightTheme } from '../../../theme/theme';
import RouteFlowCanvas from '../RouteFlowCanvas';
import { TechnologicalRoute } from '../../../types/routes';

// Mock ReactFlow
jest.mock('reactflow', () => ({
  ReactFlow: ({ children, ...props }: any) => (
    <div data-testid="react-flow" {...props}>
      {children}
    </div>
  ),
  Background: () => <div data-testid="background" />,
  Controls: () => <div data-testid="controls" />,
  MiniMap: () => <div data-testid="minimap" />,
  useNodesState: () => [[], jest.fn(), jest.fn()],
  useEdgesState: () => [[], jest.fn(), jest.fn()],
  addEdge: jest.fn(),
  MarkerType: { ArrowClosed: 'arrowclosed' },
  useReactFlow: () => ({
    getViewport: () => ({ x: 0, y: 0, zoom: 1 }),
    setViewport: jest.fn(),
    fitView: jest.fn(),
    zoomIn: jest.fn(),
    zoomOut: jest.fn(),
  }),
  ReactFlowProvider: ({ children }: any) => <div>{children}</div>,
}));

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
    nodes: [
      {
        id: 'node-1',
        type: 'operation',
        position: { x: 100, y: 100 },
        data: {
          label: 'Операция 1',
          operation: {
            id: 1,
            name: 'Операция 1',
            operation_code: 'OP-001',
            operation_type: 'machining',
            setup_time: 10,
            operation_time: 30,
            total_time: 40,
            required_equipment: ['Станок'],
            required_skills: ['Оператор'],
            quality_requirements: {},
            created_at: '2023-01-01T00:00:00Z',
            updated_at: '2023-01-01T00:00:00Z',
          },
        },
      },
    ],
    edges: [],
  },
};

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={lightTheme}>
      {component}
    </ThemeProvider>
  );
};

describe('RouteFlowCanvas', () => {
  const mockOnRouteChange = jest.fn();
  const mockOnSave = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('рендерится без ошибок', () => {
    renderWithTheme(
      <RouteFlowCanvas
        route={mockRoute}
        onRouteChange={mockOnRouteChange}
      />
    );

    expect(screen.getByTestId('react-flow')).toBeInTheDocument();
    expect(screen.getByTestId('background')).toBeInTheDocument();
    expect(screen.getByTestId('controls')).toBeInTheDocument();
    expect(screen.getByTestId('minimap')).toBeInTheDocument();
  });

  it('отображает кнопки управления', () => {
    renderWithTheme(
      <RouteFlowCanvas
        route={mockRoute}
        onRouteChange={mockOnRouteChange}
        onSave={mockOnSave}
      />
    );

    expect(screen.getByRole('button', { name: /добавить операцию/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /сохранить/i })).toBeInTheDocument();
  });

  it('скрывает кнопки управления в режиме только для чтения', () => {
    renderWithTheme(
      <RouteFlowCanvas
        route={mockRoute}
        onRouteChange={mockOnRouteChange}
        readOnly={true}
      />
    );

    expect(screen.queryByRole('button', { name: /добавить операцию/i })).not.toBeInTheDocument();
  });

  it('вызывает onSave при нажатии на кнопку сохранения', () => {
    renderWithTheme(
      <RouteFlowCanvas
        route={mockRoute}
        onRouteChange={mockOnRouteChange}
        onSave={mockOnSave}
      />
    );

    const saveButton = screen.getByRole('button', { name: /сохранить/i });
    fireEvent.click(saveButton);

    expect(mockOnSave).toHaveBeenCalledTimes(1);
  });

  it('отображает индикатор загрузки при сохранении', () => {
    renderWithTheme(
      <RouteFlowCanvas
        route={mockRoute}
        onRouteChange={mockOnRouteChange}
        onSave={mockOnSave}
        isSaving={true}
      />
    );

    const saveButton = screen.getByRole('button', { name: /сохранить/i });
    expect(saveButton).toBeDisabled();
  });

  it('вызывает onRouteChange при изменении данных', async () => {
    renderWithTheme(
      <RouteFlowCanvas
        route={mockRoute}
        onRouteChange={mockOnRouteChange}
      />
    );

    // Симулируем изменение данных
    await waitFor(() => {
      expect(mockOnRouteChange).toHaveBeenCalled();
    });
  });

  it('применяет переданный className', () => {
    const testClassName = 'test-class';
    renderWithTheme(
      <RouteFlowCanvas
        route={mockRoute}
        onRouteChange={mockOnRouteChange}
        className={testClassName}
      />
    );

    const container = screen.getByTestId('react-flow').parentElement;
    expect(container).toHaveClass(testClassName);
  });

  it('обрабатывает пустые данные маршрута', () => {
    const emptyRoute = {
      ...mockRoute,
      route_data: undefined,
    };

    renderWithTheme(
      <RouteFlowCanvas
        route={emptyRoute}
        onRouteChange={mockOnRouteChange}
      />
    );

    expect(screen.getByTestId('react-flow')).toBeInTheDocument();
  });
}); 