# src/inventory/application/dto/produto_dto.py
"""Product DTOs."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import Field, validator

from src.shared.application.dto.base import BaseDTO, CreateDTO, UpdateDTO, ResponseDTO


class ProdutoCreateDTO(CreateDTO):
    """DTO for creating products."""
    sku: str = Field(..., min_length=1, max_length=50, description="Product SKU")
    nome: str = Field(..., min_length=1, max_length=255, description="Product name")
    descricao: str = Field(default="", max_length=1000, description="Product description")
    categoria: str = Field(..., min_length=1, max_length=100, description="Product category")
    unidade_medida: str = Field(..., description="Unit of measure (UN, KG, L, etc.)")
    nivel_minimo: int = Field(default=0, ge=0, description="Minimum stock level")
    ativo: bool = Field(default=True, description="Product active status")
    
    @validator('sku')
    def validate_sku(cls, v):
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('SKU must contain only letters, numbers, hyphens and underscores')
        return v.upper()
    
    @validator('unidade_medida')
    def validate_unit(cls, v):
        valid_units = ['UN', 'KG', 'G', 'L', 'ML', 'M', 'CM', 'M2', 'M3', 'CX', 'PCT', 'FD']
        if v.upper() not in valid_units:
            raise ValueError(f'Invalid unit. Valid units: {", ".join(valid_units)}')
        return v.upper()


class ProdutoUpdateDTO(UpdateDTO):
    """DTO for updating products."""
    nome: Optional[str] = Field(None, min_length=1, max_length=255)
    descricao: Optional[str] = Field(None, max_length=1000)
    categoria: Optional[str] = Field(None, min_length=1, max_length=100)
    nivel_minimo: Optional[int] = Field(None, ge=0)
    ativo: Optional[bool] = None


class ProdutoResponseDTO(ResponseDTO):
    """DTO for product responses."""
    sku: str
    nome: str
    descricao: str
    categoria: str
    unidade_medida: str
    nivel_minimo: int
    ativo: bool


class ProdutoListResponseDTO(BaseDTO):
    """DTO for product list responses."""
    produtos: List[ProdutoResponseDTO]
    total: int
    page: int
    page_size: int


class ProdutoSearchDTO(BaseDTO):
    """DTO for product search."""
    nome: Optional[str] = Field(None, min_length=1)
    categoria: Optional[str] = Field(None, min_length=1)
    ativo: Optional[bool] = None
    sku: Optional[str] = Field(None, min_length=1)