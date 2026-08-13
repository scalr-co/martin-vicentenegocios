"""plan del taller, para que el tope de mecanicos viva en el servidor

Revision ID: b3d9f7c1a5e2
Revises: a7c3e9f1d4b2
Create Date: 2026-08-13

Con server_default para los talleres que ya existen: todos quedan en 'basico', que es lo
que son. Es la columna que decide cuantos mecanicos puede tener cada uno, asi que no
puede admitir nulos -un taller sin plan no se sabe que puede hacer-.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b3d9f7c1a5e2'
down_revision: Union[str, Sequence[str], None] = 'a7c3e9f1d4b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('workshops') as lote:
        lote.add_column(
            sa.Column('plan', sa.String(length=10), nullable=False, server_default='basico')
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('workshops') as lote:
        lote.drop_column('plan')
