import { useState } from "react";

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault(); // stops the browser's default full-page-reload form behavior

    // TODO: call fetch() here, POST to /auth/login
    // remember: OAuth2PasswordRequestForm on the backend expects
    // application/x-www-form-urlencoded, NOT JSON — same thing that
    // tripped you up in Swagger earlier

    // TODO: on success, save the access_token somewhere
    // TODO: on failure, setError(...) with a message
  }

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="email"
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="password"
      />
      <button type="submit">Log in</button>
      {error && <p>{error}</p>}
    </form>
  );
}

export default Login;
