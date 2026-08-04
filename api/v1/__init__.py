# -*- coding: utf-8 -*-
"""
===================================
API v1 模块初始化
===================================

职责：
1. 导出 v1 版本 API 的路由
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from api.v1.router import router as api_v1_router

__all__ = ["api_v1_router"]


def __getattr__(name: str) -> Any:
    """Load the aggregate router only when the application requests it."""
    if name != "api_v1_router":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from api.v1.router import router

    globals()[name] = router
    return router
