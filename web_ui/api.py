"""
DeepResearchAgent Web API
FastAPI tabanlı RESTful API servisi
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# Add project root to path
root = str(Path(__file__).resolve().parents[1])
sys.path.append(root)

# Import project modules
from src.agent import create_agent
from src.config import config
from src.logger import logger
from src.models import model_manager
from src.registry import REGISTED_AGENTS, REGISTED_TOOLS
from src.utils import assemble_project_path
from src.monitoring import monitor


# Pydantic models
class TaskRequest(BaseModel):
    task: str
    config_name: Optional[str] = "config_gemini"


class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[str] = None
    error: Optional[str] = None
    timestamp: str


class ToolRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]


class AgentStatus(BaseModel):
    is_initialized: bool
    config_name: Optional[str] = None
    available_agents: List[str]
    available_tools: List[str]
    current_task_steps: List[Dict] = []
    agent_status: str = "idle"


class SystemInfo(BaseModel):
    agents: List[str]
    tools: List[str]
    configs: List[str]
    models: List[str]


# Global variables
app = FastAPI(
    title="DeepResearchAgent API",
    description="Gelişmiş AI araştırma ve analiz platformu API'si",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent manager
current_agent = None
is_initialized = False
task_results = {}
current_task_steps = []
last_completed_task_steps = []  # Son tamamlanan görevin step'leri
current_step_status = "idle"
active_websockets = set()


@app.on_event("startup")
async def startup_event():
    """Uygulama başlangıcında çalışır"""
    logger.info("DeepResearchAgent API başlatılıyor...")


@app.on_event("shutdown")
async def shutdown_event():
    """Uygulama kapanışında çalışır"""
    logger.info("DeepResearchAgent API kapatılıyor...")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Ana sayfa"""
    return """
    <html>
        <head>
            <title>DeepResearchAgent API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                         color: white; padding: 20px; border-radius: 10px; }
                .section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 10px; }
                .endpoint { background: #f8f9fa; padding: 10px; border-radius: 5px; margin: 5px 0; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🧠 DeepResearchAgent API</h1>
                <p>Gelişmiş AI araştırma ve analiz platformu</p>
            </div>
            
            <div class="section">
                <h2>📚 API Dokümantasyonu</h2>
                <p><a href="/docs">Swagger UI</a> | <a href="/redoc">ReDoc</a></p>
            </div>
            
            <div class="section">
                <h2>🔗 Ana Endpoint'ler</h2>
                <div class="endpoint"><strong>GET</strong> /health - Sistem durumu</div>
                <div class="endpoint"><strong>GET</strong> /status - Agent durumu</div>
                <div class="endpoint"><strong>POST</strong> /agent/initialize - Agent başlat</div>
                <div class="endpoint"><strong>POST</strong> /agent/task - Görev çalıştır</div>
                <div class="endpoint"><strong>POST</strong> /tools/run - Araç çalıştır</div>
                <div class="endpoint"><strong>GET</strong> /system/info - Sistem bilgisi</div>
            </div>
            
            <div class="section">
                <h2>🚀 Hızlı Başlangıç</h2>
                <pre>
# Agent başlat
curl -X POST "http://localhost:8000/agent/initialize" 
     -H "Content-Type: application/json" 
     -d '{"config_name": "config_gemini"}'

# Görev çalıştır
curl -X POST "http://localhost:8000/agent/task" 
     -H "Content-Type: application/json" 
     -d '{"task": "AI Agent konusunu araştır"}'
                </pre>
            </div>
        </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """Sistem sağlık kontrolü"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@app.get("/status", response_model=AgentStatus)
async def get_agent_status():
    """Agent durumunu getir"""
    global current_task_steps, last_completed_task_steps
    
    # Eğer şu anda aktif step'ler varsa onları döndür
    if current_task_steps:
        steps_to_return = current_task_steps
    # Aksi halde son tamamlanan görevin step'lerini döndür
    elif last_completed_task_steps:
        steps_to_return = last_completed_task_steps
    else:
        steps_to_return = []
        
    return AgentStatus(
        is_initialized=is_initialized,
        config_name=getattr(config, 'tag', None) if is_initialized else None,
        available_agents=list(REGISTED_AGENTS.keys()),
        available_tools=list(REGISTED_TOOLS.keys()),
        current_task_steps=steps_to_return,
        agent_status=current_step_status
    )


