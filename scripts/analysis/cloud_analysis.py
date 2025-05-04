#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CloudCompare点云分析脚本
使用CloudCompare命令行接口对点云进行分析和处理
"""

import os
import sys
import argparse
import subprocess
import yaml
import glob
from datetime import datetime
from pathlib import Path

def load_config(config_file):
    """加载配置文件"""
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config

def find_cloudcompare_exe():
    """查找CloudCompare可执行文件路径"""
    # 默认查找路径
    possible_paths = [
        # Windows路径
        "C:/Program Files/CloudCompare/CloudCompare.exe",
        # Linux路径
        "/usr/bin/cloudcompare.CloudCompare",
        # macOS路径
        "/Applications/CloudCompare.app/Contents/MacOS/CloudCompare"
    ]
    
    # 检查环境变量
    if 'CLOUDCOMPARE_EXE' in os.environ:
        possible_paths.insert(0, os.environ['CLOUDCOMPARE_EXE'])
    
    # 查找可执行文件
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # 未找到可执行文件，尝试使用系统PATH中的命令
    try:
        subprocess.run(["CloudCompare", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return "CloudCompare"
    except:
        try:
            subprocess.run(["cloudcompare.CloudCompare", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return "cloudcompare.CloudCompare"
        except:
            return None

def run_cloudcompare_cmd(cc_exe, cmd_args, silent=True):
    """运行CloudCompare命令"""
    # 构建完整命令
    cmd = [cc_exe]
    
    # 添加静默模式参数
    if silent:
        cmd.extend(["-silent"])
    
    # 添加命令参数
    cmd.extend(cmd_args)
    
    # 执行命令
    print(f"执行CloudCompare命令: {' '.join(cmd)}")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # 输出结果
    if result.returncode == 0:
        print("命令执行成功!")
    else:
        print(f"命令执行失败，返回码: {result.returncode}")
        print(f"错误输出: {result.stderr}")
    
    return result.returncode == 0

def segment_point_cloud(cc_exe, input_file, output_dir, config):
    """分割点云"""
    print(f"分割点云: {input_file}")
    
    # 获取配置参数
    analysis_params = config['point_cloud']['analysis']
    segmentation_method = analysis_params['segmentation_method']
    
    # 准备输出文件名
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = os.path.join(output_dir, f"{base_name}_segmented.bin")
    
    # 构建CloudCompare命令
    cmd_args = [
        "-o", input_file,  # 打开输入文件
        "-SEGMENT_FEATURE", "SCALAR_FIELD", "deformation"  # 使用变形场进行分割
    ]
    
    # 根据分割方法设置参数
    if segmentation_method == "region_growing":
        cmd_args.extend(["-REGION_GROWING", "10", "5", "1"])  # 使用区域生长算法
    else:
        cmd_args.extend(["-LABEL_CONNECTED_COMPONENTS", "1", "10"])  # 使用连通分量分析
    
    # 设置输出
    cmd_args.extend(["-C_EXPORT_FMT", "BIN"])
    cmd_args.extend(["-AUTO_SAVE", "ON"])
    cmd_args.extend(["-SAVE_CLOUDS", "FILE", output_file])
    
    # 执行命令
    success = run_cloudcompare_cmd(cc_exe, cmd_args)
    
    return success, output_file if success else None

def classify_point_cloud(cc_exe, input_file, output_dir, config):
    """分类点云"""
    print(f"分类点云: {input_file}")
    
    # 获取配置参数
    analysis_params = config['point_cloud']['analysis']
    classification_method = analysis_params['classification_method']
    num_clusters = analysis_params['num_clusters']
    
    # 准备输出文件名
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = os.path.join(output_dir, f"{base_name}_classified.bin")
    
    # 构建CloudCompare命令
    cmd_args = [
        "-o", input_file,  # 打开输入文件
    ]
    
    # 根据分类方法设置参数
    if classification_method == "kmeans":
        cmd_args.extend(["-KMEANS", str(num_clusters), "MAX_ITER", "100", "EPSILON", "0.001"])
    else:
        cmd_args.extend(["-STAT_FEATURES", "deformation"])  # 统计特征
    
    # 设置输出
    cmd_args.extend(["-C_EXPORT_FMT", "BIN"])
    cmd_args.extend(["-AUTO_SAVE", "ON"])
    cmd_args.extend(["-SAVE_CLOUDS", "FILE", output_file])
    
    # 执行命令
    success = run_cloudcompare_cmd(cc_exe, cmd_args)
    
    return success, output_file if success else None

def create_mesh(cc_exe, input_file, output_dir):
    """创建网格模型"""
    print(f"创建网格模型: {input_file}")
    
    # 准备输出文件名
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = os.path.join(output_dir, f"{base_name}_mesh.ply")
    
    # 构建CloudCompare命令
    cmd_args = [
        "-o", input_file,  # 打开输入文件
        "-DELAUNAY", "2.5D", "XY"  # 使用Delaunay三角网创建模型
    ]
    
    # 设置输出
    cmd_args.extend(["-M_EXPORT_FMT", "PLY"])
    cmd_args.extend(["-AUTO_SAVE", "ON"])
    cmd_args.extend(["-SAVE_MESHES", "FILE", output_file])
    
    # 执行命令
    success = run_cloudcompare_cmd(cc_exe, cmd_args)
    
    return success, output_file if success else None

def compute_volume(cc_exe, input_file, output_dir):
    """计算体积"""
    print(f"计算体积: {input_file}")
    
    # 准备输出文件名
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    report_file = os.path.join(output_dir, f"{base_name}_volume.txt")
    
    # 构建CloudCompare命令
    cmd_args = [
        "-o", input_file,  # 打开输入文件
        "-VOLUME", "ABOVE_BEST_FIT_PLANE"  # 计算高于最佳拟合平面的体积
    ]
    
    # 执行命令
    success = run_cloudcompare_cmd(cc_exe, cmd_args, silent=False)
    
    # 这里无法直接获取体积值，需要用户从CloudCompare界面读取
    # 或者使用Python解析CloudCompare输出
    
    return success

def create_cross_section(cc_exe, input_file, output_dir):
    """创建剖面"""
    print(f"创建剖面: {input_file}")
    
    # 准备输出文件名
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = os.path.join(output_dir, f"{base_name}_section.bin")
    
    # 构建CloudCompare命令
    cmd_args = [
        "-o", input_file,  # 打开输入文件
        "-CROSS_SECTION", "X", "0", "10"  # 沿X轴创建剖面，厚度为10单位
    ]
    
    # 设置输出
    cmd_args.extend(["-C_EXPORT_FMT", "BIN"])
    cmd_args.extend(["-AUTO_SAVE", "ON"])
    cmd_args.extend(["-SAVE_CLOUDS", "FILE", output_file])
    
    # 执行命令
    success = run_cloudcompare_cmd(cc_exe, cmd_args)
    
    return success, output_file if success else None

def create_multitemporal_analysis(cc_exe, input_files, output_dir):
    """多时相分析"""
    print(f"多时相分析: {len(input_files)}个点云")
    
    # 准备输出文件名
    output_file = os.path.join(output_dir, "multitemporal_analysis.bin")
    
    # 构建CloudCompare命令
    cmd_args = []
    
    # 加载所有点云
    for i, file in enumerate(input_files):
        cmd_args.extend(["-o", file])
        
        # 对每个点云重命名，添加时间标签
        base_name = os.path.splitext(os.path.basename(file))[0]
        cmd_args.extend(["-RENAME_SF", f"deformation", f"deformation_{base_name}"])
    
    # 如果有多个点云，计算它们之间的差异
    if len(input_files) > 1:
        # 计算点云A和点云B之间的差异
        cmd_args.extend(["-ICP"])  # 先配准点云
        cmd_args.extend(["-DIFF"])  # 计算差异
    
    # 设置输出
    cmd_args.extend(["-C_EXPORT_FMT", "BIN"])
    cmd_args.extend(["-AUTO_SAVE", "ON"])
    cmd_args.extend(["-SAVE_CLOUDS", "FILE", output_file])
    
    # 执行命令
    success = run_cloudcompare_cmd(cc_exe, cmd_args)
    
    return success, output_file if success else None

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='CloudCompare点云分析')
    parser.add_argument('-c', '--config', default='../../config/processing_params.yml',
                        help='配置文件路径')
    parser.add_argument('-i', '--input-dir', help='点云数据目录，默认从配置文件读取')
    parser.add_argument('-o', '--output-dir', help='分析结果目录，默认从配置文件读取')
    parser.add_argument('--cc-exe', help='CloudCompare可执行文件路径')
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    # 设置输入输出路径
    if args.input_dir:
        input_dir = args.input_dir
    else:
        input_dir = os.path.join(config['paths']['results'], 'point_cloud')
    
    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = os.path.join(config['paths']['results'], 'analysis')
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 查找CloudCompare可执行文件
    cc_exe = args.cc_exe if args.cc_exe else find_cloudcompare_exe()
    if not cc_exe:
        print("错误: 无法找到CloudCompare可执行文件，请指定路径或设置CLOUDCOMPARE_EXE环境变量")
        return 1
    
    print(f"使用CloudCompare: {cc_exe}")
    
    # 获取所有点云文件
    las_files = glob.glob(os.path.join(input_dir, "*.las"))
    if not las_files:
        print(f"错误: 在{input_dir}中未找到LAS格式点云文件")
        return 1
    
    print(f"找到{len(las_files)}个点云文件")
    
    # 对每个点云文件进行分析
    for las_file in las_files:
        print(f"\n分析点云: {las_file}")
        
        # 分割点云
        segment_success, segmented_file = segment_point_cloud(cc_exe, las_file, output_dir, config)
        
        # 分类点云
        classify_success, classified_file = classify_point_cloud(cc_exe, las_file, output_dir, config)
        
        # 创建网格模型
        mesh_success, mesh_file = create_mesh(cc_exe, las_file, output_dir)
        
        # 计算体积
        volume_success = compute_volume(cc_exe, las_file, output_dir)
        
        # 创建剖面
        section_success, section_file = create_cross_section(cc_exe, las_file, output_dir)
    
    # 如果有多个点云文件，进行多时相分析
    if len(las_files) > 1:
        multi_success, multi_file = create_multitemporal_analysis(cc_exe, las_files, output_dir)
    
    print("\n点云分析完成!")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 