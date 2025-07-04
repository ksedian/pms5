import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Breadcrumbs,
  Link,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Card,
  CardContent,
  Divider
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Visibility as ViewIcon,
  Restore as RestoreIcon,
  Compare as CompareIcon,
  GetApp as ExportIcon
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';

import { TechnologicalRoute, RouteVersion } from '../../types/routes';
import { routesService } from '../../services/routesService';

const RouteHistoryPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  
  const [route, setRoute] = useState<TechnologicalRoute | null>(null);
  const [versions, setVersions] = useState<RouteVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedVersions, setSelectedVersions] = useState<number[]>([]);
  const [compareDialogOpen, setCompareDialogOpen] = useState(false);
  const [restoreDialogOpen, setRestoreDialogOpen] = useState(false);
  const [versionToRestore, setVersionToRestore] = useState<RouteVersion | null>(null);

  useEffect(() => {
    if (id) {
      loadData(parseInt(id));
    }
  }, [id]);

  const loadData = async (routeId: number) => {
    try {
      setLoading(true);
      const [routeData, versionsData] = await Promise.all([
        routesService.getRoute(routeId),
        routesService.getRouteVersions(routeId)
      ]);
      
      setRoute(routeData);
      setVersions(versionsData);
    } catch (error) {
      console.error('Ошибка загрузки данных:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleVersionSelect = (versionId: number) => {
    setSelectedVersions(prev => {
      if (prev.includes(versionId)) {
        return prev.filter(id => id !== versionId);
      } else if (prev.length < 2) {
        return [...prev, versionId];
      } else {
        return [prev[1], versionId];
      }
    });
  };

  const handleCompare = () => {
    if (selectedVersions.length === 2) {
      setCompareDialogOpen(true);
    }
  };

  const handleRestoreClick = (version: RouteVersion) => {
    setVersionToRestore(version);
    setRestoreDialogOpen(true);
  };

  const handleRestoreConfirm = async () => {
    if (!versionToRestore || !route) return;
    
    try {
      await routesService.restoreRouteVersion(route.id, versionToRestore.id);
      navigate(`/routes/${route.id}/edit`);
    } catch (error) {
      console.error('Ошибка восстановления версии:', error);
    }
    
    setRestoreDialogOpen(false);
    setVersionToRestore(null);
  };

  const getChangeTypeColor = (changeType: string) => {
    switch (changeType) {
      case 'created': return 'success';
      case 'updated': return 'primary';
      case 'published': return 'warning';
      case 'archived': return 'error';
      default: return 'default';
    }
  };

  const getChangeTypeLabel = (changeType: string) => {
    switch (changeType) {
      case 'created': return 'Создан';
      case 'updated': return 'Обновлен';
      case 'published': return 'Опубликован';
      case 'archived': return 'Архивирован';
      default: return changeType;
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!route) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="h6" color="error">
          Маршрут не найден
        </Typography>
        <Button onClick={() => navigate('/routes')} sx={{ mt: 2 }}>
          Вернуться к списку
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Заголовок */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <IconButton onClick={() => navigate(`/routes/${route.id}/view`)}>
            <BackIcon />
          </IconButton>
          <Breadcrumbs>
            <Link 
              color="inherit" 
              onClick={() => navigate('/routes')}
              sx={{ cursor: 'pointer' }}
            >
              Маршруты
            </Link>
            <Link 
              color="inherit" 
              onClick={() => navigate(`/routes/${route.id}/view`)}
              sx={{ cursor: 'pointer' }}
            >
              {route.name}
            </Link>
            <Typography color="text.primary">
              История версий
            </Typography>
          </Breadcrumbs>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<CompareIcon />}
            onClick={handleCompare}
            disabled={selectedVersions.length !== 2}
          >
            Сравнить ({selectedVersions.length}/2)
          </Button>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Основная информация */}
        <Grid size={{ xs: 12, md: 8 }}>
          <Paper sx={{ p: 2, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              История версий: {route.name}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Текущая версия: {route.version_number} • Всего версий: {versions.length}
            </Typography>
          </Paper>

          {/* Таблица версий */}
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell padding="checkbox"></TableCell>
                  <TableCell>Версия</TableCell>
                  <TableCell>Тип изменения</TableCell>
                  <TableCell>Автор</TableCell>
                  <TableCell>Дата</TableCell>
                  <TableCell>Описание</TableCell>
                  <TableCell align="center">Действия</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {versions.map((version) => (
                  <TableRow 
                    key={version.id}
                    selected={selectedVersions.includes(version.id)}
                    onClick={() => handleVersionSelect(version.id)}
                    sx={{ cursor: 'pointer' }}
                  >
                    <TableCell padding="checkbox">
                      <input
                        type="checkbox"
                        checked={selectedVersions.includes(version.id)}
                        onChange={() => handleVersionSelect(version.id)}
                      />
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body2" fontWeight="bold">
                          v{version.version_number}
                        </Typography>
                        {version.version_number === route.version_number && (
                          <Chip label="Текущая" size="small" color="primary" />
                        )}
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={getChangeTypeLabel(version.change_type || 'unknown')}
                        size="small"
                        color={getChangeTypeColor(version.change_type || 'unknown')}
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {version.created_by_name || `Пользователь ${version.created_by}`}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {new Date(version.created_at).toLocaleString()}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography 
                        variant="body2" 
                        sx={{ 
                          maxWidth: 200, 
                          overflow: 'hidden', 
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap'
                        }}
                      >
                        {version.change_summary || 'Без описания'}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <IconButton 
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation();
                            // Открыть версию для просмотра
                          }}
                          title="Просмотр"
                        >
                          <ViewIcon />
                        </IconButton>
                        
                        {version.version_number !== route.version_number && (
                          <IconButton 
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleRestoreClick(version);
                            }}
                            title="Восстановить"
                          >
                            <RestoreIcon />
                          </IconButton>
                        )}
                        
                        <IconButton 
                          size="small"
                          onClick={async (e) => {
                            e.stopPropagation();
                            try {
                              const blob = await routesService.exportRouteVersion(version.id, 'excel');
                              const url = URL.createObjectURL(blob);
                              const a = document.createElement('a');
                              a.href = url;
                              a.download = `route_${route.route_code}_v${version.version_number}.xlsx`;
                              a.click();
                              URL.revokeObjectURL(url);
                            } catch (error) {
                              console.error('Ошибка экспорта версии:', error);
                            }
                          }}
                          title="Экспорт"
                        >
                          <ExportIcon />
                        </IconButton>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Grid>

        {/* Боковая панель со статистикой */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Статистика изменений
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="textSecondary">
                  Общее количество версий
                </Typography>
                <Typography variant="h4" color="primary">
                  {versions.length}
                </Typography>
              </Box>
              
              <Divider sx={{ my: 2 }} />
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Типы изменений
                </Typography>
                {Object.entries(
                  versions.reduce((acc, version) => {
                    const changeType = version.change_type || 'unknown';
                    acc[changeType] = (acc[changeType] || 0) + 1;
                    return acc;
                  }, {} as Record<string, number>)
                ).map(([type, count]) => (
                  <Box key={type} sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Chip
                      label={getChangeTypeLabel(type)}
                      size="small"
                      color={getChangeTypeColor(type)}
                      variant="outlined"
                    />
                    <Typography variant="body2">{count}</Typography>
                  </Box>
                ))}
              </Box>
              
              <Divider sx={{ my: 2 }} />
              
              <Box>
                <Typography variant="body2" color="textSecondary">
                  Последнее изменение
                </Typography>
                <Typography variant="body2">
                  {versions.length > 0 && new Date(versions[0].created_at).toLocaleDateString()}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Диалог сравнения версий */}
      <Dialog 
        open={compareDialogOpen} 
        onClose={() => setCompareDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Сравнение версий</DialogTitle>
        <DialogContent>
          {selectedVersions.length === 2 && (
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="h6" gutterBottom>
                  Версия {versions.find(v => v.id === selectedVersions[0])?.version_number}
                </Typography>
                {/* Здесь можно добавить детальное сравнение */}
                <Typography variant="body2" color="textSecondary">
                  Функция детального сравнения будет реализована в следующих версиях
                </Typography>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="h6" gutterBottom>
                  Версия {versions.find(v => v.id === selectedVersions[1])?.version_number}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Функция детального сравнения будет реализована в следующих версиях
                </Typography>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCompareDialogOpen(false)}>
            Закрыть
          </Button>
        </DialogActions>
      </Dialog>

      {/* Диалог восстановления версии */}
      <Dialog open={restoreDialogOpen} onClose={() => setRestoreDialogOpen(false)}>
        <DialogTitle>Восстановление версии</DialogTitle>
        <DialogContent>
          <Typography>
            Вы уверены, что хотите восстановить версию {versionToRestore?.version_number}?
            Это создаст новую версию на основе выбранной.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRestoreDialogOpen(false)}>
            Отмена
          </Button>
          <Button onClick={handleRestoreConfirm} color="primary" variant="contained">
            Восстановить
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default RouteHistoryPage; 