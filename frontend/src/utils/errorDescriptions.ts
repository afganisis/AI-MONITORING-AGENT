/**
 * Error descriptions and categories for ELD compliance errors.
 * Synced with backend error_classifier.py (2026-02-06).
 * Provides human-readable descriptions in Russian.
 */

export type FixStrategy = 'obsolete' | 'info_only' | 'ai_repair' | 'custom';

export interface ErrorDescription {
  name: string;
  description: string;
  category: string;
  howToFix: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  fixStrategy: FixStrategy;
}

/**
 * Error categories - synced with backend ErrorCategory enum
 */
export const ERROR_CATEGORIES = {
  data_integrity: {
    name: 'Целостность данных',
    icon: 'Database',
    color: 'blue',
    description: 'Ошибки одометра, моточасов и данных',
  },
  location_movement: {
    name: 'Местоположение',
    icon: 'MapPin',
    color: 'green',
    description: 'Ошибки GPS, происхождения и движения',
  },
  status_event: {
    name: 'Статусы и события',
    icon: 'Activity',
    color: 'orange',
    description: 'Дублирование статусов, промежуточные события',
  },
  diagnostic: {
    name: 'Диагностика',
    icon: 'AlertTriangle',
    color: 'yellow',
    description: 'Power up/shutdown, диагностика ELD',
  },
  speed: {
    name: 'Скорость',
    icon: 'Gauge',
    color: 'red',
    description: 'Превышение скоростных лимитов',
  },
  authentication: {
    name: 'Аутентификация',
    icon: 'Shield',
    color: 'purple',
    description: 'Чрезмерные логины/логауты, загрузка событий',
  },
  uncategorized: {
    name: 'Прочее',
    icon: 'HelpCircle',
    color: 'gray',
    description: 'Другие ошибки',
  },
} as const;

/**
 * Fix strategy labels
 */
export const FIX_STRATEGY_LABELS: Record<FixStrategy, { label: string; color: string; description: string }> = {
  ai_repair: {
    label: 'AI REPAIR',
    color: 'cyan',
    description: 'Исправляется автоматически через Fortex TOOL KIT',
  },
  custom: {
    label: 'PTHORA AI',
    color: 'purple',
    description: 'Требует логики PTHORA AI',
  },
  info_only: {
    label: 'Только инфо',
    color: 'gray',
    description: 'Показывается как ошибка, но не исправляется',
  },
  obsolete: {
    label: 'Устарело',
    color: 'dark',
    description: 'Тип ошибки больше не существует в Fortex',
  },
};

/**
 * Detailed error descriptions by error_key
 * Synced with backend ERROR_FILTERS from error_classifier.py
 */
