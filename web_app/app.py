# -*- coding: utf-8 -*-
"""
飞机维修翻译评估系统 - Web版本主应用
专业的Web界面，集成模型选择、测试结果、评估展示于一体
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path
# 添加Qwen API客户端支持
sys.path.append(str(Path(__file__).parent.parent))
from qwen_api_client import QwenAPIClient

from flask import Flask, render_template, request, jsonify, session, flash, redirect, url_for
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import asyncio
from threading import Thread
import uuid

# 添加父目录到路径，以便导入核心模块
sys.path.append(str(Path(__file__).parent.parent))

from translation_evaluation_config import TranslationEvaluationConfig, ModelConfig
from translation_data_manager import TranslationDataManager, TranslationPair
from translation_engine import SpecializedTranslationEngine
from evaluation_engine import EvaluationEngine
from local_model_manager import local_model_manager, initialize_local_models

# 导入新的监控工具
from web_app.utils.performance_monitor import performance_monitor
from utils.log_manager import log_manager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'aviation-translation-evaluation-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aviation_translation.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

db = SQLAlchemy(app)

# 全局变量存储系统组件
translation_system = None
config_manager = None
data_manager = None
translation_engine = None
evaluation_engine = None

# 任务状态存储和控制
active_tasks = {}
task_control_flags = {}  # 任务控制标志：{task_id: {'paused': bool, 'terminated': bool}}

class EvaluationTask(db.Model):
    """评估任务数据模型"""
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    data_file = db.Column(db.String(500))
    results_file = db.Column(db.String(500))
    progress = db.Column(db.Integer, default=0)
    total_pairs = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)

class TranslationResult(db.Model):
    """翻译结果数据模型"""
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(36), db.ForeignKey('evaluation_task.id'), nullable=False)
    pair_id = db.Column(db.String(100), nullable=False)
    source_text = db.Column(db.Text, nullable=False)
    target_text = db.Column(db.Text, nullable=False)
    model_name = db.Column(db.String(100), nullable=False)
    translated_text = db.Column(db.Text)
    accuracy_score = db.Column(db.Float)
    fluency_score = db.Column(db.Float)
    terminology_score = db.Column(db.Float)
    overall_score = db.Column(db.Float)
    evaluation_details = db.Column(db.Text)  # JSON格式的详细评估信息

def initialize_system():
    """初始化翻译评估系统"""
    global translation_system, config_manager, data_manager, translation_engine, evaluation_engine
    
    try:
        # 创建必要的目录
        os.makedirs('uploads', exist_ok=True)
        os.makedirs('results', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
        # 初始化配置管理器
        config_file = Path(__file__).parent.parent / 'translation_config.json'
        config_manager = TranslationEvaluationConfig(str(config_file))
        if config_file.exists():
            config_manager.load_config()

        # 加载 .env（使用项目根目录 .env），并用环境变量覆盖在线模型 API Key（持久化到配置文件）
        try:
            dotenv_path = Path(__file__).parent.parent / '.env'
            load_dotenv(dotenv_path=dotenv_path)
            ernie_key = os.getenv('ERNIE_API_KEY', '').strip()
            qwen_key = os.getenv('QWEN_API_KEY', '').strip()
            qwen_base = os.getenv('QWEN_BASE_URL', '').strip()
            qwen_model = os.getenv('QWEN_MODEL_ID', '').strip()
            changed = False
            # 覆盖在线模型 Key（若提供）
            if 'ernie-4.5-0.3b' in config_manager.translation_models and ernie_key:
                config_manager.translation_models['ernie-4.5-0.3b'].api_key = ernie_key
                changed = True
            if 'qwen3-8b' in config_manager.translation_models:
                if (qwen_key or ernie_key):
                    # 兼容同一平台 Key 复用（若 QWEN_API_KEY 未提供则回落到 ERNIE_API_KEY）
                    config_manager.translation_models['qwen3-8b'].api_key = (qwen_key or ernie_key)
                    changed = True
                if qwen_base:
                    config_manager.translation_models['qwen3-8b'].base_url = qwen_base
                    changed = True
                if qwen_model:
                    config_manager.translation_models['qwen3-8b'].model_id = qwen_model
                    changed = True
            # 覆盖评估模型 Key（若提供 ERNIE_API_KEY）
            if config_manager.evaluation_model and ernie_key:
                config_manager.evaluation_model.api_key = ernie_key
                changed = True
            if changed:
                config_manager.save_config()
        except Exception as _e:
            logging.warning(f"环境变量覆盖配置失败: {_e}")
        
        # 初始化数据管理器
        data_manager = TranslationDataManager()
        
        # 初始化翻译引擎
        translation_engine = SpecializedTranslationEngine()
        
        # 初始化本地模型
        initialize_local_models()
        
        # 初始化评估引擎 (稍后配置)
        evaluation_engine = None
        
        # 启动性能监控
        performance_monitor.start_monitoring()
        # 注册两个本地模型端点用于监控
        performance_monitor.register_local_model('gemma-3-270m', 'http://127.0.0.1:8081')
        performance_monitor.register_local_model('qwen2.5-0.5b-instruct', 'http://127.0.0.1:8082')
        performance_monitor.register_local_model('qwen3-0.6b', 'http://127.0.0.1:8084')
        # 新增：注册 ERNIE-4.5-0.3B-PT 本地服务（MPS）
        performance_monitor.register_local_model('ernie-4.5-0.3b-pt', 'http://127.0.0.1:8083')
        
        # 尝试预启动本地模型（避免首次调用时启动失败）
        try:
            from local_model_manager import local_model_manager as _mgr
            _mgr.start_model("qwen2.5-0.5b-instruct")
            _mgr.start_model("ernie-4.5-0.3b-pt")
            _mgr.start_model("gemma-3-270m")
            _mgr.start_model("qwen3-0.6b")
        except Exception as _e:
            logging.warning(f"预启动本地模型失败: {_e}")

        # 移除示例性能数据，改为仅记录真实调用
        
        # 创建数据库表
        with app.app_context():
            db.create_all()
        
        logging.info("Web系统初始化完成")
        return True
        
    except Exception as e:
        logging.error(f"系统初始化失败: {e}")
        return False

@app.route('/')
def index():
    """主页 - 集成所有功能的单页面应用"""
    # 获取可用的翻译模型
    available_models = []
    if config_manager:
        for model_key, model_config in config_manager.translation_models.items():
            available_models.append({
                'key': model_key,
                'name': model_config.name,
                'configured': bool(model_config.api_key)
            })
    
    # 获取评估模型状态
    evaluation_model_configured = False
    if config_manager and config_manager.evaluation_model:
        evaluation_model_configured = bool(config_manager.evaluation_model.api_key)
    
    # 获取最近的任务
    recent_tasks = EvaluationTask.query.order_by(EvaluationTask.created_at.desc()).limit(5).all()
    
    return render_template('index.html', 
                         available_models=available_models,
                         evaluation_model_configured=evaluation_model_configured,
                         recent_tasks=recent_tasks)

@app.route('/api/models', methods=['GET', 'POST'])
def manage_models():
    """管理翻译模型API"""
    if request.method == 'GET':
        # 返回模型配置信息
        models = {}
        if config_manager:
            for model_key, model_config in config_manager.translation_models.items():
                models[model_key] = {
                    'name': model_config.name,
                    'configured': bool(model_config.api_key),
                    'base_url': model_config.base_url,
                    'model_id': model_config.model_id
                }
        return jsonify(models)
    
    elif request.method == 'POST':
        # 添加或更新模型配置
        data = request.get_json()
        model_key = data.get('model_key')
        
        if not model_key:
            return jsonify({'error': '缺少模型标识'}), 400
        
        try:
            # 使用配置管理器的方法来添加模型
            success = config_manager.add_translation_model(
                model_key=model_key,
                api_key=data.get('api_key', ''),
                name=data.get('name', ''),
                base_url=data.get('base_url', ''),
                model_id=data.get('model_id', ''),
                temperature=data.get('temperature', 0.3),
                max_tokens=data.get('max_tokens', 1000)
            )
            
            if not success:
                return jsonify({'error': f'不支持的模型类型: {model_key}'}), 400
            
            # 保存配置到文件
            config_manager.save_config()
            
            return jsonify({'message': '模型配置已保存', 'success': True})
            
        except Exception as e:
            return jsonify({'error': f'保存配置失败: {str(e)}'}), 500

@app.route('/api/evaluation_model', methods=['GET', 'POST'])
def manage_evaluation_model():
    """管理评估模型API"""
    if request.method == 'GET':
        if config_manager and config_manager.evaluation_model:
            return jsonify({
                'name': config_manager.evaluation_model.name,
                'configured': bool(config_manager.evaluation_model.api_key),
                'base_url': config_manager.evaluation_model.base_url,
                'model_id': config_manager.evaluation_model.model_id
            })
        return jsonify({'configured': False})
    
    elif request.method == 'POST':
        data = request.get_json()
        
        try:
            # 使用配置管理器的方法来更新评估模型
            success = config_manager.update_evaluation_model(
                api_key=data.get('api_key', ''),
                name=data.get('name', 'ERNIE评估模型'),
                base_url=data.get('base_url', ''),
                model_id=data.get('model_id', ''),
                temperature=data.get('temperature', 0.3),
                max_tokens=data.get('max_tokens', 1000)
            )
            
            if not success:
                return jsonify({'error': '更新评估模型失败'}), 500
            
            # 保存配置到文件
            config_manager.save_config()
            
            return jsonify({'message': '评估模型配置已保存', 'success': True})
            
        except Exception as e:
            return jsonify({'error': f'保存配置失败: {str(e)}'}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """上传翻译数据文件"""
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file and file.filename.lower().endswith('.json'):
        try:
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # 验证JSON格式
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 验证数据格式
            if 'translation_pairs' not in data:
                return jsonify({'error': 'JSON文件格式错误，缺少translation_pairs字段'}), 400
            
            pairs_count = len(data['translation_pairs'])
            
            return jsonify({
                'message': '文件上传成功',
                'filename': filename,
                'filepath': filepath,
                'pairs_count': pairs_count,
                'success': True
            })
            
        except json.JSONDecodeError:
            return jsonify({'error': 'JSON文件格式错误'}), 400
        except Exception as e:
            return jsonify({'error': f'文件处理失败: {str(e)}'}), 500
    
    return jsonify({'error': '只支持JSON格式文件'}), 400

@app.route('/api/evaluate', methods=['POST'])
def start_evaluation():
    """开始翻译评估任务"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '缺少请求数据'}), 400
    
    filepath = data.get('filepath')
    task_name = data.get('task_name', f'评估任务_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    selected_models = data.get('selected_models', [])
    
    # 数据选择参数
    data_selection = data.get('data_selection', {
        'mode': 'all',
        'value': None
    })
    
    if not filepath or not os.path.exists(filepath):
        return jsonify({'error': '数据文件不存在'}), 400
    
    if not selected_models:
        return jsonify({'error': '请至少选择一个翻译模型'}), 400
    
    # 检查评估模型是否配置
    if not config_manager or not config_manager.evaluation_model or not config_manager.evaluation_model.api_key:
        return jsonify({'error': '评估模型未配置，请先配置评估模型'}), 400
    
    try:
        # 创建评估任务
        task_id = str(uuid.uuid4())
        task = EvaluationTask(
            id=task_id,
            name=task_name,
            status='pending',
            data_file=filepath
        )
        
        # 读取数据文件获取总数
        with open(filepath, 'r', encoding='utf-8') as f:
            data_content = json.load(f)
            task.total_pairs = len(data_content.get('translation_pairs', []))
        
        db.session.add(task)
        db.session.commit()
        
        # 启动后台评估任务
        thread = Thread(target=run_evaluation_task, args=(task_id, filepath, selected_models, data_selection))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'message': '评估任务已启动',
            'task_id': task_id,
            'success': True
        })
        
    except Exception as e:
        return jsonify({'error': f'启动评估任务失败: {str(e)}'}), 500

