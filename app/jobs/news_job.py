import os
import sys
import re
import time
import asyncio
import subprocess
from datetime import datetime, timedelta, timezone
from ollama import Client
from app.databases.config import SessionLocal
from app.databases.models.news_model import News

BASE_URL = "https://www.fxstreet.com/news"

def scrape_news():
    print(f"[{datetime.now()}] Scraping news...")

    try:
        result = subprocess.run(
            ["curl", "--resolve", "www.fxstreet.com:443:104.18.28.90", "-s", BASE_URL],
            capture_output=True,
            timeout=30
        )

        if result.returncode != 0:
            print(f"curl failed: {result.stderr.decode() if result.stderr else 'unknown error'}")
            return

        html = result.stdout.decode() if isinstance(result.stdout, bytes) else result.stdout
        news_data = []

        article_pattern = r'<a[^>]*href="(https://www\.fxstreet\.com/news/[^"]+)"[^>]*>.*?<span[^>]*>.*?<span[^>]*>([^<]+)</span>.*?</span>.*?</a>.*?<p[^>]*>.*?<time[^>]*dateTime="([^"]+)"'
        articles = re.findall(article_pattern, html, re.DOTALL)

        for article in articles:
            try:
                url = article[0].strip()
                title = article[1].strip()
                datetime_str = article[2].strip()

                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', datetime_str)
                time_match = re.search(r'T(\d{2}:\d{2})', datetime_str)

                date_str = date_match.group(1) if date_match else datetime.now().strftime("%Y-%m-%d")
                time_str = time_match.group(1) if time_match else ""

                if url and title:
                    news_data.append({"url": url, "title": title, "date": date_str, "time": time_str})
            except Exception as e:
                print(f"Error parsing article: {e}")
                continue

        if not news_data:
            simple_pattern = r'<a[^>]*href="(https://www\.fxstreet\.com/news/[^"]+)"[^>]*>.*?<span[^>]*>([^<]+)</span>.*?<time[^>]*dateTime="([^"]+)"'
            articles = re.findall(simple_pattern, html)
            for article in articles:
                url = article[0].strip()
                title = article[1].strip()
                datetime_str = article[2].strip()
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', datetime_str)
                date_str = date_match.group(1) if date_match else datetime.now().strftime("%Y-%m-%d")
                if url and title:
                    news_data.append({"url": url, "title": title, "date": date_str, "time": ""})

        print(f"Parsed {len(news_data)} news items")

        db = SessionLocal()
        try:
            saved_count = 0
            for data in news_data:
                existing = db.query(News).filter(News.url == data["url"]).first()
                if not existing:
                    date_str = data.get("date", "")
                    time_str = data.get("time", "")
                    dt = None

                    if date_str and time_str:
                        try:
                            dt = datetime.fromisoformat(f"{date_str}T{time_str}".replace("Z", ""))
                            dt = dt.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=7)))
                        except Exception:
                            pass
                    elif date_str:
                        try:
                            dt = datetime.strptime(date_str, "%Y-%m-%d")
                            dt = dt.replace(tzinfo=timezone(timedelta(hours=7)))
                        except Exception:
                            dt = datetime.now()

                    news = News(
                        time=dt,
                        title=data["title"],
                        url=data["url"],
                        description="",
                        description_status=0
                    )
                    db.add(news)
                    saved_count += 1

            db.commit()
            print(f"Saved {saved_count} new items to database")
        finally:
            db.close()

    except Exception as e:
        print(f"Error scraping news: {e}")

def parse_output(text: str):
    result = {"score": None, "pair_impact": [], "direction": None, "reason": None}
    try:
        score_match     = re.search(r"score:\s*(\d+)", text)
        pair_match      = re.search(r"pair_impact:\s*(.+)", text)
        direction_match = re.search(r"direction:\s*(.+)", text)
        reason_match    = re.search(r"reason:\s*(.+)", text, re.DOTALL)

        if score_match:     result["score"]       = int(score_match.group(1))
        if pair_match:      result["pair_impact"] = [p.strip() for p in pair_match.group(1).split(",")]
        if direction_match: result["direction"]   = direction_match.group(1).strip()
        if reason_match:    result["reason"]      = reason_match.group(1).strip()
    except Exception as e:
        print("Parse error:", e)
    return result

def validate_result(parsed):
    errors = []
    if parsed["score"] is None or not (0 <= parsed["score"] <= 100):
        errors.append("invalid score")
    if not parsed["pair_impact"]:
        errors.append("no pair_impact")
    if not parsed["direction"]:
        errors.append("no direction")
    if not parsed["reason"]:
        errors.append("no reason")
    return errors

