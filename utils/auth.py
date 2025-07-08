import aiohttp
from bs4 import BeautifulSoup
from config import LOGIN_URL

async def login(username, password):
    """Авторизация на сайте и получение сессии."""
    session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False))
    async with session.get(LOGIN_URL) as resp:
        html = await resp.text()
        soup = BeautifulSoup(html, "html.parser")
        token_input = soup.find("input", {"name": "logintoken"})
        logintoken = token_input["value"] if token_input else ""
    payload = {"username": username, "password": password, "logintoken": logintoken}
    async with session.post(LOGIN_URL, data=payload) as response:
        if response.status == 200:
            return session
        else:
            await session.close()
            return None