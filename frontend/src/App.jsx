import { useState } from "react";
import Login from "./backend/Login";
import UploadResume from "./backend/uploadFile.jsx";
import UploadJobDescription from "./backend/uploadJD.jsx";
import Results  from "./backend/results.jsx";

function App() {
  const [loggedIn, setLoggedIn] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [jdUploaded, setJdUploaded] = useState(false);

  if (!loggedIn) {
    return <Login onLoginSuccess={() => setLoggedIn(true)} />;
  }

  if (!jobId) {
    return <UploadResume onUploadSuccess={(id) => setJobId(id)} />;
  }

  if (!jdUploaded) {
    return (
      <UploadJobDescription
        jobId={jobId}
        onJdUploaded={() => setJdUploaded(true)}
      />
    );
  }

  return <Results jobId={jobId} />;
}

export default App;