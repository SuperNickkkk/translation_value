# 🛩️ 航空维修翻译评估系统 - 专业版

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)](README.md)

基于Flask的现代化Web应用，专为航空维修技术文档提供专业的**AI翻译评估服务**。系统集成多个大语言模型，提供精准的英中翻译质量评估，特别优化用于民航局技术文档和国际民航组织(ICAO)标准。

---

## ✨ 核心特性

### 🎯 专业功能
- **📁 智能数据导入** - 支持JSON格式批量翻译数据，自动数据验证和预处理
- **🧠 多模型翻译引擎** - 集成文心一言、Qwen、Gemma、ERNIE等多个专业翻译模型
- **📊 三维度专业评估** - 基于航空维修领域的专业评估标准（技术准确性、文档流畅性、专业术语精度）
- **📈 实时可视化监控** - 动态图表展示评估进度和结果分析
- **🎛️ 高级任务管理** - 支持任务暂停、恢复、终止等精细化控制
- **🔬 模型测试功能** - 单例翻译测试，快速验证模型状态和质量
- **📋 数据选择机制** - 支持按百分比、数量或全量进行评估数据筛选

### 🛠 技术特性
- **现代化响应式UI** - 基于Bootstrap 5的专业界面设计
- **实时WebSocket通信** - 任务状态和进度的实时更新
- **动态数据可视化** - Chart.js图表和实时性能监控
- **RESTful API架构** - 完整的后端API接口支持
- **本地模型集成** - 支持多个轻量级本地模型，降低API成本
- **智能错误处理** - 完善的异常处理和用户友好的错误提示
- **性能监控系统** - 实时监控模型响应时间和系统健康状态

---

## 🚀 快速开始

### 系统要求
- **Python 3.8+** (推荐3.9+)
- **操作系统** - Windows 10/11, macOS 10.15+, Ubuntu 18.04+
- **内存** - 至少4GB RAM（推荐8GB+用于本地模型）
- **磁盘空间** - 至少5GB可用空间（包含模型文件）
- **网络** - 稳定的互联网连接（用于在线模型API）

### 一键部署
```bash
# 1. 克隆项目
git clone https://github.com/SuperNickkkk/translation_value.git
cd translation_value

# 2. 创建并激活虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 3. 一键启动（自动安装依赖并启动服务）
python start.py
```

### 手动部署（可选）
```bash
# 安装依赖
pip install -r requirements.txt

# 启动Web应用
cd web_app && python run.py
```

**启动成功后访问：** 🌐 **http://127.0.0.1:5001**

---

## 📁 项目架构

```
translation_value/
├── 🚀 start.py                         # 一键启动脚本
├── 📦 requirements.txt                  # Python依赖包
├── ⚙️ translation_config.json          # 系统配置文件
├── 🧠 translation_engine.py            # 核心翻译引擎
├── 📊 evaluation_engine.py             # 专业评估引擎
├── 🖥️ local_model_manager.py           # 本地模型管理器
├── 📂 web_app/                         # Web应用核心
│   ├── 🌐 app.py                      # Flask主应用
│   ├── 🚀 run.py                      # Web服务启动器
│   ├── 🎨 templates/                  # HTML模板
│   ├── 📱 static/                     # 静态资源(CSS/JS)
│   └── 🛠️ utils/                      # 工具模块
├── 📊 data/                            # 示例和测试数据
│   ├── sample_translation_pairs.json   # 示例翻译对
│   └── aviation_manual_samples.json    # 航空手册样本
├── 🤖 local_model_server_*.py          # 本地模型服务器
├── 📋 logs/                            # 系统日志
├── 📈 results/                         # 评估结果
├── 📤 uploads/                         # 用户上传文件
└── 📚 docs/                            # 详细文档
```

---

## ⚙️ 配置指南

### API密钥配置
编辑 `translation_config.json` 设置你的模型API密钥：

