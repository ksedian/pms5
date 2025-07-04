import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Chip,
  IconButton,
  Breadcrumbs,
  Link,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  Divider,
  Card,
  CardContent
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Edit as EditIcon,
  GetApp as ExportIcon,
  ExpandMore as ExpandMoreIcon,
  AccessTime as TimeIcon,
  Build as ToolIcon,
  Person as PersonIcon,
  Assignment as AssignmentIcon
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';

import { TechnologicalRoute, Operation } from '../../types/routes';
import { routesService } from '../../services/routesService';
import RouteFlowCanvas from '../../components/Routes/RouteFlowCanvas';

const RouteViewPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  
  const [route, setRoute] = useState<TechnologicalRoute | null>(null);
  const [loading, setLoading] = useState(true);
  const [operations, setOperations] = useState<Operation[]>([]);

  useEffect(() => {
    if (id) {
      loadRoute(parseInt(id));
    }
  }, [id]);

  const loadRoute = async (routeId: number) => {
    try {
      setLoading(true);
      const [loadedRoute, routeOperations] = await Promise.all([
        routesService.getRoute(routeId),
        routesService.getRouteOperations(routeId)
      ]);
      
      setRoute(loadedRoute);
      setOperations(routeOperations);
    } catch (error) {
      console.error('Ошибка загрузки маршрута:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format: 'excel' | 'pdf') => {
    if (!route) return;
    
    try {
      const blob = await routesService.exportRoute(route.id, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `route_${route.route_code}.${format === 'excel' ? 'xlsx' : 'pdf'}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Ошибка экспорта:', error);
    }
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

  const getOperationTypeLabel = (type: string) => {
    const types: Record<string, string> = {
      'machining': 'Механическая обработка',
      'assembly': 'Сборка',
      'inspection': 'Контроль',
      'transport': 'Транспортировка',
      'packaging': 'Упаковка',
      'heat_treatment': 'Термообработка',
      'surface_treatment': 'Обработка поверхности',
      'welding': 'Сварка',
      'painting': 'Покраска',
      'testing': 'Испытания'
    };
    return types[type] || type;
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
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Заголовок */}
      <Paper elevation={1} sx={{ p: 2, borderRadius: 0 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <IconButton onClick={() => navigate('/routes')}>
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
              <Typography color="text.primary">
                {route.name}
              </Typography>
            </Breadcrumbs>
          </Box>
          
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Chip
              label={getStatusLabel(route.status)}
              color={getStatusColor(route.status)}
              size="small"
            />
            
            <Button
              variant="outlined"
              startIcon={<ExportIcon />}
              onClick={() => handleExport('excel')}
            >
              Excel
            </Button>
            
            <Button
              variant="outlined"
              startIcon={<ExportIcon />}
              onClick={() => handleExport('pdf')}
            >
              PDF
            </Button>
            
            <Button
              variant="contained"
              startIcon={<EditIcon />}
              onClick={() => navigate(`/routes/${route.id}/edit`)}
            >
              Редактировать
            </Button>
          </Box>
        </Box>

        {/* Основная информация */}
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: 8 }}>
            <Typography variant="h5" gutterBottom>
              {route.name}
            </Typography>
            <Typography variant="body1" color="textSecondary" sx={{ mb: 2 }}>
              {route.description}
            </Typography>
          </Grid>
          
          <Grid size={{ xs: 12, md: 4 }}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Основные характеристики
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Код:</strong> {route.route_code}
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Версия:</strong> {route.version_number}
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Тип продукта:</strong> {route.product_type || 'Не указан'}
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Операций:</strong> {route.total_operations}
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Время:</strong> {route.estimated_time} мин
                </Typography>
                <Typography variant="body2">
                  <strong>Обновлен:</strong> {new Date(route.updated_at).toLocaleDateString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Вкладки с информацией */}
      <Box sx={{ flexGrow: 1, display: 'flex' }}>
        {/* Визуализация маршрута */}
        <Box sx={{ flexGrow: 1, position: 'relative' }}>
          <RouteFlowCanvas
            route={route}
            onRouteChange={() => {}} // Read-only режим
            readOnly={true}
          />
        </Box>

        {/* Боковая панель с деталями */}
        <Box sx={{ width: 400, borderLeft: 1, borderColor: 'divider', overflow: 'auto' }}>
          <Box sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Детали маршрута
            </Typography>

            {/* Список операций */}
            <Accordion defaultExpanded>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle1">
                  <AssignmentIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Операции ({operations.length})
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                {operations.length === 0 ? (
                  <Typography color="textSecondary" variant="body2">
                    Операции не добавлены
                  </Typography>
                ) : (
                  <List dense>
                    {operations.map((operation, index) => (
                      <React.Fragment key={operation.id}>
                        <ListItem>
                          <ListItemText
                            primary={
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <Typography variant="subtitle2">
                                  {index + 1}. {operation.name}
                                </Typography>
                                <Chip
                                  label={getOperationTypeLabel(operation.operation_type)}
                                  size="small"
                                  variant="outlined"
                                />
                              </Box>
                            }
                            secondary={
                              <Box>
                                <Typography variant="caption" display="block">
                                  Код: {operation.operation_code}
                                </Typography>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 1 }}>
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                    <TimeIcon fontSize="small" />
                                    <Typography variant="caption">
                                      {operation.total_time} мин
                                    </Typography>
                                  </Box>
                                  {operation.required_equipment && operation.required_equipment.length > 0 && (
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                      <ToolIcon fontSize="small" />
                                      <Typography variant="caption">
                                        {operation.required_equipment.length} ед.
                                      </Typography>
                                    </Box>
                                  )}
                                  {operation.required_skills && operation.required_skills.length > 0 && (
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                      <PersonIcon fontSize="small" />
                                      <Typography variant="caption">
                                        {operation.required_skills.length} навыков
                                      </Typography>
                                    </Box>
                                  )}
                                </Box>
                                {operation.description && (
                                  <Typography variant="caption" color="textSecondary" display="block" sx={{ mt: 1 }}>
                                    {operation.description}
                                  </Typography>
                                )}
                              </Box>
                            }
                          />
                        </ListItem>
                        {index < operations.length - 1 && <Divider />}
                      </React.Fragment>
                    ))}
                  </List>
                )}
              </AccordionDetails>
            </Accordion>

            {/* Статистика */}
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle1">
                  <TimeIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Временная статистика
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Параметр</TableCell>
                        <TableCell align="right">Значение</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      <TableRow>
                        <TableCell>Общее время</TableCell>
                        <TableCell align="right">{route.estimated_time} мин</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Время наладки</TableCell>
                        <TableCell align="right">
                          {operations.reduce((sum, op) => sum + op.setup_time, 0)} мин
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Время операций</TableCell>
                        <TableCell align="right">
                          {operations.reduce((sum, op) => sum + op.operation_time, 0)} мин
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Среднее время на операцию</TableCell>
                        <TableCell align="right">
                          {operations.length > 0 && route.estimated_time ? Math.round(route.estimated_time / operations.length) : 0} мин
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </AccordionDetails>
            </Accordion>

            {/* Ресурсы */}
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle1">
                  <ToolIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Требуемые ресурсы
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Оборудование:
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                    {Array.from(new Set(operations.flatMap(op => op.required_equipment || []))).map((equipment) => (
                      <Chip key={equipment} label={equipment} size="small" variant="outlined" />
                    ))}
                  </Box>
                  
                  <Typography variant="subtitle2" gutterBottom>
                    Навыки:
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {Array.from(new Set(operations.flatMap(op => op.required_skills || []))).map((skill) => (
                      <Chip key={skill} label={skill} size="small" variant="outlined" color="primary" />
                    ))}
                  </Box>
                </Box>
              </AccordionDetails>
            </Accordion>
          </Box>
        </Box>
      </Box>
    </Box>
  );
};

export default RouteViewPage; 