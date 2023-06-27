from unittest.mock import PropertyMock
from unittest.mock import patch

from src.code.const import client
from src.code.model.distributed_lock import DistributedLockHandler
from src.code.scheduler.autoclose import Autoclose
from src.code.utils.slack_webclient import SlackWebclient
from src.tests.scheduler.conftest import SchedulerManagerMock


class TestSchedulerManager:
    def test_refresh_jobs(self, mocked_scheduler_obj: SchedulerManagerMock):
        with patch.object(DistributedLockHandler, "try_to_acquire_scheduler_lock") as lock_handler:
            with patch.object(SchedulerManagerMock, "_add_jobs", return_value=None) as add_jobs_method:
                with patch.object(SchedulerManagerMock, "_remove_jobs", return_value=None) as mock_remove_jobs:
                    mocked_scheduler_obj.refresh_jobs()
                    add_jobs_method.assert_called()
                    mock_remove_jobs.assert_called()
                    lock_handler.assert_called_once_with(force=True)

    def test_add_jobs(self, manager_mocked_obj: SchedulerManagerMock):
        with patch.object(
            SchedulerManagerMock, "_add_channel_message_jobs", return_value=None
        ) as _add_channel_message_jobs_method:
            manager_mocked_obj._add_jobs()
            manager_mocked_obj.scheduler.add_job.assert_called()
            _add_channel_message_jobs_method.assert_called()

    def test_remove_jobs(self, manager_mocked_obj: SchedulerManagerMock):
        manager_mocked_obj._remove_jobs()
        manager_mocked_obj.scheduler.remove_all_jobs.assert_called()

    def test_start(self, manager_mocked_obj: SchedulerManagerMock):
        manager_mocked_obj.start()
        manager_mocked_obj.scheduler.start.assert_called()

    def test_stop(self, manager_mocked_obj: SchedulerManagerMock):
        with patch.object(DistributedLockHandler, "release_scheduler_lock") as lock_handler:
            manager_mocked_obj.stop()
            manager_mocked_obj.scheduler.shutdown.assert_called()
            lock_handler.assert_called()

    def test_handle_scheduler_lock(self, manager_mocked_obj: SchedulerManagerMock):
        with patch.object(
            SchedulerManagerMock, "_recreate_jobs_in_scheduler", return_value=None
        ) as _add_channel_message_jobs_method:
            with patch.object(
                DistributedLockHandler, "try_to_acquire_scheduler_lock", return_value=True
            ) as lock_handler:
                manager_mocked_obj._handle_scheduler_lock()
                _add_channel_message_jobs_method.assert_called()
                lock_handler.assert_called()

    def test_scheduler_job_decorator_debug_no_lock(self, manager_mocked_obj: SchedulerManagerMock):
        with patch.object(SchedulerManagerMock, "_recreate_jobs_in_scheduler", return_value=None):
            with patch.object(
                DistributedLockHandler, "scheduler_lock_acquired", new_callable=PropertyMock, return_value=True
            ) as lock_status:
                with patch.object(
                    DistributedLockHandler, "try_to_acquire_scheduler_lock", return_value=True
                ) as lock_handler:
                    with patch("logging.Logger.debug") as logger:
                        manager_mocked_obj._handle_scheduler_lock()
                        logger.assert_called()
                        lock_status.assert_not_called()
                        lock_handler.assert_called()

    def test_scheduler_job_decorator(self, manager_mocked_obj: SchedulerManagerMock):
        with patch.object(
            DistributedLockHandler, "scheduler_lock_acquired", new_callable=PropertyMock, return_value=True
        ) as lock_status:
            with patch("logging.Logger.info") as logger:
                with patch.object(Autoclose, "close_idle_threads"):
                    manager_mocked_obj._complete_idle_threads()
                    logger.assert_called()
                    lock_status.assert_called()

    def test_job_complete_idle_threads(self, manager_mocked_obj: SchedulerManagerMock):
        with patch.object(
            DistributedLockHandler, "scheduler_lock_acquired", new_callable=PropertyMock, return_value=True
        ) as lock_status:
            with patch.object(Autoclose, "close_idle_threads") as utils_mocked:
                manager_mocked_obj._complete_idle_threads()
                utils_mocked.assert_called()
                lock_status.assert_called()

    def test_job_channel_message(self, manager_mocked_obj: SchedulerManagerMock):
        with patch.object(
            DistributedLockHandler, "scheduler_lock_acquired", new_callable=PropertyMock, return_value=True
        ) as lock_status:
            with patch.object(SlackWebclient, "send_post_message_as_main_message") as utils_mocked:
                manager_mocked_obj._channel_message("bogus", {})
                utils_mocked.assert_called_once_with(client, "bogus", {})
                lock_status.assert_called()
