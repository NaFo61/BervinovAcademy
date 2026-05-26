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
const LearnPage = window.LearnPage;

const NO_FOOTER_ROUTES = new Set([Routes.PROBLEM, Routes.AUTH, Routes.LEARN]);

function App() {
  const [route, navigate, hashParams] = useHashRoute();

  const Page = {
    [Routes.LANDING]: LandingPage,
    [Routes.CATALOG]: CatalogPage,
    [Routes.COURSE]: CoursePage,
    [Routes.LEARN]: LearnPage,
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
      {!NO_FOOTER_ROUTES.has(route) && <Footer navigate={navigate}/>}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
