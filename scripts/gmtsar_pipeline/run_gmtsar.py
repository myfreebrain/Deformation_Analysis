#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GMTSAR处理主脚本
用于自动化处理SAR数据并生成形变图
"""

import os
import sys
import subprocess
import argparse
import yaml
import shutil
from datetime import datetime
from pathlib import Path

def load_config(config_file):
    """加载配置文件"""
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config

def setup_directories(config):
    """创建处理所需的目录结构"""
    paths = config['paths']
    
    # 创建目录
    for path_key in paths:
        os.makedirs(paths[path_key], exist_ok=True)
    
    # 创建处理中间结果目录
    insar_dir = os.path.join(paths['processed_data'], 'insar')
    os.makedirs(insar_dir, exist_ok=True)
    
    return insar_dir

def prepare_dem(config, insar_dir):
    """准备DEM数据"""
    print("准备DEM数据...")
    dem_params = config['processing']['dem']
    
    # 这里假设使用GMTSAR的dem2topo_ra.csh脚本
    # 实际使用时需根据GMTSAR的具体安装路径和命令进行调整
    dem_cmd = [
        "dem2topo_ra.csh", 
        dem_params['source'],
        str(dem_params['resolution'])
    ]
    
    subprocess.run(dem_cmd, cwd=insar_dir, check=True)
    print("DEM准备完成")

def run_preprocess(config, insar_dir):
    """预处理SAR数据"""
    print("预处理SAR数据...")
    sar_params = config['sar_data']
    
    # 设置预处理参数
    preprocess_cmd = [
        "preprocess.csh", 
        sar_params['satellite'],
        sar_params['orbit_direction']
    ]
    
    # 执行预处理
    subprocess.run(preprocess_cmd, cwd=insar_dir, check=True)
    print("预处理完成")

def run_interferometry(config, insar_dir):
    """运行干涉处理"""
    print("执行干涉处理...")
    insar_params = config['processing']['insar']
    
    master = insar_params['master_date']
    slaves = insar_params['slave_dates']
    
    for slave in slaves:
        print(f"处理主影像{master}和从影像{slave}的干涉对...")
        
        # 创建干涉对目录
        pair_dir = os.path.join(insar_dir, f"{master}_{slave}")
        os.makedirs(pair_dir, exist_ok=True)
        
        # 执行干涉处理
        intf_cmd = [
            "intf.csh", 
            master, 
            slave,
            str(insar_params['filter_wavelength'])
        ]
        
        subprocess.run(intf_cmd, cwd=pair_dir, check=True)
        
        # 执行解缠
        unwrap_cmd = [
            "unwrap_mod.csh", 
            insar_params['unwrap_method']
        ]
        
        subprocess.run(unwrap_cmd, cwd=pair_dir, check=True)
    
    print("干涉处理完成")

def geocode_results(config, insar_dir):
    """地理编码处理结果"""
    print("地理编码处理结果...")
    insar_params = config['processing']['insar']
    
    master = insar_params['master_date']
    slaves = insar_params['slave_dates']
    
    for slave in slaves:
        pair_dir = os.path.join(insar_dir, f"{master}_{slave}")
        
        # 执行地理编码
        geocode_cmd = [
            "geocode.csh", 
            os.path.join(pair_dir, "unwrap.grd")
        ]
        
        subprocess.run(geocode_cmd, cwd=pair_dir, check=True)
    
    print("地理编码完成")

def export_results(config, insar_dir):
    """导出处理结果到结果目录"""
    print("导出处理结果...")
    insar_params = config['processing']['insar']
    
    master = insar_params['master_date']
    slaves = insar_params['slave_dates']
    results_dir = config['paths']['results']
    
    # 创建结果目录
    deformation_dir = os.path.join(results_dir, 'deformation')
    os.makedirs(deformation_dir, exist_ok=True)
    
    for slave in slaves:
        pair_dir = os.path.join(insar_dir, f"{master}_{slave}")
        
        # 复制地理编码后的解缠相位和相干图
        for file_type in ['unwrap.geo', 'corr.geo']:
            src_file = os.path.join(pair_dir, file_type)
            dst_file = os.path.join(deformation_dir, f"{master}_{slave}_{file_type}")
            
            if os.path.exists(src_file):
                shutil.copy2(src_file, dst_file)
    
    print("结果导出完成")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='GMTSAR处理脚本')
    parser.add_argument('-c', '--config', default='../../config/processing_params.yml',
                        help='配置文件路径')
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    # 设置处理目录
    insar_dir = setup_directories(config)
    
    # 执行处理流程
    prepare_dem(config, insar_dir)
    run_preprocess(config, insar_dir)
    run_interferometry(config, insar_dir)
    geocode_results(config, insar_dir)
    export_results(config, insar_dir)
    
    print("GMTSAR处理完成!")

if __name__ == "__main__":
    main() 