@app.post("/agent/initialize")
async def initialize_agent(config_name: str = "config_gemini"):
    """Agent'ı başlat"""
    global current_agent, is_initialized
    
    try:
        config_path = assemble_project_path(f"./configs/{config_name}.toml")
        
        # Check if config file exists
        if not os.path.exists(config_path):
            raise HTTPException(status_code=400, detail=f"Konfigürasyon dosyası bulunamadı: {config_name}")
        
        config.init_config(config_path=config_path)
        logger.init_logger(config.log_path)
        model_manager.init_models(use_local_proxy=config.use_local_proxy)
        
        current_agent = await create_agent()
        is_initialized = True
        
        return {
            "status": "success",
            "message": "Agent başarıyla başlatıldı",
            "config": config_name,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent başlatılırken hata oluştu: {str(e)}")


@app.post("/agent/task", response_model=TaskResponse)
async def run_task(request: TaskRequest):
    """Görev çalıştır ve gerçek zamanlı adımları izle"""
    global current_agent, is_initialized, current_task_steps, current_step_status, last_completed_task_steps
    
    if not is_initialized or current_agent is None:
        raise HTTPException(status_code=400, detail="Agent henüz başlatılmamış")
    
    task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    # Yeni task başladığında eski current step'leri last_completed'e kaydet
    if current_task_steps:
        last_completed_task_steps = current_task_steps.copy()
    current_task_steps = []
    current_step_status = "running"
    
    # Başlangıç adımını WebSocket ile bildir
    await broadcast_step("🚀 Görev Başlatıldı", f"Görev: {request.task}", "başlatıldı")
    
    try:
        # Agent planlama
        await broadcast_step("🧠 Planlama", "Görev analiz ediliyor", "çalışıyor")
        await asyncio.sleep(0.5)
        
        # Tool seçimi
        await broadcast_step("🔧 Araç Seçimi", "Uygun araçlar belirleniyor", "çalışıyor")
        await asyncio.sleep(0.5)
        
        # Ana işlem
        await broadcast_step("⚡ Agent Çalışıyor", "Ana görev işleme başladı", "çalışıyor")
        result = await current_agent.run(request.task)
        
        # Sonuç işleme
        await broadcast_step("📊 Sonuç Hazırlanıyor", "Sonuçlar formatlanıyor", "çalışıyor")
        await asyncio.sleep(0.3)
        
        # Tamamlandı
        await broadcast_step("✅ Görev Tamamlandı", "Tüm işlemler başarıyla tamamlandı", "tamamlandı")
        current_step_status = "completed"
        
        # Tamamlanan görevin step'lerini sakla
        last_completed_task_steps = current_task_steps.copy()
        
        task_response = TaskResponse(
            task_id=task_id,
            status="completed",
            result=str(result),
            timestamp=datetime.now().isoformat()
        )
        
        # Store result for later retrieval
        task_results[task_id] = task_response
        
        return task_response
        
    except Exception as e:
        await broadcast_step("❌ Hata Oluştu", f"Hata: {str(e)}", "hata")
        current_step_status = "error"
        
        error_response = TaskResponse(
            task_id=task_id,
            status="error",
            error=str(e),
            timestamp=datetime.now().isoformat()
        )
        
        task_results[task_id] = error_response
        return error_response


async def broadcast_step(title: str, description: str, status: str):
    """Adım bilgisini tüm WebSocket bağlantılarına gönder"""
    global current_task_steps, active_websockets
    
    step = {
        "title": title,
        "description": description,
        "status": status,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }
    
    current_task_steps.append(step)
    
    # WebSocket mesajı
    message = {
        "type": "step_update",
        "step": step,
        "all_steps": current_task_steps,
        "current_status": current_step_status
    }
    
    # Tüm aktif WebSocket bağlantılarına gönder
    disconnected = set()
    for websocket in active_websockets.copy():  # Copy ile iterasyon güvenliği
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            print(f"WebSocket broadcast hatası: {e}")
            disconnected.add(websocket)
    
    # Kopuk bağlantıları temizle
    active_websockets -= disconnected


@app.get("/agent/task/{task_id}", response_model=TaskResponse)
async def get_task_result(task_id: str):
    """Görev sonucunu getir"""
    if task_id not in task_results:
        raise HTTPException(status_code=404, detail="Görev bulunamadı")
    
    return task_results[task_id]


@app.post("/tools/run")
async def run_tool(request: ToolRequest):
    """Araç çalıştır"""
    from src.tools.deep_researcher import DeepResearcherTool
    from src.tools.deep_analyzer import DeepAnalyzerTool
    from src.tools.auto_browser import AutoBrowserUseTool
    from src.tools.python_interpreter import PythonInterpreterTool
    
    tools = {
        "deep_researcher": DeepResearcherTool(),
        "deep_analyzer": DeepAnalyzerTool(),
        "auto_browser": AutoBrowserUseTool(),
        "python_interpreter": PythonInterpreterTool()
    }
    
    if request.tool_name not in tools:
        raise HTTPException(status_code=400, detail=f"Araç bulunamadı: {request.tool_name}")
    
    try:
        tool = tools[request.tool_name]
        result = await tool.forward(**request.parameters)
        
        if hasattr(result, 'output'):
            output = result.output
        else:
            output = str(result)
        
        return {
            "status": "success",
            "tool": request.tool_name,
            "result": output,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Araç çalıştırılırken hata oluştu: {str(e)}")


@app.get("/system/info", response_model=SystemInfo)
async def get_system_info():
    """Sistem bilgilerini getir"""
    config_dir = Path(root) / "configs"
    available_configs = []
    
    if config_dir.exists():
        available_configs = [f.stem for f in config_dir.glob("*.toml")]
    
    return SystemInfo(
        agents=list(REGISTED_AGENTS.keys()),
        tools=list(REGISTED_TOOLS.keys()),
        configs=available_configs,
        models=[
            "gemini-1.5-pro", "gemini-2.5-pro", "gpt-4.1", "gpt-4o",
            "claude-3.7-sonnet", "qwen2.5-7b-instruct", "qwen2.5-14b-instruct"
        ]
    )


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Dosya yükle"""
    try:
        upload_dir = Path(root) / "uploads"
        upload_dir.mkdir(exist_ok=True)
        
        file_path = upload_dir / file.filename
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return {
            "status": "success",
            "filename": file.filename,
            "path": str(file_path),
            "size": len(content),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dosya yüklenirken hata oluştu: {str(e)}")


@app.get("/logs")
async def get_logs(lines: int = 100):
    """Sistem loglarını getir"""
    try:
        log_path = Path(root) / "log.txt"
        
        if not log_path.exists():
            return {"logs": [], "message": "Log dosyası bulunamadı"}
        
        with open(log_path, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return {
            "logs": [line.strip() for line in recent_lines],
            "total_lines": len(all_lines),
            "returned_lines": len(recent_lines),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Loglar okunurken hata oluştu: {str(e)}")


@app.delete("/agent/reset")
async def reset_agent():
    """Agent'ı sıfırla"""
    global current_agent, is_initialized, task_results
    
    current_agent = None
    is_initialized = False
    task_results = {}
    
    return {
        "status": "success",
        "message": "Agent sıfırlandı",
        "timestamp": datetime.now().isoformat()
    }


# WebSocket endpoint for real-time communication
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket bağlantısı - Gerçek zamanlı adım takibi"""
    global active_websockets
    
    await websocket.accept()
    
    # WebSocket'i global set'e ekle
    active_websockets.add(websocket)
    
    # Monitor'a WebSocket ekle
    monitor.add_websocket(websocket)
    
    try:
        # Bağlantı onayı
        await websocket.send_text(json.dumps({
            "type": "connected",
            "message": "WebSocket bağlantısı kuruldu - Real-time monitoring aktif",
            "timestamp": datetime.now().isoformat()
        }))
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong", 
                    "timestamp": datetime.now().isoformat()
                }))
            
            elif message.get("type") == "get_status":
                # Anlık durumu gönder
                await websocket.send_text(json.dumps({
                    "type": "status_update",
                    "agent_initialized": is_initialized,
                    "current_status": current_step_status,
                    "current_steps": current_task_steps,
                    "timestamp": datetime.now().isoformat()
                }))
            
            elif message.get("type") == "task":
                if not is_initialized:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Agent henüz başlatılmamış"
                    }))
                    continue
                
                task = message.get("task", "")
                if task:
                    try:
                        # Görev başlatma bildirimi
                        await websocket.send_text(json.dumps({
                            "type": "task_started",
                            "task": task,
                            "timestamp": datetime.now().isoformat()
                        }))
                        
                        # Görevi çalıştır (adımlar otomatik broadcast edilecek)
                        result = await current_agent.run(task)
                        
                        # Sonuç bildirimi
                        await websocket.send_text(json.dumps({
                            "type": "task_completed",
                            "task": task,
                            "result": str(result),
                            "timestamp": datetime.now().isoformat()
                        }))
                        
                    except Exception as e:
                        await websocket.send_text(json.dumps({
                            "type": "task_error",
                            "task": task,
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        }))
            
    except Exception as e:
        print(f"WebSocket hatası: {e}")
    finally:
        # WebSocket'i global set'ten kaldır
        active_websockets.discard(websocket)
        
        # Monitor'dan WebSocket'i kaldır
        monitor.remove_websocket(websocket)


@app.get("/agent/steps")
async def get_current_steps():
    """Mevcut görev adımlarını getir"""
    global current_task_steps, last_completed_task_steps
    
    # Eğer şu anda aktif step'ler varsa onları döndür
    if current_task_steps:
        steps_to_return = current_task_steps
        status = current_step_status
    # Aksi halde son tamamlanan görevin step'lerini döndür
    elif last_completed_task_steps:
        steps_to_return = last_completed_task_steps
        status = "completed"
    else:
        steps_to_return = []
        status = "idle"
    
    return {
        "status": status,
        "steps": steps_to_return,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
