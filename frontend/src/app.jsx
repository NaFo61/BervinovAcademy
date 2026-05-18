// App shell — router

const useHashRoute = window.useHashRoute;
const Routes = window.Routes;
const TopNav = window.TopNav;
const Footer = window.Footer;
const LandingPage = window.LandingPage;
const CatalogPage = window.CatalogPage;
const ProblemPage = window.ProblemPage;
const ProfilePage = window.ProfilePage;
const AuthPage = window.AuthPage;
const CoursePage = window.CoursePage;

function App() {
  const [route, navigate, hashParams] = useHashRoute();
  const showChrome = route !== Routes.AUTH; // Auth page is full-bleed but keep nav for consistency

  const Page = {
    [Routes.LANDING]: LandingPage,
    [Routes.CATALOG]: CatalogPage,
    [Routes.COURSE]: CoursePage,
    [Routes.PROBLEM]: ProblemPage,
    [Routes.PROFILE]: ProfilePage,
    [Routes.AUTH]: AuthPage,
  }[route] || LandingPage;

  const pageProps = { navigate, hashParams, route };

  return (
    <div className="min-h-screen flex flex-col">
      <TopNav route={route} navigate={navigate}/>
      <main className="flex-1">
        <Page {...pageProps}/>
      </main>
      {route !== Routes.PROBLEM && route !== Routes.AUTH && <Footer navigate={navigate}/>}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
