import json
from typing import Union

from sqlalchemy import JSON
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy.orm.attributes import flag_modified

from src.code.db import db
from src.code.logger import create_logger

logger = create_logger(__name__)


class Block(db.Model):
    __tablename__ = "blocks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    blocks = Column(JSON, nullable=False)

    def create_or_update_existing_blocks(
        self, blocks: Union[dict, list, str, bytes, bytearray], blocks_id: int = None
    ) -> int:
        blocks_jsoned = blocks
        if isinstance(blocks_jsoned, (str, bytes, bytearray)):
            blocks_jsoned = json.loads(blocks_jsoned)
        if not blocks_id:
            new_record: Block = Block(blocks=blocks_jsoned)
            db.session.add(new_record)
            db.session.flush()
            db.session.refresh(new_record)
            record_id = new_record.id
        else:
            existing_record: Block = db.session.query(Block).filter_by(id=blocks_id).first()
            existing_record.blocks = blocks_jsoned
            flag_modified(existing_record, "blocks")
            record_id = existing_record.id
        db.session.commit()
        return record_id

    def get_blocks(self, block_id: int):
        block = db.session.query(Block).filter_by(id=block_id).first()
        return json.dumps(block.blocks) if block else None