```json
{
  "translation_models": {
    "ernie-4.5-0.3b": {
      "name": "文心一言ERNIE-4.5-0.3B",
      "api_key": "your-ernie-api-key-here",
      "base_url": "https://aistudio.baidu.com/llm/lmapi/v3",
      "model_id": "ernie-4.5-0.3b"
    },
    "qwen-turbo": {
      "name": "通义千问Turbo",
      "api_key": "your-qwen-api-key-here",
      "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
      "model_id": "qwen-turbo"
    }
  },
  "evaluation_model": {
    "name": "文心一言评估专用模型",
    "api_key": "your-evaluation-key-here",
    "model_id": "ernie-4.5-turbo-128k-preview"
  }
}
```

### 本地模型支持（无需API密钥）
系统内置多个轻量级本地模型，开箱即用：

| 模型名称 | 模型大小 | 服务端口 | 特点 |
|---------|---------|----------|------|
| **Gemma-3-270M** | 270M参数 | 8081 | Google开源，快速响应 |
| **Qwen2.5-0.5B** | 500M参数 | 8082 | 阿里云开源，中文优化 |
| **ERNIE-4.5-0.3B** | 300M参数 | 8083 | 百度开源，专业场景 |
| **Qwen3-0.6B** | 600M参数 | 8084 | 最新版本，性能提升 |

### 环境变量配置（可选）
创建 `.env` 文件进行高级配置：
```env
# Flask应用配置
SECRET_KEY=your-super-secret-key-here
FLASK_ENV=production
DEBUG=False

# API服务配置
ERNIE_API_KEY=your-ernie-api-key
QWEN_API_KEY=your-qwen-api-key
GEMINI_API_KEY=your-gemini-api-key

# 本地模型端口配置
GEMMA_PORT=8081
QWEN25_PORT=8082
ERNIE_PT_PORT=8083
QWEN3_PORT=8084

# 高级设置
MAX_UPLOAD_SIZE=50MB
REQUEST_TIMEOUT=120
BATCH_SIZE=10
```

---

## 🎨 使用指南

### 1. 数据准备
创建符合航空维修标准的JSON格式翻译数据：

```json
{
  "metadata": {
    "description": "A320飞机维修翻译评估数据集",
    "aircraft_type": "Airbus A320",
    "manual_section": "ATA 32 - Landing Gear",
    "created_time": "2024-08-31 12:00:00",
    "total_pairs": 213,
    "difficulty_distribution": {
      "easy": 89,
      "medium": 95,
      "hard": 29
    }
  },
  "translation_pairs": [
    {
      "id": "av_001",
      "source_text": "Check the hydraulic pressure in the landing gear retraction system before flight.",
      "target_text": "飞行前检查起落架收放系统的液压压力。",
      "source_lang": "en",
      "target_lang": "zh",
      "category": "维修程序",
      "difficulty": "medium",
      "context": "起落架系统维护",
      "ata_code": "ATA 32-31-00",
      "keywords": ["hydraulic", "landing gear", "pressure"]
    }
  ]
}
```

### 2. Web界面操作
1. **🌐 访问系统** - 打开 http://127.0.0.1:5001
2. **📤 上传数据** - 拖拽或选择JSON文件上传
3. **📊 数据选择** - 选择评估数据的比例或数量
4. **🤖 模型选择** - 勾选要使用的翻译模型
5. **🧪 模型测试** - 点击"测试选中模型"验证模型状态
6. **▶️ 开始评估** - 启动批量翻译评估任务
7. **🎛️ 任务控制** - 实时暂停/恢复/终止正在运行的任务
8. **📈 结果分析** - 查看实时图表和详细评估报告

### 3. 高级功能
- **📊 性能监控** - 实时查看各模型的响应时间和成功率
- **📋 日志查看** - 系统运行日志的实时查看和下载
- **🔄 任务历史** - 查看和管理历史评估任务
- **📈 对比分析** - 多模型结果的横向对比分析
- **📤 结果导出** - JSON、CSV、HTML多格式结果导出

---

