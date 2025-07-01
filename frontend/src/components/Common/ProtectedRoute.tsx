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
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Проверяем роль, если требуется
  if (requiredRole && !hasRole(requiredRole)) {
    return <Navigate to="/unauthorized" replace />;
  }

  // Проверяем разрешение, если требуется
  if (requiredPermission && !hasPermission(requiredPermission)) {
    return <Navigate to="/unauthorized" replace />;
  }

  // Проверяем ресурс и действие, если требуется
  if (requiredResource && requiredAction && !checkPermission(requiredResource, requiredAction)) {
    return <Navigate to="/unauthorized" replace />;
  }

  // Все проверки пройдены, отображаем защищенный контент
  return <>{children}</>;
};

export default ProtectedRoute; 