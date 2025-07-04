import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Typography,
  InputAdornment,
  Autocomplete,
  Divider,
  Alert
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  AccessTime as TimeIcon,
  Build as ToolIcon
} from '@mui/icons-material';

import { Operation } from '../../types/routes';

interface OperationDialogProps {
  operation: Operation | null;
  properties: Record<string, any>;
  onSave: (operation: Operation | null, properties: Record<string, any>) => void;
  onCancel: () => void;
}

const operationTypes = [
  { value: 'machining', label: 'Механическая обработка' },
  { value: 'assembly', label: 'Сборка' },
  { value: 'inspection', label: 'Контроль' },
  { value: 'transport', label: 'Транспортировка' },
  { value: 'packaging', label: 'Упаковка' },
  { value: 'heat_treatment', label: 'Термообработка' },
  { value: 'surface_treatment', label: 'Обработка поверхности' },
  { value: 'welding', label: 'Сварка' },
  { value: 'painting', label: 'Покраска' },
  { value: 'testing', label: 'Испытания' }
];

const commonEquipment = [
  'Токарный станок',
  'Фрезерный станок',
  'Сверлильный станок',
  'Шлифовальный станок',
  'Сварочный аппарат'
];

const commonSkills = [
  'Токарь',
  'Фрезеровщик',
  'Сварщик',
  'Слесарь-сборщик',
  'Контролер качества'
];

