import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA, FastICA, FactorAnalysis
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.manifold import TSNE, Isomap, LocallyLinearEmbedding
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Union, Optional, Tuple
import os
import json
import logging
from functools import wraps

try:
    import umap
except ImportError:
    umap = None

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalysisError(Exception):
    """自定义分析错误类"""
    pass

def handle_analysis_errors(func):
    """统一的错误处理装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            raise AnalysisError(str(e))
    return wrapper

class Config:
    """配置管理类"""
    SUPPORTED_FILE_EXTENSIONS = ['.csv', '.xls', '.xlsx']
    DEFAULT_OUTPUT_DIR = 'analysis_results'
    DEFAULT_TEST_SIZE = 0.2
    DEFAULT_RANDOM_STATE = 42
    DEFAULT_N_COMPONENTS = 2
    DEFAULT_N_CLUSTERS = 3

class DataAnalysisService:
    def __init__(self):
        self.scalers = {
            'standard': StandardScaler(),
            'minmax': MinMaxScaler(),
            'robust': RobustScaler()
        }

        # 定义支持的降维方法
        nonlinear_methods = {
            'tsne': {
                'name': 't-SNE',
                'description': 't分布随机邻域嵌入，保持局部结构的同时降低维度',
                'class': TSNE
            },
            'isomap': {
                'name': 'Isomap',
                'description': '等距映射，保持数据点之间的测地距离',
                'class': Isomap
            },
            'lle': {
                'name': 'Locally Linear Embedding',
                'description': '局部线性嵌入，保持局部线性关系',
                'class': LocallyLinearEmbedding
            }
        }
        if umap is not None:
            nonlinear_methods['umap'] = {
                'name': 'UMAP',
                'description': '统一流形逼近与投影，保持数据的局部和全局结构',
                'class': umap.UMAP
            }

        self.supported_dimension_reduction_methods = {
            'linear': {
                'pca': {
                    'name': 'Principal Component Analysis',
                    'description': '主成分分析，通过线性变换将数据投影到方差最大的方向',
                    'class': PCA
                },
                'lda': {
                    'name': 'Linear Discriminant Analysis',
                    'description': '线性判别分析，通过最大化类间距离和最小化类内距离来降维',
                    'class': LinearDiscriminantAnalysis
                },
                'ica': {
                    'name': 'Independent Component Analysis',
                    'description': '独立成分分析，将数据分解为统计独立的非高斯信号',
                    'class': FastICA
                },
                'factor_analysis': {
                    'name': 'Factor Analysis',
                    'description': '因子分析，通过潜在变量解释观测变量之间的相关性',
                    'class': FactorAnalysis
                }
            },
            'nonlinear': nonlinear_methods
        }

        # 定义支持的分类方法
        self.supported_classification_methods = {
            'logistic_regression': {
                'name': 'Logistic Regression',
                'description': '逻辑回归，适用于二分类和多分类问题',
                'class': LogisticRegression
            },
            'naive_bayes': {
                'name': 'Naive Bayes',
                'description': '朴素贝叶斯，基于贝叶斯定理的分类器',
                'class': GaussianNB
            },
            'knn': {
                'name': 'K-Nearest Neighbors',
                'description': 'K近邻，基于距离的分类器',
                'class': KNeighborsClassifier
            },
            'svm': {
                'name': 'Support Vector Machine',
                'description': '支持向量机，寻找最优分类边界',
                'class': SVC
            },
            'decision_tree': {
                'name': 'Decision Tree',
                'description': '决策树，基于树结构的分类器',
                'class': DecisionTreeClassifier
            },
            'random_forest': {
                'name': 'Random Forest',
                'description': '随机森林，集成多个决策树的分类器',
                'class': RandomForestClassifier
            }
        }

        # 定义支持的聚类方法
        self.supported_clustering_methods = {
            'kmeans': {
                'name': 'K-Means',
                'description': 'K均值聚类，基于距离的聚类算法',
                'class': KMeans
            },
            'dbscan': {
                'name': 'DBSCAN',
                'description': '基于密度的聚类算法，可以发现任意形状的簇',
                'class': DBSCAN
            }
        }

    def _parse_columns(self, columns: Union[str, List[str], None]) -> Optional[List[str]]:
        """
        解析列名参数，支持字符串形式的列表输入
        Args:
            columns: 列名参数，可以是字符串形式的列表或实际的列表
        Returns:
            Optional[List[str]]: 解析后的列名列表
        """
        if columns is None:
            return None
        if isinstance(columns, list):
            return columns
        try:
            # 尝试解析JSON字符串
            return json.loads(columns)
        except json.JSONDecodeError:
            # 如果不是JSON格式，尝试按逗号分割
            return [col.strip() for col in columns.strip('[]').split(',')]

    def _validate_parameters(self, method: str, supported_methods: Dict) -> None:
        """验证参数是否有效"""
        if method not in supported_methods:
            raise ValueError(f"不支持的方法: {method}，支持的方法有: {list(supported_methods.keys())}")

    def _get_output_dir(self, file_path: str) -> str:
        """获取输出目录路径"""
        output_dir = os.path.join(os.path.dirname(file_path), Config.DEFAULT_OUTPUT_DIR)
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    def _save_visualization(self, plt, file_path: str, method: str, analysis_type: str) -> str:
        """保存可视化结果"""
        output_dir = self._get_output_dir(file_path)
        image_path = os.path.join(output_dir, f'{method}_{analysis_type}.png')
        plt.savefig(image_path)
        plt.close()
        return image_path

    def _save_analysis_results(self, df: pd.DataFrame, file_path: str, method: str, analysis_type: str) -> str:
        """保存分析结果"""
        output_dir = self._get_output_dir(file_path)
        data_path = os.path.join(output_dir, f'{method}_{analysis_type}_results.csv')
        df.to_csv(data_path, index=False)
        return data_path

    def _validate_file_extension(self, file_path: str) -> None:
        """验证文件扩展名"""
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in Config.SUPPORTED_FILE_EXTENSIONS:
            raise ValueError(f"不支持的文件格式: {file_ext}")

    @handle_analysis_errors
    def _read_data(self, file_path: str) -> pd.DataFrame:
        """读取数据文件"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        self._validate_file_extension(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext == '.csv':
            df = pd.read_csv(file_path)
        elif file_ext in ['.xls', '.xlsx']:
            df = pd.read_excel(file_path)

        logger.info(f"Successfully read data from {file_path}")
        return df

    def check_data_quality(self, file_path: str) -> Dict:
        """
        检查数据质量
        Args:
            file_path: 数据文件路径
        Returns:
            dict: 数据质量检查结果
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

        return {
            'columns_info': columns_info,
            'missing_info': missing_info,
            'dtypes_info': dtypes_info,
            'numeric_stats': numeric_stats,
            'total_rows': len(df)
        }

    def handle_missing_values(self, file_path: str, strategy: str = 'mean',
                            columns: Optional[Union[str, List[str]]] = None,
                            output_path: Optional[str] = None,
                            custom_value: Optional[float] = None) -> Dict:
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
        df = self._read_data(file_path)

        # 解析列名参数
        columns = self._parse_columns(columns)
        if columns is None:
            # 如果没有指定列，则处理所有列
            columns = df.columns.tolist()

        # 记录处理前的缺失值信息
        before_missing = df[columns].isnull().sum().to_dict()

        # 处理缺失值
        if strategy == 'mean':
            df[columns] = df[columns].fillna(df[columns].mean())
        elif strategy == 'median':
            df[columns] = df[columns].fillna(df[columns].median())
        elif strategy == 'mode':
            df[columns] = df[columns].fillna(df[columns].mode().iloc[0])
        elif strategy == 'drop':
            df = df.dropna(subset=columns)
        elif strategy == 'custom':
            if custom_value is None:
                raise ValueError("使用'custom'策略时必须提供custom_value参数")
            df[columns] = df[columns].fillna(custom_value)
        else:
            raise ValueError(f"不支持的缺失值处理策略: {strategy}")

        # 记录处理后的缺失值信息
        after_missing = df[columns].isnull().sum().to_dict()

        # 生成输出文件路径
        if output_path is None:
            file_name, file_ext = os.path.splitext(file_path)
            output_path = f"{file_name}_filled{file_ext}"

        # 保存处理后的数据
        file_ext = os.path.splitext(output_path)[1].lower()
        if file_ext == '.csv':
            df.to_csv(output_path, index=False)
        elif file_ext in ['.xls', '.xlsx']:
            df.to_excel(output_path, index=False)
        else:
            raise ValueError(f"不支持的文件格式: {file_ext}")

        return {
            'strategy': strategy,
            'columns': columns,
            'before_missing': before_missing,
            'after_missing': after_missing,
            'output_path': output_path
        }

    def standardize_data(self, file_path: str, columns: Optional[Union[str, List[str]]] = None,
                        method: str = 'standard', missing_strategy: str = 'mean',
                        custom_value: Optional[float] = None,
                        output_path: Optional[str] = None) -> Dict:
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
        df = self._read_data(file_path)

        # 解析列名参数
        columns = self._parse_columns(columns)
        if columns is None:
            # 如果没有指定列，则处理所有数值型列
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        # 记录处理前的统计信息
        before_stats = {}
        for col in columns:
            before_stats[col] = {
                'mean': float(df[col].mean()),
                'std': float(df[col].std()),
                'min': float(df[col].min()),
                'max': float(df[col].max()),
                'missing_count': int(df[col].isnull().sum())
            }

        # 处理缺失值
        if missing_strategy == 'mean':
            df[columns] = df[columns].fillna(df[columns].mean())
        elif missing_strategy == 'median':
            df[columns] = df[columns].fillna(df[columns].median())
        elif missing_strategy == 'mode':
            df[columns] = df[columns].fillna(df[columns].mode().iloc[0])
        elif missing_strategy == 'drop':
            df = df.dropna(subset=columns)
        elif missing_strategy == 'custom':
            if custom_value is None:
                raise ValueError("使用'custom'策略时必须提供custom_value参数")
            df[columns] = df[columns].fillna(custom_value)
        else:
            raise ValueError(f"不支持的缺失值处理策略: {missing_strategy}")

        # 选择标准化方法
        if method not in self.scalers:
            raise ValueError(f"不支持的标准化方法: {method}，支持的方法有: {list(self.scalers.keys())}")

        # 标准化数据
        df[columns] = self.scalers[method].fit_transform(df[columns])

        # 记录标准化后的统计信息
        after_stats = {}
        for col in columns:
            after_stats[col] = {
                'mean': float(df[col].mean()),
                'std': float(df[col].std()),
                'min': float(df[col].min()),
                'max': float(df[col].max())
            }

        # 生成输出文件路径
        if output_path is None:
            file_name, file_ext = os.path.splitext(file_path)
            output_path = f"{file_name}_sted{file_ext}"

        # 保存处理后的数据
        file_ext = os.path.splitext(output_path)[1].lower()
        if file_ext == '.csv':
            df.to_csv(output_path, index=False)
        elif file_ext in ['.xls', '.xlsx']:
            df.to_excel(output_path, index=False)
        else:
            raise ValueError(f"不支持的文件格式: {file_ext}")

        return {
            'method': method,
            'missing_strategy': missing_strategy,
            'columns': columns,
            'before_stats': before_stats,
            'after_stats': after_stats,
            'output_path': output_path
        }

    def get_supported_dimension_reduction_methods(self) -> Dict:
        """
        获取支持的降维方法信息
        Returns:
            dict: 支持的降维方法信息
        """
        return self.supported_dimension_reduction_methods

    @handle_analysis_errors
    def perform_dimension_reduction(self, file_path: str, columns: Optional[Union[str, List[str]]] = None,
                                  method: str = 'pca', n_components: int = Config.DEFAULT_N_COMPONENTS, **kwargs) -> Dict:
        """执行降维分析"""
        logger.info(f"Starting dimension reduction analysis with method: {method}")

        # 解析列名参数
        columns = self._parse_columns(columns)

        # 读取数据
        df = self._read_data(file_path)

        if columns:
            df = df[columns]

        # 检查方法是否支持
        method = method.lower()
        self._validate_parameters(method, {**self.supported_dimension_reduction_methods['linear'],
                                         **self.supported_dimension_reduction_methods['nonlinear']})

        method_info = None
        for category in self.supported_dimension_reduction_methods.values():
            if method in category:
                method_info = category[method]
                break

        # 执行降维
        model = method_info['class'](n_components=n_components, **kwargs)
        reduced_data = model.fit_transform(df)

        logger.info(f"Dimension reduction completed. Reduced from {df.shape[1]} to {n_components} dimensions")

        # 初始化统计信息
        stats = {
            'n_samples': len(df),
            'n_features': len(df.columns),
            'feature_names': df.columns.tolist(),
            'method': method_info['name'],
            'method_description': method_info['description'],
            'n_components': n_components
        }

        # 如果是PCA，添加更多信息
        if method == 'pca':
            stats['pca_specific'] = {
                'explained_variance_ratio': model.explained_variance_ratio_.tolist(),
                'cumulative_variance_ratio': np.cumsum(model.explained_variance_ratio_).tolist(),
                'singular_values': model.singular_values_.tolist() if hasattr(model, 'singular_values_') else None,
                'n_components': model.n_components_,
                'feature_importance': {
                    feature: abs(model.components_[0][i]) for i, feature in enumerate(df.columns)
                }
            }
        # 如果是LDA，添加判别信息
        elif method == 'lda':
            stats['explained_variance_ratio'] = model.explained_variance_ratio_.tolist()
            stats['n_classes'] = len(model.classes_)
            stats['class_means'] = {
                str(label): model.means_[i].tolist() for i, label in enumerate(model.classes_)
            }
            stats['class_covariances'] = {
                str(label): model.covariances_[i].tolist() for i, label in enumerate(model.classes_)
            }

        # 生成可视化图像
        plt.figure(figsize=(10, 6))
        plt.scatter(reduced_data[:, 0], reduced_data[:, 1])
        plt.title(f'{method_info["name"]} Dimension Reduction')
        plt.xlabel('Component 1')
        plt.ylabel('Component 2')

        # 保存图像
        image_path = self._save_visualization(plt, file_path, method, 'reduction')

        # 保存降维后的数据
        column_names = [f'component_{i+1}' for i in range(n_components)]
        reduced_df = pd.DataFrame(reduced_data, columns=column_names)

        # 添加样本索引（如果需要与原始数据对应）
        reduced_df['sample_index'] = range(len(reduced_data))
        column_names.append('sample_index')

        # 保存数据
        data_path = self._save_analysis_results(reduced_df, file_path, method, 'reduction')

        # 添加原始特征名称和对应的权重（对于线性降维方法）
        if method in ['pca', 'lda', 'ica', 'factor_analysis']:
            # 获取特征权重
            if hasattr(model, 'components_'):
                # 创建一个新的DataFrame来存储特征权重
                weights_df = pd.DataFrame(
                    model.components_,
                    columns=df.columns,
                    index=[f'component_{i+1}' for i in range(n_components)]
                )
                # 将权重DataFrame保存到单独的文件
                weights_path = os.path.join(os.path.dirname(data_path), f'{method}_feature_weights.csv')
                weights_df.to_csv(weights_path)
                stats['feature_weights_path'] = weights_path

        # 更新统计信息
        stats['visualization_path'] = image_path
        stats['data_path'] = data_path
        stats['column_names'] = column_names

        # 添加更多统计信息
        stats['component_statistics'] = {
            f'component_{i+1}': {
                'mean': float(reduced_df[f'component_{i+1}'].mean()),
                'std': float(reduced_df[f'component_{i+1}'].std()),
                'min': float(reduced_df[f'component_{i+1}'].min()),
                'max': float(reduced_df[f'component_{i+1}'].max())
            } for i in range(n_components)
        }

        # 保存统计信息到JSON文件
        stats_path = self._save_statistics(stats, file_path, method, 'reduction')
        stats['statistics_path'] = stats_path

        return stats

    def get_supported_classification_methods(self) -> Dict:
        """
        获取支持的分类方法信息
        Returns:
            dict: 支持的分类方法信息
        """
        return self.supported_classification_methods

    def get_supported_clustering_methods(self) -> Dict:
        """
        获取支持的聚类方法信息
        Returns:
            dict: 支持的聚类方法信息
        """
        return self.supported_clustering_methods

    def _save_statistics(self, stats: Dict, file_path: str, method: str, analysis_type: str) -> str:
        """保存统计分析结果到JSON文件"""
        output_dir = self._get_output_dir(file_path)
        stats_path = os.path.join(output_dir, f'{method}_{analysis_type}_statistics.json')

        # 将numpy类型转换为Python原生类型
        def convert_numpy(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_numpy(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy(item) for item in obj]
            return obj

        # 转换统计信息
        stats = convert_numpy(stats)

        # 保存到JSON文件
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        return stats_path

    @handle_analysis_errors
    def perform_classification(self, file_path: str,
                             columns: Optional[Union[str, List[str]]] = None,
                             target_column: str = 'target',
                             method: str = 'random_forest',
                             test_size: float = Config.DEFAULT_TEST_SIZE,
                             random_state: int = Config.DEFAULT_RANDOM_STATE,
                             **kwargs) -> Dict:
        """执行分类预测"""
        logger.info(f"Starting classification analysis with method: {method}")

        # 解析列名参数
        columns = self._parse_columns(columns)

        # 读取数据
        df = self._read_data(file_path)

        # 确保目标列存在
        if target_column not in df.columns:
            raise ValueError(f"目标列 '{target_column}' 不存在于数据中。可用的列有: {df.columns.tolist()}")

        # 如果指定了列，确保目标列包含在内
        if columns:
            if target_column not in columns:
                columns.append(target_column)
            df = df[columns]

        # 检查方法是否支持
        method = method.lower()
        self._validate_parameters(method, self.supported_classification_methods)

        method_info = self.supported_classification_methods[method]

        # 分离特征和目标变量
        X = df.drop(columns=[target_column])
        y = df[target_column]

        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )

        # 选择分类器
        model = method_info['class'](**kwargs)

        # 训练模型
        model.fit(X_train, y_train)

        # 预测
        predictions = model.predict(X_test)

        # 计算分类报告
        from sklearn.metrics import classification_report, confusion_matrix
        report = classification_report(y_test, predictions, output_dict=True)
        conf_matrix = confusion_matrix(y_test, predictions)

        # 初始化统计信息
        stats = {
            'method': method_info['name'],
            'method_description': method_info['description'],
            'classification_report': report,
            'confusion_matrix': conf_matrix.tolist(),
            'basic_statistics': {
                'n_train_samples': len(X_train),
                'n_test_samples': len(X_test),
                'n_features': len(X.columns),
                'feature_names': X.columns.tolist(),
                'test_size': test_size,
                'random_state': random_state,
                'accuracy': float((predictions == y_test).mean()),
                'class_distribution': {
                    str(label): int((y_test == label).sum()) for label in model.classes_
                }
            }
        }

        # 生成可视化图像
        plt.figure(figsize=(10, 6))
        sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues')
        plt.title(f'{method_info["name"]} Classification Results')
        plt.xlabel('Predicted')
        plt.ylabel('True')

        # 保存图像
        image_path = self._save_visualization(plt, file_path, method, 'classification')

        # 保存预测结果
        column_names = ['true_label', 'predicted_label']
        results_df = pd.DataFrame({
            'true_label': y_test,
            'predicted_label': predictions
        })

        # 添加预测概率（如果模型支持）
        if hasattr(model, 'predict_proba'):
            proba = model.predict_proba(X_test)
            for i, class_label in enumerate(model.classes_):
                prob_col = f'probability_{class_label}'
                results_df[prob_col] = proba[:, i]
                column_names.append(prob_col)

        # 添加预测是否正确
        results_df['is_correct'] = results_df['true_label'] == results_df['predicted_label']
        column_names.append('is_correct')

        # 添加样本索引
        results_df['sample_index'] = range(len(y_test))
        column_names.append('sample_index')

        # 保存数据
        data_path = self._save_analysis_results(results_df, file_path, method, 'classification')

        # 计算更多评估指标
        from sklearn.metrics import roc_auc_score, average_precision_score, precision_recall_curve, roc_curve

        # 添加ROC和PR曲线数据（对于二分类问题）
        if len(model.classes_) == 2:
            try:
                fpr, tpr, _ = roc_curve(y_test, proba[:, 1])
                precision, recall, _ = precision_recall_curve(y_test, proba[:, 1])

                # 保存ROC和PR曲线数据
                roc_data = pd.DataFrame({
                    'fpr': fpr,
                    'tpr': tpr
                })
                pr_data = pd.DataFrame({
                    'precision': precision,
                    'recall': recall
                })

                roc_path = self._save_analysis_results(roc_data, file_path, method, 'roc_curve')
                pr_path = self._save_analysis_results(pr_data, file_path, method, 'pr_curve')

                stats['roc_curve_path'] = roc_path
                stats['pr_curve_path'] = pr_path

                # 计算AUC和AP分数
                stats['auc_score'] = float(roc_auc_score(y_test, proba[:, 1]))
                stats['average_precision'] = float(average_precision_score(y_test, proba[:, 1]))
            except:
                pass

        # 更新统计信息
        stats['visualization_path'] = image_path
        stats['data_path'] = data_path
        stats['column_names'] = column_names

        # 保存统计信息到JSON文件
        stats_path = self._save_statistics(stats, file_path, method, 'classification')
        stats['statistics_path'] = stats_path

        return stats

    @handle_analysis_errors
    def perform_clustering(self, file_path: str, columns: Optional[Union[str, List[str]]] = None,
                          method: str = 'kmeans', n_clusters: int = Config.DEFAULT_N_CLUSTERS, **kwargs) -> Dict:
        """执行聚类分析"""
        logger.info(f"Starting clustering analysis with method: {method}")

        # 解析列名参数
        columns = self._parse_columns(columns)

        # 读取数据
        df = self._read_data(file_path)

        if columns:
            df = df[columns]

        # 检查方法是否支持
        method = method.lower()
        self._validate_parameters(method, self.supported_clustering_methods)

        method_info = self.supported_clustering_methods[method]

        # 执行聚类
        model = method_info['class'](n_clusters=n_clusters, **kwargs)
        labels = model.fit_predict(df)

        # 初始化统计信息
        stats = {
            'method': method_info['name'],
            'method_description': method_info['description'],
            'n_clusters': len(np.unique(labels)),
            'basic_statistics': {
                'n_samples': len(df),
                'n_features': len(df.columns),
                'feature_names': df.columns.tolist(),
                'cluster_sizes': {
                    str(cluster): int((labels == cluster).sum()) for cluster in np.unique(labels)
                }
            }
        }

        # 计算聚类统计信息
        df['cluster'] = labels

        # 添加样本到聚类中心的距离（对于K-means）
        if method == 'kmeans':
            distances = model.transform(df.drop(columns=['cluster']))
            for i in range(n_clusters):
                dist_col = f'distance_to_cluster_{i}'
                df[dist_col] = distances[:, i]

        # 添加样本索引
        df['sample_index'] = range(len(df))

        # 计算每个聚类的轮廓系数
        from sklearn.metrics import silhouette_samples
        try:
            silhouette_scores = silhouette_samples(df.drop(columns=['cluster', 'sample_index']), labels)
            df['silhouette_score'] = silhouette_scores
        except:
            pass

        # 保存数据
        column_names = df.columns.tolist()
        data_path = self._save_analysis_results(df, file_path, method, 'clustering')

        # 计算更多聚类评估指标
        from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score

        try:
            # 计算整体轮廓系数
            silhouette_avg = silhouette_score(df.drop(columns=['cluster', 'sample_index']), labels)
            # 计算Calinski-Harabasz指数
            calinski_harabasz = calinski_harabasz_score(df.drop(columns=['cluster', 'sample_index']), labels)
            # 计算Davies-Bouldin指数
            davies_bouldin = davies_bouldin_score(df.drop(columns=['cluster', 'sample_index']), labels)

            stats['clustering_metrics'] = {
                'silhouette_score': float(silhouette_avg),
                'calinski_harabasz_score': float(calinski_harabasz),
                'davies_bouldin_score': float(davies_bouldin)
            }
        except:
            pass

        # 计算每个聚类的统计信息
        cluster_stats = {}
        for cluster in np.unique(labels):
            cluster_data = df[df['cluster'] == cluster]
            cluster_stats[f'cluster_{cluster}'] = {
                'size': len(cluster_data),
                'silhouette_score': float(cluster_data['silhouette_score'].mean()) if 'silhouette_score' in cluster_data.columns else None,
                'feature_statistics': {
                    col: {
                        'mean': float(cluster_data[col].mean()),
                        'std': float(cluster_data[col].std()),
                        'min': float(cluster_data[col].min()),
                        'max': float(cluster_data[col].max())
                    } for col in df.columns if col not in ['cluster', 'sample_index', 'silhouette_score']
                }
            }

        # 生成可视化图像
        plt.figure(figsize=(10, 6))
        if df.shape[1] >= 2:
            plt.scatter(df.iloc[:, 0], df.iloc[:, 1], c=labels, cmap='viridis')
            plt.title(f'{method_info["name"]} Clustering Results')
            plt.xlabel('Feature 1')
            plt.ylabel('Feature 2')
        else:
            # 如果维度小于2，使用PCA降维到2维进行可视化
            pca = PCA(n_components=2)
            X_2d = pca.fit_transform(df)
            plt.scatter(X_2d[:, 0], X_2d[:, 1], c=labels, cmap='viridis')
            plt.title(f'{method_info["name"]} Clustering Results (PCA Visualization)')
            plt.xlabel('Principal Component 1')
            plt.ylabel('Principal Component 2')

        # 保存图像
        image_path = self._save_visualization(plt, file_path, method, 'clustering')

        # 更新统计信息
        stats['cluster_statistics'] = cluster_stats
        stats['visualization_path'] = image_path
        stats['data_path'] = data_path
        stats['column_names'] = column_names

        # 保存统计信息到JSON文件
        stats_path = self._save_statistics(stats, file_path, method, 'clustering')
        stats['statistics_path'] = stats_path

        return stats
