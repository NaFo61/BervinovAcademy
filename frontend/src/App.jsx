import { Header, CourseCard } from './components';
import { useCourses } from './hooks';

function App() {
  const { courses, loading, error } = useCourses();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="max-w-6xl px-4 py-10 mx-auto sm:px-6 lg:px-8">
        <Header
          title="Bervinov Academy"
          subtitle="Список активных курсов из backend. Пиши на Tailwind, работай с API и расширяй интерфейс без лишнего шума."
        />

        <section className="space-y-4">
          {loading ? (
            <div className="p-8 text-center border shadow-xl rounded-3xl border-slate-800 bg-slate-900/90 text-slate-200 shadow-black/20">
              Загружаем курсы...
            </div>
          ) : error ? (
            <div className="p-6 text-center border rounded-3xl border-rose-500/40 bg-rose-500/10 text-rose-200">
              <h2 className="text-xl font-semibold">Ошибка запроса</h2>
              <p className="mt-2 text-sm leading-6">{error}</p>
            </div>
          ) : courses.length === 0 ? (
            <div className="p-8 text-center border shadow-xl rounded-3xl border-slate-800 bg-slate-900/90 text-slate-200 shadow-black/20">
              Пока нет активных курсов, но backend уже отвечает.
            </div>
          ) : (
            <div className="grid gap-6 sm:grid-cols-2">
              {courses.map((course) => (
                <CourseCard key={course.id} course={course} />
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

export default App;
