"""panel de admin: taller interno y quien dio de alta cada taller

Revision ID: a1c3f5d7b9e1
Revises: 9661d4b520c3
Create Date: 2026-08-09

Escrita a mano y no con autogenerate: autogenerate compara contra la base a la que
apunte la configuracion, y la de desarrollo es SQLite mientras produccion es Postgres.

`internal` va con server_default para los talleres que ya existen -ninguno es interno-.
`created_by_user_id` queda nulo en los que se crearon antes del panel: no hay forma de
saber quien los dio de alta, y inventar un responsable seria peor que dejarlo vacio.

Todo dentro de un `batch_alter_table`, como las otras migraciones: SQLite no sabe
alterar restricciones, y al hacerlo en directo esta migracion moria a la mitad -con la
columna `internal` ya agregada, porque SQLite tampoco deshace DDL-, de manera que el
segundo intento tampoco corria y no habia salida sin borrar la base a mano.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1c3f5d7b9e1'
down_revision: Union[str, Sequence[str], None] = '9661d4b520c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('workshops') as lote:
        lote.add_column(
            sa.Column('internal', sa.Boolean(), nullable=False, server_default=sa.false()),
        )
        lote.add_column(
            sa.Column('created_by_user_id', sa.String(length=36), nullable=True),
        )
        lote.create_foreign_key(
            'fk_workshops_created_by_user_id_users',
            'users',
            ['created_by_user_id'],
            ['id'],
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('workshops') as lote:
        lote.drop_constraint('fk_workshops_created_by_user_id_users', type_='foreignkey')
        lote.drop_column('created_by_user_id')
        lote.drop_column('internal')
