"""insert_initial_user

Revision ID: 121ccdd6005b
Revises: eeb5c4b9a840
Create Date: 2026-05-21 21:23:13.214051

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '121ccdd6005b'
down_revision: Union[str, Sequence[str], None] = 'eeb5c4b9a840'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    import os
    from dotenv import load_dotenv
    from sqlalchemy.sql import table, column
    
    # Carregar variáveis de ambiente do arquivo .env
    load_dotenv()
    
    user_name = os.getenv("USER_NAME")
    cpf = os.getenv("USER_CPF")
    email = os.getenv("USER_EMAIL")
    phonenumber = os.getenv("USER_PHONENUMBER")
    zip_code = os.getenv("USER_ZIP_CODE")
    city = os.getenv("USER_CITY")
    state = os.getenv("USER_STATE")
    
    if not all([user_name, cpf, phonenumber, zip_code, city, state]):
        print("Warning: Variáveis de ambiente para o usuário inicial não estão totalmente configuradas no .env. Pulando inserção.")
        return
        
    users_table = table(
        'users',
        column('user_name', sa.String),
        column('cpf', sa.String),
        column('email', sa.String),
        column('phonenumber', sa.String),
        column('zip_code', sa.String),
        column('city', sa.String),
        column('state', sa.String),
        column('active', sa.Boolean)
    )
    
    op.bulk_insert(
        users_table,
        [
            {
                'user_name': user_name,
                'cpf': cpf,
                'email': email,
                'phonenumber': phonenumber,
                'zip_code': zip_code,
                'city': city,
                'state': state,
                'active': True
            }
        ]
    )


def downgrade() -> None:
    """Downgrade schema."""
    import os
    from dotenv import load_dotenv
    from sqlalchemy.sql import table, column
    
    # Carregar variáveis de ambiente do arquivo .env
    load_dotenv()
    
    user_name = os.getenv("USER_NAME")
    if not user_name:
        print("Warning: USER_NAME não está definido no .env. Pulando remoção no downgrade.")
        return
        
    users_table = table(
        'users',
        column('user_name', sa.String)
    )
    
    op.execute(
        users_table.delete().where(users_table.c.user_name == user_name)
    )

