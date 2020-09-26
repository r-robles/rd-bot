"""Add music configuration table

Revision ID: 8f7ea2b2538c
Revises: 15bef6843f11
Create Date: 2020-09-24 14:14:46.225538

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8f7ea2b2538c'
down_revision = '15bef6843f11'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('music_configuration',
                    sa.Column('guild_id', sa.BigInteger(), nullable=False),
                    sa.Column('volume', sa.Integer(), nullable=True),
                    sa.Column('repeat', sa.Boolean(), nullable=True),
                    sa.Column('shuffle', sa.Boolean(), nullable=True),
                    sa.PrimaryKeyConstraint('guild_id'))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('music_configuration')
    # ### end Alembic commands ###
