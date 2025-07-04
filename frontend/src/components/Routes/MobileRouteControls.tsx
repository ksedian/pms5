import React, { useState } from 'react';
import {
  Box,
  Fab,
  SpeedDial,
  SpeedDialAction,
  SpeedDialIcon,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Typography,
  Divider,
  IconButton,
  useTheme,
  useMediaQuery
} from '@mui/material';
import {
  Add as AddIcon,
  Save as SaveIcon,
  Delete as DeleteIcon,
  Settings as SettingsIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  CenterFocusStrong as CenterIcon,
  Download as ExportIcon,
  Upload as ImportIcon,
  History as HistoryIcon,
  FileCopy as DuplicateIcon,
  Menu as MenuIcon,
  Close as CloseIcon
} from '@mui/icons-material';

interface MobileRouteControlsProps {
  onAddOperation: () => void;
  onSave: () => void;
  onDelete: () => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onCenter: () => void;
  onExport: () => void;
  onImport: () => void;
  onHistory: () => void;
  onDuplicate: () => void;
  onSettings: () => void;
  isSaving?: boolean;
  hasUnsavedChanges?: boolean;
  readOnly?: boolean;
}

const MobileRouteControls: React.FC<MobileRouteControlsProps> = ({
  onAddOperation,
  onSave,
  onDelete,
  onZoomIn,
  onZoomOut,
  onCenter,
  onExport,
  onImport,
  onHistory,
  onDuplicate,
  onSettings,
  isSaving = false,
  hasUnsavedChanges = false,
  readOnly = false
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [speedDialOpen, setSpeedDialOpen] = useState(false);

  if (!isMobile) {
    return null; // Показываем только на мобильных устройствах
  }

  const actions = [
    {
      icon: <AddIcon />,
      name: 'Добавить операцию',
      onClick: onAddOperation,
      disabled: readOnly
    },
    {
      icon: <SaveIcon />,
      name: 'Сохранить',
      onClick: onSave,
      disabled: readOnly || isSaving || !hasUnsavedChanges,
      color: hasUnsavedChanges ? 'primary' : 'default'
    },
    {
      icon: <DeleteIcon />,
      name: 'Удалить',
      onClick: onDelete,
      disabled: readOnly
    },
    {
      icon: <SettingsIcon />,
      name: 'Настройки',
      onClick: onSettings
    }
  ];

  const viewActions = [
    {
      icon: <ZoomInIcon />,
      name: 'Увеличить',
      onClick: onZoomIn
    },
    {
      icon: <ZoomOutIcon />,
      name: 'Уменьшить',
      onClick: onZoomOut
    },
    {
      icon: <CenterIcon />,
      name: 'По центру',
      onClick: onCenter
    }
  ];

  const utilityActions = [
    {
      icon: <ExportIcon />,
      name: 'Экспорт',
      onClick: onExport
    },
    {
      icon: <ImportIcon />,
      name: 'Импорт',
      onClick: onImport,
      disabled: readOnly
    },
    {
      icon: <HistoryIcon />,
      name: 'История',
      onClick: onHistory
    },
    {
      icon: <DuplicateIcon />,
      name: 'Дублировать',
      onClick: onDuplicate,
      disabled: readOnly
    }
  ];

  return (
    <>
      {/* Главная кнопка меню */}
      <Fab
        color="primary"
        aria-label="menu"
        sx={{
          position: 'fixed',
          bottom: 16,
          right: 16,
          zIndex: theme.zIndex.speedDial
        }}
        onClick={() => setDrawerOpen(true)}
      >
        <MenuIcon />
      </Fab>

      {/* SpeedDial для быстрых действий */}
      <SpeedDial
        ariaLabel="Быстрые действия"
        sx={{
          position: 'fixed',
          bottom: 16,
          left: 16,
          zIndex: theme.zIndex.speedDial - 1
        }}
        icon={<SpeedDialIcon />}
        open={speedDialOpen}
        onOpen={() => setSpeedDialOpen(true)}
        onClose={() => setSpeedDialOpen(false)}
        direction="up"
      >
        {actions.filter(action => !action.disabled).slice(0, 3).map((action) => (
          <SpeedDialAction
            key={action.name}
            icon={action.icon}
            tooltipTitle={action.name}
            onClick={() => {
              action.onClick();
              setSpeedDialOpen(false);
            }}
            sx={{
              color: action.color === 'primary' ? theme.palette.primary.main : undefined
            }}
          />
        ))}
      </SpeedDial>

      {/* Боковое меню */}
      <Drawer
        anchor="bottom"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        PaperProps={{
          sx: {
            maxHeight: '70vh',
            borderTopLeftRadius: theme.spacing(2),
            borderTopRightRadius: theme.spacing(2)
          }
        }}
      >
        <Box sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Управление маршрутом
            </Typography>
            <IconButton onClick={() => setDrawerOpen(false)}>
              <CloseIcon />
            </IconButton>
          </Box>

          <List>
            {/* Основные действия */}
            <Typography variant="subtitle2" color="text.secondary" sx={{ px: 2, py: 1 }}>
              Редактирование
            </Typography>
            {actions.map((action) => (
              <ListItem key={action.name} disablePadding>
                <ListItemButton
                  onClick={() => {
                    action.onClick();
                    setDrawerOpen(false);
                  }}
                  disabled={action.disabled}
                  sx={{
                    color: action.color === 'primary' ? theme.palette.primary.main : undefined
                  }}
                >
                  <ListItemIcon
                    sx={{
                      color: action.color === 'primary' ? theme.palette.primary.main : undefined
                    }}
                  >
                    {action.icon}
                  </ListItemIcon>
                  <ListItemText 
                    primary={action.name}
                    secondary={action.name === 'Сохранить' && hasUnsavedChanges ? 'Есть несохраненные изменения' : undefined}
                  />
                </ListItemButton>
              </ListItem>
            ))}

            <Divider sx={{ my: 1 }} />

            {/* Действия с видом */}
            <Typography variant="subtitle2" color="text.secondary" sx={{ px: 2, py: 1 }}>
              Вид
            </Typography>
            {viewActions.map((action) => (
              <ListItem key={action.name} disablePadding>
                <ListItemButton
                  onClick={() => {
                    action.onClick();
                    setDrawerOpen(false);
                  }}
                >
                  <ListItemIcon>{action.icon}</ListItemIcon>
                  <ListItemText primary={action.name} />
                </ListItemButton>
              </ListItem>
            ))}

            <Divider sx={{ my: 1 }} />

            {/* Утилиты */}
            <Typography variant="subtitle2" color="text.secondary" sx={{ px: 2, py: 1 }}>
              Утилиты
            </Typography>
            {utilityActions.map((action) => (
              <ListItem key={action.name} disablePadding>
                <ListItemButton
                  onClick={() => {
                    action.onClick();
                    setDrawerOpen(false);
                  }}
                  disabled={action.disabled}
                >
                  <ListItemIcon>{action.icon}</ListItemIcon>
                  <ListItemText primary={action.name} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>
    </>
  );
};

export default MobileRouteControls; 