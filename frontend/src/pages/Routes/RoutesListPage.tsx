import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  TextField,
  InputAdornment,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Snackbar,
  Fab,
  Pagination
} from '@mui/material';
import {
  Search as SearchIcon,
  Add as AddIcon,
  MoreVert as MoreIcon,
  Visibility as ViewIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  FileCopy as CopyIcon,
  GetApp as ExportIcon,
  Timeline as RouteIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

import { TechnologicalRoute } from '../../types/routes';
import { routesService } from '../../services/routesService';

const RoutesListPage: React.FC = () => {
  const navigate = useNavigate();
  
  // Состояния данных
  const [routes, setRoutes] = useState<TechnologicalRoute[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  
  // UI состояния
  const [menuAnchorEl, setMenuAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedRoute, setSelectedRoute] = useState<TechnologicalRoute | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error'>('success');

  // Загрузка данных
  useEffect(() => {
    loadRoutes();
  }, [page, searchQuery, selectedStatus]);

  const loadRoutes = async () => {
    try {
      setLoading(true);
      const filters = {
        search: searchQuery || undefined,
        status: selectedStatus !== 'all' ? selectedStatus as 'draft' | 'active' | 'archived' : undefined,
        page,
        limit: 12
      };
      
      const response = await routesService.getRoutes(filters);
      setRoutes(response.routes);
      setTotalPages(Math.ceil(response.total / 12));
    } catch (error) {
      console.error('Ошибка загрузки маршрутов:', error);
      showSnackbar('Ошибка загрузки маршрутов', 'error');
    } finally {
      setLoading(false);
    }
  };

  const showSnackbar = (message: string, severity: 'success' | 'error' = 'success') => {
    setSnackbarMessage(message);
    setSnackbarSeverity(severity);
    setSnackbarOpen(true);
  };

  // Обработчики меню
  const handleMenuClick = (event: React.MouseEvent<HTMLElement>, route: TechnologicalRoute) => {
    setMenuAnchorEl(event.currentTarget);
    setSelectedRoute(route);
  };

  const handleMenuClose = () => {
    setMenuAnchorEl(null);
    setSelectedRoute(null);
  };

  // Действия с маршрутами
  const handleView = (route: TechnologicalRoute) => {
    navigate(`/routes/${route.id}/view`);
    handleMenuClose();
  };

  const handleEdit = (route: TechnologicalRoute) => {
    navigate(`/routes/${route.id}/edit`);
    handleMenuClose();
  };

  const handleDuplicate = async (route: TechnologicalRoute) => {
    try {
      await routesService.duplicateRoute(route.id);
      showSnackbar('Маршрут успешно скопирован');
      loadRoutes();
    } catch (error) {
      showSnackbar('Ошибка копирования маршрута', 'error');
    }
    handleMenuClose();
  };

  const handleDeleteClick = (route: TechnologicalRoute) => {
    setSelectedRoute(route);
    setDeleteDialogOpen(true);
    handleMenuClose();
  };

  const handleDeleteConfirm = async () => {
    if (!selectedRoute) return;
    
    try {
      await routesService.deleteRoute(selectedRoute.id);
      showSnackbar('Маршрут успешно удален');
      loadRoutes();
    } catch (error) {
      showSnackbar('Ошибка удаления маршрута', 'error');
    }
    
    setDeleteDialogOpen(false);
    setSelectedRoute(null);
  };

  const handleExport = async (route: TechnologicalRoute) => {
    try {
      const blob = await routesService.exportRoute(route.id, 'excel');
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `route_${route.route_code}.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
      showSnackbar('Маршрут экспортирован');
    } catch (error) {
      showSnackbar('Ошибка экспорта маршрута', 'error');
    }
    handleMenuClose();
  };

  // Создание нового маршрута
  const handleCreateNew = () => {
    navigate('/routes/new');
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'draft': return 'warning';
      case 'inactive': return 'default';
      case 'archived': return 'error';
      default: return 'default';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'active': return 'Активный';
      case 'draft': return 'Черновик';
      case 'inactive': return 'Неактивный';
      case 'archived': return 'Архивный';
      default: return status;
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Заголовок и поиск */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <RouteIcon color="primary" />
          Технологические маршруты
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <TextField
            size="small"
            placeholder="Поиск маршрутов..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            sx={{ minWidth: 250 }}
          />
          
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreateNew}
          >
            Создать маршрут
          </Button>
        </Box>
      </Box>

      {/* Фильтры */}
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {[
            { value: 'all', label: 'Все' },
            { value: 'active', label: 'Активные' },
            { value: 'draft', label: 'Черновики' },
            { value: 'inactive', label: 'Неактивные' }
          ].map((filter) => (
            <Chip
              key={filter.value}
              label={filter.label}
              variant={selectedStatus === filter.value ? 'filled' : 'outlined'}
              color={selectedStatus === filter.value ? 'primary' : 'default'}
              onClick={() => setSelectedStatus(filter.value)}
              clickable
            />
          ))}
        </Box>
      </Box>

      {/* Список маршрутов */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <Typography>Загрузка...</Typography>
        </Box>
      ) : routes.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="h6" color="textSecondary">
            Маршруты не найдены
          </Typography>
          <Typography color="textSecondary" sx={{ mb: 2 }}>
            Создайте первый технологический маршрут
          </Typography>
          <Button variant="contained" startIcon={<AddIcon />} onClick={handleCreateNew}>
            Создать маршрут
          </Button>
        </Box>
      ) : (
        <>
          <Grid container spacing={3}>
            {routes.map((route) => (
              <Grid size={{ xs: 12, sm: 6, lg: 4 }} key={route.id}>
                <Card
                  sx={{
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    transition: 'transform 0.2s, box-shadow 0.2s',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: (theme) => theme.shadows[4],
                    },
                  }}
                >
                  <CardContent sx={{ flexGrow: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Typography variant="h6" component="h2" noWrap sx={{ flexGrow: 1, mr: 1 }}>
                        {route.name}
                      </Typography>
                      <IconButton
                        size="small"
                        onClick={(e) => handleMenuClick(e, route)}
                        sx={{ flexShrink: 0 }}
                      >
                        <MoreIcon />
                      </IconButton>
                    </Box>
                    
                    <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                      Код: {route.route_code}
                    </Typography>
                    
                    <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                      Версия: {route.version_number} ({route.total_operations} операций)
                    </Typography>
                    
                    {route.description && (
                      <Typography
                        variant="body2"
                        sx={{
                          mb: 2,
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden',
                        }}
                      >
                        {route.description}
                      </Typography>
                    )}
                    
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Chip
                        label={getStatusLabel(route.status)}
                        color={getStatusColor(route.status)}
                        size="small"
                      />
                      <Typography variant="caption" color="textSecondary">
                        {new Date(route.updated_at).toLocaleDateString()}
                      </Typography>
                    </Box>
                  </CardContent>
                  
                  <CardActions>
                    <Button
                      size="small"
                      startIcon={<ViewIcon />}
                      onClick={() => handleView(route)}
                    >
                      Просмотр
                    </Button>
                    <Button
                      size="small"
                      startIcon={<EditIcon />}
                      onClick={() => handleEdit(route)}
                    >
                      Изменить
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>

          {/* Пагинация */}
          {totalPages > 1 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
              <Pagination
                count={totalPages}
                page={page}
                onChange={(_, newPage) => setPage(newPage)}
                color="primary"
              />
            </Box>
          )}
        </>
      )}

      {/* FAB для создания */}
      <Fab
        color="primary"
        aria-label="создать маршрут"
        onClick={handleCreateNew}
        sx={{
          position: 'fixed',
          bottom: 16,
          right: 16,
        }}
      >
        <AddIcon />
      </Fab>

      {/* Контекстное меню */}
      <Menu
        anchorEl={menuAnchorEl}
        open={Boolean(menuAnchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => selectedRoute && handleView(selectedRoute)}>
          <ViewIcon sx={{ mr: 1 }} />
          Просмотр
        </MenuItem>
        <MenuItem onClick={() => selectedRoute && handleEdit(selectedRoute)}>
          <EditIcon sx={{ mr: 1 }} />
          Изменить
        </MenuItem>
        <MenuItem onClick={() => selectedRoute && handleDuplicate(selectedRoute)}>
          <CopyIcon sx={{ mr: 1 }} />
          Копировать
        </MenuItem>
        <MenuItem onClick={() => selectedRoute && handleExport(selectedRoute)}>
          <ExportIcon sx={{ mr: 1 }} />
          Экспорт
        </MenuItem>
        <MenuItem onClick={() => selectedRoute && handleDeleteClick(selectedRoute)} sx={{ color: 'error.main' }}>
          <DeleteIcon sx={{ mr: 1 }} />
          Удалить
        </MenuItem>
      </Menu>

      {/* Диалог подтверждения удаления */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Подтверждение удаления</DialogTitle>
        <DialogContent>
          <Typography>
            Вы уверены, что хотите удалить маршрут "{selectedRoute?.name}"?
            Это действие нельзя отменить.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>
            Отмена
          </Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            Удалить
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

export default RoutesListPage; 