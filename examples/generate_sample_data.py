#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生成示例数据脚本
用于创建模拟的地表形变数据，供系统测试使用
"""

import os
import sys
import argparse
import yaml
import numpy as np
import rasterio
from rasterio.transform import from_origin
import datetime
from pathlib import Path
import matplotlib.pyplot as plt

def load_config(config_file):
    """加载配置文件"""
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config

def create_directory_structure(base_dir):
    """创建目录结构"""
    print("创建目录结构...")
    
    # 创建原始数据目录
    raw_dir = os.path.join(base_dir, 'raw')
    os.makedirs(os.path.join(raw_dir, 'sar', 'master'), exist_ok=True)
    os.makedirs(os.path.join(raw_dir, 'sar', 'slaves'), exist_ok=True)
    os.makedirs(os.path.join(raw_dir, 'dem'), exist_ok=True)
    
    # 创建处理结果目录
    processed_dir = os.path.join(base_dir, 'processed')
    os.makedirs(os.path.join(processed_dir, 'insar'), exist_ok=True)
    
    # 创建结果目录
    results_dir = os.path.join(base_dir, 'results')
    os.makedirs(os.path.join(results_dir, 'deformation'), exist_ok=True)
    os.makedirs(os.path.join(results_dir, 'point_cloud'), exist_ok=True)
    os.makedirs(os.path.join(results_dir, 'analysis'), exist_ok=True)
    os.makedirs(os.path.join(results_dir, 'visualization'), exist_ok=True)
    
    return raw_dir, processed_dir, results_dir

def generate_dem(dem_dir, config):
    """生成模拟DEM数据"""
    print("生成模拟DEM数据...")
    
    # 设置DEM范围和分辨率
    width = 500
    height = 500
    cell_size = 30.0  # 30米分辨率
    
    # 创建坐标和高程
    x = np.linspace(0, width * cell_size, width)
    y = np.linspace(0, height * cell_size, height)
    xx, yy = np.meshgrid(x, y)
    
    # 生成山脉地形
    dem = 500 + 400 * np.sin(xx / 5000) * np.cos(yy / 5000) + 200 * np.random.random((height, width))
    
    # 保存DEM
    output_file = os.path.join(dem_dir, 'dem.tif')
    
    # 设置地理变换参数（假设是UTM投影）
    transform = from_origin(500000.0, 3000000.0, cell_size, cell_size)
    
    # 创建GeoTIFF
    with rasterio.open(
        output_file,
        'w',
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=dem.dtype,
        crs='+proj=utm +zone=50 +datum=WGS84',
        transform=transform,
    ) as dst:
        dst.write(dem, 1)
    
    print(f"DEM数据已保存: {output_file}")
    return output_file

def generate_deformation_field(x_center, y_center, width, height, amplitude, sigma_x, sigma_y):
    """生成高斯形变场"""
    x = np.linspace(0, width-1, width)
    y = np.linspace(0, height-1, height)
    xx, yy = np.meshgrid(x, y)
    
    # 计算高斯形变
    deformation = amplitude * np.exp(
        -((xx - x_center)**2 / (2 * sigma_x**2) + (yy - y_center)**2 / (2 * sigma_y**2))
    )
    
    return deformation

def generate_time_series_data(results_dir, config, num_dates=3):
    """生成时间序列形变数据"""
    print(f"生成{num_dates}个时间序列形变数据...")
    
    # 设置形变场范围和分辨率
    width = 500
    height = 500
    cell_size = 30.0  # 30米分辨率
    
    # 设置基准日期
    base_date = datetime.datetime(2021, 1, 1)
    
    # 创建形变场中心
    x_center = width // 2
    y_center = height // 2
    
    # 生成每个时间点的形变场
    deformation_files = []
    coherence_files = []
    
    for i in range(num_dates):
        # 计算日期
        current_date = base_date + datetime.timedelta(days=i*12)
        date_str = current_date.strftime('%Y%m%d')
        
        # 生成形变场（随时间线性增长）
        amplitude = -20.0 * (i + 1) / num_dates  # 最大形变幅度（负值表示沉降）
        sigma_x = 100  # x方向标准差
        sigma_y = 150  # y方向标准差
        
        # 生成基本形变场
        deformation = generate_deformation_field(x_center, y_center, width, height, amplitude, sigma_x, sigma_y)
        
        # 添加一些随机噪声
        noise = np.random.normal(0, 1, (height, width)) * (abs(amplitude) * 0.05)
        deformation += noise
        
        # 生成相干系数（边缘相干性较低）
        coherence = np.ones((height, width)) * 0.9
        edge_noise = np.random.normal(0, 1, (height, width)) * 0.3
        distance_from_center = np.sqrt((xx - x_center)**2 + (yy - y_center)**2)
        coherence -= 0.5 * distance_from_center / np.max(distance_from_center) + edge_noise * 0.2
        coherence = np.clip(coherence, 0.1, 1.0)
        
        # 保存形变场
        deformation_file = os.path.join(results_dir, 'deformation', f"{date_str}_unwrap.geo")
        coherence_file = os.path.join(results_dir, 'deformation', f"{date_str}_corr.geo")
        
        # 设置地理变换参数（假设是UTM投影）
        transform = from_origin(500000.0, 3000000.0, cell_size, cell_size)
        
        # 创建形变场GeoTIFF
        with rasterio.open(
            deformation_file,
            'w',
            driver='GTiff',
            height=height,
            width=width,
            count=1,
            dtype=deformation.dtype,
            crs='+proj=utm +zone=50 +datum=WGS84',
            transform=transform,
        ) as dst:
            dst.write(deformation, 1)
        
        # 创建相干系数GeoTIFF
        with rasterio.open(
            coherence_file,
            'w',
            driver='GTiff',
            height=height,
            width=width,
            count=1,
            dtype=coherence.dtype,
            crs='+proj=utm +zone=50 +datum=WGS84',
            transform=transform,
        ) as dst:
            dst.write(coherence, 1)
        
        deformation_files.append(deformation_file)
        coherence_files.append(coherence_file)
        
        print(f"生成形变场: {deformation_file}")
        print(f"生成相干系数: {coherence_file}")
    
    return deformation_files, coherence_files

def visualize_sample_data(deformation_files, output_dir):
    """可视化示例数据"""
    print("可视化示例数据...")
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 读取形变数据
    data = []
    dates = []
    
    for file in deformation_files:
        # 从文件名中提取日期
        base_name = os.path.basename(file)
        date_str = base_name.split('_')[0]
        dates.append(date_str)
        
        # 读取形变数据
        with rasterio.open(file) as src:
            deformation = src.read(1)
            data.append(deformation)
    
    # 创建可视化图
    fig, axes = plt.subplots(1, len(data), figsize=(5*len(data), 5))
    
    if len(data) == 1:
        axes = [axes]
    
    for i, (ax, deformation, date) in enumerate(zip(axes, data, dates)):
        im = ax.imshow(deformation, cmap='jet', vmin=-20, vmax=5)
        ax.set_title(f'形变场 - {date}')
        ax.set_xlabel('X (像素)')
        ax.set_ylabel('Y (像素)')
    
    # 添加颜色条
    cbar = fig.colorbar(im, ax=axes, orientation='horizontal', pad=0.1, shrink=0.8)
    cbar.set_label('形变量 (mm)')
    
    plt.tight_layout()
    
    # 保存图形
    output_file = os.path.join(output_dir, 'sample_deformation.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    
    print(f"可视化结果已保存: {output_file}")
    
    return output_file

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='生成示例数据')
    parser.add_argument('-c', '--config', default='../config/processing_params.yml',
                        help='配置文件路径')
    parser.add_argument('-o', '--output-dir', default='../data',
                        help='输出目录路径')
    parser.add_argument('-n', '--num-dates', type=int, default=3,
                        help='生成的时间序列数据点数')
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    # 创建目录结构
    raw_dir, processed_dir, results_dir = create_directory_structure(args.output_dir)
    
    # 生成DEM数据
    dem_file = generate_dem(os.path.join(raw_dir, 'dem'), config)
    
    # 生成时间序列形变数据
    deformation_files, coherence_files = generate_time_series_data(
        results_dir, config, num_dates=args.num_dates
    )
    
    # 可视化示例数据
    vis_file = visualize_sample_data(
        deformation_files, os.path.join(results_dir, 'visualization')
    )
    
    print("\n示例数据生成完成!")
    print(f"请使用以下命令进行后续处理:")
    print(f"1. 将形变数据转换为点云:")
    print(f"   python scripts/data_conversion/insar_to_point_cloud.py -c config/processing_params.yml")
    print(f"2. 分析点云数据:")
    print(f"   python scripts/analysis/cloud_analysis.py -c config/processing_params.yml")
    print(f"3. 可视化结果:")
    print(f"   python scripts/analysis/visualization.py -c config/processing_params.yml")
    
    return 0

if __name__ == "__main__":
    # 创建全局变量
    xx, yy = None, None
    
    # 运行主函数
    sys.exit(main()) 