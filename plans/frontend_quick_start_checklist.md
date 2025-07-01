# Чек-лист быстрого старта: Frontend интерфейсы

**Модель:** Claude-3.5-Sonnet  
**Дата:** 2024-12-19  
**Статус:** 🚀 ГОТОВ К ВЫПОЛНЕНИЮ

## 🎯 Цель
Быстро создать React SPA интерфейс для готовой системы аутентификации и RBAC.

## ⚡ Быстрый старт (первые 2 часа)

### 📦 Шаг 1: Настройка проекта (30 мин)
```bash
# В директории pms5/
npx create-react-app frontend --template typescript
cd frontend

# Установка зависимостей
npm install @mui/material @emotion/react @emotion/styled
npm install @mui/icons-material @mui/lab  
npm install react-router-dom axios
npm install @hookform/react-hook-form yup
npm install @types/node @types/react @types/react-dom

# Очистка и структура
rm -rf src/App.css src/logo.svg src/reportWebVitals.ts
mkdir -p src/{components,pages,hooks,services,context,utils,types,theme}
mkdir -p src/components/{Auth,Layout,Admin,Common}
```

### 🏗️ Шаг 2: Базовая структура (45 мин)
```typescript
// src/types/auth.ts
export interface User {
  id: number;
  username: string;
  email: string;
  roles: string[];
  permissions: string[];
  is_2fa_enabled: boolean;
  is_active: boolean;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  user: User;
  requires_2fa?: boolean;
  user_id?: number;
}
```

```typescript
// src/services/apiClient.ts
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token interceptor
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### 🎨 Шаг 3: Theme и Layout (45 мин)
```typescript
// src/theme/theme.ts
import { createTheme } from '@mui/material/styles';

export const lightTheme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#1976d2' },
    secondary: { main: '#dc004e' },
  },
});

export const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#90caf9' },
    secondary: { main: '#f48fb1' },
  },
});
```

```jsx
// src/App.tsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AuthProvider } from './context/AuthContext';
import { lightTheme } from './theme/theme';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ProtectedRoute from './components/Common/ProtectedRoute';

function App() {
  return (
    <ThemeProvider theme={lightTheme}>
      <CssBaseline />
      <AuthProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/" element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            } />
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
```

## 🔐 Приоритет 1: Authentication (следующие 3 часа)

### ✅ AuthContext
```typescript
// src/context/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, LoginRequest } from '../types/auth';
import { authService } from '../services/authService';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => void;
  hasRole: (role: string) => boolean;
  hasPermission: (permission: string) => boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const login = async (credentials: LoginRequest) => {
    const response = await authService.login(credentials);
    if (response.access_token) {
      localStorage.setItem('access_token', response.access_token);
      setUser(response.user);
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setUser(null);
  };

  const hasRole = (role: string) => user?.roles.includes(role) || false;
  const hasPermission = (permission: string) => user?.permissions.includes(permission) || false;

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout, hasRole, hasPermission }}>
      {children}
    </AuthContext.Provider>
  );
};
```

### ✅ Login Form
```jsx
// src/components/Auth/LoginForm.tsx
import React from 'react';
import { useForm } from 'react-hook-form';
import { TextField, Button, Paper, Typography, Alert } from '@mui/material';
import { useAuth } from '../../context/AuthContext';

interface LoginFormData {
  username: string;
  password: string;
}

const LoginForm: React.FC = () => {
  const { register, handleSubmit, formState: { errors } } = useForm<LoginFormData>();
  const { login } = useAuth();
  const [error, setError] = React.useState<string>('');
  const [isLoading, setIsLoading] = React.useState(false);

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    setError('');
    try {
      await login(data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Ошибка входа');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 4, maxWidth: 400, mx: 'auto', mt: 8 }}>
      <Typography variant="h4" component="h1" gutterBottom align="center">
        Вход в MES
      </Typography>
      
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      
      <form onSubmit={handleSubmit(onSubmit)}>
        <TextField
          fullWidth
          label="Имя пользователя"
          margin="normal"
          {...register('username', { required: 'Обязательное поле' })}
          error={!!errors.username}
          helperText={errors.username?.message}
        />
        
        <TextField
          fullWidth
          type="password"
          label="Пароль"
          margin="normal"
          {...register('password', { required: 'Обязательное поле' })}
          error={!!errors.password}
          helperText={errors.password?.message}
        />
        
        <Button
          type="submit"
          fullWidth
          variant="contained"
          sx={{ mt: 3, mb: 2 }}
          disabled={isLoading}
        >
          {isLoading ? 'Вход...' : 'Войти'}
        </Button>
      </form>
    </Paper>
  );
};

export default LoginForm;
```

## 🛡️ Приоритет 2: RBAC компоненты (2 часа)

### ✅ ProtectedRoute
```jsx
// src/components/Common/ProtectedRoute.tsx
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: string;
  requiredPermission?: string;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requiredRole, 
  requiredPermission 
}) => {
  const { user, isLoading } = useAuth();

  if (isLoading) return <div>Загрузка...</div>;
  if (!user) return <Navigate to="/login" />;
  
  if (requiredRole && !user.roles.includes(requiredRole)) {
    return <Navigate to="/unauthorized" />;
  }
  
  if (requiredPermission && !user.permissions.includes(requiredPermission)) {
    return <Navigate to="/unauthorized" />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
```

### ✅ RoleGuard
```jsx
// src/components/Common/RoleGuard.tsx
import React from 'react';
import { useAuth } from '../../context/AuthContext';

interface RoleGuardProps {
  roles: string[];
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

const RoleGuard: React.FC<RoleGuardProps> = ({ roles, children, fallback = null }) => {
  const { user } = useAuth();
  
  const hasRequiredRole = user?.roles.some(role => roles.includes(role));
  
  return hasRequiredRole ? <>{children}</> : <>{fallback}</>;
};

export default RoleGuard;
```

## 📱 Приоритет 3: Layout (2 часа)

### ✅ AppHeader
```jsx
// src/components/Layout/AppHeader.tsx
import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { useAuth } from '../../context/AuthContext';

const AppHeader: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          MES System
        </Typography>
        
        {user && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="body2">
              {user.username} ({user.roles.join(', ')})
            </Typography>
            <Button color="inherit" onClick={logout}>
              Выйти
            </Button>
          </Box>
        )}
      </Toolbar>
    </AppBar>
  );
};

