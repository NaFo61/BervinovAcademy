import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const coursesApi = {
  /**
   * Получить список всех курсов
   * @returns {Promise<Array>} Список курсов
   */
  getAll: () => api.get('/content/courses/'),

  /**
   * Получить детализацию курса по slug
   * @param {string} slug - URL-идентификатор курса
   * @returns {Promise<Object>} Детальная информация о курсе
   */
  getById: (slug) => api.get(`/content/courses/${slug}/`),
};

export default api;
