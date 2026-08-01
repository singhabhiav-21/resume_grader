function Start({ onAnalyze }) {
  return (
    <div className="card">
      <h1>Ready when you are</h1>
      <p className="subtitle">Upload a resume and job description to get gap analysis feedback</p>
      <button type="button" onClick={onAnalyze}>Analyze your resume</button>
    </div>
  );
}

export default Start;