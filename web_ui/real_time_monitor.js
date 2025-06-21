/*
DeepResearchAgent Real-Time Monitor
Gerçek zamanlı agent adım takibi için JavaScript komponenti
*/

class RealTimeAgentMonitor {
    constructor(apiUrl = 'ws://localhost:8000/ws') {
        this.apiUrl = apiUrl;
        this.websocket = null;
        this.isConnected = false;
        this.steps = [];
        this.currentStatus = 'idle';
        this.callbacks = {
            onStepUpdate: [],
            onStatusChange: [],
            onTaskComplete: [],
            onError: []
        };
        
        this.connect();
    }
    
    // WebSocket bağlantısı kur
    connect() {
        try {
            this.websocket = new WebSocket(this.apiUrl);
            
            this.websocket.onopen = () => {
                this.isConnected = true;
                console.log('🟢 DeepResearchAgent WebSocket bağlantısı kuruldu');
                this.requestStatus();
            };
            
            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            };
            
            this.websocket.onclose = () => {
                this.isConnected = false;
                console.log('🔴 WebSocket bağlantısı kapandı');
                // Otomatik yeniden bağlanma
                setTimeout(() => this.connect(), 3000);
            };
            
            this.websocket.onerror = (error) => {
                console.error('❌ WebSocket hatası:', error);
                this.triggerCallbacks('onError', error);
            };
            
        } catch (error) {
            console.error('WebSocket bağlantı hatası:', error);
        }
    }
    
    // Mesajları işle
    handleMessage(data) {
        console.log('📨 WebSocket mesajı:', data);
        
        switch (data.type) {
            case 'connected':
                console.log('✅ Bağlantı onaylandı');
                break;
                
            case 'step_update':
                this.steps = data.all_steps || [];
                this.currentStatus = data.current_status || 'idle';
                this.triggerCallbacks('onStepUpdate', {
                    newStep: data.step,
                    allSteps: this.steps,
                    status: this.currentStatus
                });
                break;
                
            case 'status_update':
                this.currentStatus = data.current_status || 'idle';
                this.steps = data.current_steps || [];
                this.triggerCallbacks('onStatusChange', {
                    status: this.currentStatus,
                    steps: this.steps
                });
                break;
                
            case 'task_completed':
                this.triggerCallbacks('onTaskComplete', {
                    task: data.task,
                    result: data.result
                });
                break;
                
            case 'task_error':
                this.triggerCallbacks('onError', {
                    task: data.task,
                    error: data.error
                });
                break;
                
            case 'pong':
                console.log('🏓 Ping-pong başarılı');
                break;
        }
    }
    
    // Event callback'leri çalıştır
    triggerCallbacks(eventType, data) {
        this.callbacks[eventType].forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error(`Callback hatası (${eventType}):`, error);
            }
        });
    }
    
    // Event listener ekle
    on(eventType, callback) {
        if (this.callbacks[eventType]) {
            this.callbacks[eventType].push(callback);
        }
    }
    
    // Görev gönder
    sendTask(task) {
        if (this.isConnected && this.websocket) {
            this.websocket.send(JSON.stringify({
                type: 'task',
                task: task
            }));
        } else {
            console.error('WebSocket bağlı değil');
        }
    }
    
    // Durum sorgula
    requestStatus() {
        if (this.isConnected && this.websocket) {
            this.websocket.send(JSON.stringify({
                type: 'get_status'
            }));
        }
    }
    
    // Ping gönder
    ping() {
        if (this.isConnected && this.websocket) {
            this.websocket.send(JSON.stringify({
                type: 'ping'
            }));
        }
    }
    
    // Bağlantıyı kapat
    disconnect() {
        if (this.websocket) {
            this.websocket.close();
        }
    }
}

