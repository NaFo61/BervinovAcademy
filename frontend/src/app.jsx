// App shell — router

const useHashRoute = window.useHashRoute;
const Routes = window.Routes;
const TopNav = window.TopNav;
const RecoveryBanner = window.RecoveryBanner;
const Footer = window.Footer;
const LandingPage = window.LandingPage;
const CatalogPage = window.CatalogPage;
const ProblemPage = window.ProblemPage;
const ProfilePage = window.ProfilePage;
const ProfileEditPage = window.ProfileEditPage;
const AuthPage = window.AuthPage;
const AuthCallbackPage = window.AuthCallbackPage;
const CoursePage = window.CoursePage;
const LearnPage = window.LearnPage;
const MentorPage = window.MentorPage;
const ExamPage = window.ExamPage;
const CallPage = window.CallPage;
const ConferencesPage = window.ConferencesPage;
const MessagesPage = window.MessagesPage;
const ProPage = window.ProPage;
const PlaygroundPage = window.PlaygroundPage;
const WhiteboardPage = window.WhiteboardPage;

const NO_FOOTER_ROUTES = new Set([
  Routes.PROBLEM, Routes.AUTH, Routes.AUTH_CALLBACK, Routes.LEARN, Routes.EXAM, Routes.CALL, Routes.PLAYGROUND, Routes.WHITEBOARD,
]);

function App() {
  const [route, navigate, hashParams] = useHashRoute();
  const isCallRoute = route === Routes.CALL;
  const isWhiteboardRoute = route === Routes.WHITEBOARD;

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
    [Routes.AUTH_CALLBACK]: AuthCallbackPage,
    [Routes.CALL]: CallPage,
    [Routes.CONFERENCES]: ConferencesPage,
    [Routes.MESSAGES]: MessagesPage,
    [Routes.PRO]: ProPage,
    [Routes.PLAYGROUND]: PlaygroundPage,
    [Routes.WHITEBOARD]: WhiteboardPage,
  }[route] || LandingPage;

  const pageProps = { navigate, hashParams, route };
  const hideChrome = isCallRoute || isWhiteboardRoute;

  return (
    <div className={`${hideChrome ? 'h-screen overflow-hidden' : 'min-h-screen'} flex flex-col`}>
      <TopNav route={route} navigate={navigate}/>
      {!hideChrome && <RecoveryBanner navigate={navigate}/>}
      <main className={`flex-1 min-h-0 ${hideChrome ? 'overflow-hidden' : ''}`}>
        <Page {...pageProps}/>
      </main>
      {!NO_FOOTER_ROUTES.has(route) && <Footer navigate={navigate}/>}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
