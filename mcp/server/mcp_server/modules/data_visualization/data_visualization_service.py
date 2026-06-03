import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Optional, Union
import os
from datetime import datetime
import numpy as np
import platform

class DataVisualizationService:
    """
    数据可视化服务类
    """
    def __init__(self):
        # 设置中文字体支持
        system = platform.system()
        if system == 'Darwin':  # macOS
            plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Heiti TC', 'STHeiti', 'SimHei']
        elif system == 'Windows':
            plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun']
        else:  # Linux
            plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'SimHei', 'DejaVu Sans']

        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
        plt.rcParams['font.family'] = 'sans-serif'  # 设置字体族

        # 设置字体大小
        plt.rcParams['font.size'] = 12
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['axes.labelsize'] = 12

    def get_supported_plot_types(self) -> List[str]:
        """
        获取支持的图表类型
        Returns:
            List[str]: 支持的图表类型列表
        """
        return [
            'line',      # 折线图
            'bar',       # 条形图
            'scatter',   # 散点图
            'pie',       # 饼图
            'box'        # 箱线图
        ]

    def _read_data(self, file_path: str) -> pd.DataFrame:
        """
        读取数据文件
        Args:
            file_path: 数据文件路径
        Returns:
            pd.DataFrame: 数据框
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 根据文件扩展名选择读取方法
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.csv':
            return pd.read_csv(file_path)
        elif ext in ['.xls', '.xlsx']:
            return pd.read_excel(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")

    def _generate_output_path(self, file_path: str, plot_type: str) -> str:
        """
        生成输出文件路径
        Args:
            file_path: 原始数据文件路径
            plot_type: 图表类型
        Returns:
            str: 输出文件路径
        """
        dir_name = os.path.dirname(file_path)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return os.path.join(dir_name, f"{base_name}_{plot_type}_{timestamp}.png")

    def _setup_plot(self, figsize: Optional[tuple] = None, style: Optional[str] = None):
        """
        设置图表样式
        Args:
            figsize: 图表大小
            style: matplotlib样式或'seaborn'
        """
        if style:
            if style.lower() == 'seaborn':
                sns.set_style("whitegrid")
                sns.set_context("notebook", font_scale=1.2)
            else:
                plt.style.use(style)

        # 创建新的图表并设置字体
        if figsize:
            plt.figure(figsize=figsize)
        else:
            plt.figure()

        # 显式设置字体
        system = platform.system()
        if system == 'Darwin':  # macOS
            plt.rc('font', family='Arial Unicode MS')
        elif system == 'Windows':
            plt.rc('font', family='Microsoft YaHei')
        else:  # Linux
            plt.rc('font', family='WenQuanYi Micro Hei')

    def check_visualization_data(self, file_path: str) -> Dict:
        """
        检查数据是否适合可视化，包括数据质量、分布特征等
        Args:
            file_path: 数据文件路径
        Returns:
            dict: 数据检查结果，包括基本统计信息和可视化相关的特殊问题
        """
        df = self._read_data(file_path)

        # 检查列名
        columns_info = {
            'total_columns': len(df.columns),
            'column_names': df.columns.tolist(),
            'has_empty_names': bool(df.columns.str.contains('^$').any()),
            'has_duplicate_names': bool(df.columns.duplicated().any())
        }

        # 检查缺失值
        missing_info = {
            'has_missing': bool(df.isnull().any().any()),
            'missing_columns': df.columns[df.isnull().any()].tolist(),
            'missing_counts': df.isnull().sum().to_dict(),
            'missing_percentages': (df.isnull().sum() / len(df) * 100).to_dict()
        }

        # 检查数据类型
        dtypes_info = df.dtypes.to_dict()

        # 检查数值型列的统计信息
        numeric_stats = {}
        for col in df.select_dtypes(include=[np.number]).columns:
            numeric_stats[col] = {
                'mean': float(df[col].mean()),
                'std': float(df[col].std()),
                'min': float(df[col].min()),
                'max': float(df[col].max())
            }

        # 检查分类列的统计信息
        categorical_stats = {}
        for col in df.select_dtypes(include=['object', 'category']).columns:
            value_counts = df[col].value_counts()
            categorical_stats[col] = {
                'unique_values': int(value_counts.nunique()),
                'most_common': value_counts.head(5).to_dict(),
                'has_duplicates': bool(df[col].duplicated().any())
            }

        # 检查数据可视化相关的特殊问题
        visualization_issues = {
            'potential_outliers': {},
            'skewed_distributions': {},
            'zero_variance_columns': []
        }

        # 检查数值列的异常值（使用IQR方法）
        for col in df.select_dtypes(include=[np.number]).columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = df[(df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))][col]
            if len(outliers) > 0:
                visualization_issues['potential_outliers'][col] = {
                    'count': int(len(outliers)),
                    'percentage': float(len(outliers) / len(df) * 100)
                }

        # 检查数值列的偏度
        for col in df.select_dtypes(include=[np.number]).columns:
            skewness = df[col].skew()
            if abs(skewness) > 1:  # 如果偏度绝对值大于1，认为是偏态分布
                visualization_issues['skewed_distributions'][col] = float(skewness)

        # 检查零方差列
        for col in df.columns:
            if df[col].nunique() <= 1:
                visualization_issues['zero_variance_columns'].append(col)

        return {
            'columns_info': columns_info,
            'missing_info': missing_info,
            'dtypes_info': dtypes_info,
            'numeric_stats': numeric_stats,
            'categorical_stats': categorical_stats,
            'visualization_issues': visualization_issues,
            'total_rows': len(df)
        }

    def plot_line(
        self,
        file_path: str,
        x_column: str,
        y_column: str,
        category_column: Optional[str] = None,
        title: Optional[str] = None,
        x_label: Optional[str] = None,
        y_label: Optional[str] = None,
        output_path: Optional[str] = None,
        figsize: Optional[tuple] = None,
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
            figsize: 图表大小
            style: matplotlib样式
        Returns:
            dict: 绘图结果
        """
        # 读取数据
        df = self._read_data(file_path)

        # 确保必要的列存在
        required_columns = [x_column, y_column]
        if category_column:
            required_columns.append(category_column)

        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"列 {col} 不存在")

        # 设置图表样式
        self._setup_plot(figsize, style)

        # 绘制折线图
        if category_column:
            # 按类别分组绘制多条折线
            for category in df[category_column].unique():
                category_data = df[df[category_column] == category]
                plt.plot(
                    category_data[x_column],
                    category_data[y_column],
                    label=str(category),
                    marker='o'  # 添加数据点标记
                )
            # 添加图例
            plt.legend(prop={'family': 'Arial Unicode MS'})
        else:
            # 绘制单条折线
            plt.plot(df[x_column], df[y_column], marker='o')

        # 设置标题和标签
        if title:
            plt.title(title, fontproperties='Arial Unicode MS')
        if x_label:
            plt.xlabel(x_label, fontproperties='Arial Unicode MS')
        if y_label:
            plt.ylabel(y_label, fontproperties='Arial Unicode MS')

        # 设置网格线
        plt.grid(True, linestyle='--', alpha=0.7)

        # 自动调整布局
        plt.tight_layout()

        # 保存图表
        if output_path is None:
            output_path = self._generate_output_path(file_path, 'line')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        return {
            "status": "success",
            "message": "折线图绘制成功",
            "output_path": output_path
        }

    def plot_bar(
        self,
        file_path: str,
        x_column: str,
        y_column: str,
        title: Optional[str] = None,
        x_label: Optional[str] = None,
        y_label: Optional[str] = None,
        output_path: Optional[str] = None,
        figsize: Optional[tuple] = None,
        style: Optional[str] = None,
        orientation: str = 'vertical'
    ) -> dict:
        """
        绘制条形图
        """
        # 读取数据
        df = self._read_data(file_path)

        # 确保列存在
        if x_column not in df.columns or y_column not in df.columns:
            raise ValueError(f"列 {x_column} 或 {y_column} 不存在")

        # 设置图表样式
        self._setup_plot(figsize, style)

        # 绘制条形图
        if orientation == 'vertical':
            plt.bar(df[x_column], df[y_column])
        else:
            plt.barh(df[x_column], df[y_column])

        # 设置标题和标签
        if title:
            plt.title(title, fontproperties='Arial Unicode MS')
        if x_label:
            plt.xlabel(x_label, fontproperties='Arial Unicode MS')
        if y_label:
            plt.ylabel(y_label, fontproperties='Arial Unicode MS')

        # 自动调整布局
        plt.tight_layout()

        # 保存图表
        if output_path is None:
            output_path = self._generate_output_path(file_path, 'bar')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        return {
            "status": "success",
            "message": "条形图绘制成功",
            "output_path": output_path
        }

    def plot_scatter(
        self,
        file_path: str,
        x_column: str,
        y_column: str,
        title: Optional[str] = None,
        x_label: Optional[str] = None,
        y_label: Optional[str] = None,
        output_path: Optional[str] = None,
        figsize: Optional[tuple] = None,
        style: Optional[str] = None,
        color_column: Optional[str] = None,
        size_column: Optional[str] = None
    ) -> dict:
        """
        绘制散点图
        """
        # 读取数据
        df = self._read_data(file_path)

        # 确保必要的列存在
        if x_column not in df.columns or y_column not in df.columns:
            raise ValueError(f"列 {x_column} 或 {y_column} 不存在")

        # 设置图表样式
        self._setup_plot(figsize, style)

        # 准备绘图参数
        scatter_kwargs = {}
        if color_column and color_column in df.columns:
            scatter_kwargs['c'] = df[color_column]
        if size_column and size_column in df.columns:
            scatter_kwargs['s'] = df[size_column]

        # 绘制散点图
        plt.scatter(df[x_column], df[y_column], **scatter_kwargs)

        # 设置标题和标签
        if title:
            plt.title(title, fontproperties='Arial Unicode MS')
        if x_label:
            plt.xlabel(x_label, fontproperties='Arial Unicode MS')
        if y_label:
            plt.ylabel(y_label, fontproperties='Arial Unicode MS')

        # 自动调整布局
        plt.tight_layout()

        # 保存图表
        if output_path is None:
            output_path = self._generate_output_path(file_path, 'scatter')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        return {
            "status": "success",
            "message": "散点图绘制成功",
            "output_path": output_path
        }

    def plot_pie(
        self,
        file_path: str,
        values_column: str,
        labels_column: str,
        title: Optional[str] = None,
        output_path: Optional[str] = None,
        figsize: Optional[tuple] = None,
        style: Optional[str] = None,
        autopct: Optional[str] = '%1.1f%%'
    ) -> dict:
        """
        绘制饼图
        """
        # 读取数据
        df = self._read_data(file_path)

        # 确保列存在
        if values_column not in df.columns or labels_column not in df.columns:
            raise ValueError(f"列 {values_column} 或 {labels_column} 不存在")

        # 设置图表样式
        self._setup_plot(figsize, style)

        # 绘制饼图
        plt.pie(
            df[values_column],
            labels=df[labels_column],
            autopct=autopct,
            textprops={'fontproperties': 'Arial Unicode MS'}
        )

        # 设置标题
        if title:
            plt.title(title, fontproperties='Arial Unicode MS')

        # 自动调整布局
        plt.tight_layout()

        # 保存图表
        if output_path is None:
            output_path = self._generate_output_path(file_path, 'pie')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        return {
            "status": "success",
            "message": "饼图绘制成功",
            "output_path": output_path
        }

    def plot_box(
        self,
        file_path: str,
        columns: Union[str, List[str]],
        title: Optional[str] = None,
        x_label: Optional[str] = None,
        y_label: Optional[str] = None,
        output_path: Optional[str] = None,
        figsize: Optional[tuple] = None,
        style: Optional[str] = None,
        vert: bool = True
    ) -> dict:
        """
        绘制箱线图
        """
        # 读取数据
        df = self._read_data(file_path)

        # 转换columns为列表
        if isinstance(columns, str):
            columns = [columns]

        # 确保所有列存在
        for col in columns:
            if col not in df.columns:
                raise ValueError(f"列 {col} 不存在")

        # 设置图表样式
        self._setup_plot(figsize, style)

        # 绘制箱线图
        df[columns].boxplot(vert=vert)

        # 设置标题和标签
        if title:
            plt.title(title, fontproperties='Arial Unicode MS')
        if x_label:
            plt.xlabel(x_label, fontproperties='Arial Unicode MS')
        if y_label:
            plt.ylabel(y_label, fontproperties='Arial Unicode MS')

        # 设置刻度标签字体
        plt.xticks(fontproperties='Arial Unicode MS')
        plt.yticks(fontproperties='Arial Unicode MS')

        # 自动调整布局
        plt.tight_layout()

        # 保存图表
        if output_path is None:
            output_path = self._generate_output_path(file_path, 'box')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        return {
            "status": "success",
            "message": "箱线图绘制成功",
            "output_path": output_path
        }