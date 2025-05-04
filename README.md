# 基于GMTSAR-CloudCompare框架的区域地表形变时空演化与多维特征分析

## 项目简介
本项目旨在利用InSAR数据处理与点云分析技术，实现对区域地表形变的时空演化分析与多维特征提取。系统整合了GMTSAR的InSAR处理能力和CloudCompare的点云分析功能，构建了一套完整的地表形变分析框架。

### 主要功能
- SAR数据干涉处理和形变场提取
- 形变数据格式转换与点云生成
- 多时相形变场分析与可视化
- 形变特征提取与分类
- 变形区域的三维建模与分析

## 环境设置

### 依赖项
- GMTSAR (≥ 6.0)
- CloudCompare (≥ 2.12)
- Python (≥ 3.8)
- 其他Python依赖库（详见`requirements.txt`）

### 安装步骤
1. 安装GMTSAR：
   ```bash
   # 请参考GMTSAR官方文档安装
   # https://github.com/gmtsar/gmtsar
   ```

2. 安装CloudCompare：
   从[官方网站](https://www.danielgm.net/cc/)下载并安装CloudCompare

3. 安装Python依赖：
   ```bash
   pip install -r requirements.txt
   ```

## 数据准备
1. 获取SAR数据（支持Sentinel-1、ALOS-2等卫星数据）
2. 准备数字高程模型(DEM)数据
3. 将数据放置在`data/raw`目录下

## 工作流程
1. 配置处理参数：编辑`config/*.yml`文件
2. InSAR数据处理：运行`scripts/gmtsar_pipeline`中的脚本
3. 数据格式转换：使用`scripts/data_conversion`中的工具
4. 点云分析：通过CloudCompare或`scripts/analysis`中的脚本
5. 结果可视化与分析：查看`notebooks`中的示例

## 目录结构
```
Deformation_Analysis/
├── config/               # 配置文件
├── data/                 # 数据存储
│   ├── raw/              # 原始数据
│   ├── processed/        # 处理后的数据
│   └── results/          # 分析结果
├── scripts/              # 处理脚本
│   ├── gmtsar_pipeline/  # GMTSAR处理流程脚本
│   ├── data_conversion/  # 数据格式转换脚本
│   └── analysis/         # 数据分析脚本
├── notebooks/            # Jupyter笔记本示例
├── docs/                 # 文档
├── examples/             # 使用示例
├── tests/                # 测试代码
└── requirements.txt      # Python依赖
```

## 许可证
MIT

## 联系方式
请通过GitHub Issues提交问题或建议
