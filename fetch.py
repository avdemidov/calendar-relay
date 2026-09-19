#!/usr/bin/env python3
import os, sys, pathlib
from playwright.sync_api import sync_playwright

SITE = os.environ["CAL_SITE"]      # адрес главной страницы сайта
ICS  = os.environ["CAL_ICS_URL"]   # адрес .ics
OUT  = pathlib.Path(os.environ["CAL_OUT"])
DBG  = pathlib.Path("debug")

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

def fail(page, msg):
    """При ошибке сохраняем скриншот и HTML, чтобы понять, что пошло не так."""
    DBG.mkdir(exist_ok=True)
    try:
        page.screenshot(path=str(DBG / "screen.png"), full_page=True)
        (DBG / "page.html").write_text(page.content(), encoding="utf-8")
    except Exception:
        pass
    sys.exit(msg)

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(user_agent=UA, locale="ru-RU")
    page = ctx.new_page()

    # заходим на главную: testcookie отдаёт challenge, браузер его решает
    page.goto(SITE, wait_until="networkidle", timeout=60_000)
    page.wait_for_timeout(3000)

    # теперь в контексте есть нужная кука — качаем календарь
    resp = ctx.request.get(ICS, headers={"Accept": "text/calendar,*/*"})
    if not resp.ok:
        fail(page, f"Сайт ответил HTTP {resp.status} на {ICS}")

    body = resp.body()
    if b"BEGIN:VCALENDAR" not in body[:400]:
        fail(page, "Вместо календаря пришло другое — проверка не пройдена.\n"
                   + body[:400].decode("utf-8", "replace"))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(body)
    print(f"Готово: {len(body)} байт записано в {OUT}")
    browser.close()
