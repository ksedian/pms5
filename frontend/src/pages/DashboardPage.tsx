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
} from '@mui/material';
import { useAuth } from '../context/AuthContext';

const DashboardPage: React.FC = () => {
  const { user, logout, hasRole } = useAuth();

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
                  href="/admin"
                  sx={{ mt: 2 }}
                >
                  Админ панель
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Быстрые действия */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Быстрые действия
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Button variant="outlined">Просмотр задач</Button>
                <Button variant="outlined">Маршруты</Button>
                <Button variant="outlined">Отчеты</Button>
                <Button variant="outlined">Профиль</Button>
              </Box>
            </CardContent>
          </Card>
        </Box>
      </Container>
    </>
  );
};

export default DashboardPage; 