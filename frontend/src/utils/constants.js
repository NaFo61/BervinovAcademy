/**
 * Константы приложения
 */

// API эндпоинты
export const API_ENDPOINTS = {
  COURSES: '/content/courses/',
  MODULES: '/content/modules/',
  LESSONS_THEORY: '/content/lessons-theory/',
  CHALLENGES: '/content/challenges/',
};

// Настройки приложения
export const APP_CONFIG = {
  DEFAULT_LANGUAGE: 'ru',
  DATE_FORMAT: {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  },
};

// Статусы
export const STATUS = {
  LOADING: 'loading',
  SUCCESS: 'success',
  ERROR: 'error',
  EMPTY: 'empty',
};