const OperationDialog: React.FC<OperationDialogProps> = ({
  operation,
  properties,
  onSave,
  onCancel
}) => {
  const [formData, setFormData] = useState({
    name: '',
    operation_code: '',
    operation_type: '',
    description: '',
    setup_time: 0,
    operation_time: 0,
    required_equipment: [] as string[],
    required_skills: [] as string[],
    quality_requirements: {} as Record<string, any>
  });

  const [formProperties, setFormProperties] = useState<Record<string, any>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (operation) {
      setFormData({
        name: operation.name,
        operation_code: operation.operation_code,
        operation_type: operation.operation_type,
        description: operation.description || '',
        setup_time: operation.setup_time,
        operation_time: operation.operation_time,
        required_equipment: operation.required_equipment || [],
        required_skills: operation.required_skills || [],
        quality_requirements: operation.quality_requirements || {}
      });
    } else {
      const timestamp = Date.now().toString().slice(-6);
      setFormData(prev => ({
        ...prev,
        operation_code: `OP-${timestamp}`
      }));
    }
    setFormProperties(properties);
  }, [operation, properties]);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Название операции обязательно';
    }

    if (!formData.operation_code.trim()) {
      newErrors.operation_code = 'Код операции обязателен';
    }

    if (!formData.operation_type) {
      newErrors.operation_type = 'Тип операции обязателен';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));

    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const handleSave = () => {
    if (!validateForm()) {
      return;
    }

    const operationData: Operation = {
      id: operation?.id || 0,
      name: formData.name,
      operation_code: formData.operation_code,
      operation_type: formData.operation_type,
      description: formData.description,
      setup_time: formData.setup_time,
      operation_time: formData.operation_time,
      total_time: formData.setup_time + formData.operation_time,
      required_equipment: formData.required_equipment,
      required_skills: formData.required_skills,
      quality_requirements: formData.quality_requirements,
      created_by: operation?.created_by,
      created_at: operation?.created_at || new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    onSave(operationData, formProperties);
  };

  const [newQualityKey, setNewQualityKey] = useState('');
  const [newQualityValue, setNewQualityValue] = useState('');

  const addQualityRequirement = () => {
    if (newQualityKey.trim() && newQualityValue.trim()) {
      setFormData(prev => ({
        ...prev,
        quality_requirements: {
          ...prev.quality_requirements,
          [newQualityKey]: newQualityValue
        }
      }));
      setNewQualityKey('');
      setNewQualityValue('');
    }
  };

  const removeQualityRequirement = (key: string) => {
    setFormData(prev => {
      const newRequirements = { ...prev.quality_requirements };
      delete newRequirements[key];
      return {
        ...prev,
        quality_requirements: newRequirements
      };
    });
  };

  return (
    <Box sx={{ p: 2 }}>
      <Grid container spacing={3}>
        <Grid size={12}>
          <Typography variant="h6" gutterBottom>
            Основная информация
          </Typography>
        </Grid>

        <Grid size={{ xs: 12, sm: 8 }}>
          <TextField
            fullWidth
            label="Название операции"
            value={formData.name}
            onChange={(e) => handleInputChange('name', e.target.value)}
            error={!!errors.name}
            helperText={errors.name}
            required
            variant="outlined"
          />
        </Grid>

        <Grid size={{ xs: 12, sm: 4 }}>
          <TextField
            fullWidth
            label="Код операции"
            value={formData.operation_code}
            onChange={(e) => handleInputChange('operation_code', e.target.value)}
            error={!!errors.operation_code}
            helperText={errors.operation_code}
            required
            variant="outlined"
          />
        </Grid>

        <Grid size={{ xs: 12, sm: 6 }}>
          <FormControl fullWidth error={!!errors.operation_type}>
            <InputLabel>Тип операции *</InputLabel>
            <Select
              value={formData.operation_type}
              onChange={(e) => handleInputChange('operation_type', e.target.value)}
              label="Тип операции *"
            >
              {operationTypes.map((type) => (
                <MenuItem key={type.value} value={type.value}>
                  {type.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        <Grid size={12}>
          <TextField
            fullWidth
            label="Описание"
            value={formData.description}
            onChange={(e) => handleInputChange('description', e.target.value)}
            multiline
            rows={3}
            variant="outlined"
          />
        </Grid>

        <Grid size={12}>
          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            Временные характеристики
          </Typography>
        </Grid>

        <Grid size={{ xs: 12, sm: 4 }}>
          <TextField
            fullWidth
            label="Время наладки"
            type="number"
            value={formData.setup_time}
            onChange={(e) => handleInputChange('setup_time', parseFloat(e.target.value) || 0)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <TimeIcon />
                </InputAdornment>
              ),
              endAdornment: <InputAdornment position="end">мин</InputAdornment>,
            }}
            variant="outlined"
          />
        </Grid>

        <Grid size={{ xs: 12, sm: 4 }}>
          <TextField
            fullWidth
            label="Время операции"
            type="number"
            value={formData.operation_time}
            onChange={(e) => handleInputChange('operation_time', parseFloat(e.target.value) || 0)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <TimeIcon />
                </InputAdornment>
              ),
              endAdornment: <InputAdornment position="end">мин</InputAdornment>,
            }}
            variant="outlined"
          />
        </Grid>

        <Grid size={{ xs: 12, sm: 4 }}>
          <TextField
            fullWidth
            label="Общее время"
            type="number"
            value={formData.setup_time + formData.operation_time}
            InputProps={{
              readOnly: true,
              startAdornment: (
                <InputAdornment position="start">
                  <TimeIcon />
                </InputAdornment>
              ),
              endAdornment: <InputAdornment position="end">мин</InputAdornment>,
            }}
            variant="outlined"
          />
        </Grid>

        <Grid size={12}>
          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            Ресурсы
          </Typography>
        </Grid>

        <Grid size={{ xs: 12, sm: 6 }}>
          <Autocomplete
            multiple
            value={formData.required_equipment}
            onChange={(_, newValue) => handleInputChange('required_equipment', newValue)}
            options={commonEquipment}
            freeSolo
            renderTags={(value, getTagProps) =>
              value.map((option, index) => (
                <Chip variant="outlined" label={option} {...getTagProps({ index })} />
              ))
            }
            renderInput={(params) => (
              <TextField
                {...params}
                label="Требуемое оборудование"
                variant="outlined"
                InputProps={{
                  ...params.InputProps,
                  startAdornment: (
                    <InputAdornment position="start">
                      <ToolIcon />
                    </InputAdornment>
                  ),
                }}
              />
            )}
          />
        </Grid>

        <Grid size={{ xs: 12, sm: 6 }}>
          <Autocomplete
            multiple
            value={formData.required_skills}
            onChange={(_, newValue) => handleInputChange('required_skills', newValue)}
            options={commonSkills}
            freeSolo
            renderTags={(value, getTagProps) =>
              value.map((option, index) => (
                <Chip variant="outlined" label={option} {...getTagProps({ index })} />
              ))
            }
            renderInput={(params) => (
              <TextField
                {...params}
                label="Требуемые навыки"
                variant="outlined"
              />
            )}
          />
        </Grid>

        <Grid size={12}>
          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            Требования к качеству
          </Typography>
          
          {Object.keys(formData.quality_requirements).length === 0 && (
            <Alert severity="info" sx={{ mb: 2 }}>
              Требования к качеству не заданы
            </Alert>
          )}

          {Object.entries(formData.quality_requirements).map(([key, value]) => (
            <Box
              key={key}
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                mb: 1,
                p: 1,
                border: '1px solid',
                borderColor: 'divider',
                borderRadius: 1,
              }}
            >
              <Typography variant="body2" sx={{ fontWeight: 'bold', minWidth: 120 }}>
                {key}:
              </Typography>
              <Typography variant="body2" sx={{ flexGrow: 1 }}>
                {value}
              </Typography>
              <Button
                size="small"
                color="error"
                onClick={() => removeQualityRequirement(key)}
                startIcon={<DeleteIcon />}
              >
                Удалить
              </Button>
            </Box>
          ))}

          <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end', mt: 2 }}>
            <TextField
              label="Параметр"
              value={newQualityKey}
              onChange={(e) => setNewQualityKey(e.target.value)}
              size="small"
              sx={{ flexGrow: 1 }}
            />
            <TextField
              label="Значение"
              value={newQualityValue}
              onChange={(e) => setNewQualityValue(e.target.value)}
              size="small"
              sx={{ flexGrow: 1 }}
            />
            <Button
              variant="outlined"
              onClick={addQualityRequirement}
              startIcon={<AddIcon />}
              disabled={!newQualityKey.trim() || !newQualityValue.trim()}
            >
              Добавить
            </Button>
          </Box>
        </Grid>

        <Grid size={12}>
          <Divider sx={{ my: 3 }} />
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            <Button
              variant="outlined"
              onClick={onCancel}
              size="large"
            >
              Отмена
            </Button>
            <Button
              variant="contained"
              onClick={handleSave}
              size="large"
              color="primary"
            >
              Сохранить
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
};

export default OperationDialog; 