export const ERROR_DESCRIPTIONS: Record<string, ErrorDescription> = {
  // ========================================================================
  // INFO_ONLY - Show but don't fix
  // ========================================================================
  sequentialIdBreak: {
    name: 'Нарушение последовательности ID',
    description: 'Обнаружен разрыв в последовательности идентификаторов записей логов. Может указывать на потерю данных или проблемы с синхронизацией.',
    category: 'data_integrity',
    howToFix: 'Не исправляется автоматически. Проверить целостность данных в ELD.',
    severity: 'critical',
    fixStrategy: 'info_only',
  },
  engineHoursAfterShutdown: {
    name: 'Моточасы после выключения',
    description: 'Двигатель продолжал работать после официального выключения в логах. Серьезное нарушение учета времени.',
    category: 'data_integrity',
    howToFix: 'Не исправляется автоматически. Проверить корректность записей.',
    severity: 'high',
    fixStrategy: 'info_only',
  },
  eventIsNotDownloaded: {
    name: 'Событие не загружено',
    description: 'Событие не было загружено с ELD устройства. Данные могут быть неполными.',
    category: 'authentication',
    howToFix: 'Не исправляется автоматически. Повторить синхронизацию с ELD.',
    severity: 'low',
    fixStrategy: 'info_only',
  },

  // ========================================================================
  // AI_REPAIR - Fixable via Fortex AI REPAIR TOOL KIT
  // ========================================================================
  noPowerUpError: {
    name: 'Нет Power Up',
    description: 'Отсутствует событие включения двигателя (Power Up). Нарушает целостность логов.',
    category: 'diagnostic',
    howToFix: 'AI REPAIR: FIX NO POWER UP + FIX MISSING POWER UP / SHUT DOWN + FIX NO SHUT DOWN',
    severity: 'low',
    fixStrategy: 'ai_repair',
  },
  twoIdenticalStatusesError: {
    name: 'Два одинаковых статуса',
    description: 'Обнаружены два последовательных идентичных статуса. Дублирование должно быть устранено.',
    category: 'status_event',
    howToFix: 'AI REPAIR: CLEAR TWIN EVENTS',
    severity: 'medium',
    fixStrategy: 'ai_repair',
  },
  drivingOriginWarning: {
    name: 'Предупреждение о происхождении',
    description: 'Происхождение события вождения некорректно. Может указывать на неверный источник данных.',
    category: 'location_movement',
    howToFix: 'AI REPAIR: FIX EVENT ORIGIN',
    severity: 'medium',
    fixStrategy: 'ai_repair',
  },
  missingIntermediateError: {
    name: 'Нет промежуточного события',
    description: 'Отсутствует промежуточное событие между основными записями лога.',
    category: 'status_event',
    howToFix: 'AI REPAIR: FIX INTERMEDIATE + FIX INTERMEDIATE TIME OFFSET + FIX INTERMEDIATE AFTER MAIN',
    severity: 'medium',
    fixStrategy: 'ai_repair',
  },
  noShutdownError: {
    name: 'Нет Shut Down',
    description: 'Отсутствует событие выключения двигателя (Shut Down). Нарушает целостность логов.',
    category: 'diagnostic',
    howToFix: 'AI REPAIR: FIX NO SHUT DOWN + FIX MISSING POWER UP / SHUT DOWN + FIX NO POWER UP',
    severity: 'low',
    fixStrategy: 'ai_repair',
  },

  // ========================================================================
  // CUSTOM - Requires PTHORA AI logic (future)
  // ========================================================================
  odometerError: {
    name: 'Ошибка одометра',
    description: 'Показания одометра не соответствуют ожидаемым значениям. Возможно расхождение между ELD и одометром ТС.',
    category: 'data_integrity',
    howToFix: 'Сверить показания ELD с физическим одометром. При расхождении - откалибровать ELD.',
    severity: 'high',
    fixStrategy: 'custom',
  },
  locationChangedError: {
    name: 'Ошибка изменения локации',
    description: 'Местоположение изменилось некорректно. Возможен скачок GPS координат.',
    category: 'location_movement',
    howToFix: 'Проверить GPS данные. Исправить координаты вручную.',
    severity: 'high',
    fixStrategy: 'custom',
  },
  incorrectIntermediatePlacementError: {
    name: 'Неправильное размещение промежуточного',
    description: 'Промежуточное событие расположено в неправильном месте в последовательности логов.',
    category: 'status_event',
    howToFix: 'Переместить промежуточное событие в правильную позицию.',
    severity: 'medium',
    fixStrategy: 'custom',
  },
  engineHoursWarning: {
    name: 'Предупреждение о моточасах',
    description: 'Расхождение между моточасами двигателя и записями в логах. Требует проверки.',
    category: 'data_integrity',
    howToFix: 'Сверить данные ELD с бортовым компьютером. Проверить корректность подключения.',
    severity: 'medium',
    fixStrategy: 'custom',
  },
  excessiveLogInWarning: {
    name: 'Частые входы в систему',
    description: 'Водитель слишком часто входит в систему ELD. Может указывать на проблемы с устройством.',
    category: 'authentication',
    howToFix: 'Проверить ELD устройство. Провести беседу с водителем.',
    severity: 'low',
    fixStrategy: 'custom',
  },
  excessiveLogOutWarning: {
    name: 'Частые выходы из системы',
    description: 'Водитель слишком часто выходит из системы ELD. Может указывать на попытку обхода правил HOS.',
    category: 'authentication',
    howToFix: 'Провести беседу с водителем. Проверить ELD устройство.',
    severity: 'low',
    fixStrategy: 'custom',
  },
  noDataInOdometerOrEngineHours: {
    name: 'Нет данных одометра/моточасов',
    description: 'Отсутствуют данные одометра или моточасов двигателя. Критическая проблема целостности данных.',
    category: 'data_integrity',
    howToFix: 'Проверить подключение ELD к OBD-II. Перезагрузить устройство.',
    severity: 'critical',
    fixStrategy: 'custom',
  },
  locationError: {
    name: 'Ошибка местоположения',
    description: 'GPS координаты содержат ошибку. Местоположение записано некорректно.',
    category: 'location_movement',
    howToFix: 'Проверить GPS антенну. Исправить координаты вручную.',
    severity: 'high',
    fixStrategy: 'custom',
  },
  locationDidNotChangeWarning: {
    name: 'Местоположение не изменилось',
    description: 'GPS координаты не изменились при ожидаемом движении. Возможна проблема с GPS.',
    category: 'location_movement',
    howToFix: 'Проверить GPS модуль. Убедиться в корректности данных.',
    severity: 'medium',
    fixStrategy: 'custom',
  },
  incorrectStatusPlacementError: {
    name: 'Неправильное размещение статуса',
    description: 'Статус водителя расположен в неправильном месте в хронологии событий.',
    category: 'status_event',
    howToFix: 'Переместить статус в правильную позицию в логах.',
    severity: 'high',
    fixStrategy: 'custom',
  },
  speedMuchHigherThanLimit: {
    name: 'Значительное превышение скорости',
    description: 'Скорость значительно превысила допустимый лимит. Серьезное нарушение безопасности.',
    category: 'speed',
    howToFix: 'Уведомить водителя. При повторении - дисциплинарные меры.',
    severity: 'high',
    fixStrategy: 'custom',
  },
  speedHigherThanLimit: {
    name: 'Превышение скорости',
    description: 'Зафиксировано превышение допустимой скорости. Влияет на безопасность.',
    category: 'speed',
    howToFix: 'Уведомить водителя о нарушении.',
    severity: 'medium',
    fixStrategy: 'custom',
  },

  // ========================================================================
  // OBSOLETE - No longer exist in Fortex (hidden from detection)
  // ========================================================================
  diagnosticEvent: {
    name: 'Диагностическое событие',
    description: 'Устаревший тип ошибки. Больше не существует в Fortex.',
    category: 'diagnostic',
    howToFix: 'Не требуется.',
    severity: 'low',
    fixStrategy: 'obsolete',
  },
  eventHasManualLocation: {
    name: 'Ручное местоположение',
    description: 'Устаревший тип ошибки. Больше не существует в Fortex.',
    category: 'authentication',
    howToFix: 'Не требуется.',
    severity: 'low',
    fixStrategy: 'obsolete',
  },
  unidentifiedDriverEvent: {
    name: 'Неидентифицированный водитель',
    description: 'Устаревший тип ошибки. Больше не существует в Fortex.',
    category: 'authentication',
    howToFix: 'Не требуется.',
    severity: 'medium',
    fixStrategy: 'obsolete',
  },
};

