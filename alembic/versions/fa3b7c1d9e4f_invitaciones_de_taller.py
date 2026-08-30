"""invitaciones privadas para trasladar mecanicos entre talleres

Revision ID: fa3b7c1d9e4f
Revises: c8e2b4a6d9f1
Create Date: 2026-08-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "fa3b7c1d9e4f"
down_revision: Union[str, Sequence[str], None] = "c8e2b4a6d9f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workshop_invitations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("workshop_id", sa.String(length=36), nullable=False),
        sa.Column("created_by_user_id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["workshop_id"], ["workshops.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_workshop_invitations_workshop_id", "workshop_invitations", ["workshop_id"])
    op.create_index("ix_workshop_invitations_created_by_user_id", "workshop_invitations", ["created_by_user_id"])
    op.create_index("ix_workshop_invitations_email", "workshop_invitations", ["email"])
    op.create_index("ix_workshop_invitations_token_hash", "workshop_invitations", ["token_hash"])


def downgrade() -> None:
    op.drop_index("ix_workshop_invitations_token_hash", table_name="workshop_invitations")
    op.drop_index("ix_workshop_invitations_email", table_name="workshop_invitations")
    op.drop_index("ix_workshop_invitations_created_by_user_id", table_name="workshop_invitations")
    op.drop_index("ix_workshop_invitations_workshop_id", table_name="workshop_invitations")
    op.drop_table("workshop_invitations")
