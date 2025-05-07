from enum import Enum
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.interfaces.payment_repository import PaymentRepository
from .sql_payment_repository import SQLPaymentRepository
from .nosql_payment_repository import NoSQLPaymentRepository


class RepositoryType(str, Enum):
    SQL = "sql"
    NOSQL = "nosql"


def get_payment_repository(
    repository_type: RepositoryType, db_session: Optional[Session] = None
) -> PaymentRepository:
    if repository_type == RepositoryType.SQL:
        if not db_session:
            raise ValueError("DB session is required for SQL repository")
        return SQLPaymentRepository(db_session)
    else:
        return NoSQLPaymentRepository()
