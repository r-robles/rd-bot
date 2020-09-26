from database import db


class MusicConfiguration(db.Model):
    __tablename__ = 'music_configuration'

    guild_id = db.Column(db.BigInteger(), primary_key=True)
    volume = db.Column(db.Integer())
    repeat = db.Column(db.Boolean())
    shuffle = db.Column(db.Boolean())