## 📊 评估体系

### 航空维修专业评估标准

系统采用针对航空维修领域优化的**三维度评估体系**：

| 评估维度 | 权重 | 详细说明 | 评分标准 |
|---------|------|----------|----------|
| **🎯 技术准确性** | 40% | 技术内容完全准确，与参考译文技术含义一致，严格遵循民航局/ICAO标准 | 5.0分-完全准确<br/>3.0分-基本准确<br/>1.0分-严重错误 |
| **📝 文档流畅性** | 30% | 语言自然流畅，完全符合技术文档表达习惯和规范 | 5.0分-自然流畅<br/>3.0分-可理解<br/>1.0分-严重不通 |
| **🔧 专业术语精度** | 30% | 航空专业术语使用完全正确，严格遵循行业标准词汇 | 5.0分-术语完全正确<br/>3.0分-部分正确<br/>1.0分-术语严重错误 |

#### 质量控制规则
- ❌ **未翻译检查**: 如果保留原文未翻译 → 所有维度自动降至2分以下
- ❌ **语言错误检查**: 如果目标语言使用错误 → 准确性固定1分
- ❌ **安全隐患检查**: 如果存在安全隐患误译 → 总分上限1.5分

**综合得分公式**: 总分 = 技术准确性×0.4 + 文档流畅性×0.3 + 专业术语×0.3

---

## 🔧 本地模型部署

### 自动模式（推荐）
系统启动时会自动下载和配置本地模型：
```bash
python start.py  # 自动处理所有本地模型
```

### 手动模式
```bash
# 单独启动特定模型服务器
python local_model_server_gemma_3_270m.py      # Gemma模型
python local_model_server_qwen2.5_0.5b_instruct.py  # Qwen2.5模型
python local_model_server_ernie_4_5_0_3b_pt.py      # ERNIE模型
python local_model_server_qwen3_0_6b.py             # Qwen3模型
```

### 模型健康检查
```bash
# 检查所有本地模型状态
curl http://127.0.0.1:8081/health  # Gemma
curl http://127.0.0.1:8082/health  # Qwen2.5
curl http://127.0.0.1:8083/health  # ERNIE
curl http://127.0.0.1:8084/health  # Qwen3
```

---

## 🚀 部署选项

### 开发环境
```bash
python start.py
```

### 生产环境
```bash
# 使用Gunicorn WSGI服务器
pip install gunicorn
cd web_app
gunicorn -w 4 -b 0.0.0.0:5001 --timeout 300 app:app

# 使用Docker容器化部署
docker build -t aviation-translation-system .
docker run -d -p 5001:5001 --name aviation-trans aviation-translation-system
```

### 云服务部署
详见文档：[部署指南](docs/DEPLOYMENT_GUIDE.md)

---

## 🐛 故障排除

### 常见问题解决

1. **📊 应用启动失败**
   ```bash
   # 检查Python版本和虚拟环境
   python --version && which python
   
   # 查看详细启动日志
   python start.py --verbose
   ```

2. **🔌 端口占用问题**
   ```bash
   # 查看端口占用情况
   lsof -i :5001
   
   # 清理占用进程
   pkill -f "python.*app.py"
   ```

3. **🤖 本地模型无法启动**
   ```bash
   # 检查模型文件完整性
   python -c "import torch; print('PyTorch可用' if torch.cuda.is_available() else 'CPU模式')"
   
   # 手动下载模型
   python download_real_models.py
   ```

4. **🔑 API密钥错误**
   - 验证API密钥格式和有效性
   - 检查API余额和调用限制
   - 确认网络连接和防火墙设置

5. **📁 文件上传失败**
   - 确认文件格式为UTF-8编码的JSON
   - 检查文件大小（默认限制50MB）
   - 验证JSON数据结构完整性

