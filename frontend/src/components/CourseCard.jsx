import PropTypes from 'prop-types';

/**
 * Компонент карточки курса
 * @param {Object} props - Свойства компонента
 * @param {Object} props.course - Объект курса
 */
function CourseCard({ course }) {
  const {
    id,
    title,
    description,
    is_active,
    slug,
    created_at,
    technology = [],
  } = course;

  return (
    <article
      key={id}
      className="p-6 overflow-hidden transition border shadow-2xl group rounded-3xl border-slate-800 bg-slate-900/90 shadow-black/20 hover:-translate-y-1 hover:border-slate-700"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium uppercase tracking-[0.18em] text-cyan-300">
            Курс
          </p>
          <h2 className="mt-3 text-2xl font-semibold text-white">
            {title}
          </h2>
        </div>
        <div className="rounded-full bg-slate-800 px-3 py-1 text-xs uppercase tracking-[0.18em] text-slate-200 shadow-inner shadow-black/20">
          {is_active ? 'Активный' : 'Неактивный'}
        </div>
      </div>

      <p className="mt-5 text-sm leading-6 text-slate-300">
        {description || 'Описание курса отсутствует.'}
      </p>

      {technology.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-5">
          {technology.map((tech) => (
            <span
              key={tech.id}
              className="px-3 py-1 text-xs rounded-full bg-slate-800 text-slate-200"
            >
              {tech.name}
            </span>
          ))}
        </div>
      )}

      <div className="flex items-center justify-between gap-3 mt-6 text-sm text-slate-400">
        <span>slug: {slug}</span>
        <span>{new Date(created_at).toLocaleDateString('ru')}</span>
      </div>
    </article>
  );
}

CourseCard.propTypes = {
  course: PropTypes.shape({
    id: PropTypes.number.isRequired,
    title: PropTypes.string.isRequired,
    description: PropTypes.string,
    is_active: PropTypes.bool.isRequired,
    slug: PropTypes.string.isRequired,
    created_at: PropTypes.string.isRequired,
    technology: PropTypes.arrayOf(
      PropTypes.shape({
        id: PropTypes.number.isRequired,
        name: PropTypes.string.isRequired,
      })
    ),
  }).isRequired,
};

export default CourseCard;
