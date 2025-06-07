# src/handlers/produto_handler.py
"""Produto (Product) Lambda handlers."""

import os
from datetime import datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from utils.lambda_decorators import (
    lambda_handler,
    with_database,
    require_auth,
    validate_request_body,
    success_response,
    created_response,
    LambdaException,
)
from produto.application.services.produto_application_service import ProdutoApplicationService
from produto.application.dto.produto_dto import (
    ProdutoCreateDTO,
    ProdutoUpdateDTO,
    ProdutoSearchDTO,
)
from shared.domain.exceptions.base import ValidationException, BusinessRuleException

logger = structlog.get_logger()


# === PRODUCT CRUD HANDLERS ===

@lambda_handler
@with_database
@require_auth(permissions=["produto:create"])
@validate_request_body(ProdutoCreateDTO)
async def create_product_handler(
    event,
    context,
    body,
    path_params,
    query_params,
    db: AsyncSession,
    user_info: dict,
    dto: ProdutoCreateDTO,
):
    """Handler for creating new product."""
    try:
        service = ProdutoApplicationService(db)
        product_response = await service.create_product(dto)
        return created_response(product_response.dict())

    except ValidationException as e:
        raise LambdaException(400, e.message)
    except BusinessRuleException as e:
        raise LambdaException(409, e.message)
    except Exception as e:
        logger.error("Create product error", error=str(e))
        raise LambdaException(500, "Internal server error")


@lambda_handler
@with_database
@require_auth(permissions=["produto:read"])
async def get_product_handler(
    event,
    context,
    body,
    path_params,
    query_params,
    db: AsyncSession,
    user_info: dict,
):
    """Handler for getting product by ID."""
    product_id = path_params.get("product_id")
    if not product_id:
        raise LambdaException(400, "product_id is required")

    try:
        product_uuid = UUID(product_id)
    except ValueError:
        raise LambdaException(400, "Invalid product_id format")

    try:
        service = ProdutoApplicationService(db)
        product = await service.get_product_by_id(product_uuid)
        if not product:
            raise LambdaException(404, f"Product not found: {product_id}")
        return success_response(product.dict())

    except LambdaException:
        raise
    except Exception as e:
        logger.error("Get product error", product_id=product_id, error=str(e))
        raise LambdaException(500, "Internal server error")


@lambda_handler
@with_database
@require_auth(permissions=["produto:read"])
async def get_product_by_sku_handler(
    event,
    context,
    body,
    path_params,
    query_params,
    db: AsyncSession,
    user_info: dict,
):
    """Handler for getting product by SKU."""
    sku = path_params.get("sku")
    if not sku:
        raise LambdaException(400, "sku is required")

    try:
        service = ProdutoApplicationService(db)
        product = await service.get_product_by_sku(sku)
        if not product:
            raise LambdaException(404, f"Product not found with SKU: {sku}")
        return success_response(product.dict())

    except LambdaException:
        raise
    except Exception as e:
        logger.error("Get product by SKU error", sku=sku, error=str(e))
        raise LambdaException(500, "Internal server error")


@lambda_handler
@with_database
@require_auth(permissions=["produto:read"])
async def list_products_handler(
    event,
    context,
    body,
    path_params,
    query_params,
    db: AsyncSession,
    user_info: dict,
):
    """Handler for listing products with pagination."""
    try:
        skip = int(query_params.get("skip", 0))
        limit = int(query_params.get("limit", 100))
    except ValueError:
        raise LambdaException(400, "skip and limit must be integers")

    if skip < 0:
        raise LambdaException(400, "skip must be >= 0")
    if limit < 1 or limit > 1000:
        raise LambdaException(400, "limit must be between 1 and 1000")

    try:
        service = ProdutoApplicationService(db)
        products_list = await service.get_products(skip, limit)
        return success_response(products_list.dict())

    except LambdaException:
        raise
    except Exception as e:
        logger.error("List products error", error=str(e))
        raise LambdaException(500, "Internal server error")


