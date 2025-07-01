import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Box, CircularProgress, Typography } from '@mui/material';
import { useAuth } from '../../context/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: string;
  requiredPermission?: string;
  requiredResource?: string;
  requiredAction?: string;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRole,
  requiredPermission,
  requiredResource,
  requiredAction,
}) => {
  const { user, isLoading, isAuthenticated, hasRole, hasPermission, checkPermission } = useAuth();
  const location = useLocation();

  // Добавляем логирование для отладки
  console.log('ProtectedRoute - проверка доступа:', {
    isAuthenticated,
    isLoading,
    user: user ? { username: user.username, roles: user.roles, permissions: user.permissions } : null,
    requiredRole,
    requiredPermission,
    requiredResource,
    requiredAction,
    path: location.pathname
  });

  // Показываем загрузку пока определяется статус аутентификации
  if (isLoading) {
    return (
      <Box
        display="flex"
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        minHeight="100vh"
        gap={2}
      >
        <CircularProgress />
        <Typography variant="body1">Загрузка...</Typography>
      </Box>
    );
  }

  // Если пользователь не аутентифицирован, перенаправляем на логин
  if (!isAuthenticated) {
    console.log('ProtectedRoute - пользователь не аутентифицирован, перенаправление на логин');
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Проверяем роль, если требуется
  if (requiredRole && !hasRole(requiredRole)) {
    console.log('ProtectedRoute - доступ запрещен: требуется роль', requiredRole, 'у пользователя роли:', user?.roles);
    return <Navigate to="/unauthorized" replace />;
  }

  // Проверяем разрешение, если требуется
  if (requiredPermission && !hasPermission(requiredPermission)) {
    console.log('ProtectedRoute - доступ запрещен: требуется разрешение', requiredPermission, 'у пользователя разрешения:', user?.permissions);
    return <Navigate to="/unauthorized" replace />;
  }

  // Проверяем ресурс и действие, если требуется
  if (requiredResource && requiredAction && !checkPermission(requiredResource, requiredAction)) {
    console.log('ProtectedRoute - доступ запрещен: требуется разрешение', `${requiredResource}:${requiredAction}`);
    return <Navigate to="/unauthorized" replace />;
  }

  console.log('ProtectedRoute - доступ разрешен');
  // Все проверки пройдены, отображаем защищенный контент
  return <>{children}</>;
};

export default ProtectedRoute; 