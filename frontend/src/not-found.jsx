function NotFoundPage({ navigate }) {
  const IllustrationBlock = window.IllustrationBlock;
  const img = window.appAssetUrl
    ? window.appAssetUrl('/img/page-404.jpg')
    : '/img/page-404.jpg';
  const btn = 'h-11 px-6 rounded-xl font-semibold';
  return (
    <div className="min-h-[70vh] flex items-center justify-center px-4">
      {IllustrationBlock ? (
        <IllustrationBlock
          src={img}
          alt="Страница не найдена"
          title="Такой страницы нет"
          text="Проверьте адрес или откройте каталог курсов."
          actions={
            <>
              <button
                type="button"
                onClick={() => navigate(window.Routes.CATALOG)}
                className={`btn-grad btn-shimmer text-white ${btn}`}
              >
                Каталог курсов
              </button>
              <button
                type="button"
                onClick={() => navigate(window.Routes.LANDING)}
                className={`${btn} bg-white ring-1 ring-black/[0.08] text-ink`}
              >
                На главную
              </button>
            </>
          }
        />
      ) : (
        <div className="text-center">
          <div className="text-xl font-extrabold">Такой страницы нет</div>
          <button
            type="button"
            onClick={() => navigate(window.Routes.CATALOG)}
            className="mt-4 btn-grad h-11 px-6 rounded-xl text-white font-semibold"
          >
            Каталог курсов
          </button>
        </div>
      )}
    </div>
  );
}

window.NotFoundPage = NotFoundPage;
