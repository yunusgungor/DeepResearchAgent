"""
Real-time Agent Monitoring System
Agent işlemlerini gerçek zamanlı izlemek için global broadcast sistemi
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Set, Any, Optional, Callable
import weakref
import threading

class RealTimeMonitor:
    """Global agent monitoring sistemi"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.active_websockets: Set = set()
            self.current_agents: Dict[str, Dict] = {}
            self.step_callbacks: List[Callable] = []
            self.initialized = True
            self.current_task_id = None
            self.step_counter = 0
    
    def add_websocket(self, websocket):
        """WebSocket bağlantısı ekle"""
        self.active_websockets.add(websocket)
    
    def remove_websocket(self, websocket):
        """WebSocket bağlantısını kaldır"""
        self.active_websockets.discard(websocket)
    
    def add_step_callback(self, callback):
        """Adım callback'i ekle"""
        self.step_callbacks.append(callback)
    
    async def broadcast_step(self, step_type: str, title: str, description: str, 
                           details: Optional[Dict] = None, agent_name: str = "main"):
        """Adımı tüm client'lara broadcast et"""
        self.step_counter += 1
        
        step_data = {
            "type": "detailed_step",
            "step_id": f"step_{self.step_counter}",
            "task_id": self.current_task_id,
            "agent_name": agent_name,
            "step_type": step_type,
            "title": title,
            "description": description,
            "details": details or {},
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "time_iso": datetime.now().isoformat()
        }
        
        # WebSocket broadcast
        await self._broadcast_to_websockets(step_data)
        
        # Callback'leri çağır
        for callback in self.step_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(step_data)
                else:
                    callback(step_data)
            except Exception as e:
                print(f"Callback error: {e}")
    
    async def _broadcast_to_websockets(self, data):
        """WebSocket'lere broadcast yap"""
        if not self.active_websockets:
            return
            
        disconnected = set()
        for websocket in self.active_websockets.copy():
            try:
                await websocket.send_text(json.dumps(data))
            except:
                disconnected.add(websocket)
        
        # Kopuk bağlantıları temizle
        self.active_websockets -= disconnected
    
    def start_task(self, task_id: str, task_description: str):
        """Yeni görev başlat"""
        self.current_task_id = task_id
        self.step_counter = 0
        asyncio.create_task(self.broadcast_step(
            "task_start", 
            "🚀 Görev Başlatıldı", 
            task_description,
            {"task_id": task_id}
        ))
    
    def end_task(self, success: bool = True, result: str = ""):
        """Görevi sonlandır"""
        status = "✅ Başarılı" if success else "❌ Hatalı"
        asyncio.create_task(self.broadcast_step(
            "task_end",
            f"{status} Görev Tamamlandı",
            result,
            {"success": success, "task_id": self.current_task_id}
        ))
        self.current_task_id = None


# Global monitor instance
monitor = RealTimeMonitor()


# Decorator fonksiyonları
def track_agent_step(step_type: str, title: str = "", description: str = ""):
    """Agent adımlarını izlemek için decorator"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Agent nesnesinden isim al
            agent_name = getattr(args[0], 'name', 'unknown') if args else 'unknown'
            
            # Başlangıç bildirimi
            actual_title = title or f"{func.__name__} başladı"
            actual_description = description or f"{func.__name__} fonksiyonu çalışıyor"
            
            await monitor.broadcast_step(
                step_type, 
                f"🔄 {actual_title}", 
                actual_description,
                {"function": func.__name__, "status": "started"},
                agent_name
            )
            
            try:
                # Fonksiyonu çalıştır
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Başarı bildirimi
                await monitor.broadcast_step(
                    step_type,
                    f"✅ {actual_title} Tamamlandı",
                    f"{func.__name__} başarıyla tamamlandı",
                    {"function": func.__name__, "status": "completed"},
                    agent_name
                )
                
                return result
                
            except Exception as e:
                # Hata bildirimi
                await monitor.broadcast_step(
                    step_type,
                    f"❌ {actual_title} Hatası",
                    f"Hata: {str(e)}",
                    {"function": func.__name__, "status": "error", "error": str(e)},
                    agent_name
                )
                raise
                
        return wrapper
    return decorator


def track_tool_execution(tool_name: str = ""):
    """Tool çalışmalarını izlemek için decorator"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            actual_tool_name = tool_name or getattr(args[0], '__class__', {}).get('__name__', 'unknown_tool')
            
            # Tool başlangıç
            await monitor.broadcast_step(
                "tool_execution",
                f"🔧 {actual_tool_name} Çalışıyor",
                f"Tool parametreleri hazırlanıyor",
                {"tool_name": actual_tool_name, "status": "started", "params": str(kwargs)[:200]}
            )
            
            try:
                # Tool'u çalıştır
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Sonuç bildirimi
                result_preview = str(result)[:300] if result else "Sonuç alındı"
                await monitor.broadcast_step(
                    "tool_execution",
                    f"✅ {actual_tool_name} Tamamlandı",
                    f"Tool başarıyla çalıştı: {result_preview}",
                    {"tool_name": actual_tool_name, "status": "completed", "result_length": len(str(result))}
                )
                
                return result
                
            except Exception as e:
                # Tool hatası
                await monitor.broadcast_step(
                    "tool_execution",
                    f"❌ {actual_tool_name} Hatası",
                    f"Tool hatası: {str(e)}",
                    {"tool_name": actual_tool_name, "status": "error", "error": str(e)}
                )
                raise
                
        return wrapper
    return decorator


