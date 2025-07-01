import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  CircularProgress,
  Chip,
  Button,
  Toolbar,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
  Tooltip,
  useTheme,
  alpha,
} from '@mui/material';
import {
  LockOpen as UnlockIcon,
  PersonOff as DeactivateIcon,
  PersonAdd as ActivateIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { adminService } from '../../../services/adminService';
import { User } from '../../../types/auth';

interface UserManagementProps {
  onError?: (message: string) => void;
  onSuccess?: (message: string) => void;
}

const UserManagement: React.FC<UserManagementProps> = ({ onError, onSuccess }) => {
  const theme = useTheme();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'inactive'>('all');
  const [confirmDialog, setConfirmDialog] = useState<{
    open: boolean;
    user: User | null;
    action: 'activate' | 'deactivate' | 'unlock';
    title: string;
    content: string;
  }>({
    open: false,
    user: null,
    action: 'activate',
    title: '',
    content: '',
  });

  useEffect(() => {
    loadUsers();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const loadUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await adminService.getUsers();
      setUsers(response.users);
    } catch (err: any) {
      const errorMsg = err.message || 'Ошибка загрузки пользователей';
      setError(errorMsg);
      onError?.(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleUserAction = async (action: 'activate' | 'deactivate' | 'unlock') => {
    if (!confirmDialog.user) return;

    setActionLoading(confirmDialog.user.id);
    try {
      switch (action) {
        case 'activate':
          await adminService.activateUser(confirmDialog.user.id);
          onSuccess?.(`Пользователь ${confirmDialog.user.username} активирован`);
          break;
        case 'deactivate':
          await adminService.deactivateUser(confirmDialog.user.id);
          onSuccess?.(`Пользователь ${confirmDialog.user.username} деактивирован`);
          break;
        case 'unlock':
          await adminService.unlockUser(confirmDialog.user.id);
          onSuccess?.(`Пользователь ${confirmDialog.user.username} разблокирован`);
          break;
      }
      await loadUsers();
    } catch (err: any) {
      const errorMsg = err.message || 'Ошибка выполнения операции';
      onError?.(errorMsg);
    } finally {
      setActionLoading(null);
      setConfirmDialog(prev => ({ ...prev, open: false }));
    }
  };

  const openConfirmDialog = (
    user: User,
    action: 'activate' | 'deactivate' | 'unlock',
    title: string,
    content: string
  ) => {
    setConfirmDialog({
      open: true,
      user,
      action,
      title,
      content,
    });
  };

  const filteredUsers = users.filter(user => {
    if (filterStatus === 'active') return user.is_active;
    if (filterStatus === 'inactive') return !user.is_active;
    return true;
  });

  const getUserStatusChip = (user: User) => {
    if (!user.is_active) {
      return (
        <Chip
          label="Неактивен"
          color="error"
          size="small"
          variant="outlined"
        />
      );
    }
    return (
      <Chip
        label="Активен"
        color="success"
        size="small"
        variant="outlined"
      />
    );
  };

  const formatLastLogin = (lastLogin?: string) => {
    if (!lastLogin) return 'Никогда';
    return new Date(lastLogin).toLocaleString('ru-RU');
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight={200}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Toolbar sx={{ pl: 0, pr: 0 }}>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Управление пользователями
        </Typography>
        
        <FormControl size="small" sx={{ minWidth: 150, mr: 2 }}>
          <InputLabel>Статус</InputLabel>
          <Select
            value={filterStatus}
            label="Статус"
            onChange={(e) => setFilterStatus(e.target.value as 'all' | 'active' | 'inactive')}
          >
            <MenuItem value="all">Все</MenuItem>
            <MenuItem value="active">Активные</MenuItem>
            <MenuItem value="inactive">Неактивные</MenuItem>
          </Select>
        </FormControl>

        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={loadUsers}
        >
          Обновить
        </Button>
      </Toolbar>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 'bold' }}>Пользователь</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>Email</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>Роли</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>Статус</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>2FA</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>Последний вход</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }} align="center">Действия</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredUsers.map((user) => (
                <TableRow
                  key={user.id}
                  hover
                  sx={{
                    '&:hover': {
                      backgroundColor: alpha(theme.palette.action.hover, 0.5),
                    },
                  }}
                >
                  <TableCell>
                    <Box>
                      <Typography variant="body2" fontWeight="medium">
                        {user.username}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        ID: {user.id}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>{user.email}</TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                      {user.roles.map((role, index) => (
                        <Chip
                          key={index}
                          label={role}
                          size="small"
                          variant="outlined"
                          color="primary"
                        />
                      ))}
                    </Box>
                  </TableCell>
                  <TableCell>{getUserStatusChip(user)}</TableCell>
                  <TableCell>
                    <Chip
                      label={user.is_2fa_enabled ? 'Включена' : 'Отключена'}
                      size="small"
                      color={user.is_2fa_enabled ? 'success' : 'default'}
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {formatLastLogin(user.last_login)}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center' }}>
                      {user.is_active ? (
                        <Tooltip title="Деактивировать пользователя">
                          <Button
                            size="small"
                            variant="outlined"
                            color="error"
                            startIcon={<DeactivateIcon />}
                            disabled={actionLoading === user.id}
                            onClick={() => openConfirmDialog(
                              user,
                              'deactivate',
                              'Деактивировать пользователя',
                              `Вы уверены, что хотите деактивировать пользователя ${user.username}? Он не сможет войти в систему.`
                            )}
                          >
                            Деактивировать
                          </Button>
                        </Tooltip>
                      ) : (
                        <Tooltip title="Активировать пользователя">
                          <Button
                            size="small"
                            variant="outlined"
                            color="success"
                            startIcon={<ActivateIcon />}
                            disabled={actionLoading === user.id}
                            onClick={() => openConfirmDialog(
                              user,
                              'activate',
                              'Активировать пользователя',
                              `Вы уверены, что хотите активировать пользователя ${user.username}?`
                            )}
                          >
                            Активировать
                          </Button>
                        </Tooltip>
                      )}
                      
                      <Tooltip title="Разблокировать пользователя">
                        <Button
                          size="small"
                          variant="outlined"
                          startIcon={<UnlockIcon />}
                          disabled={actionLoading === user.id}
                          onClick={() => openConfirmDialog(
                            user,
                            'unlock',
                            'Разблокировать пользователя',
                            `Вы уверены, что хотите разблокировать пользователя ${user.username}?`
                          )}
                        >
                          Разблокировать
                        </Button>
                      </Tooltip>
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
              {filteredUsers.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Typography variant="body2" color="text.secondary">
                      Пользователи не найдены
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Confirmation Dialog */}
      <Dialog
        open={confirmDialog.open}
        onClose={() => setConfirmDialog(prev => ({ ...prev, open: false }))}
      >
        <DialogTitle>{confirmDialog.title}</DialogTitle>
        <DialogContent>
          <DialogContentText>
            {confirmDialog.content}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => setConfirmDialog(prev => ({ ...prev, open: false }))}
          >
            Отмена
          </Button>
          <Button
            onClick={() => handleUserAction(confirmDialog.action)}
            disabled={actionLoading !== null}
            color="primary"
            variant="contained"
          >
            Подтвердить
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UserManagement; 