"""
app/tasks/worker.py
DESCRIPTION: placeholder for background worker code.
TODO: integrate dramatiq/celery/etc if you need a proper broker/worker model.
"""
import asyncio
async def sample_background_job(payload: dict):
    # simulate work
    await asyncio.sleep(1)
    print("background job completed:", payload)