# Utility fonksiyonlar
async def broadcast_custom_step(title: str, description: str, details: Dict = None):
    """Custom adım broadcast et"""
    await monitor.broadcast_step("custom", title, description, details)


async def broadcast_thinking(thought: str, agent_name: str = "agent"):
    """Agent düşünce sürecini broadcast et"""
    await monitor.broadcast_step(
        "thinking",
        "🧠 Agent Düşünüyor",
        thought,
        {"thought": thought},
        agent_name
    )


async def broadcast_decision(decision: str, reasoning: str = "", agent_name: str = "agent"):
    """Agent kararını broadcast et"""
    await monitor.broadcast_step(
        "decision",
        "🎯 Karar Verildi", 
        decision,
        {"decision": decision, "reasoning": reasoning},
        agent_name
    )


async def broadcast_sub_task(sub_task: str, agent_name: str = "agent"):
    """Alt görev başlatma broadcast et"""
    await monitor.broadcast_step(
        "sub_task",
        "📋 Alt Görev",
        sub_task,
        {"sub_task": sub_task},
        agent_name
    )


async def broadcast_model_call(model_name: str, input_length: int, agent_name: str = "agent"):
    """Model çağrısı broadcast et"""
    await monitor.broadcast_step(
        "model_call",
        f"🤖 {model_name} Çağrısı",
        f"Girdi uzunluğu: {input_length} karakter",
        {"model_name": model_name, "input_length": input_length},
        agent_name
    )


async def broadcast_tool_discovery(tool_name: str, tool_description: str, agent_name: str = "agent"):
    """Tool keşfi broadcast et"""
    await monitor.broadcast_step(
        "tool_discovery",
        f"🔍 Tool Bulundu: {tool_name}",
        tool_description,
        {"tool_name": tool_name, "description": tool_description},
        agent_name
    )


async def broadcast_memory_update(memory_type: str, content: str, agent_name: str = "agent"):
    """Memory güncelleme broadcast et"""
    await monitor.broadcast_step(
        "memory_update",
        f"💾 {memory_type} Güncellendi",
        content[:200] + "..." if len(content) > 200 else content,
        {"memory_type": memory_type, "content_length": len(content)},
        agent_name
    )


async def broadcast_progress(current_step: int, total_steps: int, agent_name: str = "agent"):
    """İlerleme durumu broadcast et"""
    progress_percent = (current_step / total_steps) * 100 if total_steps > 0 else 0
    await monitor.broadcast_step(
        "progress",
        f"📊 İlerleme: %{progress_percent:.1f}",
        f"Adım {current_step} / {total_steps}",
        {"current_step": current_step, "total_steps": total_steps, "progress_percent": progress_percent},
        agent_name
    )


async def broadcast_resource_usage(cpu_percent: float, memory_mb: float, agent_name: str = "agent"):
    """Kaynak kullanımı broadcast et"""
    await monitor.broadcast_step(
        "resource_usage",
        f"⚡ Kaynak Kullanımı",
        f"CPU: %{cpu_percent:.1f}, RAM: {memory_mb:.1f} MB",
        {"cpu_percent": cpu_percent, "memory_mb": memory_mb},
        agent_name
    )
