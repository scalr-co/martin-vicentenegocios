"""fecha de baja en workshops, para dar de baja un taller sin borrarlo

Revision ID: a7c3e9f1d4b2
Revises: f2a9c4d8e1b3
Create Date: 2026-08-11

Nulo -el valor de todos los talleres que ya existen- significa vigente, que es lo
correcto: ninguno de los que estan hoy se ha dado de baja.

No se borra de verdad a proposito: del taller cuelgan sus usuarios, sus clientes, sus
vehiculos, sus ordenes y los avisos que ya salieron por WhatsApp. Un taller que deja de
pagar tiene que poder volver y encontrar su historial donde lo dejo.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a7c3e9f1d4b2'
down_revision: Union[str, Sequence[str], None] = 'f2a9c4d8e1b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('workshops') as lote:
        lote.add_column(sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('workshops') as lote:
        lote.drop_column('deleted_at')
