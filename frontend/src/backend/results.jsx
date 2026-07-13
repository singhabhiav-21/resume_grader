import { useState, useEffect } from "react";

function Results({ jobId }) {
  const [feedback, setFeedback] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchResults() {
      const token = localStorage.getItem("access_token");

      try {
        const response = await fetch(
          `http://localhost:8080/analyze/analyze/${jobId}`,
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

    fetchResults();
  }, [jobId]);

  if (loading) return <p>Analyzing resume against job description...</p>;
  if (error) return <p>{error}</p>;

  return (
    <div style={{ whiteSpace: "pre-wrap" }}>
      {feedback}
    </div>
  );
}

export default Results;