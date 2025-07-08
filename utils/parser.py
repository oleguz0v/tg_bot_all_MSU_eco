import logging
import aiohttp
from bs4 import BeautifulSoup
from config import COURSES_URL


async def get_courses(session):
    """Получение списка курсов пользователя."""
    async with session.get(COURSES_URL) as response:
        html = await response.text()
        soup = BeautifulSoup(html, "html.parser")
        courses = {}
        for link in soup.select("a[href*='course/view.php?id=']"):
            course_name = link["title"].strip()
            course_url = link["href"]
            courses[course_name] = course_url
        return courses


async def get_announcements(session: aiohttp.ClientSession, course_url: str) -> list[str]:
    """
    Возвращает список строк, каждая — либо текст объявления,
    либо название ресурса + ссылка на него.
    """
    try:
        async with session.get(course_url) as resp:
            resp.raise_for_status()
            html = await resp.text()
    except Exception as e:
        logging.error(f"Failed to fetch announcements from {course_url}: {e}")
        return []

    soup = BeautifulSoup(html, "html.parser")
    results: list[str] = []

    # 1) Текстовые объявления
    for block in soup.select(".course-content .content"):
        text = " ".join(block.get_text(separator=" ", strip=True).split())
        if text:
            results.append(text)

    # 2) Ресурсы (файлы и ссылки)
    for res in soup.select("li.activity.resource"):
        # название ресурса
        name_tag = res.select_one(".activity-item")
        name = name_tag.get_text(strip=True) if name_tag else ""
        # ссылка
        link_tag = res.select_one("a[href]")
        link = link_tag["href"] if link_tag else ""
        if name or link:
            entry = f"{name}".strip()
            if link:
                entry += f" — {link}"
            results.append(entry)
    return results