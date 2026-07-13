import { useState } from "react";

function UploadResume({onUploadSuccess}) {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");

  function handleFileChange(e) {
  console.log("file selected:", e.target.files[0]);
  setFile(e.target.files[0]);
}

  async function handleUpload(e) {
    e.preventDefault();

    // TODO: get the token back out of localStorage
    const token = localStorage.getItem("access_token");

    // TODO: build a FormData object and append the file to it
    const formData = new FormData();
    formData.append("file", file );

    try {
      const response = await fetch("http://localhost:8080/analyze/upload_resume", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`
        },
        body: formData
      });

      if (!response.ok) {
        setStatus("Upload failed");
        return;
      }

      const data = await response.json();
      setStatus(`Uploaded: ${data.filename}, job_id: ${data.job_id}`);
      onUploadSuccess(data.job_id);
    } catch (err) {
      setStatus("Something went wrong");
    }
  }

  return (
  <div className="card">
    <h1>Upload your resume</h1>
    <p className="subtitle">PDF format only</p>
    <form onSubmit={handleUpload}>
      <input type="file" accept=".pdf" onChange={handleFileChange} />
      <button type="submit">Upload resume</button>
      {status && <p className="status">{status}</p>}
    </form>
  </div>
);
}

export default UploadResume;