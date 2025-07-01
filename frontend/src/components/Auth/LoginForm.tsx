import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  TextField,
  Button,
  Paper,
  Typography,
  Alert,
  Box,
  CircularProgress,
} from '@mui/material';
import { useAuth } from '../../context/AuthContext';

interface LoginFormData {
  username: string;
  password: string;
}

const LoginForm: React.FC = () => {
  const { register, handleSubmit, formState: { errors } } = useForm<LoginFormData>();
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  
  const [error, setError] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);

  // Определяем куда перенаправить после успешного входа
  const from = (location.state as any)?.from?.pathname || '/dashboard';

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    setError('');
    
    try {
      await login(data);
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err.message || 'Ошибка входа в систему');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      minHeight="100vh"
      sx={{ bgcolor: 'background.default', p: 2 }}
    >
      <Paper elevation={3} sx={{ p: 4, maxWidth: 400, width: '100%' }}>
        <Box textAlign="center" mb={3}>
          <Typography variant="h4" component="h1" gutterBottom>
            Вход в MES
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Система управления производством
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit(onSubmit)}>
          <TextField
            fullWidth
            label="Имя пользователя"
            margin="normal"
            disabled={isLoading}
            {...register('username', { 
              required: 'Имя пользователя обязательно',
              minLength: {
                value: 3,
                message: 'Минимум 3 символа'
              }
            })}
            error={!!errors.username}
            helperText={errors.username?.message}
          />

          <TextField
            fullWidth
            type="password"
            label="Пароль"
            margin="normal"
            disabled={isLoading}
            {...register('password', { 
              required: 'Пароль обязателен',
              minLength: {
                value: 6,
                message: 'Минимум 6 символов'
              }
            })}
            error={!!errors.password}
            helperText={errors.password?.message}
          />

          <Button
            type="submit"
            fullWidth
            variant="contained"
            sx={{ mt: 3, mb: 2 }}
            disabled={isLoading}
            size="large"
          >
            {isLoading ? (
              <>
                <CircularProgress size={20} sx={{ mr: 1 }} />
                Вход...
              </>
            ) : (
              'Войти'
            )}
          </Button>
        </form>

        <Box textAlign="center" mt={2}>
          <Typography variant="body2" color="text.secondary">
            Нет аккаунта?{' '}
            <Button 
              variant="text" 
              size="small"
              onClick={() => navigate('/register')}
              disabled={isLoading}
            >
              Зарегистрироваться
            </Button>
          </Typography>
        </Box>
      </Paper>
    </Box>
  );
};

export default LoginForm; 