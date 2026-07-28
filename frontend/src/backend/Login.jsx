import { useState } from "react";
import {API_URL} from "/../config.js";

function Login({onLoginSuccess}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);


async function handleSubmit(e) {
  e.preventDefault();


  const body = new URLSearchParams();
  body.append("username", email);
  body.append("password", password);
  setSubmitting(true);
  try {
    const response = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded"
      },
      body: body
    });

    if (!response.ok) {
      setError("Invalid credentials");
      return;
    }

    const data = await response.json();
    localStorage.setItem("access_token", data.access_token);
    onLoginSuccess();
    console.log("Logged in:", data);
  } catch (err) {
    setError("Something went wrong");
  }
  finally {
    setSubmitting(false);
  }
}

  return (
  <div className="card">
    <h1>Welcome back</h1>
    <p className="subtitle">Log in to analyze your resume</p>
    <form onSubmit={handleSubmit}>
      <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
      <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" />
      <button type="submit">Log in</button>
      {error && <p className="status error">{error}</p>}
    </form>
    <button type="submit" disabled={submitting}>
    {submitting && <span className="spinner"></span>}
    {submitting ? "Logging in..." : "Log in"}
    </button>
  </div>
);
}

export default Login;