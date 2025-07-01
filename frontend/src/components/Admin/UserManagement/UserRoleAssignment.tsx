import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  PersonAdd as PersonAddIcon,
  Delete as DeleteIcon,
  People as PeopleIcon,
} from '@mui/icons-material';
import { adminService } from '../../../services/adminService';
import { User, Role } from '../../../types/auth';

const UserRoleAssignment: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [assignDialogOpen, setAssignDialogOpen] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [selectedRoleId, setSelectedRoleId] = useState<number | ''>('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [usersResponse, rolesResponse] = await Promise.all([
        adminService.getUsers(),
        adminService.getRoles()
      ]);
      setUsers(usersResponse.users);
      setRoles(rolesResponse.roles);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  const handleAssignRole = (userId: number) => {
    setSelectedUserId(userId);
    setSelectedRoleId('');
    setAssignDialogOpen(true);
  };

  const confirmAssignRole = async () => {
    if (!selectedUserId || !selectedRoleId) return;

    try {
      await adminService.assignRole(selectedUserId, selectedRoleId as number);
      await loadData(); // Перезагружаем данные
      setAssignDialogOpen(false);
      setSelectedUserId(null);
      setSelectedRoleId('');
    } catch (err: any) {
      setError(err.message || 'Ошибка назначения роли');
    }
  };

  const handleRevokeRole = async (userId: number, roleId: number) => {
    try {
      await adminService.revokeRole(userId, roleId);
      await loadData(); // Перезагружаем данные
    } catch (err: any) {
      setError(err.message || 'Ошибка отзыва роли');
    }
  };

  const getUserRoles = (user: User): Role[] => {
    return roles.filter(role => user.roles.includes(role.name));
  };

  const getAvailableRoles = (userId: number): Role[] => {
    const user = users.find(u => u.id === userId);
    if (!user) return [];
    
    return roles.filter(role => !user.roles.includes(role.name) && !role.is_system_role);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box display="flex" alignItems="center" gap={1} mb={3}>
        <PeopleIcon />
        <Typography variant="h5">Назначение ролей пользователям</Typography>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Users Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Пользователь</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Статус</TableCell>
              <TableCell>Роли</TableCell>
              <TableCell align="right">Действия</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {users.map((user) => {
              const userRoles = getUserRoles(user);
              return (
                <TableRow key={user.id} hover>
                  <TableCell>
                    <Typography variant="subtitle2">{user.username}</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {user.email}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={user.is_active ? 'Активен' : 'Неактивен'}
                      color={user.is_active ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {userRoles.map((role) => (
                        <Chip
                          key={role.id}
                          label={role.name}
                          size="small"
                          onDelete={
                            !role.is_system_role 
                              ? () => handleRevokeRole(user.id, role.id)
                              : undefined
                          }
                          deleteIcon={<DeleteIcon />}
                          color={role.is_system_role ? 'primary' : 'default'}
                        />
                      ))}
                      {userRoles.length === 0 && (
                        <Typography variant="body2" color="text.secondary">
                          Нет ролей
                        </Typography>
                      )}
                    </Box>
                  </TableCell>
                  <TableCell align="right">
                    <Button
                      size="small"
                      startIcon={<PersonAddIcon />}
                      onClick={() => handleAssignRole(user.id)}
                      disabled={getAvailableRoles(user.id).length === 0}
                    >
                      Назначить роль
                    </Button>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Assign Role Dialog */}
      <Dialog open={assignDialogOpen} onClose={() => setAssignDialogOpen(false)}>
        <DialogTitle>Назначение роли пользователю</DialogTitle>
        <DialogContent sx={{ width: 300, pt: 2 }}>
          <FormControl fullWidth>
            <InputLabel>Выберите роль</InputLabel>
            <Select
              value={selectedRoleId}
              label="Выберите роль"
              onChange={(e) => setSelectedRoleId(e.target.value)}
            >
              {selectedUserId && getAvailableRoles(selectedUserId).map((role) => (
                <MenuItem key={role.id} value={role.id}>
                  {role.name} - {role.description}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAssignDialogOpen(false)}>Отмена</Button>
          <Button
            onClick={confirmAssignRole}
            variant="contained"
            disabled={!selectedRoleId}
          >
            Назначить
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UserRoleAssignment; 