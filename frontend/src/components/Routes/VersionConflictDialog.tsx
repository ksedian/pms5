import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Alert,
  Divider
} from '@mui/material';
import {
  Warning as WarningIcon,
  Refresh as RefreshIcon,
  Save as SaveIcon
} from '@mui/icons-material';

interface VersionConflictDialogProps {
  open: boolean;
  onClose: () => void;
  onRefresh: () => void;
  onForceUpdate: () => void;
  currentVersion: number;
  serverVersion: number;
  conflictDetails?: {
    lastModifiedBy?: string;
    lastModifiedAt?: string;
    changes?: string[];
  };
}

const VersionConflictDialog: React.FC<VersionConflictDialogProps> = ({
  open,
  onClose,
  onRefresh,
  onForceUpdate,
  currentVersion,
  serverVersion,
  conflictDetails
}) => {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 2,
          boxShadow: 4
        }
      }}
    >
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1, pb: 1 }}>
        <WarningIcon color="warning" />
        <Typography variant="h6">
          Конфликт версий
        </Typography>
      </DialogTitle>

      <DialogContent>
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="body2">
            Технологический маршрут был изменен другим пользователем во время вашего редактирования.
            Ваши изменения не могут быть сохранены без разрешения конфликта.
          </Typography>
        </Alert>

        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
            Информация о версиях:
          </Typography>
          <Box sx={{ display: 'flex', gap: 4, mb: 2 }}>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Ваша версия:
              </Typography>
              <Typography variant="body1" fontWeight="medium">
                {currentVersion}
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Текущая версия на сервере:
              </Typography>
              <Typography variant="body1" fontWeight="medium">
                {serverVersion}
              </Typography>
            </Box>
          </Box>

          {conflictDetails && (
            <>
              <Divider sx={{ my: 2 }} />
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Детали изменений:
                </Typography>
                {conflictDetails.lastModifiedBy && (
                  <Typography variant="body2" color="text.secondary">
                    Изменено пользователем: {conflictDetails.lastModifiedBy}
                  </Typography>
                )}
                {conflictDetails.lastModifiedAt && (
                  <Typography variant="body2" color="text.secondary">
                    Время изменения: {new Date(conflictDetails.lastModifiedAt).toLocaleString('ru-RU')}
                  </Typography>
                )}
              </Box>

              {conflictDetails.changes && conflictDetails.changes.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Конфликтующие изменения:
                  </Typography>
                  <Box component="ul" sx={{ pl: 2, mt: 1 }}>
                    {conflictDetails.changes.map((change, index) => (
                      <Typography
                        key={index}
                        component="li"
                        variant="body2"
                        color="text.secondary"
                        sx={{ mb: 0.5 }}
                      >
                        {change}
                      </Typography>
                    ))}
                  </Box>
                </Box>
              )}
            </>
          )}
        </Box>

        <Alert severity="info" sx={{ mb: 2 }}>
          <Typography variant="body2">
            <strong>Рекомендуется:</strong> Обновить данные с сервера, чтобы получить последние изменения,
            а затем внести ваши изменения заново.
          </Typography>
        </Alert>

        <Alert severity="error">
          <Typography variant="body2">
            <strong>Принудительное сохранение:</strong> Перезапишет изменения других пользователей.
            Используйте только если вы уверены в своих действиях.
          </Typography>
        </Alert>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 3 }}>
        <Button
          onClick={onClose}
          variant="outlined"
          color="secondary"
        >
          Отмена
        </Button>
        
        <Button
          onClick={onRefresh}
          variant="contained"
          color="primary"
          startIcon={<RefreshIcon />}
          sx={{ ml: 1 }}
        >
          Обновить данные
        </Button>
        
        <Button
          onClick={onForceUpdate}
          variant="contained"
          color="warning"
          startIcon={<SaveIcon />}
          sx={{ ml: 1 }}
        >
          Принудительно сохранить
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default VersionConflictDialog; 