### 获取技术支持
- 📋 **系统日志**: 查看 `logs/` 目录下的详细日志
- 🔍 **健康检查**: 访问 `/api/health` 端点查看系统状态
- 📖 **API文档**: 访问 `/api/docs` 查看完整API说明
- 🐛 **问题反馈**: 提交Issue到 [GitHub仓库](https://github.com/SuperNickkkk/translation_value/issues)

---

## 📝 更新日志

### v3.0.0 (最新版本 - 2024.08.31)
- ✨ **重大功能更新**
  - 🎛️ **任务控制系统** - 支持评估任务的暂停、恢复、终止操作
  - 🧪 **模型测试功能** - 单例翻译测试，快速验证模型状态
  - 📊 **数据选择机制** - 灵活的数据筛选（百分比/数量/全量）
  - 🔧 **航空维修专业化** - 针对航空维修领域深度优化的提示词

- 🚀 **性能优化**
  - ⚡ **并发处理优化** - 提升多模型并行评估效率
  - 📈 **实时监控增强** - 更精确的性能指标和健康检查
  - 🛡️ **错误处理完善** - 更robust的异常处理和用户提示

- 🎨 **用户体验提升**
  - 📱 **响应式界面优化** - 更现代化的UI/UX设计
  - 🔄 **实时状态更新** - WebSocket实时通信优化
  - 📊 **可视化增强** - 更丰富的图表和数据展示

### v2.x.x (已升级)
- 基础Web版本功能
- 多模型支持和基础评估功能

---

## 📄 许可证

本项目采用 **MIT License** 开源许可证。详见 [LICENSE](LICENSE) 文件。

---

## 🤝 贡献指南

欢迎社区贡献！我们鼓励以下类型的贡献：

1. **🐛 Bug修复** - 发现问题请提交Issue
2. **✨ 新功能开发** - 提交Feature Request
3. **📚 文档改进** - 完善使用说明和API文档
4. **🧪 测试用例** - 增加测试覆盖率
5. **🌐 国际化** - 多语言界面支持

### 贡献流程
```bash
1. Fork本仓库
2. 创建特性分支: git checkout -b feature/AmazingFeature
3. 提交更改: git commit -m 'Add some AmazingFeature'
4. 推送到分支: git push origin feature/AmazingFeature
5. 提交Pull Request
```

---

## 📞 联系方式

- 🏠 **项目主页**: [GitHub Repository](https://github.com/SuperNickkkk/translation_value)
- 🐛 **问题反馈**: [GitHub Issues](https://github.com/SuperNickkkk/translation_value/issues)
- 💬 **讨论区**: [GitHub Discussions](https://github.com/SuperNickkkk/translation_value/discussions)
- 📧 **技术支持**: [Email Support](mailto:support@example.com)

---

## 🏆 致谢

感谢以下开源项目和技术支持：
- **🔥 PyTorch** - 深度学习框架
- **🌐 Flask** - Web应用框架  
- **🎨 Bootstrap** - 前端UI框架
- **📊 Chart.js** - 数据可视化
- **🤗 Hugging Face** - 预训练模型
- **📊 Pandas** - 数据分析
- **🚀 各大模型提供商** - API服务支持

---

**⭐ 如果这个项目对你有帮助，请给它一个star支持我们！**

## 🎯 快速开始检查清单

- [ ] **1. 环境准备** - Python 3.8+, 虚拟环境激活
- [ ] **2. 项目克隆** - `git clone` 并进入项目目录
- [ ] **3. 依赖安装** - `python start.py` 自动安装
- [ ] **4. 配置设置** - 编辑 `translation_config.json` 添加API密钥
- [ ] **5. 服务启动** - 访问 http://127.0.0.1:5001
- [ ] **6. 数据上传** - 使用 `data/` 目录示例文件测试
- [ ] **7. 模型测试** - 点击"测试选中模型"验证功能
- [ ] **8. 评估启动** - 选择数据和模型，开始翻译评估
- [ ] **9. 结果查看** - 监控进度并下载评估报告

🎉 **现在就开始你的专业航空维修翻译评估之旅吧！**

---

*最后更新时间: 2024年8月31日*