import sys
import os
import shutil
from dotenv import load_dotenv
load_dotenv()

def clear_cache():
    project_root = os.path.dirname(os.path.abspath(__file__))
    cleared = 0
    for root, dirs, files in os.walk(project_root):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            shutil.rmtree(pycache_path)
            cleared += 1
            dirs.remove('__pycache__')
        for file in files:
            if file.endswith('.pyc'):
                os.remove(os.path.join(root, file))
                cleared += 1
    print(f"Cache cleared: {cleared} items removed")

if len(sys.argv) < 2:
    print("Usage: python get.py <job>")
    print("Available jobs: cache, calendar, calendar:description, news, news:description, ohlc, timeframe, structure, position, swings, decision")
    sys.exit(1)

job = sys.argv[1]

if job == "cache":
    clear_cache()
elif job == "timeframe":
    from app.jobs.timeframe_job import run_job
    run_job()

elif job == "decision":
    from app.jobs.decision_job import run_job
    run_job()
else:
    print(f"Unknown job: {job}")
    sys.exit(1)
