// App shell — router

function App() {
  const [route, navigate] = useHashRoute();
  const showChrome = route !== Routes.AUTH; // Auth page is full-bleed but keep nav for consistency

  const Page = {
    [Routes.LANDING]: LandingPage,
    [Routes.CATALOG]: CatalogPage,
    [Routes.PROBLEM]: ProblemPage,
    [Routes.PROFILE]: ProfilePage,
    [Routes.AUTH]: AuthPage,
  }[route] || LandingPage;

  return (
    <div className="min-h-screen flex flex-col">
      <TopNav route={route} navigate={navigate}/>
      <main className="flex-1">
        <Page navigate={navigate}/>
      </main>
      {route !== Routes.PROBLEM && route !== Routes.AUTH && <Footer navigate={navigate}/>}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
