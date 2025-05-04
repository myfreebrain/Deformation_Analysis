#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
InSAR处理结果转点云脚本
将GMTSAR处理的形变场转换为点云格式，供CloudCompare分析使用
"""

import os
import sys
import argparse
import yaml
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_origin
from scipy.interpolate import griddata
import laspy
from laspy.header import HeaderBlock
from datetime import datetime
from pathlib import Path

def load_config(config_file):
    """加载配置文件"""
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config

def read_deformation_data(file_path):
    """读取形变数据"""
    print(f"读取形变数据: {file_path}")
    
    try:
        with rasterio.open(file_path) as src:
            # 读取栅格数据
            deformation = src.read(1)
            # 获取地理变换参数
            transform = src.transform
            # 获取坐标系统
            crs = src.crs
            
            print(f"数据尺寸: {deformation.shape}")
            
            return deformation, transform, crs
    except Exception as e:
        print(f"读取形变数据失败: {e}")
        return None, None, None

def read_coherence_data(file_path):
    """读取相干系数数据"""
    print(f"读取相干系数数据: {file_path}")
    
    try:
        with rasterio.open(file_path) as src:
            # 读取栅格数据
            coherence = src.read(1)
            return coherence
    except Exception as e:
        print(f"读取相干系数数据失败: {e}")
        return None

def create_point_cloud(deformation, coherence, transform, config):
    """创建点云数据"""
    print("创建点云数据...")
    
    # 获取配置参数
    point_cloud_params = config['point_cloud']['conversion']
    resolution = point_cloud_params['resolution']
    
    # 创建坐标网格
    height, width = deformation.shape
    rows, cols = np.indices((height, width))
    
    # 转换为地理坐标
    x_coords = transform[0] + cols * transform[1] + rows * transform[2]
    y_coords = transform[3] + cols * transform[4] + rows * transform[5]
    
    # 按照指定分辨率降采样
    mask = (cols % resolution == 0) & (rows % resolution == 0)
    x_coords = x_coords[mask]
    y_coords = y_coords[mask]
    z_values = deformation[mask]
    
    # 如果有相干系数数据，也进行降采样
    if coherence is not None:
        coherence_values = coherence[mask]
    else:
        coherence_values = np.ones_like(z_values)
    
    # 过滤无效值
    valid_mask = ~np.isnan(z_values) & (coherence_values > 0.3)
    x_coords = x_coords[valid_mask]
    y_coords = y_coords[valid_mask]
    z_values = z_values[valid_mask]
    coherence_values = coherence_values[valid_mask]
    
    # 创建点云数据
    points = np.vstack((x_coords, y_coords, z_values)).T
    
    # 创建点云属性
    attributes = {
        'deformation': z_values,
        'coherence': coherence_values
    }
    
    print(f"点云点数: {len(points)}")
    
    return points, attributes

def save_to_las(points, attributes, output_file):
    """保存为LAS格式点云"""
    print(f"保存为LAS格式点云: {output_file}")
    
    # 创建LAS文件
    header = HeaderBlock()
    # 设置版本
    header.version_major = 1
    header.version_minor = 4
    
    # 创建LAS文件
    outfile = laspy.create(point_format=7, file_version="1.4")
    
    # 设置点数据
    outfile.x = points[:, 0]
    outfile.y = points[:, 1]
    outfile.z = points[:, 2]
    
    # 设置点云属性
    for attr_name, attr_values in attributes.items():
        # 添加自定义维度
        outfile.add_extra_dim(laspy.ExtraBytesParams(
            name=attr_name,
            type=np.float32,
            description=f"{attr_name} values"
        ))
        # 设置属性值
        outfile[attr_name] = attr_values
    
    # 保存LAS文件
    outfile.write(output_file)
    print(f"LAS文件已保存: {output_file}")

def save_to_xyz(points, attributes, output_file):
    """保存为XYZ格式点云"""
    print(f"保存为XYZ格式点云: {output_file}")
    
    # 创建数据框
    df = pd.DataFrame(points, columns=['X', 'Y', 'Z'])
    
    # 添加属性
    for attr_name, attr_values in attributes.items():
        df[attr_name] = attr_values
    
    # 保存为CSV文件
    df.to_csv(output_file, index=False, sep=' ')
    print(f"XYZ文件已保存: {output_file}")

def process_deformation_file(deformation_file, coherence_file, output_dir, config):
    """处理单个形变文件"""
    # 读取形变数据
    deformation, transform, crs = read_deformation_data(deformation_file)
    if deformation is None:
        return False
    
    # 读取相干系数数据
    coherence = None
    if coherence_file and os.path.exists(coherence_file):
        coherence = read_coherence_data(coherence_file)
    
    # 创建点云
    points, attributes = create_point_cloud(deformation, coherence, transform, config)
    
    # 准备输出文件名
    base_name = os.path.splitext(os.path.basename(deformation_file))[0]
    las_output = os.path.join(output_dir, f"{base_name}.las")
    xyz_output = os.path.join(output_dir, f"{base_name}.xyz")
    
    # 保存点云
    save_to_las(points, attributes, las_output)
    save_to_xyz(points, attributes, xyz_output)
    
    return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='InSAR形变场转点云')
    parser.add_argument('-c', '--config', default='../../config/processing_params.yml',
                        help='配置文件路径')
    parser.add_argument('-i', '--input-dir', help='形变数据目录，默认从配置文件读取')
    parser.add_argument('-o', '--output-dir', help='输出点云目录，默认从配置文件读取')
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    # 设置输入输出路径
    if args.input_dir:
        input_dir = args.input_dir
    else:
        input_dir = os.path.join(config['paths']['results'], 'deformation')
    
    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = os.path.join(config['paths']['results'], 'point_cloud')
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 处理所有形变文件
    processed_count = 0
    for file in os.listdir(input_dir):
        if file.endswith('_unwrap.geo'):
            deformation_file = os.path.join(input_dir, file)
            coherence_file = os.path.join(input_dir, file.replace('_unwrap.geo', '_corr.geo'))
            
            if process_deformation_file(deformation_file, coherence_file, output_dir, config):
                processed_count += 1
    
    print(f"处理完成! 共转换{processed_count}个形变场为点云格式。")

if __name__ == "__main__":
    main() 