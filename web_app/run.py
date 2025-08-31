#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞机维修翻译评估系统 Web版本启动脚本
"""

import os
import sys
from pathlib import Path

# 添加当前目录到路径以便导入app模块
sys.path.insert(0, str(Path(__file__).parent))

from app import app, initialize_system

if __name__ == '__main__':
    print("🛩️ 飞机维修翻译评估系统 - Web版本")
    print("=" * 50)
    
    # 初始化系统
    if initialize_system():
        print("✅ 系统初始化成功")
        print("🌐 启动Web服务器...")
        print("📱 访问地址: http://localhost:5001")
        print("🚀 功能特性:")
        print("   • 一体化界面 - 模型选择、评估、结果展示")
        print("   • 实时进度监控")
        print("   • 可视化结果对比")
        print("   • 专业评估报告")
        print("=" * 50)
        
        # 启动Flask应用
        app.run(
            debug=False,  # 暂时禁用调试模式
            host='127.0.0.1',
            port=5001,
            threaded=True
        )
    else:
        print("❌ 系统初始化失败")
        print("请检查:")
        print("1. Python依赖包是否安装完整")
        print("2. 核心模块是否存在")
        print("3. 配置文件是否正确")
        sys.exit(1)

