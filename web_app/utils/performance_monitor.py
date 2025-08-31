#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能监控工具
监控本地模型的资源使用情况和翻译性能
"""

import time
import psutil
import threading
import json
from datetime import datetime
from collections import deque
import requests
import logging

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    def __init__(self, local_model_url="http://127.0.0.1:8081", max_history=100):
        self.local_model_url = local_model_url
        self.max_history = max_history
        # 多本地模型端点: 名称 -> URL（用于显示多个本地模型状态）
        self.local_endpoints = {}
        
        # 性能数据历史记录
        self.cpu_history = deque(maxlen=max_history)
        self.memory_history = deque(maxlen=max_history)
        self.gpu_memory_history = deque(maxlen=max_history)
        self.timestamps = deque(maxlen=max_history)
        
        # 翻译性能记录
        self.translation_stats = {
            'local_model': {
                'total_requests': 0,
                'total_tokens': 0,
                'total_time': 0,
                'avg_tokens_per_sec': 0,
                'last_speed': 0
            },
            'local_models': {},  # 分模型统计: model_name -> stats
            'api_models': {}
        }
        
        # 监控线程
        self.monitoring = False
        self.monitor_thread = None
        
    def start_monitoring(self):
        """开始性能监控"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            logger.info("性能监控已启动")
    
    def stop_monitoring(self):
        """停止性能监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("性能监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                # 获取系统资源使用情况
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                # 获取GPU内存使用情况（如果可用）
                gpu_memory = self._get_gpu_memory_usage()
                
                # 记录数据
                current_time = datetime.now()
                self.timestamps.append(current_time)
                self.cpu_history.append(cpu_percent)
                self.memory_history.append(memory.percent)
                self.gpu_memory_history.append(gpu_memory)
                
                time.sleep(2)  # 每2秒更新一次
                
            except Exception as e:
                logger.error(f"性能监控出错: {e}")
                time.sleep(5)
    
    def _get_gpu_memory_usage(self):
        """获取GPU内存使用情况"""
        try:
            # 对于Apple Silicon，这里可以扩展获取GPU使用情况
            # 目前返回0作为占位符
            return 0
        except Exception:
            return 0
    
    def record_translation(self, model_name, tokens_generated, time_taken, is_local=False):
        """记录翻译性能"""
        try:
            # 确保输入参数有效
            if tokens_generated is None or tokens_generated <= 0:
                tokens_generated = 1  # 默认值避免除零错误
            if time_taken is None or time_taken <= 0:
                time_taken = 0.1  # 默认值避免除零错误
                
            if is_local:
                # 分模型统计
                if model_name not in self.translation_stats['local_models']:
                    self.translation_stats['local_models'][model_name] = {
                        'total_requests': 0,
                        'total_tokens': 0,
                        'total_time': 0,
                        'avg_tokens_per_sec': 0,
                        'last_speed': 0
                    }
                per_stats = self.translation_stats['local_models'][model_name]
                per_stats['total_requests'] += 1
                per_stats['total_tokens'] += tokens_generated
                per_stats['total_time'] += time_taken
                if per_stats['total_time'] > 0:
                    per_stats['avg_tokens_per_sec'] = round(per_stats['total_tokens'] / per_stats['total_time'], 2)
                per_stats['last_speed'] = round(tokens_generated / time_taken, 2)

                # 聚合（向后兼容）
                stats = self.translation_stats['local_model']
                stats['total_requests'] += 1
                stats['total_tokens'] += tokens_generated
                stats['total_time'] += time_taken
                if stats['total_time'] > 0:
                    stats['avg_tokens_per_sec'] = round(stats['total_tokens'] / stats['total_time'], 2)
                stats['last_speed'] = round(tokens_generated / time_taken, 2)
                
                logger.info(f"本地模型性能记录 {model_name}: {tokens_generated} tokens, {time_taken:.2f}s, {per_stats['last_speed']:.2f} tokens/s")
            else:
                # API模型统计
                if model_name not in self.translation_stats['api_models']:
                    self.translation_stats['api_models'][model_name] = {
                        'total_requests': 0,
                        'total_tokens': 0,
                        'total_time': 0,
                        'avg_tokens_per_sec': 0,
                        'last_speed': 0
                    }
                
                stats = self.translation_stats['api_models'][model_name]
                stats['total_requests'] += 1
                stats['total_tokens'] += tokens_generated
                stats['total_time'] += time_taken
                
                if stats['total_time'] > 0:
                    stats['avg_tokens_per_sec'] = round(stats['total_tokens'] / stats['total_time'], 2)
                
                stats['last_speed'] = round(tokens_generated / time_taken, 2)
                
                logger.info(f"API模型性能记录 {model_name}: {tokens_generated} tokens, {time_taken:.2f}s, {stats['last_speed']:.2f} tokens/s")
                    
        except Exception as e:
            logger.error(f"记录翻译性能出错: {e}")
    
    def get_current_stats(self):
        """获取当前性能统计"""
        try:
            # 系统资源
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 检查本地模型服务器状态（支持多端点）
            local_models_status = {}
            if self.local_endpoints:
                for name, url in self.local_endpoints.items():
                    local_models_status[name] = self._check_endpoint_status(url)
            else:
                # 向后兼容：仅单一默认端点
                local_models_status['default'] = self._check_endpoint_status(self.local_model_url)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_used_gb': memory.used / (1024**3),
                    'memory_total_gb': memory.total / (1024**3),
                    'disk_percent': disk.percent,
                    'disk_used_gb': disk.used / (1024**3),
                    'disk_total_gb': disk.total / (1024**3)
                },
                'local_models': {
                    'endpoints': self.local_endpoints,
                    'status': local_models_status
                },
                'translation_stats': self.translation_stats,
                'history': {
                    'timestamps': [t.isoformat() for t in list(self.timestamps)],
                    'cpu': list(self.cpu_history),
                    'memory': list(self.memory_history),
                    'gpu_memory': list(self.gpu_memory_history)
                }
            }
        except Exception as e:
            logger.error(f"获取性能统计出错: {e}")
            return {'error': str(e)}
    
    def _check_endpoint_status(self, base_url: str):
        """检查指定端点健康状态"""
        try:
            response = requests.get(f"{base_url}/health", timeout=2)
            if response.status_code == 200:
                data = response.json()
                return {
                    'online': True,
                    'model_loaded': data.get('model_loaded', False)
                }
            else:
                return {'online': False, 'model_loaded': False}
        except Exception:
            return {'online': False, 'model_loaded': False}

    def _check_local_model_status(self):
        """检查本地模型服务器状态"""
        try:
            response = requests.get(f"{self.local_model_url}/health", timeout=2)
            if response.status_code == 200:
                data = response.json()
                return {
                    'online': True,
                    'model_loaded': data.get('model_loaded', False)
                }
            else:
                return {'online': False, 'model_loaded': False}
        except Exception:
            return {'online': False, 'model_loaded': False}
    
    def get_speed_comparison(self):
        """获取速度对比数据"""
        try:
            local_stats = self.translation_stats['local_model']
            api_stats = self.translation_stats['api_models']
            per_local = self.translation_stats.get('local_models', {})
            
            comparison = {
                'local_model': {  # 聚合数据显示（向后兼容）
                    'name': 'Local Models (aggregated)',
                    'avg_speed': local_stats['avg_tokens_per_sec'],
                    'last_speed': local_stats['last_speed'],
                    'total_requests': local_stats['total_requests'],
                    'total_tokens': local_stats['total_tokens']
                },
                'local_models': [],
                'api_models': []
            }
            
            for name, stats in per_local.items():
                comparison['local_models'].append({
                    'name': name,
                    'avg_speed': stats['avg_tokens_per_sec'],
                    'last_speed': stats['last_speed'],
                    'total_requests': stats['total_requests'],
                    'total_tokens': stats['total_tokens']
                })

            for model_name, stats in api_stats.items():
                comparison['api_models'].append({
                    'name': model_name,
                    'avg_speed': stats['avg_tokens_per_sec'],
                    'last_speed': stats['last_speed'],
                    'total_requests': stats['total_requests'],
                    'total_tokens': stats['total_tokens']
                })
            
            return comparison
        except Exception as e:
            logger.error(f"获取速度对比出错: {e}")
            return {'error': str(e)}

    def register_local_model(self, name: str, url: str):
        """注册一个本地模型端点供监控展示"""
        try:
            self.local_endpoints[name] = url
            logger.info(f"注册本地模型端点: {name} -> {url}")
        except Exception as e:
            logger.error(f"注册本地模型端点失败: {e}")

# 全局性能监控实例
performance_monitor = PerformanceMonitor()
