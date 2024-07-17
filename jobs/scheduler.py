from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.jobstores.redis import RedisJobStore
import logging
from custom_jobs import CustomJobs

# Configure logging
logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)

# Define the job stores
jobstores = {
    'default': SQLAlchemyJobStore(url='mysql+mysqlconnector://vch_user:rQMK5oLIg5i7KBiyk7uhy7uQqVg3cyjx@mysql/vch')
    # 'redis': RedisJobStore(jobs_key='apscheduler.jobs', run_times_key='apscheduler.run_times', host='localhost', port=6379, db=0)
}

# Define the executors
executors = {
    'default': ProcessPoolExecutor(20),  # Adjust the number of workers as needed
}

# Define the job defaults
job_defaults = {
    'coalesce': False,
    'max_instances': 3
}

# Create the scheduler
scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults)

# Start the scheduler
scheduler.start()

# Check if the job exists and add it if it doesn't
job_id = 'my_job_id'
if not scheduler.get_job(job_id):
    scheduler.add_job(CustomJobs.my_job, 'interval', seconds=30, id=job_id)
else:
    print(f"Job with id '{job_id}' already exists.")

# Keep the script running
try:
    while True:
        pass
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()
