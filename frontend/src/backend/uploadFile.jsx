import { useState, useRef, useEffect } from "react";
import { API_URL } from "../config.js";

const COOLDOWN_MS = 3500;

function UploadResume({ onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [cooldown, setCooldown] = useState(false);
  const cooldownTimer = useRef(null);

  useEffect(() => () => clearTimeout(cooldownTimer.current), []);

  function handleFileChange(e) {
    setFile(e.target.files[0]);
  }

  async function handleUpload(e) {
    e.preventDefault();
    if (cooldown || submitting || !file) return;

    setCooldown(true);
    cooldownTimer.current = setTimeout(() => setCooldown(false), COOLDOWN_MS);

    const token = localStorage.getItem("access_token");
    const formData = new FormData();
    formData.append("file", file);

    setSubmitting(true);
    try {
      const response = await fetch(`${API_URL}/analyze/upload_resume`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      if (!response.ok) {
        setStatus("Upload failed");
        return;
      }

      const data = await response.json();
      setStatus(`Uploaded: ${data.filename}`);
      onUploadSuccess(data.job_id);
    } catch (err) {
      setStatus("Something went wrong");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="card">
      <h1>Upload your resume</h1>
      <p className="subtitle">PDF format only</p>
      <form onSubmit={handleUpload}>
        <input type="file" accept=".pdf" onChange={handleFileChange} />
        <button type="submit" disabled={submitting || cooldown || !file}>
          {submitting ? "Uploading..." : cooldown ? "Please wait..." : "Upload resume"}
        </button>
        {status && <p className="status">{status}</p>}
      </form>
    </div>
  );
}

export default UploadResume;