/**
 * Get error description by error_key
 */
export function getErrorDescription(errorKey: string): ErrorDescription {
  // Try exact match
  if (ERROR_DESCRIPTIONS[errorKey]) {
    return ERROR_DESCRIPTIONS[errorKey];
  }

  // Try normalized match (handle snake_case / camelCase variants)
  const normalized = errorKey.toLowerCase().replace(/[_-]/g, '');
  const found = Object.entries(ERROR_DESCRIPTIONS).find(
    ([key]) => key.toLowerCase().replace(/[_-]/g, '') === normalized
  );

  if (found) {
    return found[1];
  }

  // Return default
  return {
    name: errorKey.replace(/_/g, ' ').replace(/([A-Z])/g, ' $1').trim(),
    description: 'Описание для этого типа ошибки отсутствует.',
    category: 'uncategorized',
    howToFix: 'Обратитесь к администратору для получения инструкций.',
    severity: 'medium',
    fixStrategy: 'custom',
  };
}

/**
 * Get category info
 */
export function getCategoryInfo(category: string) {
  return ERROR_CATEGORIES[category as keyof typeof ERROR_CATEGORIES] || ERROR_CATEGORIES.uncategorized;
}

/**
 * Check if error is fixable (AI_REPAIR or CUSTOM)
 */
export function isFixable(errorKey: string): boolean {
  const desc = getErrorDescription(errorKey);
  return desc.fixStrategy === 'ai_repair' || desc.fixStrategy === 'custom';
}

/**
 * Get fix strategy info for an error
 */
export function getFixStrategyInfo(errorKey: string) {
  const desc = getErrorDescription(errorKey);
  return FIX_STRATEGY_LABELS[desc.fixStrategy];
}

/**
 * Format date/time for display
 */
export function formatErrorDateTime(isoString: string): { date: string; time: string; relative: string } {
  const date = new Date(isoString);

  const dateStr = date.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });

  const timeStr = date.toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });

  // Calculate relative time
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  let relative: string;
  if (diffMins < 1) {
    relative = 'только что';
  } else if (diffMins < 60) {
    relative = `${diffMins} мин. назад`;
  } else if (diffHours < 24) {
    relative = `${diffHours} ч. назад`;
  } else if (diffDays < 7) {
    relative = `${diffDays} дн. назад`;
  } else {
    relative = dateStr;
  }

  return { date: dateStr, time: timeStr, relative };
}

/**
 * Severity labels in Russian
 */
export const SEVERITY_LABELS = {
  critical: 'Критично',
  high: 'Высокий',
  medium: 'Средний',
  low: 'Низкий',
} as const;

/**
 * Status labels in Russian
 */
export const STATUS_LABELS = {
  pending: 'Ожидает',
  fixing: 'Исправляется',
  fixed: 'Исправлено',
  failed: 'Ошибка',
  ignored: 'Игнорируется',
} as const;

/**
 * Get severity label
 */
export function getSeverityLabel(severity: string): string {
  return SEVERITY_LABELS[severity as keyof typeof SEVERITY_LABELS] || severity;
}

/**
 * Get status label
 */
export function getStatusLabel(status: string): string {
  return STATUS_LABELS[status as keyof typeof STATUS_LABELS] || status;
}
