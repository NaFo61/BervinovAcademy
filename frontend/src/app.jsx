// App shell — router

const useHashRoute = window.useHashRoute;
const Routes = window.Routes;
const TopNav = window.TopNav;
const Footer = window.Footer;
const LandingPage = window.LandingPage;
const CatalogPage = window.CatalogPage;
const ProblemPage = window.ProblemPage;
const ProfilePage = window.ProfilePage;
const ProfileEditPage = window.ProfileEditPage;
const AuthPage = window.AuthPage;
const CoursePage = window.CoursePage;
const LearnPage = window.LearnPage;
const MentorPage = window.MentorPage;
const ExamPage = window.ExamPage;
const CallPage = window.CallPage;
const ConferencesPage = window.ConferencesPage;

const NO_FOOTER_ROUTES = new Set([Routes.PROBLEM, Routes.AUTH, Routes.LEARN, Routes.EXAM, Routes.CALL]);

function App() {
  const [route, navigate, hashParams] = useHashRoute();

  const Page = {
    [Routes.LANDING]: LandingPage,
    [Routes.CATALOG]: CatalogPage,
    [Routes.COURSE]: CoursePage,
    [Routes.LEARN]: LearnPage,
    [Routes.EXAM]: ExamPage,
    [Routes.PROBLEM]: ProblemPage,
    [Routes.PROFILE]: ProfilePage,
    [Routes.PROFILE_EDIT]: ProfileEditPage,
    [Routes.MENTOR]: MentorPage,
    [Routes.AUTH]: AuthPage,
    [Routes.CALL]: CallPage,
    [Routes.CONFERENCES]: ConferencesPage,
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
