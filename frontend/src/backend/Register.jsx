import { useState } from "react";
import { API_URL } from "../config.js";

const SPECIAL_CHARS = "!#€%&/()=?^*_:;©@£$∞§|[]≈±´~™''æ…‚§¶°";
const DIGITS = "1234567890";

function hasAny(str, chars) {
  return [...str].some((c) => chars.includes(c));
}

function checkName(name) {
  const trimmed = name.toLowerCase().trim();
  return {
    length: trimmed.length >= 5,
    noDigits: !hasAny(trimmed, DIGITS),
    noSpecial: !hasAny(trimmed, SPECIAL_CHARS),
  };
}

function checkPassword(password) {
  const trimmed = password.trim();
  return {
    length: trimmed.length >= 6,
    special: hasAny(trimmed, SPECIAL_CHARS),
    lower: /[a-z]/.test(trimmed),
    upper: /[A-Z]/.test(trimmed),
    digit: hasAny(trimmed, DIGITS),
  };
}

function Checklist({ items }) {
  return (
    <ul className="checklist">
      {items.map(([label, passed]) => (
        <li key={label} className={passed ? "valid" : ""}>
          {passed ? "✓" : "○"} {label}
        </li>
      ))}
    </ul>
  );
}

function Register({ onRegisterSuccess, onGoLogin }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const nameChecks = checkName(name);
  const passwordChecks = checkPassword(password);
  const nameValid = Object.values(nameChecks).every(Boolean);
  const passwordValid = Object.values(passwordChecks).every(Boolean);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const response = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password }),
      });

      if (!response.ok) {
        setError("Registration failed — that email may already be in use");
        return;
      }

      onRegisterSuccess();
    } catch (err) {
      setError("Something went wrong");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="card">
      <h1>Create your account</h1>
      <p className="subtitle">Sign up to start analyzing resumes</p>
      <form onSubmit={handleSubmit}>
        <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Full name" required />
        {name.length > 0 && (
          <Checklist
            items={[
              ["At least 5 characters", nameChecks.length],
              ["No numbers", nameChecks.noDigits],
              ["No special characters", nameChecks.noSpecial],
            ]}
          />
        )}

        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" required />

        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" required />
        {password.length > 0 && (
          <Checklist
            items={[
              ["At least 4 characters", passwordChecks.length],
              ["One lowercase letter", passwordChecks.lower],
              ["One uppercase letter", passwordChecks.upper],
              ["One number", passwordChecks.digit],
              ["One special character", passwordChecks.special],
            ]}
          />
        )}

        <button type="submit" disabled={submitting || !nameValid || !passwordValid}>
          {submitting && <span className="spinner"></span>}
          {submitting ? "Creating account..." : "Create account"}
        </button>
        {error && <p className="status error">{error}</p>}
      </form>
      <p className="switch-link">
        Already have an account?{" "}
        <button type="button" className="link-button" onClick={onGoLogin}>Log in</button>
      </p>
    </div>
  );
}

export default Register;