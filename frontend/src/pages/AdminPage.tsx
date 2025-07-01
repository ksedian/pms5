import React, { useState } from 'react';
import {
  Container,
  Typography,
  AppBar,
  Toolbar,
  Button,
  Box,
  Tabs,
  Tab,
  Paper,
  Alert,
  Snackbar,
} from '@mui/material';
import {
  Security as SecurityIcon,
  People as PeopleIcon,
  Assignment as AssignmentIcon,
  Home as HomeIcon,
  VpnKey as PermissionIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import RoleList from '../components/Admin/RoleManagement/RoleList';
import PermissionMatrix from '../components/Admin/RoleManagement/PermissionMatrix';
import UserRoleAssignment from '../components/Admin/UserManagement/UserRoleAssignment';
import UserManagement from '../components/Admin/UserManagement/UserManagement';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`admin-tabpanel-${index}`}
      aria-labelledby={`admin-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const AdminPage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [tabValue, setTabValue] = useState(0);
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error';
  }>({ open: false, message: '', severity: 'success' });

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleError = (message: string) => {
    setSnackbar({ open: true, message, severity: 'error' });
  };

  const handleSuccess = (message: string) => {
    setSnackbar({ open: true, message, severity: 'success' });
  };

  const handleSnackbarClose = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  return (
    <>
      {/* Admin Header */}
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Админ панель MES
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Button
              color="inherit"
              startIcon={<HomeIcon />}
              onClick={() => navigate('/dashboard')}
            >
              На главную
            </Button>
            <Typography variant="body2">{user?.username}</Typography>
            <Button color="inherit" onClick={logout}>
              Выйти
            </Button>
          </Box>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Администрирование системы
        </Typography>

        {/* Navigation Tabs */}
        <Paper sx={{ mb: 3 }}>
          <Tabs value={tabValue} onChange={handleTabChange}>
            <Tab
              icon={<SecurityIcon />}
              label="Управление ролями"
              id="admin-tab-0"
              aria-controls="admin-tabpanel-0"
            />
            <Tab
              icon={<PermissionIcon />}
              label="Матрица разрешений"
              id="admin-tab-1"
              aria-controls="admin-tabpanel-1"
            />
            <Tab
              icon={<AssignmentIcon />}
              label="Назначение ролей"
              id="admin-tab-2"
              aria-controls="admin-tabpanel-2"
            />
            <Tab
              icon={<PeopleIcon />}
              label="Пользователи"
              id="admin-tab-3"
              aria-controls="admin-tabpanel-3"
            />
          </Tabs>
        </Paper>

        {/* Tab Panels */}
        <TabPanel value={tabValue} index={0}>
          <RoleList />
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <PermissionMatrix onError={handleError} onSuccess={handleSuccess} />
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <UserRoleAssignment />
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <UserManagement onError={handleError} onSuccess={handleSuccess} />
        </TabPanel>
      </Container>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={handleSnackbarClose} 
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </>
  );
};

export default AdminPage; 