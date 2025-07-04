import React from 'react';
import {
  Container,
  Typography,
  Card,
  CardContent,
  AppBar,
  Toolbar,
  Button,
  Box,
  Chip,
  Grid,
} from '@mui/material';
import {
  Timeline as RouteIcon,
  AdminPanelSettings as AdminIcon,
  Assignment as TaskIcon,
  Assessment as ReportIcon,
  Person as ProfileIcon
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const DashboardPage: React.FC = () => {
  const { user, logout, hasRole } = useAuth();
  const navigate = useNavigate();

  if (!user) {
    return <Typography>Загрузка...</Typography>;
  }

  return (
    <>
      {/* Header */}
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            MES System Dashboard
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="body2">
              {user.username}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              {user.roles && user.roles.map((role) => (
                <Chip
                  key={role}
                  label={role}
                  size="small"
                  variant="outlined"
                  sx={{ color: 'white', borderColor: 'white' }}
                />
              ))}
            </Box>
            <Button color="inherit" onClick={logout}>
              Выйти
            </Button>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Добро пожаловать, {user.username}!
        </Typography>
        
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {/* Профиль пользователя */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Профиль пользователя
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Email: {user.email}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                2FA: {user.is_2fa_enabled ? 'Включен' : 'Отключен'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Статус: {user.is_active ? 'Активен' : 'Неактивен'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Роли: {user.roles ? user.roles.join(', ') : 'Нет ролей'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Разрешений: {user.permissions ? user.permissions.length : 0}
              </Typography>
            </CardContent>
          </Card>

          {/* Админ панель */}
          {hasRole('admin') && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Администрирование
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Управление пользователями и ролями
                </Typography>
                <Button
                  variant="contained"
                  onClick={() => navigate('/admin')}
                  sx={{ mt: 2 }}
                >
                  Админ панель
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Основные модули */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Основные модули системы
              </Typography>
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Card 
                    variant="outlined" 
                    sx={{ 
                      cursor: 'pointer', 
                      transition: 'all 0.2s',
                      '&:hover': { 
                        boxShadow: 2,
                        transform: 'translateY(-2px)'
                      }
                    }}
                    onClick={() => navigate('/routes')}
                  >
                    <CardContent sx={{ textAlign: 'center', py: 3 }}>
                      <RouteIcon color="primary" sx={{ fontSize: 48, mb: 1 }} />
                      <Typography variant="h6" gutterBottom>
                        Технологические маршруты
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Управление производственными процессами
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Card 
                    variant="outlined" 
                    sx={{ 
                      cursor: 'pointer', 
                      transition: 'all 0.2s',
                      '&:hover': { 
                        boxShadow: 2,
                        transform: 'translateY(-2px)'
                      }
                    }}
                    onClick={() => navigate('/bom')}
                  >
                    <CardContent sx={{ textAlign: 'center', py: 3 }}>
                      <TaskIcon color="primary" sx={{ fontSize: 48, mb: 1 }} />
                      <Typography variant="h6" gutterBottom>
                        BOM
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Спецификации материалов и компонентов
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Card 
                    variant="outlined" 
                    sx={{ 
                      cursor: 'pointer', 
                      transition: 'all 0.2s',
                      '&:hover': { 
                        boxShadow: 2,
                        transform: 'translateY(-2px)'
                      }
                    }}
                    onClick={() => navigate('/reports')}
                  >
                    <CardContent sx={{ textAlign: 'center', py: 3 }}>
                      <ReportIcon color="primary" sx={{ fontSize: 48, mb: 1 }} />
                      <Typography variant="h6" gutterBottom>
                        Отчеты
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Аналитика и отчетность
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Card 
                    variant="outlined" 
                    sx={{ 
                      cursor: 'pointer', 
                      transition: 'all 0.2s',
                      '&:hover': { 
                        boxShadow: 2,
                        transform: 'translateY(-2px)'
                      }
                    }}
                    onClick={() => navigate('/profile')}
                  >
                    <CardContent sx={{ textAlign: 'center', py: 3 }}>
                      <ProfileIcon color="primary" sx={{ fontSize: 48, mb: 1 }} />
                      <Typography variant="h6" gutterBottom>
                        Профиль
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Настройки учетной записи
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Box>
      </Container>
    </>
  );
};

export default DashboardPage; 