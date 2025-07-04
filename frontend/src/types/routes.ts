// Типы для технологических маршрутов
export interface TechnologicalRoute {
  id: number;
  name: string;
  description?: string;
  route_code: string;
  status: 'draft' | 'active' | 'archived';
  route_data?: ReactFlowData;
  version_number: number;
  estimated_time?: number;
  product_type?: string;
  total_operations?: number;
  complexity_level?: 'low' | 'medium' | 'high';
  created_by?: string;
  created_at: string;
  updated_at: string;
  operations?: Operation[];
}

// Типы для операций
export interface Operation {
  id: number;
  name: string;
  description?: string;
  operation_code: string;
  operation_type: string;
  setup_time: number;
  operation_time: number;
  total_time: number;
  required_equipment: string[];
  required_skills: string[];
  quality_requirements: Record<string, any>;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

// Типы для версий маршрутов
export interface RouteVersion {
  id: number;
  route_id: number;
  version_number: number;
  description?: string;
  route_data: any;
  change_type?: string;
  change_summary?: string;
  created_by?: string;
  created_by_name?: string;
  created_at: string;
}

// Типы для React Flow
export interface ReactFlowData {
  nodes: ReactFlowNode[];
  edges: ReactFlowEdge[];
  viewport?: {
    x: number;
    y: number;
    zoom: number;
  };
}

export interface ReactFlowNode {
  id: string;
  type: 'operation' | 'start' | 'end' | 'decision';
  position: {
    x: number;
    y: number;
  };
  data: {
    label: string;
    operation?: Operation;
    properties?: Record<string, any>;
  };
  style?: Record<string, any>;
  className?: string;
}

export interface ReactFlowEdge {
  id: string;
  source: string;
  target: string;
  type?: 'default' | 'straight' | 'step' | 'smoothstep';
  style?: Record<string, any>;
  label?: string;
  animated?: boolean;
  data?: {
    condition?: string;
    properties?: Record<string, any>;
  };
}

// Типы для API запросов
export interface CreateRouteRequest {
  name: string;
  route_code: string;
  description?: string;
  status?: 'draft' | 'active' | 'archived';
  route_data?: ReactFlowData;
  estimated_time?: number;
  product_type?: string;
  complexity_level?: 'low' | 'medium' | 'high';
}

export interface UpdateRouteRequest {
  name?: string;
  description?: string;
  status?: 'draft' | 'active' | 'archived';
  route_data?: ReactFlowData;
  estimated_time?: number;
  product_type?: string;
  complexity_level?: 'low' | 'medium' | 'high';
  version_number?: number; // Для контроля конкурентности
}

// Типы для API ответов
export interface RoutesListResponse {
  routes: TechnologicalRoute[]; // Изменено с data
  total: number; // Добавлено для совместимости
  pagination?: {
    total: number;
    pages: number;
    current_page: number;
    per_page: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

export interface RouteVersionsResponse {
  data: RouteVersion[];
  pagination: {
    total: number;
    pages: number;
    current_page: number;
    per_page: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

export interface VersionDiffResponse {
  version_1: RouteVersion;
  version_2: RouteVersion;
  differences: {
    added: any[];
    removed: any[];
    modified: any[];
  };
}

// Типы для фильтров и параметров запросов
export interface RoutesListParams {
  page?: number;
  per_page?: number;
  status?: 'draft' | 'active' | 'archived';
  search?: string;
}

export interface CreateVersionRequest {
  description?: string;
}

// Типы для ошибок
export interface ApiError {
  error: string;
  details?: Record<string, any>;
}

export interface ConflictError extends ApiError {
  current_version: number;
  provided_version: number;
}

// Типы для состояний UI
export interface RouteFormState {
  name: string;
  route_code: string;
  description: string;
  status: 'draft' | 'active' | 'archived';
  estimated_time: number | null;
  product_type: string;
  complexity_level: 'low' | 'medium' | 'high';
}

export interface RouteEditorState {
  route: TechnologicalRoute | null;
  isLoading: boolean;
  isSaving: boolean;
  hasUnsavedChanges: boolean;
  error: string | null;
  selectedNodes: string[];
  selectedEdges: string[];
}

// Дополнительные типы для контекста и хуков
export interface RoutesContextValue {
  routes: TechnologicalRoute[];
  currentRoute: TechnologicalRoute | null;
  isLoading: boolean;
  error: string | null;
  fetchRoutes: (params?: RoutesListParams) => Promise<void>;
  createRoute: (data: CreateRouteRequest) => Promise<TechnologicalRoute>;
  updateRoute: (id: number, data: UpdateRouteRequest) => Promise<TechnologicalRoute>;
  deleteRoute: (id: number) => Promise<void>;
  loadRoute: (id: number) => Promise<void>;
}

// Типы для компонентов
export interface RouteFlowCanvasProps {
  route: TechnologicalRoute;
  onRouteChange: (data: ReactFlowData) => void;
  readOnly?: boolean;
  className?: string;
}

export interface OperationNodeProps {
  data: {
    label: string;
    operation?: Operation;
    properties?: Record<string, any>;
  };
  selected?: boolean;
}

export interface RoutePropertiesPanelProps {
  route: TechnologicalRoute;
  onUpdate: (data: UpdateRouteRequest) => void;
  isLoading?: boolean;
} 