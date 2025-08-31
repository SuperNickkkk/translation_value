/**
 * 飞机维修翻译评估系统 - 主JavaScript文件
 * 处理所有前端交互和API调用
 */

class TranslationEvaluationApp {
    constructor() {
        this.currentTaskId = null;
        this.taskPollingInterval = null;
        this.uploadedFile = null;
        
        this.initializeEventListeners();
        this.loadInitialData();
    }

    initializeEventListeners() {
        // 文件上传相关
        this.setupFileUpload();
        
        // 模型配置相关
        this.setupModelConfiguration();
        
        // 任务控制相关
        this.setupTaskControl();
        
        // 评估任务相关
        this.setupEvaluationTask();
        
        // 结果查看相关
        this.setupResultsViewing();
    }

    setupFileUpload() {
        const uploadZone = document.getElementById('uploadZone');
        const fileInput = document.getElementById('fileInput');

        // 点击上传区域选择文件
        uploadZone.addEventListener('click', () => {
            fileInput.click();
        });

        // 文件选择处理
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileUpload(e.target.files[0]);
            }
        });

        // 拖拽上传处理
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('dragover');
        });
        
        // 设置数据选择功能
        this.setupDataSelection();

        uploadZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
        });

        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileUpload(files[0]);
            }
        });
    }
    
    setupDataSelection() {
        const selectionMode = document.getElementById('selectionMode');
        const selectionValue = document.getElementById('selectionValue');
        
        // 检查必需的DOM元素是否存在
        if (!selectionMode || !selectionValue) {
            console.warn('数据选择相关元素未找到，跳过设置');
            return;
        }
        
        // 模式切换处理
        selectionMode.addEventListener('change', (e) => {
            const mode = e.target.value;
            this.updateDataSelectionUI(mode);
        });
        
        // 数值变化处理
        selectionValue.addEventListener('input', (e) => {
            this.updateSelectionHint();
        });
        
        // 初始化UI
        this.updateDataSelectionUI('percentage');
    }
    
    updateDataSelectionUI(mode) {
        const valueLabel = document.getElementById('valueLabel');
        const valueInputGroup = document.getElementById('valueInputGroup');
        const selectionValue = document.getElementById('selectionValue');
        
        // 检查必需的DOM元素是否存在
        if (!valueLabel || !valueInputGroup || !selectionValue) {
            console.warn('数据选择UI相关元素未完全加载');
            return;
        }
        
        switch(mode) {
            case 'percentage':
                valueInputGroup.style.display = 'block';
                valueLabel.textContent = '数据比例 (%)';
                selectionValue.min = '1';
                selectionValue.max = '100';
                selectionValue.value = '20';
                selectionValue.placeholder = '1-100';
                break;
            case 'count':
                valueInputGroup.style.display = 'block';
                valueLabel.textContent = '数据数量';
                selectionValue.min = '1';
                selectionValue.max = '1000';
                selectionValue.value = '50';
                selectionValue.placeholder = '请输入数量';
                break;
            case 'all':
                valueInputGroup.style.display = 'none';
                break;
        }
        
        this.updateSelectionHint();
    }
    
    updateSelectionHint() {
        const selectionModeEl = document.getElementById('selectionMode');
        const selectionValueEl = document.getElementById('selectionValue');
        const selectionHint = document.getElementById('selectionHint');
        
        // 检查必需的DOM元素是否存在
        if (!selectionModeEl || !selectionValueEl || !selectionHint) {
            console.warn('选择提示相关元素未完全加载');
            return;
        }
        
        const selectionMode = selectionModeEl.value;
        const selectionValue = selectionValueEl.value;
        
        let hintText = '';
        
        switch(selectionMode) {
            case 'percentage':
                if (selectionValue) {
                    hintText = `将使用数据集中的${selectionValue}%数据进行评估测试`;
                } else {
                    hintText = '请输入数据比例 (1-100%)';
                }
                break;
            case 'count':
                if (selectionValue) {
                    hintText = `将使用数据集中的前${selectionValue}条数据进行评估测试`;
                } else {
                    hintText = '请输入数据数量';
                }
                break;
            case 'all':
                hintText = '将使用数据集中的全部数据进行评估测试';
                break;
        }
        
        selectionHint.textContent = hintText;
        
        // 如果有上传的文件，显示预计数据量
        if (this.uploadedFile && this.uploadedFile.totalPairs) {
            this.updateDataPreview();
        }
    }
    
    updateDataPreview() {
        const selectionMode = document.getElementById('selectionMode');
        const selectionValue = document.getElementById('selectionValue');
        const dataPreview = document.getElementById('dataPreview');
        const dataPreviewText = document.getElementById('dataPreviewText');
        
        // 检查所有必需的DOM元素是否存在
        if (!selectionMode || !selectionValue || !dataPreview || !dataPreviewText) {
            console.warn('数据预览相关元素未完全加载');
            return;
        }
        
        if (!this.uploadedFile || !this.uploadedFile.totalPairs) {
            dataPreview.style.display = 'none';
            return;
        }
        
        const modeValue = selectionMode.value;
        const numValue = parseInt(selectionValue.value) || 0;
        
        const totalPairs = this.uploadedFile.totalPairs;
        let actualCount = 0;
        
        switch(modeValue) {
            case 'percentage':
                if (numValue > 0 && numValue <= 100) {
                    actualCount = Math.ceil(totalPairs * numValue / 100);
                }
                break;
            case 'count':
                if (numValue > 0) {
                    actualCount = Math.min(numValue, totalPairs);
                }
                break;
            case 'all':
                actualCount = totalPairs;
                break;
        }
        
        if (actualCount > 0) {
            dataPreviewText.textContent = `数据集总计 ${totalPairs} 条，将使用 ${actualCount} 条数据进行测试`;
            dataPreview.style.display = 'block';
        } else {
            dataPreview.style.display = 'none';
        }
    }

    async handleFileUpload(file) {
        if (!file.name.toLowerCase().endsWith('.json')) {
            this.showAlert('请选择JSON格式的文件', 'warning');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        const uploadStatus = document.getElementById('uploadStatus');
        uploadStatus.style.display = 'block';
        uploadStatus.innerHTML = `
            <div class="alert alert-info">
                <div class="loading-spinner me-2"></div>
                正在上传文件...
            </div>
        `;

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                this.uploadedFile = {
                    ...result,
                    totalPairs: result.pairs_count
                };
                
                uploadStatus.innerHTML = `
                    <div class="alert alert-success">
                        <i class="fas fa-check-circle me-2"></i>
                        文件上传成功！包含 ${result.pairs_count} 个翻译对
                    </div>
                `;
                
                // 显示数据选择面板
                const dataSelectionPanel = document.getElementById('dataSelectionPanel');
                if (dataSelectionPanel) {
                    dataSelectionPanel.style.display = 'block';
                    
                    // 更新数据预览
                    this.updateDataPreview();
                } else {
                    console.warn('数据选择面板元素未找到');
                }
                
                this.updateStartButton();
            } else {
                uploadStatus.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        ${result.error}
                    </div>
                `;
            }
        } catch (error) {
            uploadStatus.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    上传失败：${error.message}
                </div>
            `;
        }
    }

    setupModelConfiguration() {
        // 模型选择器
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('model-selector')) {
                this.updateStartButton();
                this.updateTestButton();
            }
        });

        // 保存翻译模型配置
        document.getElementById('saveModelBtn').addEventListener('click', async () => {
            await this.saveModelConfiguration();
        });

        // 保存评估模型配置
        document.getElementById('saveEvalModelBtn').addEventListener('click', async () => {
            await this.saveEvaluationModelConfiguration();
        });

        // 模型类型选择自动填充
        document.getElementById('modelKey').addEventListener('change', (e) => {
            const modelKey = e.target.value;
            const presets = {
                'ernie-4.5-0.3b': {
                    name: '文心一言 ERNIE-4.5-Turbo',
                    baseUrl: 'https://aistudio.baidu.com/llm/lmapi/v3',
                    modelId: 'ernie-4.5-turbo-128k-preview'
                },
                'qwen3-8b': {
                    name: '通义千问 Qwen3-8B',
                    baseUrl: 'https://aistudio.baidu.com/llm/lmapi/v3',
                    modelId: 'qwen3-8b'
                },
                'gemini-270m': {
                    name: 'Gemini 270M',
                    baseUrl: 'https://generativelanguage.googleapis.com/v1',
                    modelId: 'gemini-pro'
                }
            };

            if (presets[modelKey]) {
                const preset = presets[modelKey];
                document.getElementById('modelName').value = preset.name;
                document.getElementById('baseUrl').value = preset.baseUrl;
                document.getElementById('modelId').value = preset.modelId;
            }
        });
    }

    async saveModelConfiguration() {
        const formData = {
            model_key: document.getElementById('modelKey').value,
            name: document.getElementById('modelName').value,
            api_key: document.getElementById('apiKey').value,
            base_url: document.getElementById('baseUrl').value,
            model_id: document.getElementById('modelId').value,
            temperature: 0.3,
            max_tokens: 1000
        };

        try {
            const response = await fetch('/api/models', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (result.success) {
                this.showAlert('模型配置保存成功', 'success');
                bootstrap.Modal.getInstance(document.getElementById('modelConfigModal')).hide();
                location.reload(); // 刷新页面以更新模型列表
            } else {
                this.showAlert(result.error, 'danger');
            }
        } catch (error) {
            this.showAlert(`保存失败：${error.message}`, 'danger');
        }
    }

    async saveEvaluationModelConfiguration() {
        const formData = {
            name: document.getElementById('evalModelName').value,
            api_key: document.getElementById('evalApiKey').value,
            base_url: document.getElementById('evalBaseUrl').value,
            model_id: document.getElementById('evalModelId').value,
            temperature: 0.3,
            max_tokens: 1000
        };

        try {
            const response = await fetch('/api/evaluation_model', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (result.success) {
                this.showAlert('评估模型配置保存成功', 'success');
                bootstrap.Modal.getInstance(document.getElementById('evalModelConfigModal')).hide();
                location.reload(); // 刷新页面以更新状态
            } else {
                this.showAlert(result.error, 'danger');
            }
        } catch (error) {
            this.showAlert(`保存失败：${error.message}`, 'danger');
        }
    }

    setupEvaluationTask() {
        document.getElementById('startEvaluationBtn').addEventListener('click', async () => {
            await this.startEvaluation();
        });
    }

    async startEvaluation() {
        if (!this.uploadedFile) {
            this.showAlert('请先上传翻译数据文件', 'warning');
            return;
        }

        const selectedModels = Array.from(document.querySelectorAll('.model-selector:checked'))
            .map(checkbox => checkbox.value);

        if (selectedModels.length === 0) {
            this.showAlert('请至少选择一个翻译模型', 'warning');
            return;
        }

        const taskName = document.getElementById('taskName').value || 
            `评估任务_${new Date().toLocaleString('zh-CN')}`;

        // 获取数据选择参数
        const selectionModeEl = document.getElementById('selectionMode');
        const selectionValueEl = document.getElementById('selectionValue');
        
        let selectionMode = 'all';
        let selectionValue = null;
        
        if (selectionModeEl && selectionValueEl) {
            selectionMode = selectionModeEl.value;
            selectionValue = parseInt(selectionValueEl.value) || null;
        } else {
            console.warn('数据选择元素未找到，使用默认值');
        }
        
        const requestData = {
            filepath: this.uploadedFile.filepath,
            task_name: taskName,
            selected_models: selectedModels,
            data_selection: {
                mode: selectionMode,
                value: selectionValue
            }
        };

        try {
            const response = await fetch('/api/evaluate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });

            const result = await response.json();

            if (result.success) {
                this.currentTaskId = result.task_id;
                this.showCurrentTask();
                this.startTaskPolling();
                this.showAlert('评估任务已启动', 'success');
            } else {
                this.showAlert(result.error, 'danger');
            }
        } catch (error) {
            this.showAlert(`启动评估失败：${error.message}`, 'danger');
        }
    }

    showCurrentTask() {
        const currentTaskCard = document.getElementById('currentTaskCard');
        currentTaskCard.style.display = 'block';
        currentTaskCard.scrollIntoView({ behavior: 'smooth' });
    }

    startTaskPolling() {
        if (this.taskPollingInterval) {
            clearInterval(this.taskPollingInterval);
        }

        this.taskPollingInterval = setInterval(async () => {
            await this.updateTaskStatus();
        }, 2000); // 每2秒更新一次

        // 立即更新一次
        this.updateTaskStatus();
    }

    async updateTaskStatus() {
        if (!this.currentTaskId) return;

        try {
            const response = await fetch(`/api/tasks/${this.currentTaskId}`);
            const task = await response.json();

            this.updateTaskDisplay(task);

            if (task.status === 'completed') {
                clearInterval(this.taskPollingInterval);
                this.taskPollingInterval = null;
                await this.loadTaskResults(this.currentTaskId);
                this.showAlert('评估任务完成！', 'success');
            } else if (task.status === 'failed') {
                clearInterval(this.taskPollingInterval);
                this.taskPollingInterval = null;
                this.showAlert(`评估任务失败：${task.error_message}`, 'danger');
            }
        } catch (error) {
            console.error('更新任务状态失败:', error);
        }
    }

    updateTaskDisplay(task) {
        document.getElementById('currentTaskName').textContent = task.name;
        document.getElementById('currentTaskProgress').textContent = `${task.progress}%`;
        
        const statusElement = document.getElementById('currentTaskStatus');
        statusElement.className = `status-badge status-${task.status}`;
        statusElement.textContent = this.getStatusText(task.status);

        const progressBar = document.getElementById('progressBar');
        progressBar.style.width = `${task.progress}%`;

        // 更新圆形进度条
        const progressCircle = document.getElementById('progressCircle');
        const circumference = 2 * Math.PI * 26; // r=26
        const offset = circumference - (task.progress / 100) * circumference;
        progressCircle.style.strokeDashoffset = offset;
        
        // 更新任务控制按钮状态
        this.updateTaskControlButtons(task.status);
    }

    getStatusText(status) {
        const statusMap = {
            'pending': '等待中',
            'running': '运行中',
            'paused': '已暂停',
            'completed': '已完成',
            'failed': '失败',
            'terminated': '已终止'
        };
        return statusMap[status] || status;
    }

    setupResultsViewing() {
        // 刷新结果按钮
        document.getElementById('refreshResultsBtn').addEventListener('click', () => {
            if (this.currentTaskId) {
                this.loadTaskResults(this.currentTaskId);
            }
        });

        // 查看任务按钮
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('view-task-btn') || 
                e.target.closest('.view-task-btn')) {
                const button = e.target.classList.contains('view-task-btn') ? 
                    e.target : e.target.closest('.view-task-btn');
                const taskId = button.getAttribute('data-task-id');
                this.loadTaskResults(taskId);
            }
        });
    }

    async loadTaskResults(taskId) {
        try {
            const [taskResponse, resultsResponse] = await Promise.all([
                fetch(`/api/tasks/${taskId}`),
                fetch(`/api/tasks/${taskId}/results`)
            ]);

            const task = await taskResponse.json();
            const results = await resultsResponse.json();

            this.displayResults(task, results);
        } catch (error) {
            console.error('加载结果失败:', error);
            this.showAlert('加载结果失败', 'danger');
        }
    }

    displayResults(task, results) {
        const resultsContent = document.getElementById('resultsContent');
        
        if (results.length === 0) {
            resultsContent.innerHTML = `
                <div class="text-center text-muted py-5">
                    <i class="fas fa-chart-bar fa-3x mb-3"></i>
                    <p>暂无评估结果</p>
                </div>
            `;
            return;
        }

        // 按模型分组结果
        const modelResults = {};
        results.forEach(result => {
            if (!modelResults[result.model_name]) {
                modelResults[result.model_name] = [];
            }
            modelResults[result.model_name].push(result);
        });

        // 计算模型平均分
        const modelStats = {};
        Object.keys(modelResults).forEach(model => {
            const modelData = modelResults[model];
            modelStats[model] = {
                count: modelData.length,
                avgAccuracy: this.calculateAverage(modelData, 'accuracy_score'),
                avgFluency: this.calculateAverage(modelData, 'fluency_score'),
                avgTerminology: this.calculateAverage(modelData, 'terminology_score'),
                avgOverall: this.calculateAverage(modelData, 'overall_score')
            };
        });

        // 生成结果展示HTML
        let html = `
            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="mb-3">模型性能对比</h6>
                    <div class="row">
        `;

        Object.keys(modelStats).forEach(model => {
            const stats = modelStats[model];
            html += `
                <div class="col-md-6 col-lg-4 mb-3">
                    <div class="card h-100">
                        <div class="card-body text-center">
                            <h6 class="card-title">${model}</h6>
                            <div class="score-display ${this.getScoreClass(stats.avgOverall)}">
                                <div class="h4 mb-1">${stats.avgOverall.toFixed(2)}</div>
                                <small>综合评分</small>
                            </div>
                            <div class="row text-center mt-2">
                                <div class="col-4">
                                    <div class="text-muted small">准确性</div>
                                    <div class="fw-bold">${stats.avgAccuracy.toFixed(1)}</div>
                                </div>
                                <div class="col-4">
                                    <div class="text-muted small">流畅性</div>
                                    <div class="fw-bold">${stats.avgFluency.toFixed(1)}</div>
                                </div>
                                <div class="col-4">
                                    <div class="text-muted small">术语</div>
                                    <div class="fw-bold">${stats.avgTerminology.toFixed(1)}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });

        html += `
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-12">
                    <canvas id="performanceChart" width="400" height="200"></canvas>
                </div>
            </div>
        `;

        resultsContent.innerHTML = html;

        // 绘制性能对比图表
        this.drawPerformanceChart(modelStats);

        // 显示详细结果表格
        this.displayDetailedResults(results);
    }

    calculateAverage(data, field) {
        const validData = data.filter(item => item[field] !== null && item[field] !== undefined);
        if (validData.length === 0) return 0;
        return validData.reduce((sum, item) => sum + item[field], 0) / validData.length;
    }

    getScoreClass(score) {
        if (score >= 4.5) return 'score-excellent';
        if (score >= 3.5) return 'score-good';
        if (score >= 2.5) return 'score-average';
        return 'score-poor';
    }

    drawPerformanceChart(modelStats) {
        const ctx = document.getElementById('performanceChart').getContext('2d');
        
        const models = Object.keys(modelStats);
        const accuracyData = models.map(model => modelStats[model].avgAccuracy);
        const fluencyData = models.map(model => modelStats[model].avgFluency);
        const terminologyData = models.map(model => modelStats[model].avgTerminology);
        const overallData = models.map(model => modelStats[model].avgOverall);

        new Chart(ctx, {
            type: 'radar',
            data: {
                labels: models,
                datasets: [
                    {
                        label: '准确性',
                        data: accuracyData,
                        borderColor: 'rgb(37, 99, 235)',
                        backgroundColor: 'rgba(37, 99, 235, 0.2)',
                        pointBackgroundColor: 'rgb(37, 99, 235)'
                    },
                    {
                        label: '流畅性',
                        data: fluencyData,
                        borderColor: 'rgb(5, 150, 105)',
                        backgroundColor: 'rgba(5, 150, 105, 0.2)',
                        pointBackgroundColor: 'rgb(5, 150, 105)'
                    },
                    {
                        label: '专业术语',
                        data: terminologyData,
                        borderColor: 'rgb(217, 119, 6)',
                        backgroundColor: 'rgba(217, 119, 6, 0.2)',
                        pointBackgroundColor: 'rgb(217, 119, 6)'
                    },
                    {
                        label: '综合评分',
                        data: overallData,
                        borderColor: 'rgb(220, 38, 38)',
                        backgroundColor: 'rgba(220, 38, 38, 0.2)',
                        pointBackgroundColor: 'rgb(220, 38, 38)'
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 5,
                        ticks: {
                            stepSize: 1
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: '模型性能雷达图'
                    }
                }
            }
        });
    }

    displayDetailedResults(results) {
        const detailedResultsCard = document.getElementById('detailedResultsCard');
        const tableBody = document.querySelector('#detailedResultsTable tbody');
        
        if (results.length === 0) {
            detailedResultsCard.style.display = 'none';
            return;
        }

        detailedResultsCard.style.display = 'block';
        
        let html = '';
        results.forEach(result => {
            html += `
                <tr>
                    <td class="text-wrap" style="max-width: 200px;">${result.source_text}</td>
                    <td class="text-wrap" style="max-width: 200px;">${result.target_text}</td>
                    <td><span class="badge bg-primary">${result.model_name}</span></td>
                    <td class="text-wrap" style="max-width: 200px;">${result.translated_text || '-'}</td>
                    <td class="text-center">
                        <span class="badge ${this.getScoreBadgeClass(result.accuracy_score)}">
                            ${result.accuracy_score ? result.accuracy_score.toFixed(1) : '-'}
                        </span>
                    </td>
                    <td class="text-center">
                        <span class="badge ${this.getScoreBadgeClass(result.fluency_score)}">
                            ${result.fluency_score ? result.fluency_score.toFixed(1) : '-'}
                        </span>
                    </td>
                    <td class="text-center">
                        <span class="badge ${this.getScoreBadgeClass(result.terminology_score)}">
                            ${result.terminology_score ? result.terminology_score.toFixed(1) : '-'}
                        </span>
                    </td>
                    <td class="text-center">
                        <span class="badge ${this.getScoreBadgeClass(result.overall_score)}">
                            ${result.overall_score ? result.overall_score.toFixed(1) : '-'}
                        </span>
                    </td>
                </tr>
            `;
        });
        
        tableBody.innerHTML = html;
    }

    getScoreBadgeClass(score) {
        if (!score) return 'bg-secondary';
        if (score >= 4.5) return 'bg-success';
        if (score >= 3.5) return 'bg-info';
        if (score >= 2.5) return 'bg-warning';
        return 'bg-danger';
    }

    updateStartButton() {
        const startBtn = document.getElementById('startEvaluationBtn');
        const selectedModels = document.querySelectorAll('.model-selector:checked').length;
        const hasFile = this.uploadedFile !== null;
        
        startBtn.disabled = !(hasFile && selectedModels > 0);
    }

    updateTestButton() {
        const testBtn = document.getElementById('testModelsBtn');
        const selectedModels = document.querySelectorAll('.model-selector:checked').length;
        
        if (testBtn) {
            testBtn.disabled = selectedModels === 0;
        }
    }

    setupTaskControl() {
        // 测试模型按钮
        const testBtn = document.getElementById('testModelsBtn');
        if (testBtn) {
            testBtn.addEventListener('click', () => this.testSelectedModels());
        }

        // 任务控制按钮
        const pauseBtn = document.getElementById('pauseTaskBtn');
        const resumeBtn = document.getElementById('resumeTaskBtn');
        const terminateBtn = document.getElementById('terminateTaskBtn');

        if (pauseBtn) {
            pauseBtn.addEventListener('click', () => this.pauseTask());
        }
        if (resumeBtn) {
            resumeBtn.addEventListener('click', () => this.resumeTask());
        }
        if (terminateBtn) {
            terminateBtn.addEventListener('click', () => this.terminateTask());
        }

        // 重新测试按钮
        const retestBtn = document.getElementById('retestModelsBtn');
        if (retestBtn) {
            retestBtn.addEventListener('click', () => this.retestModels());
        }
    }

    async testSelectedModels() {
        const selectedModels = Array.from(document.querySelectorAll('.model-selector:checked'))
            .map(checkbox => checkbox.value);

        if (selectedModels.length === 0) {
            this.showAlert('请先选择要测试的模型', 'warning');
            return;
        }

        // 显示模态框和加载状态
        const modal = new bootstrap.Modal(document.getElementById('testResultsModal'));
        modal.show();

        const testResultsContent = document.getElementById('testResultsContent');
        const testLoadingSpinner = document.getElementById('testLoadingSpinner');

        testResultsContent.style.display = 'none';
        testLoadingSpinner.style.display = 'block';

        try {
            const response = await fetch('/api/models/test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    selected_models: selectedModels
                })
            });

            const result = await response.json();

            if (result.success) {
                this.displayTestResults(result);
            } else {
                this.showAlert(`模型测试失败: ${result.error}`, 'danger');
                modal.hide();
            }
        } catch (error) {
            this.showAlert(`模型测试失败: ${error.message}`, 'danger');
            modal.hide();
        } finally {
            testLoadingSpinner.style.display = 'none';
            testResultsContent.style.display = 'block';
        }
    }

    displayTestResults(result) {
        // 显示示例文本
        const testSourceText = document.getElementById('testSourceText');
        const testReferenceText = document.getElementById('testReferenceText');

        if (testSourceText && testReferenceText) {
            testSourceText.textContent = result.sample_text.source;
            testReferenceText.textContent = result.sample_text.reference;
        }

        // 显示测试结果表格
        const testResultsTable = document.getElementById('testResultsTable');
        if (testResultsTable) {
            testResultsTable.innerHTML = '';

            result.test_results.forEach(testResult => {
                const row = document.createElement('tr');
                
                const statusBadge = testResult.status === 'success' ? 
                    '<span class="badge bg-success">成功</span>' : 
                    '<span class="badge bg-danger">失败</span>';

                const qualityBadge = this.getQualityStatusBadge(testResult.quality_status);
                
                const translatedText = testResult.translated_text || testResult.error_message || '无输出';
                const displayText = translatedText.length > 50 ? 
                    translatedText.substring(0, 50) + '...' : translatedText;

                row.innerHTML = `
                    <td>${testResult.model}</td>
                    <td>${statusBadge}</td>
                    <td title="${translatedText}">${displayText}</td>
                    <td>${testResult.processing_time}s</td>
                    <td>${qualityBadge}</td>
                `;

                testResultsTable.appendChild(row);
            });
        }
    }

    getQualityStatusBadge(status) {
        const badges = {
            '正常': '<span class="badge bg-success">正常</span>',
            '错误': '<span class="badge bg-danger">错误</span>',
            '未翻译': '<span class="badge bg-warning">未翻译</span>',
            '语言错误': '<span class="badge bg-warning">语言错误</span>',
            '连接失败': '<span class="badge bg-secondary">连接失败</span>'
        };
        return badges[status] || `<span class="badge bg-secondary">${status}</span>`;
    }

    async retestModels() {
        await this.testSelectedModels();
    }

    async pauseTask() {
        if (!this.currentTaskId) {
            this.showAlert('没有正在运行的任务', 'warning');
            return;
        }

        try {
            const response = await fetch(`/api/tasks/${this.currentTaskId}/pause`, {
                method: 'POST'
            });

            const result = await response.json();
            if (result.success) {
                this.showAlert('任务暂停请求已发送', 'info');
            } else {
                this.showAlert(`暂停失败: ${result.error}`, 'danger');
            }
        } catch (error) {
            this.showAlert(`暂停失败: ${error.message}`, 'danger');
        }
    }

    async resumeTask() {
        if (!this.currentTaskId) {
            this.showAlert('没有可恢复的任务', 'warning');
            return;
        }

        try {
            const response = await fetch(`/api/tasks/${this.currentTaskId}/resume`, {
                method: 'POST'
            });

            const result = await response.json();
            if (result.success) {
                this.showAlert('任务恢复请求已发送', 'info');
            } else {
                this.showAlert(`恢复失败: ${result.error}`, 'danger');
            }
        } catch (error) {
            this.showAlert(`恢复失败: ${error.message}`, 'danger');
        }
    }

    async terminateTask() {
        if (!this.currentTaskId) {
            this.showAlert('没有可终止的任务', 'warning');
            return;
        }

        if (!confirm('确定要终止当前任务吗？此操作不可撤销。')) {
            return;
        }

        try {
            const response = await fetch(`/api/tasks/${this.currentTaskId}/terminate`, {
                method: 'POST'
            });

            const result = await response.json();
            if (result.success) {
                this.showAlert('任务终止请求已发送', 'info');
            } else {
                this.showAlert(`终止失败: ${result.error}`, 'danger');
            }
        } catch (error) {
            this.showAlert(`终止失败: ${error.message}`, 'danger');
        }
    }

    updateTaskControlButtons(taskStatus) {
        const taskControlButtons = document.getElementById('taskControlButtons');
        const pauseBtn = document.getElementById('pauseTaskBtn');
        const resumeBtn = document.getElementById('resumeTaskBtn');
        const terminateBtn = document.getElementById('terminateTaskBtn');

        if (!taskControlButtons) return;

        switch (taskStatus) {
            case 'running':
                taskControlButtons.style.display = 'block';
                if (pauseBtn) pauseBtn.disabled = false;
                if (resumeBtn) resumeBtn.disabled = true;
                if (terminateBtn) terminateBtn.disabled = false;
                break;

            case 'paused':
                taskControlButtons.style.display = 'block';
                if (pauseBtn) pauseBtn.disabled = true;
                if (resumeBtn) resumeBtn.disabled = false;
                if (terminateBtn) terminateBtn.disabled = false;
                break;

            case 'completed':
            case 'failed':
            case 'terminated':
                taskControlButtons.style.display = 'none';
                break;

            default:
                taskControlButtons.style.display = 'none';
                break;
        }
    }

    async loadInitialData() {
        // 可以在这里加载初始数据，比如最近的任务等
    }

    showAlert(message, type = 'info') {
        // 创建alert元素
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(alertDiv);

        // 3秒后自动消失
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv);
            }
        }, 3000);
    }
}

// 监控功能类
class MonitoringSystem {
    constructor() {
        this.logAutoScroll = true;
        this.performanceChart = null;
        this.speedComparisonChart = null;
        this.logPollingInterval = null;
        this.performancePollingInterval = null;
        
        this.initializeCharts();
        this.startMonitoring();
    }
    
    initializeCharts() {
        console.log('正在初始化监控图表...');
        
        // 检查canvas元素是否存在
        const performanceCanvas = document.getElementById('performance-chart');
        const speedCanvas = document.getElementById('speed-comparison-chart');
        
        if (!performanceCanvas) {
            console.error('未找到performance-chart canvas元素');
            return;
        }
        
        if (!speedCanvas) {
            console.error('未找到speed-comparison-chart canvas元素');
            return;
        }
        
        console.log('Canvas元素已找到，正在创建图表...');
        
        // 初始化性能趋势图表
        const performanceCtx = performanceCanvas.getContext('2d');
        this.performanceChart = new Chart(performanceCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'CPU使用率',
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1,
                    fill: false
                }, {
                    label: '内存使用率',
                    data: [],
                    borderColor: 'rgb(255, 99, 132)',
                    tension: 0.1,
                    fill: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false, // 禁用动画提高性能
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            font: {
                                size: 10
                            }
                        }
                    },
                    x: {
                        ticks: {
                            font: {
                                size: 9
                            },
                            maxTicksLimit: 8 // 限制X轴标签数量
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            font: {
                                size: 10
                            },
                            boxWidth: 12
                        }
                    }
                }
            }
        });
        
        // 初始化速度对比图表
        const speedCtx = speedCanvas.getContext('2d');
        this.speedComparisonChart = new Chart(speedCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: '平均速度',
                    data: [],
                    backgroundColor: [
                        'rgba(54, 162, 235, 0.8)',
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(75, 192, 192, 0.8)',
                        'rgba(255, 206, 86, 0.8)'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false, // 禁用动画提高性能
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            font: {
                                size: 10
                            }
                        }
                    },
                    x: {
                        ticks: {
                            font: {
                                size: 9
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + context.parsed.y.toFixed(2) + ' tokens/s';
                            }
                        }
                    }
                }
            }
        });
    }
    
    startMonitoring() {
        // 启动日志轮询
        this.logPollingInterval = setInterval(() => {
            this.updateLogs();
        }, 2000);
        
        // 启动性能监控轮询
        this.performancePollingInterval = setInterval(() => {
            this.updatePerformanceStats();
            this.updateSpeedComparison();
        }, 3000);
    }
    
    async updateLogs() {
        try {
            const response = await fetch('/api/logs?limit=50');
            const logs = await response.json();
            
            const logWindow = document.getElementById('log-window');
            if (!logWindow) return;
            
            let logHtml = '';
            logs.forEach(log => {
                const timestamp = new Date(log.timestamp).toLocaleTimeString();
                const levelClass = this.getLogLevelClass(log.level);
                const message = this.formatLogMessage(log);
                
                logHtml += `
                    <div class="log-entry ${levelClass}">
                        <span class="log-time">[${timestamp}]</span>
                        <span class="log-level">[${log.level}]</span>
                        <span class="log-message">${message}</span>
                    </div>
                `;
            });
            
            logWindow.innerHTML = logHtml;
            
            // 自动滚动到底部
            if (this.logAutoScroll) {
                logWindow.scrollTop = logWindow.scrollHeight;
            }
            
        } catch (error) {
            console.error('更新日志失败:', error);
        }
    }
    
    async updatePerformanceStats() {
        try {
            const response = await fetch('/api/performance');
            const stats = await response.json();
            
            if (stats.error) {
                console.error('性能统计错误:', stats.error);
                return;
            }
            
            // 更新系统资源显示
            document.getElementById('cpu-usage').textContent = `${stats.system.cpu_percent.toFixed(1)}%`;
            document.getElementById('memory-usage').textContent = `${stats.system.memory_percent.toFixed(1)}%`;
            
            // 更新本地模型状态（多模型）
            const localModelStatus = document.getElementById('local-model-status');
            if (stats.local_models && stats.local_models.status) {
                const s = stats.local_models.status;
                const labels = Object.keys(s);
                const parts = labels.map(k => `${s[k].online ? '🟢' : '🔴'} ${k}`);
                localModelStatus.innerHTML = parts.join(' · ');
                localModelStatus.className = 'h6 mb-0';
            } else if (stats.local_model && stats.local_model.status) {
                // 兼容旧结构
                localModelStatus.textContent = stats.local_model.status.online ? '在线' : '离线';
                localModelStatus.className = stats.local_model.status.online ? 'h4 mb-0 text-success' : 'h4 mb-0 text-danger';
            }
            
            // 更新性能图表
            if (stats.history && stats.history.timestamps.length > 0) {
                const maxPoints = 20;
                const timestamps = stats.history.timestamps.slice(-maxPoints);
                const cpuData = stats.history.cpu.slice(-maxPoints);
                const memoryData = stats.history.memory.slice(-maxPoints);
                
                this.performanceChart.data.labels = timestamps.map(t => 
                    new Date(t).toLocaleTimeString()
                );
                this.performanceChart.data.datasets[0].data = cpuData;
                this.performanceChart.data.datasets[1].data = memoryData;
                this.performanceChart.update('none');
            }
            
        } catch (error) {
            console.error('更新性能统计失败:', error);
        }
    }
    
    async updateSpeedComparison() {
        try {
            const response = await fetch('/api/performance/comparison');
            const comparison = await response.json();
            
            if (comparison.error) {
                console.error('速度对比错误:', comparison.error);
                return;
            }
            
            const labels = [];
            const speeds = [];
            
            // 添加本地模型分模型数据优先
            if (comparison.local_models && comparison.local_models.length) {
                comparison.local_models.forEach(m => {
                    labels.push(`Local · ${m.name}`);
                    speeds.push(m.avg_speed || 0);
                });
            } else if (comparison.local_model) {
                // 向后兼容
                labels.push(comparison.local_model.name);
                speeds.push(comparison.local_model.avg_speed || 0);
            }
            
            // 添加API模型数据
            comparison.api_models.forEach(model => {
                if (model.avg_speed > 0) {
                    labels.push(model.name);
                    speeds.push(model.avg_speed);
                }
            });
            
            // 更新图表（tooltip 显示 last_speed + avg_speed）
            this.speedComparisonChart.data.labels = labels;
            this.speedComparisonChart.data.datasets[0].data = speeds;
            this.speedComparisonChart.options.plugins.tooltip.callbacks = {
                label: function(context) {
                    const idx = context.dataIndex;
                    const name = context.chart.data.labels[idx];
                    // 在 comparison 中查找 last_speed
                    let last = null;
                    if (comparison.local_models) {
                        const m = comparison.local_models.find(x => `Local · ${x.name}` === name || x.name === name);
                        if (m) last = m.last_speed;
                    }
                    if (last === null && comparison.api_models) {
                        const m = comparison.api_models.find(x => x.name === name);
                        if (m) last = m.last_speed;
                    }
                    const avg = context.parsed.y;
                    if (last != null) {
                        return `最近: ${last.toFixed(2)} tokens/s · 平均: ${avg.toFixed(2)} tokens/s`;
                    }
                    return `平均: ${avg.toFixed(2)} tokens/s`;
                }
            };
            this.speedComparisonChart.update('none');
            
        } catch (error) {
            console.error('更新速度对比失败:', error);
        }
    }
    
    getLogLevelClass(level) {
        switch (level.toLowerCase()) {
            case 'error': return 'text-danger';
            case 'warning': return 'text-warning';
            case 'info': return 'text-info';
            default: return 'text-light';
        }
    }
    
    formatLogMessage(log) {
        if (log.type === 'translation') {
            return `🔄 ${log.model_name} - ${log.text_id}: ${log.message}`;
        } else if (log.type === 'performance') {
            return `📊 ${log.message}`;
        } else if (log.level === 'ERROR') {
            return `❌ ${log.message}`;
        } else if (log.level === 'WARNING') {
            return `⚠️ ${log.message}`;
        } else {
            // 简化普通日志信息
            const message = log.message;
            if (message.includes('翻译')) {
                return `🔤 ${message}`;
            } else if (message.includes('模型')) {
                return `🤖 ${message}`;
            } else if (message.includes('初始化')) {
                return `🚀 ${message}`;
            } else {
                return `ℹ️ ${message}`;
            }
        }
    }
    
    stopMonitoring() {
        if (this.logPollingInterval) {
            clearInterval(this.logPollingInterval);
        }
        if (this.performancePollingInterval) {
            clearInterval(this.performancePollingInterval);
        }
    }
}

// 全局监控功能函数
function clearLogs() {
    fetch('/api/logs/clear')
        .then(response => response.json())
        .then(data => {
            console.log('日志已清空');
            document.getElementById('log-window').innerHTML = '<div class="text-muted">日志已清空</div>';
        })
        .catch(error => console.error('清空日志失败:', error));
}

function toggleLogAutoScroll() {
    const monitoring = window.monitoringSystem;
    const btn = document.getElementById('log-auto-scroll-btn');
    
    if (monitoring.logAutoScroll) {
        monitoring.logAutoScroll = false;
        btn.innerHTML = '<i class="fas fa-play"></i> 开始滚动';
        btn.className = 'btn btn-sm btn-outline-success';
    } else {
        monitoring.logAutoScroll = true;
        btn.innerHTML = '<i class="fas fa-pause"></i> 暂停滚动';
        btn.className = 'btn btn-sm btn-outline-primary';
    }
}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    console.log('页面DOM加载完成，正在初始化应用...');
    new TranslationEvaluationApp();
    
    // 延迟初始化监控系统，确保DOM完全加载
    setTimeout(() => {
        console.log('正在初始化监控系统...');
        window.monitoringSystem = new MonitoringSystem();
        console.log('监控系统初始化完成');
    }, 1000);
});

