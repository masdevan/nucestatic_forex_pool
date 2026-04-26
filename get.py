import sys

if len(sys.argv) < 2:
    print("Usage: python get.py <job>")
    print("Available jobs: cache, calendar, news, timeframe")
    sys.exit(1)

job = sys.argv[1]

if job == "cache":
    print("Cache clearing not implemented")
elif job == "timeframe":
    from app.jobs.timeframe_job import run_job
    run_job()
elif job == "calendar":
    from app.jobs.calendar_job import run_job
    run_job()
elif job == "news":
    from app.jobs.news_job import run_job
    run_job()
else:
    print(f"Unknown job: {job}")
    sys.exit(1)