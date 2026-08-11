"""version de sesion en users, para poder cerrar sesiones abiertas

Revision ID: f2a9c4d8e1b3
Revises: d5f1a3c7e2b9
Create Date: 2026-08-11

Con server_default="1" para las cuentas que ya existen: todas parten en la version 1, la
misma con la que se emiten sus tokens desde ahora.

Los tokens emitidos antes de este cambio no traen la version adentro y dejan de servir:
todos los que esten con la sesion abierta tienen que entrar una vez mas.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f2a9c4d8e1b3'
down_revision: Union[str, Sequence[str], None] = 'd5f1a3c7e2b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('users') as lote:
        lote.add_column(
            sa.Column('token_version', sa.Integer(), nullable=False, server_default='1'),
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('users') as lote:
        lote.drop_column('token_version')
