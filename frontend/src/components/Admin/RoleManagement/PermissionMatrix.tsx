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
  Checkbox,
  Alert,
  CircularProgress,
  Chip,
  Toolbar,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Tooltip,
  useTheme,
  alpha,
} from '@mui/material';
import { Save as SaveIcon, Refresh as RefreshIcon } from '@mui/icons-material';
import { adminService } from '../../../services/adminService';
import { Role, Permission } from '../../../types/auth';

interface PermissionMatrixProps {
  onError?: (message: string) => void;
  onSuccess?: (message: string) => void;
}

interface RolePermission {
  roleId: number;
  permissionId: number;
  hasPermission: boolean;
}

const PermissionMatrix: React.FC<PermissionMatrixProps> = ({ onError, onSuccess }) => {
  const theme = useTheme();
  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [matrix, setMatrix] = useState<RolePermission[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedRole, setSelectedRole] = useState<number | ''>('');
  const [changes, setChanges] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadData();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [rolesResponse, permissionsResponse] = await Promise.all([
        adminService.getRoles(),
        adminService.getPermissions(),
      ]);

      setRoles(rolesResponse.roles);
      setPermissions(permissionsResponse.permissions);
      
      // Создаем матрицу разрешений
      const matrixData: RolePermission[] = [];
      rolesResponse.roles.forEach(role => {
        permissionsResponse.permissions.forEach(permission => {
          matrixData.push({
            roleId: role.id,
            permissionId: permission.id,
            hasPermission: role.permissions?.includes(permission.name) || false,
          });
        });
      });
      
      setMatrix(matrixData);
    } catch (err: any) {
      const errorMsg = err.message || 'Ошибка загрузки данных';
      setError(errorMsg);
      onError?.(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const togglePermission = (roleId: number, permissionId: number) => {
    const key = `${roleId}-${permissionId}`;
    const currentMatrix = [...matrix];
    const index = currentMatrix.findIndex(
      item => item.roleId === roleId && item.permissionId === permissionId
    );

    if (index !== -1) {
      currentMatrix[index].hasPermission = !currentMatrix[index].hasPermission;
      setMatrix(currentMatrix);
      
      const newChanges = new Set(changes);
      if (newChanges.has(key)) {
        newChanges.delete(key);
      } else {
        newChanges.add(key);
      }
      setChanges(newChanges);
    }
  };

  const saveChanges = async () => {
    if (changes.size === 0) return;

    setSaving(true);
    try {
      const promises: Promise<any>[] = [];

      changes.forEach(key => {
        const [roleId, permissionId] = key.split('-').map(Number);
        const matrixItem = matrix.find(
          item => item.roleId === roleId && item.permissionId === permissionId
        );

        if (matrixItem) {
          if (matrixItem.hasPermission) {
            promises.push(adminService.assignPermission(roleId, permissionId));
          } else {
            promises.push(adminService.revokePermission(roleId, permissionId));
          }
        }
      });

      await Promise.all(promises);
      setChanges(new Set());
      onSuccess?.('Изменения разрешений сохранены успешно');
      
      // Перезагружаем данные для синхронизации
      await loadData();
    } catch (err: any) {
      const errorMsg = err.message || 'Ошибка сохранения изменений';
      setError(errorMsg);
      onError?.(errorMsg);
    } finally {
      setSaving(false);
    }
  };

  const hasPermission = (roleId: number, permissionId: number): boolean => {
    const item = matrix.find(
      item => item.roleId === roleId && item.permissionId === permissionId
    );
    return item?.hasPermission || false;
  };

  const getPermissionsByResource = () => {
    const grouped: { [key: string]: Permission[] } = {};
    permissions.forEach(permission => {
      const resource = permission.resource || 'other';
      if (!grouped[resource]) {
        grouped[resource] = [];
      }
      grouped[resource].push(permission);
    });
    return grouped;
  };

  const filteredRoles = selectedRole ? roles.filter(role => role.id === selectedRole) : roles;
  const groupedPermissions = getPermissionsByResource();

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
          Матрица разрешений
        </Typography>
        
        <FormControl size="small" sx={{ minWidth: 200, mr: 2 }}>
          <InputLabel>Фильтр по роли</InputLabel>
          <Select
            value={selectedRole}
            label="Фильтр по роли"
            onChange={(e) => setSelectedRole(e.target.value as number | '')}
          >
            <MenuItem value="">Все роли</MenuItem>
            {roles.map(role => (
              <MenuItem key={role.id} value={role.id}>
                {role.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={loadData}
          sx={{ mr: 1 }}
        >
          Обновить
        </Button>

        <Button
          variant="contained"
          startIcon={<SaveIcon />}
          onClick={saveChanges}
          disabled={changes.size === 0 || saving}
          color="primary"
        >
          {saving ? 'Сохранение...' : `Сохранить (${changes.size})`}
        </Button>
      </Toolbar>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {changes.size > 0 && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Несохраненных изменений: {changes.size}. Нажмите "Сохранить" для применения.
        </Alert>
      )}

      <Paper>
        <TableContainer sx={{ maxHeight: 600 }}>
          <Table stickyHeader size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 'bold', minWidth: 150 }}>
                  Разрешения / Роли
                </TableCell>
                {filteredRoles.map(role => (
                  <TableCell
                    key={role.id}
                    align="center"
                    sx={{ 
                      fontWeight: 'bold', 
                      minWidth: 120,
                      backgroundColor: alpha(theme.palette.primary.main, 0.1)
                    }}
                  >
                    <Tooltip title={role.description || role.name}>
                      <Box>
                        {role.name}
                        {role.is_system_role && (
                          <Chip
                            label="Система"
                            size="small"
                            color="secondary"
                            sx={{ ml: 1, fontSize: '0.6rem' }}
                          />
                        )}
                      </Box>
                    </Tooltip>
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.entries(groupedPermissions).map(([resource, resourcePermissions]) => (
                <React.Fragment key={resource}>
                  <TableRow>
                    <TableCell
                      colSpan={filteredRoles.length + 1}
                      sx={{
                        backgroundColor: alpha(theme.palette.secondary.main, 0.1),
                        fontWeight: 'bold',
                        textTransform: 'uppercase',
                        fontSize: '0.85rem',
                      }}
                    >
                      {resource}
                    </TableCell>
                  </TableRow>
                  {resourcePermissions.map(permission => (
                    <TableRow
                      key={permission.id}
                      hover
                      sx={{
                        '&:hover': {
                          backgroundColor: alpha(theme.palette.action.hover, 0.5),
                        },
                      }}
                    >
                      <TableCell>
                        <Tooltip title={permission.description}>
                          <Box>
                            <Typography variant="body2" fontWeight="medium">
                              {permission.name}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {permission.action}
                            </Typography>
                          </Box>
                        </Tooltip>
                      </TableCell>
                      {filteredRoles.map(role => (
                        <TableCell key={role.id} align="center">
                          <Checkbox
                            checked={hasPermission(role.id, permission.id)}
                            onChange={() => togglePermission(role.id, permission.id)}
                            disabled={role.is_system_role && role.name === 'Super Admin'}
                            color="primary"
                            sx={{
                              '&.Mui-checked': {
                                color: theme.palette.success.main,
                              },
                            }}
                          />
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </React.Fragment>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );
};

export default PermissionMatrix; 