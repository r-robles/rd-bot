import logging
from gino import Gino

log = logging.getLogger(__name__)
db = Gino()

from database.models.prefix import Prefix
from database.models.tag import Tag


def _get_connection_url(config):
    return ''.join((
        'postgres://',
        config['user'],
        ':',
        config['password'],
        '@',
        config['host'],
        '/',
        config['database']))


async def connect_to_database(config):
    connection = _get_connection_url(config)

    log.info('Connecting to PostgreSQL database.')
    await db.set_bind(connection)
    await db.gino.create_all()


async def disconnect_from_database():
    log.info('Disconnecting from PostgreSQL database.')
    await db.pop_bind().close()
