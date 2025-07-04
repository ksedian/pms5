import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import {
  Box,
  Typography,
  Chip,
  useTheme,
  Paper,
  Tooltip,
  alpha
} from '@mui/material';
import {
  Settings as SettingsIcon,
  AccessTime as TimeIcon,
  Build as ToolIcon,
  CheckCircle as QualityIcon
} from '@mui/icons-material';

import { Operation } from '../../types/routes';

export interface OperationNodeData {
  label: string;
  operation?: Operation;
  properties?: Record<string, any>;
}

interface OperationNodeProps {
  data: OperationNodeData;
  selected?: boolean;
}

const OperationNode: React.FC<OperationNodeProps> = memo(({ data, selected }) => {
  const theme = useTheme();
  const { operation, label } = data;

  // Цветовая схема в зависимости от типа операции
  const getOperationColor = (type?: string) => {
    switch (type) {
      case 'machining':
        return theme.palette.primary.main;
      case 'assembly':
        return theme.palette.secondary.main;
      case 'inspection':
        return theme.palette.warning.main;
      case 'transport':
        return theme.palette.info.main;
      default:
        return theme.palette.grey[600];
    }
  };

  const operationColor = getOperationColor(operation?.operation_type);

  // Стили узла
  const nodeStyles = {
    minWidth: 200,
    maxWidth: 300,
    backgroundColor: theme.palette.background.paper,
    border: `2px solid ${selected ? theme.palette.primary.main : operationColor}`,
    borderRadius: theme.spacing(1),
    boxShadow: selected 
      ? `0 0 0 3px ${alpha(theme.palette.primary.main, 0.2)}`
      : theme.shadows[2],
    transition: 'all 0.2s ease-in-out',
    cursor: 'pointer',
    '&:hover': {
      boxShadow: theme.shadows[4],
      transform: 'translateY(-1px)',
    }
  };

  const headerStyles = {
    backgroundColor: alpha(operationColor, 0.1),
    borderBottom: `1px solid ${alpha(operationColor, 0.2)}`,
    padding: theme.spacing(1),
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between'
  };

  const contentStyles = {
    padding: theme.spacing(1.5),
    display: 'flex',
    flexDirection: 'column',
    gap: theme.spacing(1)
  };

  const formatTime = (minutes: number) => {
    if (minutes < 60) {
      return `${minutes}мин`;
    }
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return remainingMinutes > 0 ? `${hours}ч ${remainingMinutes}мин` : `${hours}ч`;
  };

  return (
    <Paper sx={nodeStyles} elevation={selected ? 8 : 2}>
      {/* Входящие соединения (сверху) */}
      <Handle
        type="target"
        position={Position.Top}
        style={{
          background: operationColor,
          width: 12,
          height: 12,
          border: `2px solid ${theme.palette.background.paper}`,
        }}
      />

      {/* Заголовок узла */}
      <Box sx={headerStyles}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: operationColor,
            }}
          />
          <Typography
            variant="subtitle2"
            fontWeight="bold"
            color="text.primary"
            noWrap
            sx={{ maxWidth: 150 }}
          >
            {operation?.operation_code || 'OP-XXX'}
          </Typography>
        </Box>
        
        {operation && (
          <Tooltip title="Настройки операции">
            <SettingsIcon 
              fontSize="small" 
              sx={{ 
                color: theme.palette.text.secondary,
                opacity: 0.7 
              }} 
            />
          </Tooltip>
        )}
      </Box>

      {/* Содержимое узла */}
      <Box sx={contentStyles}>
        {/* Название операции */}
        <Typography
          variant="body2"
          color="text.primary"
          fontWeight="medium"
          sx={{
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
          }}
        >
          {label}
        </Typography>

        {/* Информация об операции */}
        {operation && (
          <>
            {/* Тип операции */}
            <Chip
              label={operation.operation_type}
              size="small"
              variant="outlined"
              sx={{
                borderColor: operationColor,
                color: operationColor,
                fontSize: '0.75rem',
                height: 20,
                alignSelf: 'flex-start'
              }}
            />

            {/* Временные характеристики */}
            {(operation.setup_time > 0 || operation.operation_time > 0) && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <TimeIcon fontSize="small" color="action" />
                <Typography variant="caption" color="text.secondary">
                  {operation.setup_time > 0 && `Настройка: ${formatTime(operation.setup_time)}`}
                  {operation.setup_time > 0 && operation.operation_time > 0 && ' | '}
                  {operation.operation_time > 0 && `Выполнение: ${formatTime(operation.operation_time)}`}
                </Typography>
              </Box>
            )}

            {/* Общее время */}
            {operation.total_time > 0 && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Typography
                  variant="caption"
                  color="primary"
                  fontWeight="bold"
                >
                  Общее время: {formatTime(operation.total_time)}
                </Typography>
              </Box>
            )}

            {/* Требования к оборудованию */}
            {operation.required_equipment.length > 0 && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <ToolIcon fontSize="small" color="action" />
                <Typography variant="caption" color="text.secondary" noWrap>
                  {operation.required_equipment.slice(0, 2).join(', ')}
                  {operation.required_equipment.length > 2 && '...'}
                </Typography>
              </Box>
            )}

            {/* Требования к качеству */}
            {Object.keys(operation.quality_requirements).length > 0 && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <QualityIcon fontSize="small" color="success" />
                <Typography variant="caption" color="text.secondary">
                  Контроль качества
                </Typography>
              </Box>
            )}
          </>
        )}

        {/* Если операция не задана */}
        {!operation && (
          <Typography variant="caption" color="text.secondary" fontStyle="italic">
            Нажмите дважды для настройки
          </Typography>
        )}
      </Box>

      {/* Исходящие соединения (снизу) */}
      <Handle
        type="source"
        position={Position.Bottom}
        style={{
          background: operationColor,
          width: 12,
          height: 12,
          border: `2px solid ${theme.palette.background.paper}`,
        }}
      />

      {/* Боковые соединения для параллельных операций */}
      <Handle
        type="source"
        position={Position.Right}
        id="parallel-right"
        style={{
          background: theme.palette.secondary.main,
          width: 10,
          height: 10,
          border: `2px solid ${theme.palette.background.paper}`,
          right: -5,
        }}
      />
      
      <Handle
        type="target"
        position={Position.Left}
        id="parallel-left"
        style={{
          background: theme.palette.secondary.main,
          width: 10,
          height: 10,
          border: `2px solid ${theme.palette.background.paper}`,
          left: -5,
        }}
      />
    </Paper>
  );
});

OperationNode.displayName = 'OperationNode';

export default OperationNode; 