from core.module_interface import ModuleInterface
from .data_analysis_service import DataAnalysisService
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Union

class DataAnalysisModule(ModuleInterface):
    """
    数据分析模块
    """
    def __init__(self, config=None):
        super().__init__(config)
        self.service = DataAnalysisService()

    def get_info(self):
        """
        获取模块信息
        Returns:
            dict: 模块信息
        """
        return {
            "name": "Data Analysis",
            "version": "1.0.0",
            "description": "提供数据分析和机器学习功能",
            "supported_methods": {
                "classification": self.service.get_supported_classification_methods(),
                "clustering": self.service.get_supported_clustering_methods(),
                "dimension_reduction": self.service.get_supported_dimension_reduction_methods()
            }
        }

    def register(self, server):
        """
        向MCP服务器注册功能
        Args:
            server: FastMCP服务器实例
        """
        # 注册数据质量检查工具
        @server.tool()
        def check_data_quality(file_path: str) -> dict:
            """
            检查数据质量
            Args:
                file_path: 数据文件路径
            Returns:
                dict: 数据质量检查结果
            """
            return self.service.check_data_quality(file_path=file_path)

        # 注册缺失值处理工具
        @server.tool()
        def handle_missing_values(
            file_path: str,
            strategy: str = 'mean',
            columns: Optional[Union[str, List[str]]] = None,
            output_path: Optional[str] = None,
            custom_value: Optional[float] = None
        ) -> dict:
            """
            处理缺失值
            Args:
                file_path: 数据文件路径
                strategy: 处理策略，支持 'mean', 'median', 'mode', 'drop', 'custom'
                columns: 要处理的列名列表，可以是字符串形式的列表或实际的列表，如果为None则处理所有列
                output_path: 输出文件路径，如果为None则自动在原文件名后添加_filled
                custom_value: 当strategy为'custom'时，用于填充的指定数值
            Returns:
                dict: 处理结果
            """
            return self.service.handle_missing_values(
                file_path=file_path,
                strategy=strategy,
                columns=columns,
                output_path=output_path,
                custom_value=custom_value
            )

        # 注册数据标准化工具
        @server.tool()
        def standardize_data(
            file_path: str,
            columns: Optional[Union[str, List[str]]] = None,
            method: str = 'standard',
            missing_strategy: str = 'mean',
            custom_value: Optional[float] = None,
            output_path: Optional[str] = None
        ) -> dict:
            """
            处理缺失值并标准化数据
            Args:
                file_path: 数据文件路径
                columns: 要标准化的列名列表，可以是字符串形式的列表或实际的列表
                method: 标准化方法，支持 'standard'(Z-score标准化), 'minmax'(0-1标准化), 'robust'(稳健标准化)
                missing_strategy: 缺失值处理策略，支持 'mean', 'median', 'mode', 'drop', 'custom'
                custom_value: 当missing_strategy为'custom'时，用于填充的指定数值
                output_path: 输出文件路径，如果为None则自动在原文件名后添加_sted
            Returns:
                dict: 标准化结果
            """
            return self.service.standardize_data(
                file_path=file_path,
                columns=columns,
                method=method,
                missing_strategy=missing_strategy,
                custom_value=custom_value,
                output_path=output_path
            )

        # 注册分类预测工具
        @server.tool()
        def perform_classification(
            file_path: str,
            columns: Optional[Union[str, List[str]]] = None,
            target_column: str = 'target',
            method: Optional[str] = None,
            test_size: float = 0.2,
            random_state: int = 42
        ) -> dict:
            """
            执行分类预测
            Args:
                file_path: 数据文件路径
                columns: 要分析的列名列表，可以是字符串形式的列表或实际的列表
                target_column: 目标列名
                method: 分类方法，支持的方法可以通过get_info()查询
                test_size: 测试集比例
                random_state: 随机种子
            Returns:
                dict: 分类结果
            """
            method = method or self.config.get('default_classification_method', 'random_forest')
            return self.service.perform_classification(
                file_path=file_path,
                columns=columns,
                target_column=target_column,
                method=method,
                test_size=test_size,
                random_state=random_state
            )

        # 注册聚类分析工具
        @server.tool()
        def perform_clustering(
            file_path: str,
            columns: Optional[Union[str, List[str]]] = None,
            method: Optional[str] = None,
            n_clusters: int = 3
        ) -> dict:
            """
            执行聚类分析
            Args:
                file_path: 数据文件路径
                columns: 要分析的列名列表，可以是字符串形式的列表或实际的列表
                method: 聚类方法，支持的方法可以通过get_info()查询
                n_clusters: 聚类数量
            Returns:
                dict: 聚类结果
            """
            method = method or self.config.get('default_clustering_method', 'kmeans')
            return self.service.perform_clustering(
                file_path=file_path,
                columns=columns,
                method=method,
                n_clusters=n_clusters
            )

        # 注册降维分析工具
        @server.tool()
        def perform_dimension_reduction(
            file_path: str,
            columns: Optional[Union[str, List[str]]] = None,
            method: Optional[str] = None,
            n_components: int = 2
        ) -> dict:
            """
            执行降维分析
            Args:
                file_path: 数据文件路径
                columns: 要分析的列名列表，可以是字符串形式的列表或实际的列表
                method: 降维方法，支持的方法可以通过get_info()查询
                n_components: 降维后的维度
            Returns:
                dict: 降维结果
            """
            method = method or self.config.get('default_dimension_reduction_method', 'pca')
            return self.service.perform_dimension_reduction(
                file_path=file_path,
                columns=columns,
                method=method,
                n_components=n_components
            )
