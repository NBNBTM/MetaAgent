"""
数据分析模块初始化
"""

from .data_analysis_module import DataAnalysisModule

# 导出模块类
__all__ = ['DataAnalysisModule']

# 为了兼容性，也导出模块类作为模块级别的变量
DataAnalysis = DataAnalysisModule

# 确保模块类可以直接从包中导入
Module = DataAnalysisModule