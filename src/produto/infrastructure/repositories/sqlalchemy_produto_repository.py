# src/inventory/infrastructure/repositories/sqlalchemy_produto_repository.py
"""SQLAlchemy implementation of ProdutoRepository."""

from typing import List, Optional
from uuid import UUID

import structlog
from sqlalchemy import and_, func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.produto.domain.entities.produto import Produto
from src.produto.domain.repositories.produto_repository import ProdutoRepository
from src.produto.domain.value_objects.sku import SKU
from src.produto.domain.value_objects.unidade_medida import UnidadeMedida
from src.produto.infrastructure.models.produto_model import ProdutoModel

logger = structlog.get_logger()


class SqlAlchemyProdutoRepository(ProdutoRepository):
    """SQLAlchemy implementation of ProdutoRepository."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db)
    
    async def get_by_id(self, id: UUID) -> Optional[Produto]:
        """Get product by ID."""
        try:
            query = select(ProdutoModel).where(ProdutoModel.id == id)
            result = await self.db.execute(query)
            model = result.scalar_one_or_none()
            
            if model is None:
                return None
            
            return self._model_to_entity(model)
            
        except Exception as e:
            logger.error("Error getting product by ID", product_id=str(id), error=str(e))
            raise
    
    async def get_by_sku(self, sku: SKU | str) -> Optional[Produto]:
        """Get product by SKU."""
        try:
            sku_str = sku.codigo if isinstance(sku, SKU) else sku
            
            query = select(ProdutoModel).where(ProdutoModel.sku == sku_str)
            result = await self.db.execute(query)
            model = result.scalar_one_or_none()
            
            if model is None:
                return None
            
            return self._model_to_entity(model)
            
        except Exception as e:
            logger.error("Error getting product by SKU", sku=str(sku), error=str(e))
            raise
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Produto]:
        """Get all products with pagination."""
        try:
            query = (
                select(ProdutoModel)
                .offset(skip)
                .limit(limit)
                .order_by(ProdutoModel.created_at.desc())
            )
            result = await self.db.execute(query)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models]
            
        except Exception as e:
            logger.error("Error getting all products", skip=skip, limit=limit, error=str(e))
            raise
    
    async def get_by_category(self, categoria: str, skip: int = 0, limit: int = 100) -> List[Produto]:
        """Get products by category."""
        try:
            query = (
                select(ProdutoModel)
                .where(ProdutoModel.categoria == categoria)
                .offset(skip)
                .limit(limit)
                .order_by(ProdutoModel.nome)
            )
            result = await self.db.execute(query)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models]
            
        except Exception as e:
            logger.error("Error getting products by category", categoria=categoria, error=str(e))
            raise
    
    async def get_active_products(self, skip: int = 0, limit: int = 100) -> List[Produto]:
        """Get active products."""
        try:
            query = (
                select(ProdutoModel)
                .where(ProdutoModel.ativo == True)
                .offset(skip)
                .limit(limit)
                .order_by(ProdutoModel.nome)
            )
            result = await self.db.execute(query)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models]
            
        except Exception as e:
            logger.error("Error getting active products", skip=skip, limit=limit, error=str(e))
            raise
    
    async def search_by_name(self, name: str, skip: int = 0, limit: int = 100) -> List[Produto]:
        """Search products by name."""
        try:
            search_term = f"%{name.lower()}%"
            
            query = (
                select(ProdutoModel)
                .where(
                    or_(
                        func.lower(ProdutoModel.nome).like(search_term),
                        func.lower(ProdutoModel.descricao).like(search_term)
                    )
                )
                .offset(skip)
                .limit(limit)
                .order_by(ProdutoModel.nome)
            )
            result = await self.db.execute(query)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models]
            
        except Exception as e:
            logger.error("Error searching products by name", name=name, error=str(e))
            raise
    
    async def create(self, entity: Produto) -> Produto:
        """Create new product."""
        try:
            model = self._entity_to_model(entity)
            self.db.add(model)
            await self.db.flush()
            await self.db.refresh(model)
            
            return self._model_to_entity(model)
            
        except Exception as e:
            logger.error("Error creating product", sku=entity.sku.codigo, error=str(e))
            await self.db.rollback()
            raise
    
    async def update(self, entity: Produto) -> Produto:
        """Update existing product."""
        try:
            query = select(ProdutoModel).where(ProdutoModel.id == entity.id)
            result = await self.db.execute(query)
            model = result.scalar_one_or_none()
            
            if model is None:
                raise ValueError(f"Product not found: {entity.id}")
            
            # Update fields
            model.sku = entity.sku.codigo
            model.nome = entity.nome
            model.descricao = entity.descricao
            model.categoria = entity.categoria
            model.unidade_medida = entity.unidade_medida.codigo
            model.nivel_minimo = entity.nivel_minimo
            model.ativo = entity.ativo
            model.updated_at = entity.updated_at
            
            await self.db.flush()
            await self.db.refresh(model)
            
            logger.info("Product updated", product_id=str(model.id), sku=model.sku)
            return self._model_to_entity(model)
            
        except Exception as e:
            logger.error("Error updating product", product_id=str(entity.id), error=str(e))
            await self.db.rollback()
            raise
    
    async def delete(self, id: UUID) -> bool:
        """Delete product by ID."""
        try:
            query = select(ProdutoModel).where(ProdutoModel.id == id)
            result = await self.db.execute(query)
            model = result.scalar_one_or_none()
            
            if model is None:
                return False
            
            await self.db.delete(model)
            await self.db.flush()
            
            logger.info("Product deleted", product_id=str(id))
            return True
            
        except Exception as e:
            logger.error("Error deleting product", product_id=str(id), error=str(e))
            await self.db.rollback()
            raise
    
    async def count(self) -> int:
        """Count total products."""
        try:
            query = select(func.count(ProdutoModel.id))
            result = await self.db.execute(query)
            return result.scalar_one()
            
        except Exception as e:
            logger.error("Error counting products", error=str(e))
            raise
    
    async def sku_exists(self, sku: SKU | str) -> bool:
        """Check if SKU already exists."""
        try:
            sku_str = sku.codigo if isinstance(sku, SKU) else sku
            
            query = select(func.count(ProdutoModel.id)).where(ProdutoModel.sku == sku_str)
            result = await self.db.execute(query)
            count = result.scalar_one()
            
            return count > 0
            
        except Exception as e:
            logger.error("Error checking SKU existence", sku=str(sku), error=str(e))
            raise
    
    def _entity_to_model(self, entity: Produto) -> ProdutoModel:
        """Convert entity to SQLAlchemy model."""
        return ProdutoModel(
            id=entity.id,
            sku=entity.sku.codigo,
            nome=entity.nome,
            descricao=entity.descricao,
            categoria=entity.categoria,
            unidade_medida=entity.unidade_medida.codigo,
            nivel_minimo=entity.nivel_minimo,
            ativo=entity.ativo,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
    
    def _model_to_entity(self, model: ProdutoModel) -> Produto:
        """Convert SQLAlchemy model to entity."""
        entity = Produto(
            id=model.id,
            sku=SKU(model.sku),
            nome=model.nome,
            descricao=model.descricao,
            categoria=model.categoria,
            unidade_medida=UnidadeMedida(model.unidade_medida),
            nivel_minimo=model.nivel_minimo,
            ativo=model.ativo
        )
        
        # Set timestamps manually
        entity._created_at = model.created_at
        entity._updated_at = model.updated_at
        
        return entity