# src/inventory/domain/repositories/produto_repository.py
"""Product repository interface."""

from abc import abstractmethod
from typing import Optional, List
from uuid import UUID

from src.shared.infrastructure.repositories.base import BaseRepository
from src.produto.domain.entities.produto import Produto
from src.produto.domain.value_objects.sku import SKU


class ProdutoRepository(BaseRepository[Produto]):
    """Product repository interface."""
    
    @abstractmethod
    async def get_by_sku(self, sku: SKU | str) -> Optional[Produto]:
        """Get product by SKU."""
        pass
    
    @abstractmethod
    async def get_by_category(self, categoria: str, skip: int = 0, limit: int = 100) -> List[Produto]:
        """Get products by category."""
        pass
    
    @abstractmethod
    async def get_active_products(self, skip: int = 0, limit: int = 100) -> List[Produto]:
        """Get active products."""
        pass
    
    @abstractmethod
    async def sku_exists(self, sku: SKU | str) -> bool:
        """Check if SKU already exists."""
        pass
    
    @abstractmethod
    async def search_by_name(self, name: str, skip: int = 0, limit: int = 100) -> List[Produto]:
        """Search products by name."""
        pass