import hashlib

def normalize_texts(texts: list[str]) -> list[str]:
    return [" ".join(t.split()) for t in texts]

def get_course_hash(announcements: list[str]) -> str:
    combined = "|||".join(announcements)
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()