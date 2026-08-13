"""fecha de termino de la suspension, para que el taller vuelva solo

Revision ID: c8e2b4a6d9f1
Revises: b3d9f7c1a5e2
Create Date: 2026-08-13

Nulo -el valor de todos los talleres que ya existen- significa "sin fecha": los que estan
suspendidos hoy lo siguen estando hasta que alguien los reactive, que es exactamente como
se los suspendio. La fecha solo cambia algo en los que se suspendan de aca en adelante.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c8e2b4a6d9f1'
down_revision: Union[str, Sequence[str], None] = 'b3d9f7c1a5e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('workshops') as lote:
        lote.add_column(
            sa.Column('suspended_until', sa.DateTime(timezone=True), nullable=True)
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('workshops') as lote:
        lote.drop_column('suspended_until')
