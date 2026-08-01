import { useState } from "react";
import Login from "./backend/Login";
import Register from "./backend/Register";
import Start from "./backend/Start";
import UploadResume from "./backend/uploadFile.jsx";
import UploadJobDescription from "./backend/uploadJD.jsx";
import Results from "./backend/results.jsx";

const FLOW_STEPS = ["upload", "jd", "results"];

function Steps({ current }) {
  const currentIndex = FLOW_STEPS.indexOf(current);
  if (currentIndex === -1) return null; // don't show on login/register/start

  return (
    <div className="steps">
      {FLOW_STEPS.map((step, i) => (
        <div
          key={step}
          className={
            "step-dot" +
            (i === currentIndex ? " active" : i < currentIndex ? " done" : "")
          }
        />
      ))}
    </div>
  );
}
function App() {
  const [view, setView] = useState("login");
  const [jobId, setJobId] = useState(null);

  function goToStart() {
    setJobId(null);
    setView("start");
  }

  function renderScreen() {
    switch (view) {
      case "login":
        return <Login onLoginSuccess={goToStart} onGoRegister={() => setView("register")} />;
      case "register":
        return <Register onRegisterSuccess={() => setView("login")} onGoLogin={() => setView("login")} />;
      case "start":
        return <Start onAnalyze={() => setView("upload")} />;
      case "upload":
        return <UploadResume onUploadSuccess={(id) => { setJobId(id); setView("jd"); }} />;
      case "jd":
        return <UploadJobDescription jobId={jobId} onJdUploaded={() => setView("results")} />;
      case "results":
        return <Results jobId={jobId} onBack={goToStart} />;
      default:
        return null;
    }
  }

  return (
    <div className="app-shell">
      {renderScreen()}
      <Steps current={view} />
    </div>
  );
}

export default App;