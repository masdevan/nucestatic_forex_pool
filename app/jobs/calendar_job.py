import re
import time
import httpx
from datetime import datetime, date, timezone
from zoneinfo import ZoneInfo  
from app.databases.config import SessionLocal
from app.databases.models.calendar_model import Calendar

BASE_URL = "https://www.mql5.com/en/economic-calendar"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

LOCAL_TZ = ZoneInfo("Asia/Jakarta")

def scrape_calendar():
    print(f"[{datetime.now()}] Scraping calendar...")

    try:
        response = httpx.get(BASE_URL, timeout=30.0, headers=HEADERS)
        response.raise_for_status()
        html = response.text

        calendar_data = []

        item_pattern = r'<div class="ec-table__item[^"]*"[^>]*>([\s\S]*?)</div>'
        items = re.findall(item_pattern, html)

        if not items:
            item_pattern = r'<div class="ec-table__item[^"]*"[^>]*>([^<]+)</div>'
            items = re.findall(item_pattern, html)

        for item in items:
            try:
                item = item.strip()
                if not item or len(item) < 10:
                    continue

                time_match = re.search(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2})', item)
                time_str = time_match.group(1) if time_match else ""

                currency_match = re.search(r',\s*([A-Z]{3}),', item)
                currency = currency_match.group(1) if currency_match else ""

                event_match = re.search(r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', item)
                event_url, event_name = "", ""
                if event_match:
                    event_url  = "https://www.mql5.com" + event_match.group(1)
                    event_name = event_match.group(2)

                actual_match   = re.search(r'Actual:\s*([^,]+)', item)
                forecast_match = re.search(r'Forecast:\s*([^,]+)', item)
                previous_match = re.search(r'Previous:\s*([^,]+)', item)
                impact_match   = re.search(r'ec-table__importance\s+(high|medium|low)', item)

                actual   = actual_match.group(1).strip()   if actual_match   else ""
                forecast = forecast_match.group(1).strip() if forecast_match else ""
                previous = previous_match.group(1).strip() if previous_match else ""
                impact   = impact_match.group(1).lower()   if impact_match   else None

                if time_str and event_name:
                    dt_utc   = datetime.strptime(time_str, "%Y.%m.%d %H:%M").replace(tzinfo=timezone.utc)
                    dt_local = dt_utc.astimezone(LOCAL_TZ)

                    if dt_local.date() != date.today():
                        continue

                    calendar_data.append({
                        "time":               dt_local.strftime("%Y.%m.%d %H:%M"),
                        "currency":           currency,
                        "event":              event_name,
                        "url":                event_url,
                        "impact":             impact,
                        "actual":             actual,
                        "forecast":           forecast,
                        "previous":           previous,
                        "description":        "",
                        "description_status": 0
                    })

            except Exception as e:
                print(f"Error parsing item: {e}")
                continue

        print(f"Parsed {len(calendar_data)} calendar items")

        db = SessionLocal()
        try:
            saved_count = 0
            for data in calendar_data:
                existing = db.query(Calendar).filter(
                    Calendar.time     == data["time"],
                    Calendar.currency == data["currency"],
                    Calendar.event    == data["event"]
                ).first()

                if not existing:
                    db.add(Calendar(**data))
                    saved_count += 1

            db.commit()
            print(f"Saved {saved_count} new items to database")
        finally:
            db.close()

    except Exception as e:
        print(f"Error scraping calendar: {e}")

def scrape_description(url: str) -> tuple:
    try:
        response = httpx.get(url, timeout=30.0, headers=HEADERS)
        response.raise_for_status()
        html = response.text

        description = ""
        impact = None

        impact_match = re.search(r'<td\s+class="event-table__importance\s+(high|medium|low)"', html)
        if not impact_match:
            impact_match = re.search(r'<span class="economic-calendar__importance economic-calendar__importance--([^"]+)"', html)
        if impact_match:
            impact = impact_match.group(1).lower()

        json_match = re.search(
            r'{"@context":"https://schema\.org","@type":"Dataset","name":"([^"]+)","alternateName":"[^"]+","description":"([^"]+)"',
            html
        )
        if json_match:
            description = json_match.group(2)

        if not description:
            desc_match = re.search(r'<div class="economic-calendar__event-desc">([\s\S]*?)</div>', html)
            if desc_match:
                texts = re.findall(r'<p>([^<]+)</p>', desc_match.group(1))
                if texts:
                    description = " ".join(texts)

        return description or "", impact

    except Exception:
        return "", None

def scrape_descriptions():
    print(f"[{datetime.now()}] Scraping descriptions...")

    while True:
        db = SessionLocal()
        try:
            items = db.query(Calendar).filter(
                Calendar.description_status == 0,
                Calendar.url != ""
            ).all()

            if not items:
                print("No pending items.")
                break  

            print(f"Found {len(items)} pending items")

            for item in items:
                if not item.url:
                    continue

                description, impact = scrape_description(item.url)

                item.description        = description
                item.description_status = 1
                if item.impact is None and impact is not None:
                    item.impact = impact

                db.commit()
                print(f"Saved: [{item.currency}] {item.event}")

                time.sleep(1)

        except Exception as e:
            print(f"Error in scrape_descriptions: {e}")
            db.rollback()
            break  
        finally:
            db.close()

def run_job():
    while True:
        scrape_calendar()
        scrape_descriptions()  
        print(f"[{datetime.now()}] All done. Next calendar scrape in 3 hours...")
        for remaining in range(10800, 0, -30):
            print(f"Countdown: {remaining // 60}m {remaining % 60}s", end="\r")
            time.sleep(30)
        print("")

if __name__ == "__main__":
    run_job()