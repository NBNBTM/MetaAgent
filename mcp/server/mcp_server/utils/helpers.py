"""
工具函数
"""

import importlib
import os
import sys
from pathlib import Path

def ensure_directory(path):
    """
    确保目录存在

    Args:
        path: 目录路径

    Returns:
        Path: 实际创建的目录路径
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def import_module_from_path(module_name, module_path):
    """
    从指定路径导入模块

    Args:
        module_name: 模块名称
        module_path: 模块路径

    Returns:
        Module: 导入的模块
    """
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None:
        return None

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def format_error(e):
    """
    格式化错误信息

    Args:
        e: 异常对象

    Returns:
        str: 格式化后的错误信息
    """
    return f"{type(e).__name__}: {str(e)}"