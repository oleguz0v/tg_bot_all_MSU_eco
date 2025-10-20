import hashlib

def normalize_texts(texts: list[str]) -> list[str]:
    return [" ".join(t.split()) for t in texts]

def get_course_hash_v1(announcements: list[str]) -> str:
    """Старая схема хеширования (без нормализации и сортировки)."""
    combined = "|||".join(announcements)
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()

def get_course_hash_v2(announcements: list[str]) -> str:
    """Новая устойчивая схема: нормализация и сортировка элементов."""
    normalized_sorted = sorted(normalize_texts(announcements))
    combined = "|||".join(normalized_sorted)
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()

# Текущая версия
get_course_hash = get_course_hash_v2

def matches_existing_hash(announcements: list[str], stored_hash: str) -> bool:
    """Проверяет, соответствует ли сохранённый хеш текущему содержимому
    при любой из известных схем (v1 или v2)."""
    if not stored_hash:
        return False
    if stored_hash == get_course_hash_v2(announcements):
        return True
    if stored_hash == get_course_hash_v1(announcements):
        return True
    return False