def analyze_news(client, model, title, description):
    prompt = f"""Analyze this news article for its potential impact on the forex market.

Focus ONLY on short-term market impact (intraday to 1-2 days).

Scoring guidelines:
- 0–10: No impact / fully repetitive / pure technical or opinion
- 20–35: Weak catalyst, minor sentiment influence
- 40–60: Moderate impact, can move specific currency pairs
- 60–80: Strong impact, clear macro or policy driver
- 80–100: High-impact event (surprise data, central bank action, major geopolitical shock)

Evaluation criteria (priority order):
1. Monetary policy signals
2. Macroeconomic data
3. Geopolitical risk
4. Surprise vs expectations
5. Relevance to major currencies (USD, EUR, JPY, GBP, AUD, NZD, CAD, CHF, CNY, KRW, etc.)

Core rules:
- Do NOT give score 0 unless absolutely no new information.
- If ANY bias, movement, or impact exists → score MUST be at least 20.
- Distinguish ROOT CAUSE vs REACTION (root cause gets higher score).
- Similar themes → similar scores (±5).
- Score >60 requires clear surprise or escalation.
- Be concise and decisive.

Direction rules (DYNAMIC):
- Format: bullish [CURRENCY], bearish [CURRENCY], or mixed
- Currency must be valid forex code (USD, EUR, JPY, GBP, AUD, NZD, CAD, CHF, CNY, KRW, etc.)
- Only ONE dominant currency allowed
- If no clear dominance → use "mixed"
- No extra words

Pair rules:
- Include only directly affected pairs
- Maximum 4 pairs
- Must include the currency from direction

Strict output rules:
- Plain text only
- No symbols like **, *, -, etc.
- Follow format EXACTLY

Consistency check:
- If reasoning implies movement → score ≥20
- weak → 20–40
- moderate → 40–60
- strong → 60+

Title: {title}
Description: {description}

Output format:
score: [integer]
pair_impact: [comma-separated pairs]
direction: [bullish XXX / bearish XXX / mixed]
reason: [max 2 sentences]
"""
    response = asyncio.run(asyncio.wait_for(
        asyncio.to_thread(client.chat, model=model, messages=[{"role": "user", "content": prompt}]),
        timeout=60.0
    ))
    return response["message"]["content"] if response and "message" in response else ""

def analyze_with_retry(client, model, title, description, max_retry=2):
    parsed = {}
    for i in range(max_retry):
        raw = analyze_news(client, model, title, description)
        parsed = parse_output(raw)
        errors = validate_result(parsed)
        if not errors:
            return parsed
        print(f"Retry {i + 1} karena:", errors)
    return parsed

def score_news_item(title: str, description: str):
    token = os.getenv("AI_TOKEN", "958b3d2135214e7f87c74f43d10db86d.GfMAOVJZUAidYNNffKpZOXpZ")
    model = os.getenv("AI_MODEL", "deepseek-v3.1:671b")
    client = Client(host="https://ollama.com", headers={"Authorization": f"Bearer {token}"})

    try:
        parsed = analyze_with_retry(client, model, title, description, max_retry=2)
        score      = parsed["score"] if parsed.get("score") is not None and 0 <= parsed["score"] <= 100 else 0
        pair_impact = ", ".join(parsed.get("pair_impact", []))[:255]
        direction  = (parsed.get("direction") or "")[:50]
        reason     = (parsed.get("reason") or "Failed to parse reason")[:500]
        return score, pair_impact, direction, reason
    except Exception as e:
        print(f"Error scoring news: {e}")
        return 0, "", "", f"Scoring failed: {str(e)}"

def scrape_descriptions():
    print(f"[{datetime.now()}] Scraping descriptions...")

    db = SessionLocal()
    try:
        news_items = db.query(News).filter(News.description_status == 0).all()
        print(f"Found {len(news_items)} pending items")

        for item in news_items:
            try:
                url = item.url
                domain = url.split("/")[2]

                result = subprocess.run(
                    ["curl", "--resolve", f"{domain}:443:104.18.28.90", "-s", url],
                    capture_output=True,
                    timeout=30
                )

                if result.returncode != 0:
                    print(f"curl failed for {url}: {result.stderr.decode() if result.stderr else 'unknown error'}")
                    item.description_status = 2
                    db.commit()
                    continue

                html = result.stdout.decode() if isinstance(result.stdout, bytes) else result.stdout

                article_pattern = r'<div[^>]*id="post-content"[^>]*>([\s\S]*?)</div>\s*</div>\s*</article>'
                article_match = re.search(article_pattern, html, re.DOTALL)

                if article_match:
                    content = article_match.group(1)
                    content = re.sub(r'<div[^>]*>.*?</div>', '', content, flags=re.DOTALL)
                    content = re.sub(r'<table.*?</table>', '', content, flags=re.DOTALL)
                    content = re.sub(r'<[^>]+>', '', content)
                    for pattern, repl in [
                        (r'&nbsp;', ' '), (r'&amp;', '&'), (r'&lt;', '<'), (r'&gt;', '>'),
                        (r'&#8211;', '-'), (r'&#8217;', "'"), (r'&#8220;', '"'),
                        (r'&#8221;', '"'), (r'&quot;', '"'),
                    ]:
                        content = re.sub(pattern, repl, content)
                    content = re.sub(r'\s+', ' ', content).strip()

                    item.description = content
                    item.description_status = 1

                    score, pair_impact, direction, reason = score_news_item(item.title, item.description)
                    item.score      = score
                    item.pair_impact = pair_impact
                    item.direction  = direction
                    item.reason     = reason

                    db.commit()
                    print(f"Updated: {item.title} (score: {score})")
                else:
                    item.description_status = 2
                    db.commit()
                    print(f"Content not found: {item.url}")

            except Exception as e:
                item.description_status = 2
                db.commit()
                print(f"Error for {item.url}: {e}")
                continue

        print("Description scraping complete")
    finally:
        db.close()

def run_job():
    while True:
        scrape_news()
        scrape_descriptions()
        print(f"[{datetime.now()}] Cycle complete. Next run in 10 minutes...")
        for remaining in range(600, 0, -30):
            print(f"Countdown: {remaining}s", end="\r")
            time.sleep(30)
        print("")

if __name__ == "__main__":
    run_job()