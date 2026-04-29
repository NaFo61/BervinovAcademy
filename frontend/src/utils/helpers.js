import { APP_CONFIG } from './constants';

/**
 * Форматирует дату в строку
 * @param {string|Date} dateString - Дата для форматирования
 * @param {Object} options - Опции форматирования
 * @returns {string} Отформатированная дата
 */
export function formatDate(dateString, options = APP_CONFIG.DATE_FORMAT) {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString(APP_CONFIG.DEFAULT_LANGUAGE, options);
  } catch {
    return dateString;
  }
}

/**
 * Обрезает строку до указанной длины
 * @param {string} str - Строка
 * @param {number} maxLength - Максимальная длина
 * @returns {string} Обрезанная строка
 */
export function truncateString(str, maxLength = 100) {
  if (!str || str.length <= maxLength) return str;
  return str.slice(0, maxLength) + '...';
}

/**
 * Генерирует slug из строки
 * @param {string} text - Текст для преобразования
 * @returns {string} Slug
 */
export function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

/**
 * Проверяет, является ли значение пустым
 * @param {*} value - Значение для проверки
 * @returns {boolean} true если значение пустое
 */
export function isEmpty(value) {
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === 'object') return Object.keys(value).length === 0;
  return !value;
}
