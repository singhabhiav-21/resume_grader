import { useState } from "react";

function UploadJobDescription({ jobId, onJdUploaded }) {
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();

    const token = localStorage.getItem("access_token");

    try {
      const response = await fetch("http://localhost:8080/analyze/upload/job_description", {
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
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <textarea
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="Paste job description here"
        rows={10}
      />
      <button type="submit">Upload job description</button>
      {status && <p>{status}</p>}
    </form>
  );
}

export default UploadJobDescription;