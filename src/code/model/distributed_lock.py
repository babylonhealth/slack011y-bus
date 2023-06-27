import datetime
import random
import socket
import string
from typing import Optional

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import delete
from sqlalchemy import insert
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.engine.base import Connection

from src.code.db import db
from src.code.logger import create_logger

logger = create_logger(__name__)


class DistributedLockHandler:
    _db_conn: Connection = None
    scheduler_lock_acquired: bool = False
    scheduler_lock_check_interval_seconds: int = 5
    _scheduler_lock_stale_time: datetime.timedelta = datetime.timedelta(seconds=60)
    bot_instance: str = f"{socket.gethostname()}-{''.join(random.choices(string.ascii_letters, k=8))}"

    @classmethod
    def _refresh_conn(cls) -> None:
        try:
            if cls._db_conn:
                cls._db_conn.close()
        except Exception:
            logger.exception("Error while closing _db_conn")
            pass
        cls._db_conn = db.engine.connect().execution_options(isolation_level="SERIALIZABLE", autocommit=False)

    @classmethod
    def _try_to_acquire_lock(cls, type: str, force: bool = False) -> bool:
        if not cls._db_conn:
            cls._refresh_conn()
        try:
            with cls._db_conn.begin():
                cur_utc_time = datetime.datetime.utcnow()
                logger.debug("Grabbing lock. Type: %s", type)
                select_dlock = select(DistributedLock).where(DistributedLock.lock_type == type).with_for_update()
                dlock = cls._db_conn.execute(select_dlock).first()
                logger.debug("Query result: %s", str(dlock))
                if not dlock:
                    logger.debug("No lock found of type: %s. Inserting new lock, setting myself as owner.", type)
                    dlock_insert = insert(DistributedLock).values(
                        lock_type=type, bot_instance=cls.bot_instance, last_heartbeat_utc=cur_utc_time
                    )
                    cls._db_conn.execute(dlock_insert)
                    return True
                elif any(
                    [
                        dlock.bot_instance == cls.bot_instance,
                        dlock.last_heartbeat_utc < (cur_utc_time - cls._scheduler_lock_stale_time),
                        force,
                    ]
                ):
                    logger.debug(
                        (
                            "Existing lock of type found: %s. Either owned by myself, stale or force is True (%s)."
                            " Refreshing it."
                        ),
                        type,
                        str(force),
                    )
                    dlock_update = (
                        update(DistributedLock)
                        .where(DistributedLock.lock_type == type)
                        .values(bot_instance=cls.bot_instance, last_heartbeat_utc=cur_utc_time)
                    )
                    cls._db_conn.execute(dlock_update)
                    return True
                logger.debug(
                    "Lock not owned by me '%s' and fresher than '%s'. Not acquiring it.",
                    cls.bot_instance,
                    str(cls._scheduler_lock_stale_time),
                )
                return False
        except Exception:
            logger.exception("Error while trying to acquire lock. Type: '%s'", type)
            cls._refresh_conn()
            raise

    @classmethod
    def _release_lock(cls, type: str) -> None:
        if not cls._db_conn:
            cls._refresh_conn()
        try:
            with cls._db_conn.begin():
                logger.debug("Checking if lock type: '%s' owned by myself.", type)
                select_dlock = (
                    select(DistributedLock)
                    .where(DistributedLock.lock_type == type, DistributedLock.bot_instance == cls.bot_instance)
                    .with_for_update()
                )
                dlock = cls._db_conn.execute(select_dlock).first()
                logger.debug("Query result for lock: %s", dlock)
                if dlock:
                    logger.debug("Lock owned by myself. Releasing it.")
                    dlock_delete = delete(DistributedLock).where(
                        DistributedLock.lock_type == type, DistributedLock.bot_instance == cls.bot_instance
                    )
                    cls._db_conn.execute(dlock_delete)
        except Exception:
            logger.exception("Error while trying to release lock. Type: '%s'", type)
            cls._refresh_conn()
            raise

    @classmethod
    def try_to_acquire_scheduler_lock(cls, force: bool = False) -> Optional[bool]:
        if force:
            logger.info("Forcing scheduler lock acquire.")
        previous_scheduler_lock = cls.scheduler_lock_acquired
        cls.scheduler_lock_acquired = cls._try_to_acquire_lock("scheduler", force=force)
        if previous_scheduler_lock != cls.scheduler_lock_acquired:
            logger.info(
                "Scheduler lock acquired state change. Previous: %s. Current: %s",
                str(previous_scheduler_lock),
                str(cls.scheduler_lock_acquired),
            )
            return cls.scheduler_lock_acquired
        else:
            return None

    @classmethod
    def release_scheduler_lock(cls) -> None:
        logger.info("Releasing scheduler lock if owned.")
        cls._release_lock("scheduler")
        cls.scheduler_lock_acquired = False


class DistributedLock(db.Model):
    __tablename__ = "distributed_lock"

    id = Column(Integer, primary_key=True)
    lock_type = Column(String(255), nullable=False, unique=True)
    bot_instance = Column(String(255), nullable=False)
    last_heartbeat_utc = Column(DateTime, nullable=False)

    def serialize(self):
        return {
            "id": self.id,
            "lock_type": self.lock_type,
            "bot_instance": self.bot_instance,
            "last_heartbeat_utc": self.last_heartbeat_utc,
        }
