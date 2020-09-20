from database import db


class Prefix(db.Model):
    __tablename__ = 'prefix'

    guild_id = db.Column(db.BigInteger(), primary_key=True)
    prefix = db.Column(db.String())
