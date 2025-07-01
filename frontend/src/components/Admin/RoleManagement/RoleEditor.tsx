import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  Alert,
  CircularProgress,
} from '@mui/material';
import { adminService } from '../../../services/adminService';
import { Role } from '../../../types/auth';

interface RoleEditorProps {
  open: boolean;
  role: Role | null; // null для создания новой роли
  onClose: () => void;
  onSaved: () => void;
}

interface RoleFormData {
  name: string;
  description: string;
}

const RoleEditor: React.FC<RoleEditorProps> = ({ open, role, onClose, onSaved }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  
  const { register, handleSubmit, formState: { errors }, reset, setValue } = useForm<RoleFormData>();

  const isEditMode = !!role;

  useEffect(() => {
    if (open) {
      if (role) {
        // Заполняем форму данными роли для редактирования
        setValue('name', role.name);
        setValue('description', role.description || '');
      } else {
        // Очищаем форму для создания новой роли
        reset();
      }
      setError('');
    }
  }, [open, role, setValue, reset]);

  const onSubmit = async (data: RoleFormData) => {
    setLoading(true);
    setError('');

    try {
      if (isEditMode && role) {
        // Обновляем существующую роль
        await adminService.updateRole(role.id, data);
      } else {
        // Создаем новую роль
        await adminService.createRole(data);
      }
      
      onSaved(); // Уведомляем родительский компонент об успешном сохранении
    } catch (err: any) {
      setError(err.message || `Ошибка ${isEditMode ? 'обновления' : 'создания'} роли`);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {isEditMode ? `Редактирование роли "${role?.name}"` : 'Создание новой роли'}
      </DialogTitle>

      <form onSubmit={handleSubmit(onSubmit)}>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              fullWidth
              label="Название роли"
              disabled={loading || (isEditMode && role?.is_system_role)}
              {...register('name', {
                required: 'Название роли обязательно',
                minLength: {
                  value: 2,
                  message: 'Минимум 2 символа'
                },
                pattern: {
                  value: /^[a-zA-Z0-9_-]+$/,
                  message: 'Только буквы, цифры, дефисы и подчеркивания'
                }
              })}
              error={!!errors.name}
              helperText={errors.name?.message}
            />

            <TextField
              fullWidth
              label="Описание"
              multiline
              rows={3}
              disabled={loading}
              {...register('description')}
              error={!!errors.description}
              helperText={errors.description?.message}
            />

            {isEditMode && role?.is_system_role && (
              <Alert severity="info">
                Системные роли имеют ограничения на редактирование
              </Alert>
            )}
          </Box>
        </DialogContent>

        <DialogActions>
          <Button onClick={handleClose} disabled={loading}>
            Отмена
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={loading}
          >
            {loading ? (
              <>
                <CircularProgress size={20} sx={{ mr: 1 }} />
                {isEditMode ? 'Обновление...' : 'Создание...'}
              </>
            ) : (
              isEditMode ? 'Обновить' : 'Создать'
            )}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default RoleEditor; 