def apply_data_selection(translation_pairs, data_selection):
    """根据数据选择参数筛选翻译对数据"""
    if not data_selection or data_selection.get('mode') == 'all':
        return translation_pairs
    
    mode = data_selection.get('mode')
    value = data_selection.get('value')
    
    if not value or value <= 0:
        return translation_pairs
    
    total_pairs = len(translation_pairs)
    
    if mode == 'percentage':
        # 按百分比选择
        percentage = min(100, max(1, value))  # 确保在1-100范围内
        selected_count = max(1, int(total_pairs * percentage / 100))
        return translation_pairs[:selected_count]
    
    elif mode == 'count':
        # 按数量选择
        selected_count = min(total_pairs, max(1, int(value)))  # 不超过总数
        return translation_pairs[:selected_count]
    
    return translation_pairs

def run_evaluation_task(task_id, filepath, selected_models, data_selection=None):
    """运行评估任务的后台函数"""
    with app.app_context():
        task = EvaluationTask.query.get(task_id)
        if not task:
            return
        
        # 初始化任务控制标志
        task_control_flags[task_id] = {'paused': False, 'terminated': False}
        
        try:
            task.status = 'running'
            db.session.commit()
            
            # 清空之前的数据，避免ID重复
            data_manager.translation_pairs.clear()
            
            # 加载翻译数据（兼容英->中测试集）
            data_manager.load_translation_pairs_from_json(filepath)
            translation_pairs = list(data_manager.translation_pairs.values())
            
            # 根据数据选择参数筛选数据
            if data_selection:
                translation_pairs = apply_data_selection(translation_pairs, data_selection)
            
            # 配置翻译引擎
            for model_key in selected_models:
                if model_key in config_manager.translation_models:
                    model_config = config_manager.translation_models[model_key]
                    translation_engine.add_model(model_key, model_config)
            
            # 初始化评估引擎
            if config_manager.evaluation_model:
                # 确保传递正确的ModelConfig对象
                eval_config = config_manager.evaluation_model
                if hasattr(eval_config, '__dict__'):
                    # 如果是ModelConfig对象，直接使用
                    evaluation_engine = EvaluationEngine(eval_config)
                else:
                    # 如果是字典，转换为ModelConfig对象
                    from translation_evaluation_config import ModelConfig
                    eval_config_dict = eval_config if isinstance(eval_config, dict) else eval_config.__dict__
                    evaluation_engine = EvaluationEngine(ModelConfig(**eval_config_dict))
            else:
                raise Exception("评估模型未配置")
            
            # 执行翻译和评估
            all_results = []
            total_pairs = len(translation_pairs)
            
            for i, pair in enumerate(translation_pairs):
                try:
                    # 检查任务控制标志
                    control_flags = task_control_flags.get(task_id, {})
                    
                    # 检查是否被终止
                    if control_flags.get('terminated', False):
                        task.status = 'terminated'
                        task.error_message = "任务被用户终止"
                        db.session.commit()
                        return
                    
                    # 检查是否被暂停
                    while control_flags.get('paused', False):
                        task.status = 'paused'
                        db.session.commit()
                        time.sleep(1)  # 等待1秒后重新检查
                        control_flags = task_control_flags.get(task_id, {})
                        
                        # 在暂停期间也要检查终止
                        if control_flags.get('terminated', False):
                            task.status = 'terminated'
                            task.error_message = "任务在暂停期间被终止"
                            db.session.commit()
                            return
                    
                    # 恢复运行状态
                    if task.status == 'paused':
                        task.status = 'running'
                        db.session.commit()
                    
                    # 更新进度
                    progress = int((i / total_pairs) * 100)
                    task.progress = progress
                    db.session.commit()
                    
                    # 对每个选择的模型进行翻译
                    for model_key in selected_models:
                        # 执行翻译（返回 TranslationResult 对象）
                        translation_result = translation_engine.translate_single(
                            model_key,
                            pair
                        )
                        
                        # 执行评估（返回 EvaluationResult 对象）
                        evaluation_result = evaluation_engine.evaluate_single(
                            pair,
                            translation_result
                        )
                        
                        # 保存结果到数据库
                        result = TranslationResult(
                            task_id=task_id,
                            pair_id=pair.id,
                            source_text=pair.source_text,
                            target_text=pair.target_text,
                            model_name=model_key,
                            translated_text=translation_result.translated_text,
                            accuracy_score=evaluation_result.accuracy_score,
                            fluency_score=evaluation_result.fluency_score,
                            terminology_score=evaluation_result.terminology_score,
                            overall_score=evaluation_result.overall_score,
                            evaluation_details=json.dumps(evaluation_result.__dict__, ensure_ascii=False)
                        )
                        db.session.add(result)
                        all_results.append(result)
                
                except Exception as e:
                    logging.error(f"处理翻译对 {pair.id} 时出错: {e}")
                    continue
            
            # 保存最终结果
            results_filename = f"evaluation_results_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            results_filepath = os.path.join('results', results_filename)
            
            # 生成结果报告
            report_data = generate_evaluation_report(all_results, selected_models)
            with open(results_filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            # 更新任务状态
            task.status = 'completed'
            task.progress = 100
            task.completed_at = datetime.utcnow()
            task.results_file = results_filepath
            db.session.commit()
            
        except Exception as e:
            # 任务失败
            task.status = 'failed'
            task.error_message = str(e)
            db.session.commit()
            # 详细的错误日志
            import traceback
            error_details = traceback.format_exc()
            logging.error(f"评估任务 {task_id} 失败: {e}")
            logging.error(f"详细错误信息: {error_details}")
            print(f"[DEBUG] 评估任务失败详情: {error_details}")

def generate_evaluation_report(results, models):
    """生成评估报告"""
    report = {
        'summary': {
            'total_pairs': len(set(r.pair_id for r in results)),
            'models_tested': models,
            'evaluation_time': datetime.now().isoformat()
        },
        'model_performance': {},
        'detailed_results': []
    }
    
    # 按模型统计性能
    for model in models:
        model_results = [r for r in results if r.model_name == model]
        if model_results:
            avg_accuracy = sum(r.accuracy_score or 0 for r in model_results) / len(model_results)
            avg_fluency = sum(r.fluency_score or 0 for r in model_results) / len(model_results)
            avg_terminology = sum(r.terminology_score or 0 for r in model_results) / len(model_results)
            avg_overall = sum(r.overall_score or 0 for r in model_results) / len(model_results)
            
            report['model_performance'][model] = {
                'average_accuracy': round(avg_accuracy, 2),
                'average_fluency': round(avg_fluency, 2),
                'average_terminology': round(avg_terminology, 2),
                'average_overall': round(avg_overall, 2),
                'total_translations': len(model_results)
            }
    
    # 详细结果
    for result in results:
        report['detailed_results'].append({
            'pair_id': result.pair_id,
            'source_text': result.source_text,
            'target_text': result.target_text,
            'model_name': result.model_name,
            'translated_text': result.translated_text,
            'scores': {
                'accuracy': result.accuracy_score,
                'fluency': result.fluency_score,
                'terminology': result.terminology_score,
                'overall': result.overall_score
            }
        })
    
    return report

@app.route('/api/tasks/<task_id>')
def get_task_status(task_id):
    """获取任务状态"""
    task = EvaluationTask.query.get_or_404(task_id)
    
    # 获取任务的翻译结果
    results = TranslationResult.query.filter_by(task_id=task_id).all()
    
    task_data = {
        'id': task.id,
        'name': task.name,
        'status': task.status,
        'progress': task.progress,
        'created_at': task.created_at.isoformat() if task.created_at else None,
        'completed_at': task.completed_at.isoformat() if task.completed_at else None,
        'total_pairs': task.total_pairs,
        'error_message': task.error_message,
        'results_count': len(results)
    }
    
    # 如果任务完成，包含结果统计
    if task.status == 'completed' and results:
        # 按模型分组结果
        model_stats = {}
        for result in results:
            if result.model_name not in model_stats:
                model_stats[result.model_name] = {
                    'count': 0,
                    'avg_accuracy': 0,
                    'avg_fluency': 0,
                    'avg_terminology': 0,
                    'avg_overall': 0
                }
            
            stats = model_stats[result.model_name]
            stats['count'] += 1
            stats['avg_accuracy'] += result.accuracy_score or 0
            stats['avg_fluency'] += result.fluency_score or 0
            stats['avg_terminology'] += result.terminology_score or 0
            stats['avg_overall'] += result.overall_score or 0
        
        # 计算平均值
        for model, stats in model_stats.items():
            count = stats['count']
            stats['avg_accuracy'] = round(stats['avg_accuracy'] / count, 2)
            stats['avg_fluency'] = round(stats['avg_fluency'] / count, 2)
            stats['avg_terminology'] = round(stats['avg_terminology'] / count, 2)
            stats['avg_overall'] = round(stats['avg_overall'] / count, 2)
        
        task_data['model_statistics'] = model_stats
    
    return jsonify(task_data)

@app.route('/api/tasks/<task_id>/pause', methods=['POST'])
def pause_task(task_id):
    """暂停任务"""
    task = EvaluationTask.query.get_or_404(task_id)
    
    if task.status not in ['running']:
        return jsonify({'error': '只能暂停正在运行的任务'}), 400
    
    # 设置暂停标志
    if task_id in task_control_flags:
        task_control_flags[task_id]['paused'] = True
    
    return jsonify({'success': True, 'message': '任务暂停请求已发送'})

@app.route('/api/tasks/<task_id>/resume', methods=['POST'])
def resume_task(task_id):
    """恢复任务"""
    task = EvaluationTask.query.get_or_404(task_id)
    
    if task.status not in ['paused']:
        return jsonify({'error': '只能恢复已暂停的任务'}), 400
    
    # 清除暂停标志
    if task_id in task_control_flags:
        task_control_flags[task_id]['paused'] = False
    
    return jsonify({'success': True, 'message': '任务恢复请求已发送'})

@app.route('/api/tasks/<task_id>/terminate', methods=['POST'])
def terminate_task(task_id):
    """终止任务"""
    task = EvaluationTask.query.get_or_404(task_id)
    
    if task.status not in ['running', 'paused']:
        return jsonify({'error': '只能终止正在运行或暂停的任务'}), 400
    
    # 设置终止标志
    if task_id in task_control_flags:
        task_control_flags[task_id]['terminated'] = True
    
    return jsonify({'success': True, 'message': '任务终止请求已发送'})

@app.route('/api/models/test', methods=['POST'])
def test_models():
    """使用示例翻译对测试选中的模型"""
    try:
        data = request.get_json()
        selected_models = data.get('selected_models', [])
        
        if not selected_models:
            return jsonify({'error': '未选择任何模型'}), 400
        
        # 获取示例翻译对（使用数据集中的第一条）
        sample_pair = None
        try:
            # 尝试从最近上传的文件获取示例
            data_manager.translation_pairs.clear()
            
            # 查找最近的JSON数据文件
            data_dir = Path(__file__).parent.parent / "data"
            json_files = list(data_dir.glob("*.json"))
            
            if json_files:
                # 使用最新的JSON文件
                latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
                data_manager.load_translation_pairs_from_json(str(latest_file))
                
                if data_manager.translation_pairs:
                    sample_pair = next(iter(data_manager.translation_pairs.values()))
        except Exception as e:
            app.logger.warning(f"加载示例数据失败: {e}")
        
        # 如果没有找到示例数据，使用内置示例
        if not sample_pair:
            from translation_data_manager import TranslationPair
            sample_pair = TranslationPair(
                id="test_sample",
                source_text="This chapter defines the aircraft dimensions and areas for maintenance operations.",
                target_text="本章定义了维修操作中的飞机尺寸和区域。",
                source_lang="en",
                target_lang="zh",
                category="technical_manual",
                difficulty="medium",
                context="航空维修手册"
            )
        
        # 配置翻译引擎
        for model_key in selected_models:
            if model_key in config_manager.translation_models:
                model_config = config_manager.translation_models[model_key]
                translation_engine.add_model(model_key, model_config)
        
        # 测试每个模型
        test_results = []
        for model_key in selected_models:
            try:
                start_time = time.time()
                
                # 执行翻译测试
                translation_result = translation_engine.translate_single(model_key, sample_pair)
                
                processing_time = time.time() - start_time
                
                # 简单的质量检查
                quality_status = "正常"
                if translation_result.error_message:
                    quality_status = "错误"
                elif translation_result.translated_text == sample_pair.source_text:
                    quality_status = "未翻译"
                elif sample_pair.target_lang == "zh" and not any('\u4e00' <= c <= '\u9fff' for c in translation_result.translated_text):
                    quality_status = "语言错误"
                
                test_results.append({
                    'model': model_key,
                    'status': 'success' if not translation_result.error_message else 'error',
                    'translated_text': translation_result.translated_text,
                    'processing_time': round(processing_time, 2),
                    'error_message': translation_result.error_message,
                    'quality_status': quality_status
                })
                
            except Exception as e:
                test_results.append({
                    'model': model_key,
                    'status': 'error',
                    'translated_text': '',
                    'processing_time': 0,
                    'error_message': str(e),
                    'quality_status': '连接失败'
                })
        
        return jsonify({
            'success': True,
            'sample_text': {
                'source': sample_pair.source_text,
                'reference': sample_pair.target_text
            },
            'test_results': test_results
        })
        
    except Exception as e:
        app.logger.error(f"模型测试失败: {e}")
        return jsonify({'error': f'模型测试失败: {str(e)}'}), 500

@app.route('/api/tasks/<task_id>/results')
def get_task_results(task_id):
    """获取任务的详细结果"""
    task = EvaluationTask.query.get_or_404(task_id)
    results = TranslationResult.query.filter_by(task_id=task_id).all()
    
    results_data = []
    for result in results:
        results_data.append({
            'pair_id': result.pair_id,
            'source_text': result.source_text,
            'target_text': result.target_text,
            'model_name': result.model_name,
            'translated_text': result.translated_text,
            'accuracy_score': result.accuracy_score,
            'fluency_score': result.fluency_score,
            'terminology_score': result.terminology_score,
            'overall_score': result.overall_score
        })
    
    return jsonify(results_data)

@app.route('/api/tasks')
def get_all_tasks():
    """获取所有任务列表"""
    tasks = EvaluationTask.query.order_by(EvaluationTask.created_at.desc()).all()
    
    tasks_data = []
    for task in tasks:
        tasks_data.append({
            'id': task.id,
            'name': task.name,
            'status': task.status,
            'progress': task.progress,
            'created_at': task.created_at.isoformat() if task.created_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'total_pairs': task.total_pairs
        })
    
    return jsonify(tasks_data)

@app.route('/api/logs')
def get_logs():
    """获取实时日志"""
    limit = request.args.get('limit', 50, type=int)
    log_type = request.args.get('type', None)
    
    logs = log_manager.get_recent_logs(limit=limit, log_type=log_type)
    return jsonify(logs)

@app.route('/api/logs/translation/<task_id>')
def get_translation_logs(task_id):
    """获取特定任务的翻译日志"""
    logs = log_manager.get_recent_logs(log_type='translation')
    task_logs = [log for log in logs if log.get('task_id') == task_id]
    return jsonify(task_logs)

@app.route('/api/performance')
def get_performance_stats():
    """获取性能统计"""
    stats = performance_monitor.get_current_stats()
    return jsonify(stats)

@app.route('/api/performance/comparison')
def get_speed_comparison():
    """获取速度对比数据"""
    comparison = performance_monitor.get_speed_comparison()
    return jsonify(comparison)

@app.route('/api/performance/start')
def start_performance_monitoring():
    """启动性能监控"""
    performance_monitor.start_monitoring()
    return jsonify({'status': 'started'})

@app.route('/api/performance/stop')
def stop_performance_monitoring():
    """停止性能监控"""
    performance_monitor.stop_monitoring()
    return jsonify({'status': 'stopped'})

@app.route('/api/config/reload', methods=['POST'])
def reload_config_from_env():
    """从 .env 重载在线模型 API Key 并持久化到配置文件"""
    try:
        if not config_manager:
            return jsonify({'error': '配置管理器未初始化'}), 500
        dotenv_path = Path(__file__).parent.parent / '.env'
        load_dotenv(dotenv_path=dotenv_path)
        ernie_key = os.getenv('ERNIE_API_KEY', '').strip()
        qwen_key = os.getenv('QWEN_API_KEY', '').strip()
        qwen_base = os.getenv('QWEN_BASE_URL', '').strip()
        qwen_model = os.getenv('QWEN_MODEL_ID', '').strip()
        changed = False
        if 'ernie-4.5-0.3b' in config_manager.translation_models and ernie_key:
            config_manager.translation_models['ernie-4.5-0.3b'].api_key = ernie_key
            changed = True
        if 'qwen3-8b' in config_manager.translation_models:
            if (qwen_key or ernie_key):
                config_manager.translation_models['qwen3-8b'].api_key = (qwen_key or ernie_key)
                changed = True
            if qwen_base:
                config_manager.translation_models['qwen3-8b'].base_url = qwen_base
                changed = True
            if qwen_model:
                config_manager.translation_models['qwen3-8b'].model_id = qwen_model
                changed = True
        if config_manager.evaluation_model and ernie_key:
            config_manager.evaluation_model.api_key = ernie_key
            changed = True
        if changed:
            config_manager.save_config()
        return jsonify({'success': True, 'changed': changed})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs/clear')
def clear_logs():
    """清空日志"""
    log_manager.clear_logs()
    return jsonify({'status': 'cleared'})

if __name__ == '__main__':
    # 初始化系统
    if initialize_system():
        print("🚀 飞机维修翻译评估系统 Web版本启动中...")
        print("📱 访问地址: http://localhost:5001")
        print("✨ 功能特性: 模型选择、实时评估、结果展示、任务控制、模型测试")
        app.run(debug=True, host='0.0.0.0', port=5001)
    else:
        print("❌ 系统初始化失败，请检查配置")
