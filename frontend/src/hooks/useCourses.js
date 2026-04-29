import { useEffect, useState } from 'react';
import { coursesApi } from '../api/courses';

/**
 * Кастомный хук для управления курсами
 * @returns {Object} Состояние и методы для работы с курсами
 */
function useCourses() {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchCourses = async () => {
    try {
      setLoading(true);
      const response = await coursesApi.getAll();
      setCourses(response.data);
      setError(null);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          'Не удалось загрузить курсы. Проверьте, что backend доступен.'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCourses();
  }, []);

  return { courses, loading, error, refetch: fetchCourses };
}

export default useCourses;