export default AppHeader;
```

## 🏠 Приоритет 4: Dashboard (1 час)

### ✅ Dashboard
```jsx
// src/pages/DashboardPage.tsx
import React from 'react';
import { Container, Typography, Grid, Card, CardContent } from '@mui/material';
import { useAuth } from '../context/AuthContext';
import AppHeader from '../components/Layout/AppHeader';
import RoleGuard from '../components/Common/RoleGuard';

const DashboardPage: React.FC = () => {
  const { user } = useAuth();

  return (
    <>
      <AppHeader />
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Добро пожаловать, {user?.username}!
        </Typography>
        
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6">Профиль</Typography>
                <Typography variant="body2">Email: {user?.email}</Typography>
                <Typography variant="body2">2FA: {user?.is_2fa_enabled ? 'Включен' : 'Отключен'}</Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <RoleGuard roles={['admin']}>
            <Grid item xs={12} sm={6} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6">Администрирование</Typography>
                  <Typography variant="body2">Управление пользователями и ролями</Typography>
                </CardContent>
              </Card>
            </Grid>
          </RoleGuard>
        </Grid>
      </Container>
    </>
  );
};

export default DashboardPage;
```

## 🔧 Environment Setup

### ✅ .env файл
```bash
# frontend/.env
REACT_APP_API_URL=http://localhost:5000
REACT_APP_APP_NAME=MES Authentication System
```

### ✅ package.json scripts
```json
{
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "dev": "REACT_APP_API_URL=http://localhost:5000 npm start"
  }
}
```

## 🚀 Порядок выполнения

### День 1 (8 часов):
1. ✅ **Час 1-2:** Настройка проекта + базовая структура
2. ✅ **Час 3-5:** Authentication system (Context + Login)
3. ✅ **Час 6-7:** RBAC компоненты (ProtectedRoute + Guards)
4. ✅ **Час 8:** Layout + Dashboard

### День 2 (8 часов):
1. ✅ **Час 1-3:** 2FA интерфейсы (Setup + Verify)
2. ✅ **Час 4-5:** Theme system + Responsive
3. ✅ **Час 6-8:** Admin interface (Users + Roles)

### День 3 (6 часов):
1. ✅ **Час 1-2:** Admin interface (Permissions + Audit)
2. ✅ **Час 3-4:** Error handling + Loading states
3. ✅ **Час 5-6:** Testing + Polish

## 📋 Критерии готовности

### Минимальный MVP (8 часов):
- [ ] Login с backend интеграцией
- [ ] Dashboard с role-based content
- [ ] RBAC route protection
- [ ] Basic responsive layout

### Полная версия (22 часа):
- [ ] Полный 2FA workflow
- [ ] Admin panel со всеми CRUD операциями
- [ ] Theme switching
- [ ] Mobile optimization
- [ ] Comprehensive testing

## 🎯 API Endpoints для интеграции

```typescript
// Готовые Flask API endpoints:
POST /api/auth/login           // Вход
POST /api/auth/register        // Регистрация  
POST /api/auth/setup-2fa       // Настройка 2FA
POST /api/auth/verify-2fa      // Проверка 2FA
GET  /api/auth/profile         // Профиль пользователя
POST /api/auth/logout          // Выход

GET  /api/admin/users          // Список пользователей
GET  /api/admin/roles          // Список ролей
GET  /api/admin/permissions    // Список разрешений
POST /api/admin/users/{id}/roles // Назначение роли

GET  /api/health               // Health check
```

---

**План готов к немедленному выполнению!** 🚀  
**Начинайте с создания React проекта и базовой структуры.** 