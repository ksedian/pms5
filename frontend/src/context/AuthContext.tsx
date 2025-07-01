import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, LoginRequest } from '../types/auth';
import { authService } from '../services/authService';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => void;
  hasRole: (role: string) => boolean;
  hasPermission: (permission: string) => boolean;
  checkPermission: (resource: string, action: string) => boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!user;

  // Инициализация - проверяем сохраненный токен
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const userData = await authService.getProfile();
          console.log('User data loaded:', userData);
          
          // Убеждаемся что roles и permissions являются массивами
          const safeUserData = {
            ...userData,
            roles: Array.isArray(userData.roles) ? userData.roles : [],
            permissions: Array.isArray(userData.permissions) ? userData.permissions : []
          };
          
          setUser(safeUserData);
        } catch (error) {
          console.error('Failed to load user profile:', error);
          // Токен недействителен, очищаем
          localStorage.removeItem('access_token');
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = async (credentials: LoginRequest): Promise<void> => {
    const response = await authService.login(credentials);
    if (response.access_token) {
      localStorage.setItem('access_token', response.access_token);
      
      // Убеждаемся что roles и permissions являются массивами
      const safeUserData = {
        ...response.user,
        roles: Array.isArray(response.user.roles) ? response.user.roles : [],
        permissions: Array.isArray(response.user.permissions) ? response.user.permissions : []
      };
      
      setUser(safeUserData);
    }
  };

  const logout = (): void => {
    localStorage.removeItem('access_token');
    setUser(null);
  };

  const hasRole = (role: string): boolean => {
    const result = user?.roles?.includes(role) || false;
    console.log('hasRole проверка:', { user: user?.username, userRoles: user?.roles, requiredRole: role, result });
    return result;
  };

  const hasPermission = (permission: string): boolean => {
    return user?.permissions?.includes(permission) || user?.permissions?.includes('*:*') || false;
  };

  const checkPermission = (resource: string, action: string): boolean => {
    const permission = `${resource}:${action}`;
    return hasPermission(permission) || hasPermission(`${resource}:*`) || hasPermission('*:*');
  };

  const contextValue: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    login,
    logout,
    hasRole,
    hasPermission,
    checkPermission,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}; 