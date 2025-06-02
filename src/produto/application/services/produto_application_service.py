# src/inventory/application/services/produto_application_service.py
"""Product application service."""

from typing import List, Optional
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.application.services.base import BaseApplicationService
from src.shared.domain.exceptions.base import ValidationException, BusinessRuleException
from src.produto.domain.entities.produto import Produto
from src.produto.domain.value_objects.sku import SKU
from src.produto.domain.value_objects.unidade_medida import UnidadeMedida
from src.produto.infrastructure.repositories.sqlalchemy_produto_repository import SqlAlchemyProdutoRepository
from src.produto.application.dto.produto_dto import (
    ProdutoCreateDTO,
    ProdutoUpdateDTO,
    ProdutoResponseDTO,
    ProdutoListResponseDTO,
    ProdutoSearchDTO
)

logger = structlog.get_logger()


class ProdutoApplicationService(BaseApplicationService[Produto]):
    """Product application service."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.produto_repository = SqlAlchemyProdutoRepository(db)
    
    async def create_product(self, create_dto: ProdutoCreateDTO) -> ProdutoResponseDTO:
        """Create new product."""
        try:
            # Check if SKU already exists
            if await self.produto_repository.sku_exists(create_dto.sku):
                raise BusinessRuleException(f"SKU already exists: {create_dto.sku}")
            
            # Create product entity
            product = Produto(
                sku=SKU(create_dto.sku),
                nome=create_dto.nome,
                descricao=create_dto.descricao,
                categoria=create_dto.categoria,
                unidade_medida=UnidadeMedida(create_dto.unidade_medida),
                nivel_minimo=create_dto.nivel_minimo,
                ativo=create_dto.ativo
            )
            
            # Save to repository
            product = await self.produto_repository.create(product)
            await self.db.commit()
            
            logger.info("Product created", product_id=str(product.id), sku=product.sku.codigo)
            
            return self._entity_to_response_dto(product)
            
        except Exception as e:
            logger.error("Product creation failed", sku=create_dto.sku, error=str(e))
            await self.db.rollback()
            raise
    
    async def get_product_by_id(self, product_id: UUID) -> Optional[ProdutoResponseDTO]:
        """Get product by ID."""
        try:
            product = await self.produto_repository.get_by_id(product_id)
            
            if product is None:
                return None
            
            return self._entity_to_response_dto(product)
            
        except Exception as e:
            logger.error("Error getting product", product_id=str(product_id), error=str(e))
            raise
    
    async def get_product_by_sku(self, sku: str) -> Optional[ProdutoResponseDTO]:
        """Get product by SKU."""
        try:
            product = await self.produto_repository.get_by_sku(sku)
            
            if product is None:
                return None
            
            return self._entity_to_response_dto(product)
            
        except Exception as e:
            logger.error("Error getting product by SKU", sku=sku, error=str(e))
            raise
    
    async def get_products(self, skip: int = 0, limit: int = 100) -> ProdutoListResponseDTO:
        """Get products with pagination."""
        try:
            products = await self.produto_repository.get_all(skip, limit)
            total = await self.produto_repository.count()
            
            product_dtos = [self._entity_to_response_dto(product) for product in products]
            
            return ProdutoListResponseDTO(
                produtos=product_dtos,
                total=total,
                page=skip // limit + 1 if limit > 0 else 1,
                page_size=limit
            )
            
        except Exception as e:
            logger.error("Error getting products", skip=skip, limit=limit, error=str(e))
            raise
    
    async def search_products(self, search_dto: ProdutoSearchDTO, skip: int = 0, limit: int = 100) -> ProdutoListResponseDTO:
        """Search products."""
        try:
            products = []
            
            if search_dto.sku:
                product = await self.produto_repository.get_by_sku(search_dto.sku)
                products = [product] if product else []
            elif search_dto.nome:
                products = await self.produto_repository.search_by_name(search_dto.nome, skip, limit)
            elif search_dto.categoria:
                products = await self.produto_repository.get_by_category(search_dto.categoria, skip, limit)
            else:
                if search_dto.ativo is not None and search_dto.ativo:
                    products = await self.produto_repository.get_active_products(skip, limit)
                else:
                    products = await self.produto_repository.get_all(skip, limit)
            
            # Apply additional filters
            if search_dto.ativo is not None:
                products = [p for p in products if p.ativo == search_dto.ativo]
            
            product_dtos = [self._entity_to_response_dto(product) for product in products]
            
            return ProdutoListResponseDTO(
                produtos=product_dtos,
                total=len(product_dtos),
                page=skip // limit + 1 if limit > 0 else 1,
                page_size=limit
            )
            
        except Exception as e:
            logger.error("Error searching products", error=str(e))
            raise
    
    async def update_product(
        self,
        product_id: UUID,
        update_dto: ProdutoUpdateDTO
    ) -> Optional[ProdutoResponseDTO]:
        """Update product."""
        try:
            product = await self.produto_repository.get_by_id(product_id)
            
            if product is None:
                return None
            
            # Update fields
            if update_dto.nome is not None or update_dto.descricao is not None or update_dto.categoria is not None:
                product.update_info(
                    nome=update_dto.nome,
                    descricao=update_dto.descricao,
                    categoria=update_dto.categoria
                )
            
            if update_dto.nivel_minimo is not None:
                product.update_minimum_level(update_dto.nivel_minimo)
            
            if update_dto.ativo is not None:
                if update_dto.ativo:
                    product.activate()
                else:
                    product.deactivate()
            
            # Save changes
            product = await self.produto_repository.update(product)
            await self.db.commit()
            
            logger.info("Product updated", product_id=str(product_id))
            
            return self._entity_to_response_dto(product)
            
        except Exception as e:
            logger.error("Product update failed", product_id=str(product_id), error=str(e))
            await self.db.rollback()
            raise
    
    async def delete_product(self, product_id: UUID) -> bool:
        """Delete product."""
        try:
            success = await self.produto_repository.delete(product_id)
            
            if success:
                await self.db.commit()
                logger.info("Product deleted", product_id=str(product_id))
            
            return success
            
        except Exception as e:
            logger.error("Product deletion failed", product_id=str(product_id), error=str(e))
            await self.db.rollback()
            raise
    
    async def get_products_by_category(self, categoria: str, skip: int = 0, limit: int = 100) -> ProdutoListResponseDTO:
        """Get products by category."""
        try:
            products = await self.produto_repository.get_by_category(categoria, skip, limit)
            
            product_dtos = [self._entity_to_response_dto(product) for product in products]
            
            return ProdutoListResponseDTO(
                produtos=product_dtos,
                total=len(product_dtos),
                page=skip // limit + 1 if limit > 0 else 1,
                page_size=limit
            )
            
        except Exception as e:
            logger.error("Error getting products by category", categoria=categoria, error=str(e))
            raise
    
    def _entity_to_response_dto(self, product: Produto) -> ProdutoResponseDTO:
        """Convert entity to response DTO."""
        return ProdutoResponseDTO(
            id=product.id,
            sku=product.sku.codigo,
            nome=product.nome,
            descricao=product.descricao,
            categoria=product.categoria,
            unidade_medida=product.unidade_medida.codigo,
            nivel_minimo=product.nivel_minimo,
            ativo=product.ativo,
            created_at=product.created_at,
            updated_at=product.updated_at
        )