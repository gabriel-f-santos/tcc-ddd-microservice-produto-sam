# src/inventory/infrastructure/models/produto_model.py
"""SQLAlchemy model for Produto."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, Column, DateTime, String, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func

from src.shared.infrastructure.database.connection import Base


class ProdutoModel(Base):
    """SQLAlchemy model for Produto entity."""
    
    __tablename__ = "produtos"
    __table_args__ = {"schema": "product"}
    
    id = Column(PGUUID(as_uuid=True), primary_key=True)
    sku = Column(String(50), unique=True, nullable=False, index=True)
    nome = Column(String(255), nullable=False)
    descricao = Column(String(1000), nullable=False, default="")
    categoria = Column(String(100), nullable=False, index=True)
    unidade_medida = Column(String(10), nullable=False)
    nivel_minimo = Column(Integer, nullable=False, default=0)
    ativo = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<ProdutoModel(id={self.id}, sku={self.sku}, nome={self.nome})>"