// HTML'e adım listesi render et
class StepRenderer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.steps = [];
    }
    
    updateSteps(steps) {
        this.steps = steps;
        this.render();
    }
    
    render() {
        if (!this.container) return;
        
        const html = this.steps.map(step => {
            const statusIcon = {
                'başlatıldı': '🔵',
                'çalışıyor': '🟡',
                'tamamlandı': '🟢',
                'hata': '🔴'
            }[step.status] || '⚪';
            
            const statusColor = {
                'başlatıldı': '#007bff',
                'çalışıyor': '#ffc107',
                'tamamlandı': '#28a745',
                'hata': '#dc3545'
            }[step.status] || '#6c757d';
            
            return `
                <div style="border-left: 4px solid ${statusColor}; padding: 12px; margin: 8px 0; background: #f8f9fa; border-radius: 8px;">
                    <div style="font-weight: bold; margin-bottom: 4px;">
                        ${statusIcon} ${step.title}
                    </div>
                    <div style="color: #666; margin-bottom: 4px;">
                        ${step.description}
                    </div>
                    <div style="font-size: 12px; color: #999;">
                        🕒 ${step.timestamp}
                    </div>
                </div>
            `;
        }).join('');
        
        this.container.innerHTML = html;
        
        // Auto scroll to bottom
        this.container.scrollTop = this.container.scrollHeight;
    }
}

// Progress bar güncelle
class ProgressTracker {
    constructor(progressBarId, statusTextId) {
        this.progressBar = document.getElementById(progressBarId);
        this.statusText = document.getElementById(statusTextId);
        this.progress = 0;
    }
    
    updateProgress(status, steps) {
        // Progress hesapla
        const completedSteps = steps.filter(s => s.status === 'tamamlandı').length;
        const totalSteps = steps.length;
        this.progress = totalSteps > 0 ? (completedSteps / totalSteps) * 100 : 0;
        
        // Progress bar güncelle
        if (this.progressBar) {
            this.progressBar.style.width = `${this.progress}%`;
            this.progressBar.setAttribute('aria-valuenow', this.progress);
        }
        
        // Status text güncelle
        if (this.statusText) {
            const statusTexts = {
                'idle': 'Beklemede',
                'running': 'Çalışıyor',
                'completed': 'Tamamlandı',
                'error': 'Hata'
            };
            this.statusText.textContent = statusTexts[status] || status;
        }
    }
}

// Ana uygulama sınıfı
class DeepResearchAgentUI {
    constructor() {
        this.monitor = new RealTimeAgentMonitor();
        this.stepRenderer = new StepRenderer('step-container');
        this.progressTracker = new ProgressTracker('progress-bar', 'status-text');
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Adım güncelleme
        this.monitor.on('onStepUpdate', (data) => {
            this.stepRenderer.updateSteps(data.allSteps);
            this.progressTracker.updateProgress(data.status, data.allSteps);
        });
        
        // Durum değişikliği
        this.monitor.on('onStatusChange', (data) => {
            this.stepRenderer.updateSteps(data.steps);
            this.progressTracker.updateProgress(data.status, data.steps);
        });
        
        // Görev tamamlandı
        this.monitor.on('onTaskComplete', (data) => {
            console.log('✅ Görev tamamlandı:', data);
            this.showNotification('Görev başarıyla tamamlandı!', 'success');
        });
        
        // Hata
        this.monitor.on('onError', (error) => {
            console.error('❌ Hata:', error);
            this.showNotification('Bir hata oluştu: ' + (error.error || error.message), 'error');
        });
    }
    
    // Görev gönder
    sendTask(task) {
        this.monitor.sendTask(task);
        this.showNotification('Görev gönderildi: ' + task, 'info');
    }
    
    // Bildirim göster
    showNotification(message, type = 'info') {
        const colors = {
            'info': '#17a2b8',
            'success': '#28a745',
            'error': '#dc3545',
            'warning': '#ffc107'
        };
        
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${colors[type]};
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            z-index: 1000;
            max-width: 300px;
        `;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // 5 saniye sonra kaldır
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
}

// Sayfa yüklendiğinde başlat
document.addEventListener('DOMContentLoaded', () => {
    window.deepResearchUI = new DeepResearchAgentUI();
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        RealTimeAgentMonitor,
        StepRenderer,
        ProgressTracker,
        DeepResearchAgentUI
    };
}
