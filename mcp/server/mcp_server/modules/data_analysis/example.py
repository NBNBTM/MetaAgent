import pandas as pd
import numpy as np
from .data_analysis_service import DataAnalysisService
from ..data_visualization.data_visualization_service import DataVisualizationService
import os

def example_usage():
    # 创建示例数据
    data = pd.DataFrame({
        'feature1': np.random.normal(0, 1, 100),
        'feature2': np.random.normal(0, 1, 100),
        'feature3': np.random.normal(0, 1, 100),
        'target': np.random.randint(0, 2, 100)
    })

    # 保存示例数据到临时文件
    temp_data_file = 'temp_example_data.csv'
    data.to_csv(temp_data_file, index=False)

    # 初始化服务
    analysis_service = DataAnalysisService()
    visualization_service = DataVisualizationService()

    try:
        # 聚类分析
        clustering_result = analysis_service.perform_clustering(
            file_path=temp_data_file,
            columns=['feature1', 'feature2', 'feature3'],
            method='kmeans',
            n_clusters=3
        )

        # 降维分析
        reduction_result = analysis_service.perform_dimension_reduction(
            file_path=temp_data_file,
            columns=['feature1', 'feature2', 'feature3'],
            method='pca',
            n_components=2
        )

        # 分类预测
        classification_result = analysis_service.perform_classification(
            file_path=temp_data_file,
            columns=['feature1', 'feature2', 'feature3'],
            target_column='target',
            method='random_forest',
            test_size=0.2,
            random_state=42
        )

        # 可视化结果
        # 读取降维结果数据
        reduced_data = pd.read_csv(reduction_result['data_path'])
        # 读取聚类结果数据
        clustered_data = pd.read_csv(clustering_result['data_path'])

        # 合并降维结果和聚类标签
        visualization_data = pd.DataFrame({
            'PC1': reduced_data['component_1'],
            'PC2': reduced_data['component_2'],
            'Cluster': clustered_data['cluster']
        })

        # 保存临时可视化数据文件
        temp_viz_file = 'temp_visualization_data.csv'
        visualization_data.to_csv(temp_viz_file, index=False)

        # 使用可视化服务绘制散点图
        visualization_result = visualization_service.plot_scatter(
            file_path=temp_viz_file,
            x_column='PC1',
            y_column='PC2',
            color_column='Cluster',
            title='PCA + K-means Clustering',
            x_label='Principal Component 1',
            y_label='Principal Component 2'
        )

        # 删除临时可视化数据文件
        os.remove(temp_viz_file)

        return {
            'clustering': clustering_result,
            'reduction': reduction_result,
            'classification': classification_result,
            'visualization': visualization_result
        }

    finally:
        # 清理临时数据文件
        if os.path.exists(temp_data_file):
            os.remove(temp_data_file)

if __name__ == '__main__':
    results = example_usage()
    print("Analysis completed successfully!")
    print("\nResults summary:")
    print(f"Clustering visualization saved to: {results['clustering']['visualization_path']}")
    print(f"Clustering data saved to: {results['clustering']['data_path']}")
    print(f"Dimension reduction visualization saved to: {results['reduction']['visualization_path']}")
    print(f"Dimension reduction data saved to: {results['reduction']['data_path']}")
    print(f"Classification visualization saved to: {results['classification']['visualization_path']}")
    print(f"Classification results saved to: {results['classification']['data_path']}")