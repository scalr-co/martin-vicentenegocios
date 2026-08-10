"""archivar clientes y ordenes

Revision ID: c4e8a1b2d6f7
Revises: b7d2e4f6a8c3
Create Date: 2026-08-10

Escrita a mano y no con autogenerate, por lo mismo de siempre: desarrollo es SQLite y
produccion es Postgres.

`deleted_at` es la marca de archivado. Nulo -el valor de todas las filas que ya existen-
significa vigente, que es lo correcto: nada de lo que hay hoy esta archivado. Se guarda la
fecha y no un booleano porque saber cuando se archivo algo es justo lo que se pregunta
cuando un taller reclama que le falta una ficha.

No se borra de verdad a proposito: del cliente cuelgan sus vehiculos, sus ordenes y sus
avisos, y de la orden cuelgan los avisos que ya salieron por WhatsApp.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c4e8a1b2d6f7'
down_revision: Union[str, Sequence[str], None] = 'b7d2e4f6a8c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('clients', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('orders', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('orders', 'deleted_at')
    op.drop_column('clients', 'deleted_at')
