import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline, createTheme } from '@mui/material';
import { AuthProvider } from './context/AuthContext';
import { lightTheme, darkTheme } from './theme/theme';
import ProtectedRoute from './components/Common/ProtectedRoute';
import LoginForm from './components/Auth/LoginForm';

// Pages
import DashboardPage from './pages/DashboardPage';
import AdminPage from './pages/AdminPage';
import UnauthorizedPage from './pages/UnauthorizedPage';

// Routes Pages
import RoutesListPage from './pages/Routes/RoutesListPage';
import RouteEditorPage from './pages/Routes/RouteEditorPage';
import RouteViewPage from './pages/Routes/RouteViewPage';
import RouteHistoryPage from './pages/Routes/RouteHistoryPage';

function App() {
  const [isDarkMode, setIsDarkMode] = useState(false);
  
  const currentTheme = isDarkMode ? darkTheme : lightTheme;

  return (
    <ThemeProvider theme={currentTheme}>
      <CssBaseline />
      <AuthProvider>
        <Router>
          <Routes>
            {/* Публичные маршруты */}
            <Route path="/login" element={<LoginForm />} />
            <Route path="/unauthorized" element={<UnauthorizedPage />} />
            
            {/* Защищенные маршруты */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            
            {/* Админ панель - только для администраторов */}
            <Route
              path="/admin/*"
              element={
                <ProtectedRoute requiredRole="admin">
                  <AdminPage />
                </ProtectedRoute>
              }
            />
            
            {/* Технологические маршруты */}
            <Route
              path="/routes"
              element={
                <ProtectedRoute>
                  <RoutesListPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/routes/new"
              element={
                <ProtectedRoute requiredPermission="create_route">
                  <RouteEditorPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/routes/:id/edit"
              element={
                <ProtectedRoute requiredPermission="edit_route">
                  <RouteEditorPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/routes/:id/view"
              element={
                <ProtectedRoute requiredPermission="view_route">
                  <RouteViewPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/routes/:id/history"
              element={
                <ProtectedRoute requiredPermission="view_route">
                  <RouteHistoryPage />
                </ProtectedRoute>
              }
            />
            
            {/* Перенаправления */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
