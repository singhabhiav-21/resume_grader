import { useState, useEffect, useRef } from "react";
import { API_URL } from "../config.js";

function Results({ jobId, onBack }) {
  const [feedback, setFeedback] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const hasFetched = useRef(false);

  useEffect(() => {
    async function fetchResults() {
      const token = localStorage.getItem("access_token");

      try {
        const response = await fetch(`${API_URL}/analyze/analyze/${jobId}`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!response.ok) {
          setError("Failed to get analysis");
          setLoading(false);
          return;
        }

        // loading stays true here — headers arriving isn't the same as
        // having actual content to show

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          let boundary;
          while ((boundary = buffer.indexOf("\n\n")) !== -1) {
            const message = buffer.slice(0, boundary);
            buffer = buffer.slice(boundary + 2);

            if (message.startsWith("event: error")) {
              setError("Analysis service is temporarily unavailable, please try again shortly");
              setLoading(false);
              return;
            }
            if (message.startsWith("data: ")) {
              const text = JSON.parse(message.slice(6));
              setLoading(false); // first real chunk arrived — swap to results view now
              setFeedback((prev) => prev + text);
            }
          }
        }
      } catch (err) {
        setError("Something went wrong");
        setLoading(false);
      }
    }

    if (hasFetched.current) return;
    hasFetched.current = true;
    fetchResults();
  }, [jobId]);

  if (loading) {
  return (
    <div className="card card-wide">
      <div className="loading-center">
        <div className="spinner-lg"></div>
        <p className="status">Analyzing resume against job description...</p>
      </div>
    </div>
  );
}

  return (
    <div className="card card-wide">
      <h1>Your results</h1>
      {error && <p className="status error">{error}</p>}
      {!error && <div className="results-content">{feedback}</div>}
      <button type="button" onClick={onBack}>Back to start</button>
    </div>
  );
}

export default Results;