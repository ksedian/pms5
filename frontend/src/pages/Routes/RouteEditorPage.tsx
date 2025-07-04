import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar,
  Alert,
  Breadcrumbs,
  Link,
  CircularProgress,
  Divider
} from '@mui/material';
import {
  Save as SaveIcon,
  ArrowBack as BackIcon,
  Publish as PublishIcon,
  Preview as PreviewIcon,
  History as HistoryIcon,
  Settings as SettingsIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';

import { TechnologicalRoute, ReactFlowData, CreateRouteRequest, UpdateRouteRequest } from '../../types/routes';
import { routesService } from '../../services/routesService';
import RouteFlowCanvas from '../../components/Routes/RouteFlowCanvas';

const RouteEditorPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isNewRoute = id === 'new';
  
  // Основные состояния
  const [route, setRoute] = useState<TechnologicalRoute | null>(null);
  const [loading, setLoading] = useState(!isNewRoute);
  const [saving, setSaving] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  
  // Форма основной информации
  const [routeForm, setRouteForm] = useState({
    name: '',
    route_code: '',
    description: '',
    status: 'draft' as 'draft' | 'active' | 'archived',
    product_type: '',
    estimated_time: 0
  });
  
  // UI состояния
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error'>('success');
  const [publishDialogOpen, setPublishDialogOpen] = useState(false);
  const [unsavedDialogOpen, setUnsavedDialogOpen] = useState(false);
  const [pendingNavigation, setPendingNavigation] = useState<string | null>(null);

  // Загрузка маршрута
  useEffect(() => {
    if (!isNewRoute && id) {
      loadRoute(parseInt(id));
    } else {
      // Инициализация нового маршрута
      const timestamp = Date.now().toString().slice(-6);
      setRouteForm(prev => ({
        ...prev,
        route_code: `ROUTE-${timestamp}`
      }));
    }
  }, [id, isNewRoute]);

  const loadRoute = async (routeId: number) => {
    try {
      setLoading(true);
      const loadedRoute = await routesService.getRoute(routeId);
      setRoute(loadedRoute);
      setRouteForm({
        name: loadedRoute.name,
        route_code: loadedRoute.route_code,
        description: loadedRoute.description || '',
        status: loadedRoute.status,
        product_type: loadedRoute.product_type || '',
        estimated_time: loadedRoute.estimated_time || 0
      });
    } catch (error) {
      console.error('Ошибка загрузки маршрута:', error);
      showSnackbar('Ошибка загрузки маршрута', 'error');
    } finally {
      setLoading(false);
    }
  };

  const showSnackbar = (message: string, severity: 'success' | 'error' = 'success') => {
    setSnackbarMessage(message);
    setSnackbarSeverity(severity);
    setSnackbarOpen(true);
  };

  // Обработка изменений формы
  const handleFormChange = (field: string, value: any) => {
    setRouteForm(prev => ({ ...prev, [field]: value }));
    setHasUnsavedChanges(true);
  };

  // Обработка изменений маршрута (граф)
  const handleRouteDataChange = useCallback((data: ReactFlowData) => {
    if (route) {
      setRoute(prev => prev ? { ...prev, route_data: data } : null);
      setHasUnsavedChanges(true);
    }
  }, [route]);

  // Сохранение маршрута
  const handleSave = async () => {
    try {
      setSaving(true);
      
      if (isNewRoute) {
        const createData: CreateRouteRequest = {
          name: routeForm.name,
          route_code: routeForm.route_code,
          description: routeForm.description,
          status: routeForm.status,
          estimated_time: routeForm.estimated_time > 0 ? routeForm.estimated_time : undefined,
          product_type: routeForm.product_type,
          route_data: route?.route_data || { nodes: [], edges: [], viewport: { x: 0, y: 0, zoom: 1 } }
        };
        
        const newRoute = await routesService.createRoute(createData);
        setRoute(newRoute);
        navigate(`/routes/${newRoute.id}/edit`, { replace: true });
        showSnackbar('Маршрут создан успешно');
      } else if (route) {
        const updateData: UpdateRouteRequest = {
          ...routeForm,
          route_data: route.route_data
        };
        
        const updatedRoute = await routesService.updateRoute(route.id, updateData);
        setRoute(updatedRoute);
        showSnackbar('Маршрут сохранен успешно');
      }
      
      setHasUnsavedChanges(false);
    } catch (error) {
      console.error('Ошибка сохранения:', error);
      showSnackbar('Ошибка сохранения маршрута', 'error');
    } finally {
      setSaving(false);
    }
  };

  // Публикация маршрута
  const handlePublish = async () => {
    if (!route) return;
    
    try {
      await routesService.updateRoute(route.id, { status: 'active' });
      setRoute(prev => prev ? { ...prev, status: 'active' } : null);
      setRouteForm(prev => ({ ...prev, status: 'active' }));
      setPublishDialogOpen(false);
      showSnackbar('Маршрут опубликован');
    } catch (error) {
      showSnackbar('Ошибка публикации маршрута', 'error');
    }
  };

  // Навигация с проверкой несохраненных изменений
  const handleNavigation = (path: string) => {
    if (hasUnsavedChanges) {
      setPendingNavigation(path);
      setUnsavedDialogOpen(true);
    } else {
      navigate(path);
    }
  };

  const handleUnsavedDialogConfirm = () => {
    if (pendingNavigation) {
      navigate(pendingNavigation);
    }
    setUnsavedDialogOpen(false);
    setPendingNavigation(null);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Заголовок и панель управления */}
      <Paper elevation={1} sx={{ p: 2, borderRadius: 0 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <IconButton onClick={() => handleNavigation('/routes')}>
              <BackIcon />
            </IconButton>
            <Breadcrumbs>
              <Link 
                color="inherit" 
                onClick={() => handleNavigation('/routes')}
                sx={{ cursor: 'pointer' }}
              >
                Маршруты
              </Link>
              <Typography color="text.primary">
                {isNewRoute ? 'Новый маршрут' : routeForm.name || 'Редактирование'}
              </Typography>
            </Breadcrumbs>
          </Box>
          
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            {route?.status && (
              <Chip
                label={route.status === 'active' ? 'Активный' : 
                       route.status === 'draft' ? 'Черновик' : 'Архивный'}
                color={route.status === 'active' ? 'success' : 
                       route.status === 'draft' ? 'warning' : 'default'}
                size="small"
              />
            )}
            
            {!isNewRoute && (
              <Tooltip title="История версий">
                <IconButton onClick={() => handleNavigation(`/routes/${route?.id}/history`)}>
                  <HistoryIcon />
                </IconButton>
              </Tooltip>
            )}
            
            <Button
              variant="outlined"
              startIcon={<PreviewIcon />}
              onClick={() => handleNavigation(`/routes/${route?.id}/view`)}
              disabled={isNewRoute}
            >
              Просмотр
            </Button>
            
            <Button
              variant="outlined"
              startIcon={<SaveIcon />}
              onClick={handleSave}
              disabled={saving || !hasUnsavedChanges}
            >
              {saving ? <CircularProgress size={20} /> : 'Сохранить'}
            </Button>
            
            {route?.status === 'draft' && (
              <Button
                variant="contained"
                color="success"
                startIcon={<PublishIcon />}
                onClick={() => setPublishDialogOpen(true)}
                disabled={hasUnsavedChanges}
              >
                Опубликовать
              </Button>
            )}
          </Box>
        </Box>

        {/* Основная информация о маршруте */}
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: 4 }}>
            <TextField
              fullWidth
              label="Название маршрута"
              value={routeForm.name}
              onChange={(e) => handleFormChange('name', e.target.value)}
              variant="outlined"
              size="small"
            />
          </Grid>
          
          <Grid size={{ xs: 12, md: 2 }}>
            <TextField
              fullWidth
              label="Код маршрута"
              value={routeForm.route_code}
              onChange={(e) => handleFormChange('route_code', e.target.value)}
              variant="outlined"
              size="small"
            />
          </Grid>
          
          <Grid size={{ xs: 12, md: 2 }}>
            <TextField
              fullWidth
              label="Тип продукта"
              value={routeForm.product_type}
              onChange={(e) => handleFormChange('product_type', e.target.value)}
              variant="outlined"
              size="small"
            />
          </Grid>
          
          <Grid size={{ xs: 12, md: 2 }}>
            <FormControl fullWidth size="small">
              <InputLabel>Статус</InputLabel>
              <Select
                value={routeForm.status}
                onChange={(e) => handleFormChange('status', e.target.value)}
                label="Статус"
              >
                <MenuItem value="draft">Черновик</MenuItem>
                <MenuItem value="active">Активный</MenuItem>
                <MenuItem value="archived">Архивный</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid size={{ xs: 12, md: 2 }}>
            <TextField
              fullWidth
              label="Время (мин)"
              type="number"
              value={routeForm.estimated_time}
              onChange={(e) => handleFormChange('estimated_time', parseFloat(e.target.value) || 0)}
              variant="outlined"
              size="small"
            />
          </Grid>
        </Grid>
        
        {routeForm.description !== undefined && (
          <TextField
            fullWidth
            label="Описание"
            value={routeForm.description}
            onChange={(e) => handleFormChange('description', e.target.value)}
            variant="outlined"
            size="small"
            multiline
            rows={2}
            sx={{ mt: 2 }}
          />
        )}
      </Paper>

      {/* Основная область редактирования */}
      <Box sx={{ flexGrow: 1, position: 'relative' }}>
        {route || isNewRoute ? (
          <RouteFlowCanvas
            route={route || {
              id: 0,
              name: routeForm.name,
              route_code: routeForm.route_code,
              description: routeForm.description,
              status: routeForm.status,
              version_number: 1,
              route_data: { nodes: [], edges: [], viewport: { x: 0, y: 0, zoom: 1 } },
              created_by: '1',
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
              total_operations: 0,
              estimated_time: routeForm.estimated_time,
              product_type: routeForm.product_type
            }}
            onRouteChange={handleRouteDataChange}
            onSave={handleSave}
            isSaving={saving}
            readOnly={false}
          />
        ) : (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
            <Typography color="textSecondary">Загрузка редактора...</Typography>
          </Box>
        )}
      </Box>

      {/* Диалог публикации */}
      <Dialog open={publishDialogOpen} onClose={() => setPublishDialogOpen(false)}>
        <DialogTitle>Публикация маршрута</DialogTitle>
        <DialogContent>
          <Typography>
            Вы уверены, что хотите опубликовать этот маршрут? 
            После публикации маршрут станет активным и будет доступен для использования.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPublishDialogOpen(false)}>
            Отмена
          </Button>
          <Button onClick={handlePublish} variant="contained" color="success">
            Опубликовать
          </Button>
        </DialogActions>
      </Dialog>

      {/* Диалог несохраненных изменений */}
      <Dialog open={unsavedDialogOpen} onClose={() => setUnsavedDialogOpen(false)}>
        <DialogTitle>Несохраненные изменения</DialogTitle>
        <DialogContent>
          <Typography>
            У вас есть несохраненные изменения. Вы уверены, что хотите покинуть страницу без сохранения?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUnsavedDialogOpen(false)}>
            Остаться
          </Button>
          <Button onClick={handleUnsavedDialogConfirm} color="error">
            Покинуть без сохранения
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar для уведомлений */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={() => setSnackbarOpen(false)}
      >
        <Alert
          onClose={() => setSnackbarOpen(false)}
          severity={snackbarSeverity}
          sx={{ width: '100%' }}
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default RouteEditorPage; 