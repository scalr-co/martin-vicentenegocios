"""rut del cliente

Revision ID: b7d2e4f6a8c3
Revises: a1c3f5d7b9e1
Create Date: 2026-08-10

Escrita a mano y no con autogenerate, por lo mismo de siempre: desarrollo es SQLite y
produccion es Postgres.

Nullable y sin default: el rut es opcional -la mayoria de los autos entran al taller sin
que nadie lo pida- y las fichas que ya existen no lo tienen. Sin restriccion de unicidad
a proposito: el telefono ya evita la ficha duplicada, y una familia puede traer dos autos
con el rut del mismo pagador.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b7d2e4f6a8c3'
down_revision: Union[str, Sequence[str], None] = 'a1c3f5d7b9e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('clients', sa.Column('rut', sa.String(length=12), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('clients', 'rut')
