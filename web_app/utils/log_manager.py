#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志管理器
实时收集和管理翻译过程中的日志信息
"""

import time
import logging
import threading
from datetime import datetime
from collections import deque
from typing import List, Dict
import json

class TranslationLogHandler(logging.Handler):
    """自定义日志处理器，用于捕获翻译相关日志"""
    
    def __init__(self, log_manager):
        super().__init__()
        self.log_manager = log_manager
        
    def emit(self, record):
        """处理日志记录"""
        try:
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'level': record.levelname,
                'message': record.getMessage(),
                'module': record.name,
                'line': record.lineno
            }
            self.log_manager.add_log(log_entry)
        except Exception:
            pass  # 避免日志处理器本身出错

class LogManager:
    def __init__(self, max_logs=500):
        self.max_logs = max_logs
        self.logs = deque(maxlen=max_logs)
        self.lock = threading.Lock()
        
        # 设置自定义日志处理器
        self.handler = TranslationLogHandler(self)
        self.handler.setLevel(logging.INFO)
        
        # 添加到根日志记录器
        root_logger = logging.getLogger()
        root_logger.addHandler(self.handler)
        
        # 翻译进度日志
        self.translation_progress = {}
        
    def add_log(self, log_entry):
        """添加日志条目"""
        with self.lock:
            self.logs.append(log_entry)
    
    def add_translation_log(self, task_id, model_name, text_id, status, message, extra_data=None):
        """添加翻译特定日志"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': 'INFO',
            'type': 'translation',
            'task_id': task_id,
            'model_name': model_name,
            'text_id': text_id,
            'status': status,  # 'started', 'progress', 'completed', 'error'
            'message': message,
            'extra_data': extra_data or {}
        }
        
        with self.lock:
            self.logs.append(log_entry)
            
        # 更新进度信息
        if task_id not in self.translation_progress:
            self.translation_progress[task_id] = {
                'total': 0,
                'completed': 0,
                'models': {}
            }
        
        if model_name not in self.translation_progress[task_id]['models']:
            self.translation_progress[task_id]['models'][model_name] = {
                'total': 0,
                'completed': 0,
                'errors': 0
            }
        
        model_progress = self.translation_progress[task_id]['models'][model_name]
        
        if status == 'started':
            model_progress['total'] += 1
            self.translation_progress[task_id]['total'] += 1
        elif status == 'completed':
            model_progress['completed'] += 1
            self.translation_progress[task_id]['completed'] += 1
        elif status == 'error':
            model_progress['errors'] += 1
    
    def add_evaluation_log(self, task_id, text_id, status, message, extra_data=None):
        """添加评估特定日志"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': 'INFO',
            'type': 'evaluation',
            'task_id': task_id,
            'text_id': text_id,
            'status': status,
            'message': message,
            'extra_data': extra_data or {}
        }
        
        with self.lock:
            self.logs.append(log_entry)
    
    def add_error_log(self, task_id, component, error_message, extra_data=None):
        """添加错误日志"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': 'ERROR',
            'type': 'error',
            'task_id': task_id,
            'component': component,
            'message': error_message,
            'extra_data': extra_data or {}
        }
        
        with self.lock:
            self.logs.append(log_entry)
    
    def add_performance_log(self, model_name, operation, duration, extra_data=None):
        """添加性能日志"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': 'INFO',
            'type': 'performance',
            'model_name': model_name,
            'operation': operation,
            'duration': duration,
            'message': f"{model_name} {operation} 耗时 {duration:.2f}秒",
            'extra_data': extra_data or {}
        }
        
        with self.lock:
            self.logs.append(log_entry)
    
    def get_recent_logs(self, limit=50, log_type=None):
        """获取最近的日志"""
        with self.lock:
            logs = list(self.logs)
        
        # 按类型过滤
        if log_type:
            logs = [log for log in logs if log.get('type') == log_type]
        
        # 按时间倒序排列，取最新的
        logs.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return logs[:limit]
    
    def get_task_logs(self, task_id, limit=100):
        """获取特定任务的日志"""
        with self.lock:
            logs = list(self.logs)
        
        # 过滤任务日志
        task_logs = [log for log in logs if log.get('task_id') == task_id]
        
        # 按时间排序
        task_logs.sort(key=lambda x: x['timestamp'])
        
        return task_logs[-limit:]
    
    def get_translation_progress(self, task_id):
        """获取翻译进度"""
        return self.translation_progress.get(task_id, {
            'total': 0,
            'completed': 0,
            'models': {}
        })
    
    def clear_task_progress(self, task_id):
        """清理任务进度"""
        if task_id in self.translation_progress:
            del self.translation_progress[task_id]
    
    def get_performance_summary(self, limit=20):
        """获取性能摘要"""
        with self.lock:
            logs = list(self.logs)
        
        # 过滤性能日志
        perf_logs = [log for log in logs if log.get('type') == 'performance']
        
        # 按时间倒序
        perf_logs.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return perf_logs[:limit]
    
    def get_error_summary(self, limit=20):
        """获取错误摘要"""
        with self.lock:
            logs = list(self.logs)
        
        # 过滤错误日志
        error_logs = [log for log in logs if log.get('level') == 'ERROR']
        
        # 按时间倒序
        error_logs.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return error_logs[:limit]
    
    def get_logs_json(self, limit=50, log_type=None):
        """返回JSON格式的日志"""
        logs = self.get_recent_logs(limit=limit, log_type=log_type)

        return json.dumps(logs, ensure_ascii=False, indent=2)

# 全局日志管理器实例
log_manager = LogManager()

def get_logger(name):
    """获取带有翻译日志功能的logger"""
    logger = logging.getLogger(name)
    return logger