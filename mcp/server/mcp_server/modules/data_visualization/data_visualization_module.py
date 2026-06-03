from core.module_interface import ModuleInterface
from .data_visualization_service import DataVisualizationService
from typing import List, Dict, Optional, Union
import os

class DataVisualizationModule(ModuleInterface):
    """
    数据可视化模块
    """
    def __init__(self, config=None):
        super().__init__(config)
        self.service = DataVisualizationService()

    def get_info(self):
        """
        获取模块信息
        Returns:
            dict: 模块信息
        """
        return {
            "name": "Data Visualization",
            "version": "1.0.0",
            "description": "提供基于matplotlib的数据可视化功能",
            "author": "Chenyu Tian",
            "email": "cytian9@gmail.com",
            "supported_methods": {
                "plot_types": self.service.get_supported_plot_types()
            }
        }

    def register(self, server):
        """
        向MCP服务器注册功能
        Args:
            server: FastMCP服务器实例
        """
        # 注册数据检查工具
        @server.tool()
        def check_visualization_data(file_path: str) -> dict:
            """
            检查数据是否适合可视化，包括数据质量、分布特征等
            Args:
                file_path: 数据文件路径
            Returns:
                dict: 数据检查结果，包括基本统计信息和可视化相关的特殊问题
            """
            return self.service.check_visualization_data(file_path=file_path)

        # 注册折线图绘制工具
        @server.tool()
        def plot_line(
            file_path: str,
            x_column: str,
            y_column: str,
            category_column: Optional[str] = None,
            title: Optional[str] = None,
            x_label: Optional[str] = None,
            y_label: Optional[str] = None,
            output_path: Optional[str] = None,
            figsize: Optional[Union[List[str], str]] = None,
            style: Optional[str] = None
        ) -> dict:
            """
            绘制折线图
            Args:
                file_path: 数据文件路径
                x_column: x轴数据列名
                y_column: y轴数据列名
                category_column: 用于分组的类别列名，如果提供则按此列分组绘制多条折线
                title: 图表标题
                x_label: x轴标签
                y_label: y轴标签
                output_path: 输出图片路径，如果为None则自动生成
                figsize: 图表大小，格式为[width, height]或"[width, height]"
                style: matplotlib样式
            Returns:
                dict: 绘图结果
            """
            if figsize is not None:
                if isinstance(figsize, str):
                    import json
                    figsize = json.loads(figsize)
                figsize = tuple(map(float, figsize))
            return self.service.plot_line(
                file_path=file_path,
                x_column=x_column,
                y_column=y_column,
                category_column=category_column,
                title=title,
                x_label=x_label,
                y_label=y_label,
                output_path=output_path,
                figsize=figsize,
                style=style
            )

        # 注册条形图绘制工具
        @server.tool()
        def plot_bar(
            file_path: str,
            x_column: str,
            y_column: str,
            title: Optional[str] = None,
            x_label: Optional[str] = None,
            y_label: Optional[str] = None,
            output_path: Optional[str] = None,
            figsize: Optional[Union[List[str], str]] = None,
            style: Optional[str] = None,
            orientation: str = 'vertical'
        ) -> dict:
            """
            绘制条形图
            Args:
                file_path: 数据文件路径
                x_column: x轴数据列名
                y_column: y轴数据列名
                title: 图表标题
                x_label: x轴标签
                y_label: y轴标签
                output_path: 输出图片路径，如果为None则自动生成
                figsize: 图表大小，格式为[width, height]或"[width, height]"
                style: matplotlib样式
                orientation: 条形图方向，'vertical'或'horizontal'
            Returns:
                dict: 绘图结果
            """
            if figsize is not None:
                if isinstance(figsize, str):
                    import json
                    figsize = json.loads(figsize)
                figsize = tuple(map(float, figsize))
            return self.service.plot_bar(
                file_path=file_path,
                x_column=x_column,
                y_column=y_column,
                title=title,
                x_label=x_label,
                y_label=y_label,
                output_path=output_path,
                figsize=figsize,
                style=style,
                orientation=orientation
            )

        # 注册散点图绘制工具
        @server.tool()
        def plot_scatter(
            file_path: str,
            x_column: str,
            y_column: str,
            title: Optional[str] = None,
            x_label: Optional[str] = None,
            y_label: Optional[str] = None,
            output_path: Optional[str] = None,
            figsize: Optional[Union[List[str], str]] = None,
            style: Optional[str] = None,
            color_column: Optional[str] = None,
            size_column: Optional[str] = None
        ) -> dict:
            """
            绘制散点图
            Args:
                file_path: 数据文件路径
                x_column: x轴数据列名
                y_column: y轴数据列名
                title: 图表标题
                x_label: x轴标签
                y_label: y轴标签
                output_path: 输出图片路径，如果为None则自动生成
                figsize: 图表大小，格式为[width, height]或"[width, height]"
                style: matplotlib样式
                color_column: 用于设置点颜色的列名
                size_column: 用于设置点大小的列名
            Returns:
                dict: 绘图结果
            """
            if figsize is not None:
                if isinstance(figsize, str):
                    import json
                    figsize = json.loads(figsize)
                figsize = tuple(map(float, figsize))
            return self.service.plot_scatter(
                file_path=file_path,
                x_column=x_column,
                y_column=y_column,
                title=title,
                x_label=x_label,
                y_label=y_label,
                output_path=output_path,
                figsize=figsize,
                style=style,
                color_column=color_column,
                size_column=size_column
            )

        # 注册饼图绘制工具
        @server.tool()
        def plot_pie(
            file_path: str,
            values_column: str,
            labels_column: str,
            title: Optional[str] = None,
            output_path: Optional[str] = None,
            figsize: Optional[Union[List[str], str]] = None,
            style: Optional[str] = None,
            autopct: Optional[str] = '%1.1f%%'
        ) -> dict:
            """
            绘制饼图
            Args:
                file_path: 数据文件路径
                values_column: 数值列名
                labels_column: 标签列名
                title: 图表标题
                output_path: 输出图片路径，如果为None则自动生成
                figsize: 图表大小，格式为[width, height]或"[width, height]"
                style: matplotlib样式
                autopct: 显示百分比的格式
            Returns:
                dict: 绘图结果
            """
            if figsize is not None:
                if isinstance(figsize, str):
                    import json
                    figsize = json.loads(figsize)
                figsize = tuple(map(float, figsize))
            return self.service.plot_pie(
                file_path=file_path,
                values_column=values_column,
                labels_column=labels_column,
                title=title,
                output_path=output_path,
                figsize=figsize,
                style=style,
                autopct=autopct
            )

        # 注册箱线图绘制工具
        @server.tool()
        def plot_box(
            file_path: str,
            columns: Union[str, List[str]],
            title: Optional[str] = None,
            x_label: Optional[str] = None,
            y_label: Optional[str] = None,
            output_path: Optional[str] = None,
            figsize: Optional[Union[List[str], str]] = None,
            style: Optional[str] = None,
            vert: bool = True
        ) -> dict:
            """
            绘制箱线图
            Args:
                file_path: 数据文件路径
                columns: 要绘制的列名，可以是单个列名或列名列表
                title: 图表标题
                x_label: x轴标签
                y_label: y轴标签
                output_path: 输出图片路径，如果为None则自动生成
                figsize: 图表大小，格式为[width, height]或"[width, height]"
                style: matplotlib样式
                vert: 是否垂直显示
            Returns:
                dict: 绘图结果
            """
            if figsize is not None:
                if isinstance(figsize, str):
                    import json
                    figsize = json.loads(figsize)
                figsize = tuple(map(float, figsize))
            return self.service.plot_box(
                file_path=file_path,
                columns=columns,
                title=title,
                x_label=x_label,
                y_label=y_label,
                output_path=output_path,
                figsize=figsize,
                style=style,
                vert=vert
            )