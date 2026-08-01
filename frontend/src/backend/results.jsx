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
          return;
        }

        setLoading(false); // headers are in, text starts arriving next

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const text = decoder.decode(value, { stream: true });
          const lines = text.split("\n\n").filter(Boolean);

          for (const line of lines) {
            if (line.startsWith("event: error")) {
              setError("Analysis service is temporarily unavailable, please try again shortly");
              return;
            }
            if (line.startsWith("data: ")) {
              setFeedback((prev) => prev + line.slice(6));
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
        <p className="status">Analyzing resume against job description...</p>
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