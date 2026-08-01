from app.services.sentence_embedder import model


def get_results(resume, jd):
    jd_data = jd.get(include=["documents", "metadatas"])

    filtered = [
        (text, meta) for text, meta in zip(jd_data["documents"], jd_data["metadatas"])
        if meta["category"] != "responsibilities"
    ]
    text = [_ for _ in filtered]
    query_embedding = model.encode([text], normalize_embeddings=True).tolist()
    results = []
    for (text, meta), embedding in zip(filtered, query_embedding):
        match = resume.query(query_embeddings=[embedding], n_results=3)
        results.append({
            "jd_text": text,
            "jd_category": meta["category"],
            "matches": match,
        })
    return results


def check_gap(chunks):
    summary = {
        "requirements": {"covered": [], "partial": [], "gap": []},
        "optional": {"covered": [], "partial": [], "gap": []},
    }
    for chunk in chunks:
        jd_text = chunk["jd_text"]
        jd_category = chunk["jd_category"]
        distance = chunk["matches"]["distances"][0][0]
        resume_text = chunk["matches"]["documents"][0][0]
        resume_category = chunk["matches"]["metadatas"][0][0]["category"]

        if distance < 0.70:
            bucket = "covered"
        elif distance < 0.85:
            bucket = "partial"
        else:
            bucket = "gap"

        summary[jd_category][bucket].append({"jd_text": jd_text, "distance": distance, "resume_text": resume_text, "resume_section": resume_category})
    return summary



