#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
形变分析可视化脚本
用于生成各种形变分析结果的可视化图表
"""

import os
import sys
import argparse
import yaml
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.colors import Normalize
import seaborn as sns
import glob
import rasterio
from rasterio.plot import show
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from pathlib import Path

def load_config(config_file):
    """加载配置文件"""
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config

def plot_deformation_map(file_path, output_dir, config):
    """绘制形变图"""
    print(f"绘制形变图: {file_path}")
    
    # 获取可视化参数
    vis_params = config['visualization']
    cmap = vis_params['color_map']
    vmin = vis_params['min_deformation']
    vmax = vis_params['max_deformation']
    
    # 读取形变数据
    with rasterio.open(file_path) as src:
        deformation = src.read(1)
        transform = src.transform
    
    # 准备输出文件名
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_file = os.path.join(output_dir, f"{base_name}_map.png")
    
    # 创建图形
    plt.figure(figsize=(12, 10))
    
    # 绘制形变图
    img = show(deformation, transform=transform, cmap=cmap, vmin=vmin, vmax=vmax, 
               title=f'形变图 - {base_name}')
    
    # 添加颜色条
    cbar = plt.colorbar(img, shrink=0.6)
    cbar.set_label(f'形变量 ({config["processing"]["time_series"]["deformation_unit"]})')
    
    # 保存图形
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"形变图已保存: {output_file}")
    return output_file

def plot_coherence_map(file_path, output_dir):
    """绘制相干系数图"""
    print(f"绘制相干系数图: {file_path}")
    
    # 读取相干系数数据
    with rasterio.open(file_path) as src:
        coherence = src.read(1)
        transform = src.transform
    
    # 准备输出文件名
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_file = os.path.join(output_dir, f"{base_name}_map.png")
    
    # 创建图形
    plt.figure(figsize=(12, 10))
    
    # 绘制相干系数图
    img = show(coherence, transform=transform, cmap='viridis', vmin=0, vmax=1, 
               title=f'相干系数图 - {base_name}')
    
    # 添加颜色条
    cbar = plt.colorbar(img, shrink=0.6)
    cbar.set_label('相干系数')
    
    # 保存图形
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"相干系数图已保存: {output_file}")
    return output_file

def plot_3d_point_cloud(file_path, output_dir, config):
    """绘制3D点云图"""
    print(f"绘制3D点云图: {file_path}")
    
    # 获取可视化参数
    vis_params = config['visualization']
    cmap = vis_params['color_map']
    vmin = vis_params['min_deformation']
    vmax = vis_params['max_deformation']
    
    # 读取点云数据
    df = pd.read_csv(file_path, sep=' ')
    
    # 准备输出文件名
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_file = os.path.join(output_dir, f"{base_name}_3d.html")
    
    # 创建颜色映射
    if 'deformation' in df.columns:
        color_values = df['deformation']
        color_label = f'形变量 ({config["processing"]["time_series"]["deformation_unit"]})'
    else:
        color_values = df['Z']
        color_label = '高程值'
    
    # 创建3D散点图
    fig = px.scatter_3d(df, x='X', y='Y', z='Z', 
                        color=color_values,
                        color_continuous_scale=cmap,
                        range_color=[vmin, vmax],
                        labels={'X': '经度', 'Y': '纬度', 'Z': '高程', 'color': color_label},
                        title=f'3D点云图 - {base_name}')
    
    # 调整布局
    fig.update_layout(scene=dict(aspectmode='data'))
    
    # 保存图形
    fig.write_html(output_file)
    
    print(f"3D点云图已保存: {output_file}")
    return output_file

def plot_time_series(deformation_files, output_dir, config):
    """绘制时间序列分析图"""
    print(f"绘制时间序列分析图: {len(deformation_files)}个形变场")
    
    # 获取配置参数
    time_series_params = config['processing']['time_series']
    ref_point = time_series_params['reference_point']
    unit = time_series_params['deformation_unit']
    
    # 准备数据
    dates = []
    deformations = []
    
    for file in deformation_files:
        # 从文件名中提取日期
        base_name = os.path.basename(file)
        date_str = base_name.split('_')[0]  # 假设文件名格式为"YYYYMMDD_*.geo"
        dates.append(datetime.strptime(date_str, '%Y%m%d'))
        
        # 读取形变数据
        with rasterio.open(file) as src:
            deformation = src.read(1)
            transform = src.transform
            
            # 将参考点坐标转换为像素坐标
            row, col = src.index(ref_point[0], ref_point[1])
            
            # 获取参考点处的形变值
            if 0 <= row < deformation.shape[0] and 0 <= col < deformation.shape[1]:
                deformations.append(deformation[row, col])
            else:
                deformations.append(np.nan)
    
    # 排序
    sorted_data = sorted(zip(dates, deformations))
    dates = [item[0] for item in sorted_data]
    deformations = [item[1] for item in sorted_data]
    
    # 准备输出文件名
    output_file = os.path.join(output_dir, "time_series.png")
    
    # 创建图形
    plt.figure(figsize=(12, 8))
    plt.plot(dates, deformations, 'o-', linewidth=2)
    plt.xlabel('日期')
    plt.ylabel(f'形变量 ({unit})')
    plt.title(f'参考点 ({ref_point[0]}, {ref_point[1]}) 处的时间序列形变')
    plt.grid(True)
    plt.xticks(rotation=45)
    
    # 保存图形
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"时间序列分析图已保存: {output_file}")
    return output_file

def plot_histogram(file_path, output_dir, config):
    """绘制形变直方图"""
    print(f"绘制形变直方图: {file_path}")
    
    # 获取可视化参数
    vis_params = config['visualization']
    vmin = vis_params['min_deformation']
    vmax = vis_params['max_deformation']
    unit = config['processing']['time_series']['deformation_unit']
    
    # 读取数据
    if file_path.endswith('.xyz'):
        # 点云数据
        df = pd.read_csv(file_path, sep=' ')
        if 'deformation' in df.columns:
            data = df['deformation']
        else:
            data = df['Z']
    else:
        # 栅格数据
        with rasterio.open(file_path) as src:
            data = src.read(1)
            data = data.flatten()
            # 过滤无效值
            data = data[~np.isnan(data)]
    
    # 准备输出文件名
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_file = os.path.join(output_dir, f"{base_name}_histogram.png")
    
    # 创建图形
    plt.figure(figsize=(10, 6))
    sns.histplot(data, bins=50, kde=True)
    plt.xlabel(f'形变量 ({unit})')
    plt.ylabel('频率')
    plt.title(f'形变分布直方图 - {base_name}')
    plt.xlim(vmin, vmax)
    plt.grid(True)
    
    # 保存图形
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"形变直方图已保存: {output_file}")
    return output_file

def plot_classification_results(file_path, output_dir, config):
    """绘制分类结果图"""
    print(f"绘制分类结果图: {file_path}")
    
    # 读取点云数据
    df = pd.read_csv(file_path, sep=' ')
    
    # 准备输出文件名
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_file = os.path.join(output_dir, f"{base_name}_classification.html")
    
    # 检查是否有分类标签
    if 'class' in df.columns:
        color_values = df['class']
        discrete_colors = True
    elif 'label' in df.columns:
        color_values = df['label']
        discrete_colors = True
    else:
        # 如果没有明确的分类标签，使用形变量作为颜色
        color_values = df['deformation'] if 'deformation' in df.columns else df['Z']
        discrete_colors = False
    
    # 创建3D散点图
    if discrete_colors:
        fig = px.scatter_3d(df, x='X', y='Y', z='Z', 
                            color=color_values,
                            category_orders={color_values.name: sorted(color_values.unique())},
                            labels={'X': '经度', 'Y': '纬度', 'Z': '高程', 'color': '分类类别'},
                            title=f'分类结果 - {base_name}')
    else:
        vis_params = config['visualization']
        fig = px.scatter_3d(df, x='X', y='Y', z='Z', 
                            color=color_values,
                            color_continuous_scale=vis_params['color_map'],
                            range_color=[vis_params['min_deformation'], vis_params['max_deformation']],
                            labels={'X': '经度', 'Y': '纬度', 'Z': '高程', 'color': '形变量'},
                            title=f'形变分布 - {base_name}')
    
    # 调整布局
    fig.update_layout(scene=dict(aspectmode='data'))
    
    # 保存图形
    fig.write_html(output_file)
    
    print(f"分类结果图已保存: {output_file}")
    return output_file

def create_dashboard(output_files, output_dir):
    """创建仪表盘汇总页面"""
    print("创建仪表盘汇总页面...")
    
    # 准备输出文件名
    output_file = os.path.join(output_dir, "dashboard.html")
    
    # 创建HTML内容
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>地表形变分析仪表盘</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
            h1 { text-align: center; color: #333; }
            .container { display: flex; flex-wrap: wrap; justify-content: center; }
            .chart-container { margin: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); border-radius: 5px; overflow: hidden; }
            .chart-title { background-color: #f0f0f0; padding: 10px; font-weight: bold; }
            img { max-width: 100%; display: block; }
            iframe { border: none; width: 800px; height: 600px; }
        </style>
    </head>
    <body>
        <h1>地表形变分析仪表盘</h1>
        <div class="container">
    """
    
    # 添加图表
    for file in output_files:
        if file.endswith('.html'):
            # 嵌入HTML文件
            file_name = os.path.basename(file)
            title = file_name.replace('_', ' ').replace('.html', '')
            
            html_content += f"""
            <div class="chart-container">
                <div class="chart-title">{title}</div>
                <iframe src="{file_name}" width="800" height="600"></iframe>
            </div>
            """
        elif file.endswith('.png'):
            # 嵌入图片
            file_name = os.path.basename(file)
            title = file_name.replace('_', ' ').replace('.png', '')
            
            html_content += f"""
            <div class="chart-container">
                <div class="chart-title">{title}</div>
                <img src="{file_name}" alt="{title}">
            </div>
            """
    
    # 关闭HTML
    html_content += """
        </div>
    </body>
    </html>
    """
    
    # 保存HTML文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"仪表盘已保存: {output_file}")
    return output_file

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='形变分析可视化')
    parser.add_argument('-c', '--config', default='../../config/processing_params.yml',
                        help='配置文件路径')
    parser.add_argument('-d', '--deformation-dir', 
                        help='形变数据目录，默认从配置文件读取')
    parser.add_argument('-p', '--point-cloud-dir',
                        help='点云数据目录，默认从配置文件读取')
    parser.add_argument('-o', '--output-dir',
                        help='可视化输出目录，默认从配置文件读取')
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    # 设置输入输出路径
    if args.deformation_dir:
        deformation_dir = args.deformation_dir
    else:
        deformation_dir = os.path.join(config['paths']['results'], 'deformation')
    
    if args.point_cloud_dir:
        point_cloud_dir = args.point_cloud_dir
    else:
        point_cloud_dir = os.path.join(config['paths']['results'], 'point_cloud')
    
    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = os.path.join(config['paths']['results'], 'visualization')
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 收集输出文件
    output_files = []
    
    # 处理形变数据文件
    deformation_files = glob.glob(os.path.join(deformation_dir, '*_unwrap.geo'))
    for file in deformation_files:
        # 绘制形变图
        output_file = plot_deformation_map(file, output_dir, config)
        output_files.append(output_file)
        
        # 绘制形变直方图
        output_file = plot_histogram(file, output_dir, config)
        output_files.append(output_file)
    
    # 处理相干系数文件
    coherence_files = glob.glob(os.path.join(deformation_dir, '*_corr.geo'))
    for file in coherence_files:
        output_file = plot_coherence_map(file, output_dir)
        output_files.append(output_file)
    
    # 处理点云文件
    xyz_files = glob.glob(os.path.join(point_cloud_dir, '*.xyz'))
    for file in xyz_files:
        # 绘制3D点云图
        output_file = plot_3d_point_cloud(file, output_dir, config)
        output_files.append(output_file)
        
        # 绘制分类结果图
        output_file = plot_classification_results(file, output_dir, config)
        output_files.append(output_file)
    
    # 如果有多个形变文件，绘制时间序列
    if len(deformation_files) > 1:
        output_file = plot_time_series(deformation_files, output_dir, config)
        output_files.append(output_file)
    
    # 创建仪表盘
    dashboard_file = create_dashboard(output_files, output_dir)
    
    print(f"\n可视化完成! 请打开仪表盘查看结果: {dashboard_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 