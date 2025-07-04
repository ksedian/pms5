import React, { useCallback, useMemo, useState, useEffect } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
  Node,
  MarkerType,
  useReactFlow,
  ReactFlowProvider
} from 'reactflow';
import 'reactflow/dist/style.css';

import { 
  Box, 
  Paper, 
  useTheme,
  Toolbar,
  IconButton,
  Tooltip,
  Fab,
  Dialog,
  DialogContent,
  DialogTitle,
  Snackbar,
  Alert
} from '@mui/material';
import {
  Save as SaveIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Settings as SettingsIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  CenterFocusStrong as CenterIcon,
  Download as ExportIcon
} from '@mui/icons-material';

import { TechnologicalRoute, ReactFlowData, ReactFlowNode, ReactFlowEdge, Operation } from '../../types/routes';
import OperationNode from './OperationNode';
import OperationDialog from './OperationDialog';
import VersionConflictDialog from './VersionConflictDialog';

const nodeTypes = {
  operation: OperationNode,
};

interface RouteFlowCanvasProps {
  route: TechnologicalRoute;
  onRouteChange: (data: ReactFlowData) => void;
  readOnly?: boolean;
  className?: string;
  onSave?: () => void;
  isSaving?: boolean;
}

// Внутренний компонент с доступом к ReactFlow контексту
const RouteFlowCanvasInner: React.FC<RouteFlowCanvasProps> = ({
  route,
  onRouteChange,
  readOnly = false,
  className,
  onSave,
  isSaving = false
}) => {
  const theme = useTheme();
  const reactFlowInstance = useReactFlow();

  // Состояния для узлов и связей
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // UI состояния
  const [selectedNodes, setSelectedNodes] = useState<string[]>([]);
  const [selectedEdges, setSelectedEdges] = useState<string[]>([]);
  const [operationDialogOpen, setOperationDialogOpen] = useState(false);
  const [editingNode, setEditingNode] = useState<Node | null>(null);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');

  // Инициализация данных из маршрута
  useEffect(() => {
    if (route?.route_data) {
      setNodes(route.route_data.nodes || []);
      setEdges(route.route_data.edges || []);
      
      // Восстановление viewport
      if (route.route_data.viewport && reactFlowInstance) {
        const { x, y, zoom } = route.route_data.viewport;
        reactFlowInstance.setViewport({ x, y, zoom });
      }
    }
  }, [route, setNodes, setEdges, reactFlowInstance]);

  // Обновление данных маршрута при изменении узлов/связей
  useEffect(() => {
    const viewport = reactFlowInstance?.getViewport() || { x: 0, y: 0, zoom: 1 };
    const routeData: ReactFlowData = {
      nodes: nodes as ReactFlowNode[],
      edges: edges as ReactFlowEdge[],
      viewport
    };
    onRouteChange(routeData);
  }, [nodes, edges, onRouteChange, reactFlowInstance]);

  // Создание соединения между узлами
  const onConnect = useCallback(
    (params: Connection) => {
      if (readOnly || !params.source || !params.target) return;
      
      const newEdge: Edge = {
        ...params,
        id: `edge-${params.source}-${params.target}`,
        source: params.source,
        target: params.target,
        type: 'smoothstep',
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: theme.palette.primary.main,
        },
        style: {
          stroke: theme.palette.primary.main,
          strokeWidth: 2,
        },
      };
      
      setEdges((eds) => addEdge(newEdge, eds));
    },
    [setEdges, readOnly, theme]
  );

  // Добавление новой операции
  const addNewOperation = useCallback(() => {
    if (readOnly) return;

    const newNode: Node = {
      id: `node-${Date.now()}`,
      type: 'operation',
      position: {
        x: Math.random() * 400 + 100,
        y: Math.random() * 400 + 100,
      },
      data: {
        label: 'Новая операция',
        operation: null,
        properties: {},
      },
      style: {
        background: theme.palette.background.paper,
        border: `2px solid ${theme.palette.primary.main}`,
        borderRadius: 8,
        fontSize: '12px',
        color: theme.palette.text.primary,
      },
    };

    setNodes((nds) => [...nds, newNode]);
    setEditingNode(newNode);
    setOperationDialogOpen(true);
  }, [readOnly, setNodes, theme]);

  // Удаление выбранных элементов
  const deleteSelected = useCallback(() => {
    if (readOnly) return;

    setNodes((nds) => nds.filter((node) => !selectedNodes.includes(node.id)));
    setEdges((eds) => eds.filter((edge) => !selectedEdges.includes(edge.id)));
    setSelectedNodes([]);
    setSelectedEdges([]);
    
    setSnackbarMessage('Выбранные элементы удалены');
    setSnackbarOpen(true);
  }, [readOnly, selectedNodes, selectedEdges, setNodes, setEdges]);

  // Обработка выбора узлов
  const onSelectionChange = useCallback(
    ({ nodes: selectedNodes, edges: selectedEdges }: { nodes: Node[]; edges: Edge[] }) => {
      setSelectedNodes(selectedNodes.map((node) => node.id));
      setSelectedEdges(selectedEdges.map((edge) => edge.id));
    },
    []
  );

  // Редактирование узла
  const onNodeDoubleClick = useCallback(
    (event: React.MouseEvent, node: Node) => {
      if (readOnly) return;
      setEditingNode(node);
      setOperationDialogOpen(true);
    },
    [readOnly]
  );

  // Сохранение изменений операции
  const handleOperationSave = useCallback(
    (operation: Operation | null, properties: Record<string, any>) => {
      if (!editingNode) return;

      setNodes((nds) =>
        nds.map((node) =>
          node.id === editingNode.id
            ? {
                ...node,
                data: {
                  ...node.data,
                  label: operation?.name || 'Операция без названия',
                  operation,
                  properties,
                },
              }
            : node
        )
      );

      setOperationDialogOpen(false);
      setEditingNode(null);
      
      setSnackbarMessage('Операция сохранена');
      setSnackbarOpen(true);
    },
    [editingNode, setNodes]
  );

  // Центрирование view
  const centerView = useCallback(() => {
    reactFlowInstance?.fitView({ padding: 0.2 });
  }, [reactFlowInstance]);

  // Масштабирование
  const zoomIn = useCallback(() => {
    reactFlowInstance?.zoomIn();
  }, [reactFlowInstance]);

  const zoomOut = useCallback(() => {
    reactFlowInstance?.zoomOut();
  }, [reactFlowInstance]);

  // Экспорт в изображение
  const exportImage = useCallback(() => {
    if (!reactFlowInstance) return;
    
    // Получаем canvas элемент и создаем изображение
    const viewportElement = document.querySelector('.react-flow__viewport') as HTMLElement;
    if (viewportElement) {
      // Здесь можно использовать html2canvas или аналогичную библиотеку
      setSnackbarMessage('Экспорт изображения (функция в разработке)');
      setSnackbarOpen(true);
    }
  }, [reactFlowInstance]);

  // Стили для темной/светлой темы
  const flowStyles = useMemo(() => ({
    background: theme.palette.background.default,
    border: `1px solid ${theme.palette.divider}`,
  }), [theme]);

  const miniMapStyle = useMemo(() => ({
    backgroundColor: theme.palette.background.paper,
    border: `1px solid ${theme.palette.divider}`,
  }), [theme]);

  return (
    <Box className={className} sx={{ height: '100%', width: '100%', position: 'relative' }}>
      {/* Панель инструментов */}
      <Paper 
        elevation={2} 
        sx={{ 
          position: 'absolute', 
          top: 16, 
          left: 16, 
          zIndex: 1000,
          backgroundColor: theme.palette.background.paper,
        }}
      >
        <Toolbar variant="dense" sx={{ minHeight: 48 }}>
          {!readOnly && (
            <>
              <Tooltip title="Добавить операцию">
                <IconButton onClick={addNewOperation} size="small">
                  <AddIcon />
                </IconButton>
              </Tooltip>
              
              <Tooltip title="Удалить выбранное">
                <IconButton 
                  onClick={deleteSelected} 
                  size="small"
                  disabled={selectedNodes.length === 0 && selectedEdges.length === 0}
                >
                  <DeleteIcon />
                </IconButton>
              </Tooltip>

              {onSave && (
                <Tooltip title="Сохранить">
                  <IconButton 
                    onClick={onSave} 
                    size="small"
                    disabled={isSaving}
                  >
                    <SaveIcon />
                  </IconButton>
                </Tooltip>
              )}
            </>
          )}

          <Tooltip title="Увеличить">
            <IconButton onClick={zoomIn} size="small">
              <ZoomInIcon />
            </IconButton>
          </Tooltip>

          <Tooltip title="Уменьшить">
            <IconButton onClick={zoomOut} size="small">
              <ZoomOutIcon />
            </IconButton>
          </Tooltip>

          <Tooltip title="Центрировать">
            <IconButton onClick={centerView} size="small">
              <CenterIcon />
            </IconButton>
          </Tooltip>

          <Tooltip title="Экспорт">
            <IconButton onClick={exportImage} size="small">
              <ExportIcon />
            </IconButton>
          </Tooltip>
        </Toolbar>
      </Paper>

      {/* React Flow Canvas */}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onSelectionChange={onSelectionChange}
        onNodeDoubleClick={onNodeDoubleClick}
        nodeTypes={nodeTypes}
        fitView
        style={flowStyles}
        attributionPosition="bottom-left"
        nodesDraggable={!readOnly}
        nodesConnectable={!readOnly}
        elementsSelectable={!readOnly}
        deleteKeyCode={readOnly ? null : 'Delete'}
      >
        <Background 
          color={theme.palette.divider}
          gap={20}
          size={1}
        />
        <Controls 
          position="bottom-right"
          style={{
            background: theme.palette.background.paper,
            border: `1px solid ${theme.palette.divider}`,
          }}
        />
        <MiniMap 
          position="bottom-left"
          style={miniMapStyle}
          nodeColor={theme.palette.primary.main}
        />
      </ReactFlow>

      {/* FAB для быстрого добавления операций */}
      {!readOnly && (
        <Fab
          color="primary"
          aria-label="Добавить операцию"
          onClick={addNewOperation}
          sx={{
            position: 'absolute',
            bottom: 16,
            right: 16,
            zIndex: 1000,
          }}
        >
          <AddIcon />
        </Fab>
      )}

      {/* Диалог редактирования операции */}
      <Dialog
        open={operationDialogOpen}
        onClose={() => setOperationDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {editingNode?.data.operation ? 'Редактировать операцию' : 'Создать операцию'}
        </DialogTitle>
        <DialogContent>
          <OperationDialog
            operation={editingNode?.data.operation || null}
            properties={editingNode?.data.properties || {}}
            onSave={handleOperationSave}
            onCancel={() => setOperationDialogOpen(false)}
          />
        </DialogContent>
      </Dialog>

      {/* Уведомления */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={3000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity="success" onClose={() => setSnackbarOpen(false)}>
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

// Основной компонент с провайдером ReactFlow
const RouteFlowCanvas: React.FC<RouteFlowCanvasProps> = (props) => {
  return (
    <ReactFlowProvider>
      <RouteFlowCanvasInner {...props} />
    </ReactFlowProvider>
  );
};

export default RouteFlowCanvas; 