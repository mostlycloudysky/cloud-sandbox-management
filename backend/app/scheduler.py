from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the scheduler
scheduler = BackgroundScheduler()
scheduler.start()


def schedule_task(func, delay_minutes: int, sandbox_name: str):
    """
    Schedule a task to run after a specified delay.
    """
    run_time = datetime.utcnow() + timedelta(minutes=delay_minutes)
    logger.info(f"Scheduling task for sandbox '{sandbox_name}' at {run_time}")
    scheduler.add_job(
        func,
        "date",
        run_date=run_time,
        args=[sandbox_name],
        id=f"terminate-{sandbox_name}",  # Unique job ID for each sandbox
        replace_existing=True,  # Avoid duplicate tasks
    )
