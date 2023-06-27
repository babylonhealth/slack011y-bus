import atexit
import os
import time
from functools import wraps

from cron_validator import CronValidator
from flask import Flask
from flask_apscheduler import APScheduler

from src.code.const import client
from src.code.logger import create_logger
from src.code.model.control_panel import ControlPanel
from src.code.model.distributed_lock import DistributedLockHandler
from src.code.report.request_report import RequestReport
from src.code.scheduler.autoclose import Autoclose
from src.code.utils.slack_webclient import SlackWebclient

logger = create_logger(__name__)


def scheduler_job(with_lock=True, debug_level=False):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            with self.scheduler.app.app_context():
                if debug_level:
                    logger.debug("Apscheduler triggered %s", func.__name__)
                else:
                    logger.info("Apscheduler triggered %s", func.__name__)
                if with_lock:
                    if DistributedLockHandler.scheduler_lock_acquired:
                        func(self, *args, **kwargs)
                    else:
                        if debug_level:
                            logger.debug("Node does not have scheduler lock - skipping %s run", func.__name__)
                        else:
                            logger.info("Node does not have scheduler lock - skipping %s run", func.__name__)
                else:
                    func(self, *args, **kwargs)

        return wrapper

    return decorator


class SchedulerManager:
    scheduler: APScheduler

    def __init__(self, app: Flask):
        logger.info("Initializing scheduler")
        self.scheduler = APScheduler()
        self.scheduler.init_app(app)
        self.scheduler.add_job(
            id="handle_scheduler_lock",
            func=self._handle_scheduler_lock,
            trigger="interval",
            seconds=DistributedLockHandler.scheduler_lock_check_interval_seconds,
        )
        atexit.register(self.stop)

    def start(self):
        logger.info("Starting scheduler")
        self.scheduler.start()

    def stop(self):
        logger.info("Stopping scheduler")
        try:
            self.scheduler.shutdown()
        finally:
            with self.scheduler.app.app_context():
                DistributedLockHandler.release_scheduler_lock()

    def _add_jobs(self):
        logger.info("Adding scheduler jobs")
        logger.info("Adding handle_scheduler_lock")
        self.scheduler.add_job(
            id="handle_scheduler_lock",
            func=self._handle_scheduler_lock,
            trigger="interval",
            seconds=DistributedLockHandler.scheduler_lock_check_interval_seconds,
        )
        if os.environ.get("FEATURE_COMPLETE_IDLE_THREADS", "False").lower() == "true":
            logger.info("Adding complete_idle_threads")
            self.scheduler.add_job(
                id="complete_idle_threads",
                func=self._complete_idle_threads,
                trigger="cron",
                hour="*",
                day_of_week="1-4",
            )
        logger.info("Adding daily_report")
        self.scheduler.add_job(id="daily_report", func=self._daily_report, trigger="interval", minutes=10)
        self._add_channel_message_jobs()

    def _add_channel_message_jobs(self):
        logger.info("Adding channel message jobs")
        with self.scheduler.app.app_context():
            for control_panel in ControlPanel().get_all_active_control_panels():
                if "channel_message" in control_panel.channel_properties:
                    logger.info("Adding message job for channel %s", control_panel.slack_channel_name)
                    try:
                        cron_string = control_panel.channel_properties["channel_message"]["cron_string"]
                        blocks = control_panel.channel_properties["channel_message"]["blocks"]
                        logger.debug("cron_string: %s", cron_string)
                        logger.debug("blocks: %s", blocks)
                        CronValidator.parse(cron_string)
                        split_cron_string = cron_string.split()
                        self.scheduler.add_job(
                            id=f"channel_message_{control_panel.slack_channel_name}",
                            func=self._channel_message,
                            args=[control_panel.slack_channel_name, blocks],
                            trigger="cron",
                            minute=split_cron_string[0],
                            hour=split_cron_string[1],
                            day=split_cron_string[2],
                            month=split_cron_string[3],
                            day_of_week=split_cron_string[4],
                        )
                        logger.info("Message job added for channel %s", control_panel.slack_channel_name)
                    except Exception:
                        logger.exception("Adding channel message for %s failed", control_panel.slack_channel_name)
        logger.info("Adding channel message jobs done.")

    def _remove_jobs(self):
        logger.info("Removing all jobs from scheduler")
        self.scheduler.remove_all_jobs()
        logger.info("All jobs removed")

    def refresh_jobs(self):
        logger.info("Refresh_jobs triggered")
        self.scheduler.remove_job("handle_scheduler_lock")
        time.sleep(DistributedLockHandler.scheduler_lock_check_interval_seconds)
        with self.scheduler.app.app_context():
            DistributedLockHandler.try_to_acquire_scheduler_lock(force=True)
        self._recreate_jobs_in_scheduler()

    def _recreate_jobs_in_scheduler(self):
        logger.info("Recreating jobs in scheduler")
        self._remove_jobs()
        self._add_jobs()
        logger.info("Scheduler jobs recreated")

    @scheduler_job(with_lock=False, debug_level=True)
    def _handle_scheduler_lock(self):
        if DistributedLockHandler.try_to_acquire_scheduler_lock():
            self._recreate_jobs_in_scheduler()

    @scheduler_job()
    def _complete_idle_threads(self):
        Autoclose.close_idle_threads(client)

    @scheduler_job()
    def _daily_report(self):
        RequestReport().daily_report()

    @scheduler_job()
    def _channel_message(self, channel_name: str, blocks: dict):
        SlackWebclient.send_post_message_as_main_message(client, channel_name, blocks)
