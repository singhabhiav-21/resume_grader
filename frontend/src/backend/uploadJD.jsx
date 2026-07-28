import { useState } from "react";
import {API_URL} from "/../config.js";

function UploadJobDescription({ jobId, onJdUploaded }) {
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();

    const token = localStorage.getItem("access_token");
    setSubmitting(true)
    try {
      const response = await fetch(`${API_URL}/analyze/upload/job_description`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          // TODO: this endpoint's Pydantic model (UserUploadJobDesc) expects
          // JSON, not form-urlencoded like login was — what Content-Type
          // matches a JSON body?
          "Content-Type": "application/json"
        },
        // TODO: fetch's body must be a STRING, not a raw JS object —
        // JSON.stringify() converts your object into that string.
        // Your backend expects two fields: description, job_id
        body: JSON.stringify({
          description: description,
          job_id: jobId
        })
      });

      if (!response.ok) {
        setStatus("Failed to upload job description");
        return;
      }

      // TODO: on success, call onJdUploaded() so the parent (App)
      // knows to move to the next screen
        onJdUploaded();
    } catch (err) {
      setStatus("Something went wrong");
    } finally {
      setSubmitting(false)
    }
  }

  return (
  <div className="card card-wide">
    <h1>Job description</h1>
    <p className="subtitle">Paste the full job posting</p>
    <form onSubmit={handleSubmit}>
      <textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Paste job description here" />
      <button type="submit">Analyze</button>
      {status && <p className="status">{status}</p>}
    </form>
  </div>
);
}

export default UploadJobDescription;