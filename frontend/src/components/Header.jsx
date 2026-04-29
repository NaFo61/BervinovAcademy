import PropTypes from 'prop-types';

/**
 * Компонент заголовка страницы
 * @param {Object} props - Свойства компонента
 * @param {string} props.title - Заголовок
 * @param {string} props.subtitle - Подзаголовок
 */
function Header({ title = 'Bervinov Academy', subtitle }) {
  return (
    <header className="p-8 mb-10 border shadow-2xl rounded-3xl border-slate-800 bg-slate-900/95 shadow-black/20">
      <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
        {title}
      </h1>
      {subtitle && (
        <p className="max-w-2xl mt-3 text-slate-300 sm:text-lg">
          {subtitle}
        </p>
      )}
    </header>
  );
}

Header.propTypes = {
  title: PropTypes.string,
  subtitle: PropTypes.string,
};

export default Header;
