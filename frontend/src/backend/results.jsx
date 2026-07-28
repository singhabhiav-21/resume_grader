import { useState, useEffect, useRef } from "react";
import {API_URL} from "/../config.js";

function Results({ jobId }) {
  const [feedback, setFeedback] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const hasFetched = useRef(false);

  useEffect(() => {
    async function fetchResults() {
      const token = localStorage.getItem("access_token");

      try {
        const response = await fetch(`${API_URL}/analyze/analyze/${jobId}`,
          {
            method: "POST",
            headers: {
              Authorization: `Bearer ${token}`
            }
          }
        );

        if (!response.ok) {
          setError("Failed to get analysis");
          setLoading(false);
          return;
        }

        const data = await response.json();
        setFeedback(data);
      } catch (err) {
        setError("Something went wrong");
      } finally {
        setLoading(false);
      }
    }

    if (hasFetched.current) return;
    hasFetched.current = true;
    fetchResults();
  }, [jobId]);

  if (loading) return <div className="card card-wide"><p className="status">Analyzing resume against job description...</p></div>;
  if (error) return <div className="card card-wide"><p className="status error">{error}</p></div>;

  return (
    <div className="card card-wide">
      <h1>Your results</h1>
      <div className="results-content">{feedback}</div>
    </div>
  );
}

export default Results;