@lambda_handler
@with_database
@require_auth(permissions=["produto:update"])
@validate_request_body(ProdutoUpdateDTO)
async def update_product_handler(
    event,
    context,
    body,
    path_params,
    query_params,
    db: AsyncSession,
    user_info: dict,
    dto: ProdutoUpdateDTO,
):
    """Handler for updating product."""
    product_id = path_params.get("product_id")
    if not product_id:
        raise LambdaException(400, "product_id is required")

    try:
        product_uuid = UUID(product_id)
    except ValueError:
        raise LambdaException(400, "Invalid product_id format")

    try:
        service = ProdutoApplicationService(db)
        product = await service.update_product(product_uuid, dto)
        if not product:
            raise LambdaException(404, f"Product not found: {product_id}")
        return success_response(product.dict())

    except ValidationException as e:
        raise LambdaException(400, e.message)
    except BusinessRuleException as e:
        raise LambdaException(409, e.message)
    except LambdaException:
        raise
    except Exception as e:
        logger.error("Update product error", product_id=product_id, error=str(e))
        raise LambdaException(500, "Internal server error")


@lambda_handler
@with_database
@require_auth(permissions=["produto:delete"])
async def delete_product_handler(
    event,
    context,
    body,
    path_params,
    query_params,
    db: AsyncSession,
    user_info: dict,
):
    """Handler for deleting product."""
    product_id = path_params.get("product_id")
    if not product_id:
        raise LambdaException(400, "product_id is required")

    try:
        product_uuid = UUID(product_id)
    except ValueError:
        raise LambdaException(400, "Invalid product_id format")

    try:
        service = ProdutoApplicationService(db)
        success = await service.delete_product(product_uuid)
        if not success:
            raise LambdaException(404, f"Product not found: {product_id}")
        return success_response({"message": "Product deleted successfully"})

    except LambdaException:
        raise
    except Exception as e:
        logger.error("Delete product error", product_id=product_id, error=str(e))
        raise LambdaException(500, "Internal server error")


@lambda_handler
@with_database
@require_auth(permissions=["produto:search"])
@validate_request_body(ProdutoSearchDTO)
async def search_products_handler(
    event,
    context,
    body,
    path_params,
    query_params,
    db: AsyncSession,
    user_info: dict,
    dto: ProdutoSearchDTO,
):
    """Handler for searching products."""
    try:
        skip = int(query_params.get("skip", 0))
        limit = int(query_params.get("limit", 100))
    except ValueError:
        raise LambdaException(400, "skip and limit must be integers")

    if skip < 0:
        raise LambdaException(400, "skip must be >= 0")
    if limit < 1 or limit > 1000:
        raise LambdaException(400, "limit must be between 1 and 1000")

    try:
        service = ProdutoApplicationService(db)
        search_results = await service.search_products(dto, skip, limit)
        return success_response(search_results.dict())

    except ValidationException as e:
        raise LambdaException(400, e.message)
    except LambdaException:
        raise
    except Exception as e:
        logger.error("Search products error", error=str(e))
        raise LambdaException(500, "Internal server error")


@lambda_handler
@with_database
@require_auth(permissions=["produto:read"])
async def get_products_by_category_handler(
    event,
    context,
    body,
    path_params,
    query_params,
    db: AsyncSession,
    user_info: dict,
):
    """Handler for getting products by category."""
    categoria = path_params.get("categoria")
    if not categoria:
        raise LambdaException(400, "categoria is required")

    try:
        skip = int(query_params.get("skip", 0))
        limit = int(query_params.get("limit", 100))
    except ValueError:
        raise LambdaException(400, "skip and limit must be integers")

    if skip < 0:
        raise LambdaException(400, "skip must be >= 0")
    if limit < 1 or limit > 1000:
        raise LambdaException(400, "limit must be between 1 and 1000")

    try:
        service = ProdutoApplicationService(db)
        products_list = await service.get_products_by_category(categoria, skip, limit)
        return success_response(products_list.dict())

    except LambdaException:
        raise
    except Exception as e:
        logger.error("Get products by category error", categoria=categoria, error=str(e))
        raise LambdaException(500, "Internal server error")


# === UTILITY HANDLER ===

@lambda_handler
async def health_check_handler(event, context, body, path_params, query_params):
    """Health check endpoint."""
    return success_response({
        "status": "healthy",
        "service": "produto-service",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "timestamp": datetime.utcnow().isoformat()
    })
