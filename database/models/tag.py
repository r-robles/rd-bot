from datetime import datetime
from database import db


class Tag(db.Model):
    __tablename__ = 'tag'

    guild_id = db.Column(db.BigInteger(), primary_key=True)
    name = db.Column(db.String(), primary_key=True)
    content = db.Column(db.String())
    owner = db.Column(db.BigInteger())
    last_modified = db.Column(db.DateTime())
