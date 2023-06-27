from datetime import datetime
from datetime import timedelta

from sqlalchemy.engine.base import Connection

from src.code.db import db
from src.code.model.distributed_lock import DistributedLock
from src.code.model.distributed_lock import DistributedLockHandler


class TestDistributedLockHandler:
    def test_refresh_conn(self, db_setup) -> None:
        assert DistributedLockHandler._db_conn is None
        DistributedLockHandler._refresh_conn()
        assert isinstance(DistributedLockHandler._db_conn, Connection)

    def test_refresh_conn_results_close_connection(self, db_setup) -> None:
        DistributedLockHandler._db_conn = db.engine.connect().execution_options(
            isolation_level="SERIALIZABLE", autocommit=False
        )
        assert isinstance(DistributedLockHandler._db_conn, Connection)
        DistributedLockHandler._refresh_conn()

    def test_acquire_lock(self, db_setup) -> None:
        assert DistributedLockHandler.scheduler_lock_acquired is False
        DistributedLockHandler.try_to_acquire_scheduler_lock()
        assert DistributedLockHandler.scheduler_lock_acquired is True
        lock = db.session.query(DistributedLock).filter_by(bot_instance=DistributedLockHandler.bot_instance).first()
        assert lock is not None

    def test_refresh_lock(self, db_setup) -> None:
        lock_time = datetime.utcnow()
        db.session.add(
            DistributedLock(
                lock_type="scheduler", bot_instance=DistributedLockHandler.bot_instance, last_heartbeat_utc=lock_time
            )
        )
        db.session.commit()
        DistributedLockHandler.scheduler_lock_acquired = True
        DistributedLockHandler.try_to_acquire_scheduler_lock()
        assert DistributedLockHandler.scheduler_lock_acquired is True
        lock = db.session.query(DistributedLock).filter_by(bot_instance=DistributedLockHandler.bot_instance).first()
        assert lock is not None
        assert (lock.last_heartbeat_utc > lock_time) is True

    def test_lock_taken_by_other_instance_not_stale(self, db_setup) -> None:
        DistributedLockHandler._scheduler_lock_stale_time = timedelta(seconds=9999)
        lock_time = datetime.utcnow()
        db.session.add(
            DistributedLock(lock_type="scheduler", bot_instance="Some_other_bot", last_heartbeat_utc=lock_time)
        )
        db.session.commit()
        DistributedLockHandler.try_to_acquire_scheduler_lock()
        assert DistributedLockHandler.scheduler_lock_acquired is False
        lock = db.session.query(DistributedLock).filter_by(bot_instance=DistributedLockHandler.bot_instance).first()
        assert lock is None

    def test_lock_taken_by_other_instance_stale(self, db_setup) -> None:
        DistributedLockHandler._scheduler_lock_stale_time = timedelta(seconds=0)
        lock_time = datetime.utcnow() - timedelta(hours=1)
        db.session.add(
            DistributedLock(lock_type="scheduler", bot_instance="Some_other_bot", last_heartbeat_utc=lock_time)
        )
        db.session.commit()
        DistributedLockHandler.try_to_acquire_scheduler_lock()
        assert DistributedLockHandler.scheduler_lock_acquired is True
        lock = db.session.query(DistributedLock).filter_by(bot_instance=DistributedLockHandler.bot_instance).first()
        assert lock is not None

    def test_release_lock(self, db_setup) -> None:
        lock_time = datetime.utcnow()
        db.session.add(
            DistributedLock(
                lock_type="scheduler", bot_instance=DistributedLockHandler.bot_instance, last_heartbeat_utc=lock_time
            )
        )
        db.session.commit()
        DistributedLockHandler.scheduler_lock_acquired = True
        DistributedLockHandler.release_scheduler_lock()
        assert DistributedLockHandler.scheduler_lock_acquired is False
        lock = db.session.query(DistributedLock).filter_by(bot_instance=DistributedLockHandler.bot_instance).first()
        assert lock is None

    def test_release_lock_if_not_owned(self, db_setup) -> None:
        DistributedLockHandler.scheduler_lock_acquired = False
        DistributedLockHandler.release_scheduler_lock()
        assert DistributedLockHandler.scheduler_lock_acquired is False
        lock = db.session.query(DistributedLock).filter_by(bot_instance=DistributedLockHandler.bot_instance).first()
        assert lock is None
