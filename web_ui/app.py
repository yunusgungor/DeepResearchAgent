"""
DeepResearchAgent Web UI
Modern web arayüzü ile tüm agent yeteneklerini kullanabilir.
"""

import asyncio
import json
import os
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

# Add project root to path
root = str(Path(__file__).resolve().parents[1])
sys.path.append(root)

warnings.filterwarnings("ignore", category=DeprecationWarning)

# Import project modules
from src.agent import create_agent
from src.config import config
from src.logger import logger
from src.models import model_manager
from src.registry import REGISTED_AGENTS, REGISTED_TOOLS
from src.utils import assemble_project_path
from src.monitoring import monitor

# Config'i hemen initialize et
config_path = assemble_project_path("./configs/config_webui.toml")
config.init_config(config_path=config_path)
logger.info(f"Web UI: Config yüklendi: {config_path}")

# Model manager'ı initialize et
try:
    model_manager.init_models(use_local_proxy=config.use_local_proxy)
    logger.info(f"Model manager initialized with {len(model_manager.registed_models)} models")
except Exception as e:
    logger.warning(f"Model manager initialization failed: {e}")


class WebUIConfig:
    """Web UI konfigürasyon sınıfı"""
    
    def __init__(self):
        self.available_configs = self._get_available_configs()
        self.available_models = [
            "gemini-2.5-flash", "gemini-1.5-pro", "gemini-2.5-pro", "gpt-4.1", "gpt-4o", 
            "claude-3.7-sonnet", "qwen2.5-7b-instruct", "qwen2.5-14b-instruct"
        ]
        self.agent_types = list(REGISTED_AGENTS.keys())
        self.tool_types = list(REGISTED_TOOLS.keys())
    
    def _get_available_configs(self) -> List[str]:
        """Mevcut konfigürasyon dosyalarını listele"""
        config_dir = Path(root) / "configs"
        if config_dir.exists():
            return [f.stem for f in config_dir.glob("*.toml") if f.name != "config_example.toml"]
        return ["config_gemini", "config_gaia", "config_hle", "config_mcp", "config_qwen"]
    
    def check_api_keys(self) -> Dict[str, bool]:
        """API anahtarlarının durumunu kontrol et"""
        try:
            import os
            api_keys_status = {
                "GOOGLE_API_KEY": bool(os.environ.get("GOOGLE_API_KEY")),
                "OPENAI_API_KEY": bool(os.environ.get("OPENAI_API_KEY")),
                "ANTHROPIC_API_KEY": bool(os.environ.get("ANTHROPIC_API_KEY")),
                "QWEN_API_KEY": bool(os.environ.get("QWEN_API_KEY", "")),
                "SERPER_API_KEY": bool(os.environ.get("SERPER_API_KEY")),
            }
            return api_keys_status
        except Exception as e:
            logger.error(f"API anahtarları kontrol edilirken hata: {e}")
            return {
                "GOOGLE_API_KEY": False,
                "OPENAI_API_KEY": False,
                "ANTHROPIC_API_KEY": False,
                "QWEN_API_KEY": False,
                "SERPER_API_KEY": False,
            }


class AgentManager:
    """Agent yönetimi için sınıf"""
    
    def __init__(self):
        self.current_agent = None
        self.is_initialized = False
        self.current_task_steps = []
        self.current_step_status = "idle"
        self.step_progress = 0
        self.detailed_steps = []  # Detaylı adım izleme
        self.step_callback_added = False
    
    async def initialize_agent(self, config_path: str = None) -> bool:
        """Agent'ı başlat"""
        try:
            if config_path:
                logger.info(f"Agent Manager: Config path verildi: {config_path}")
                config.init_config(config_path=config_path)
            else:
                # Web UI için özel config dosyasını kullan
                webui_config_path = assemble_project_path("./configs/config_webui.toml")
                logger.info(f"Agent Manager: Varsayılan config kullanılıyor: {webui_config_path}")
                config.init_config(config_path=webui_config_path)
            
            logger.info(f"Agent Manager: Config yüklendi, deep_researcher_tool config: {config.deep_researcher_tool}")
            
            logger.init_logger(config.log_path)
            model_manager.init_models(use_local_proxy=config.use_local_proxy)
            
            # Model kontrolü
            if not model_manager.registed_models:
                raise ValueError("Hiç model kayıtlı değil! API anahtarlarını kontrol edin.")
            
            self.current_agent = await create_agent()
            self.is_initialized = True
            
            # Monitoring callback'ini agent'a ekle
            if not self.step_callback_added and self.current_agent:
                logger.info(f"Agent monitoring callback sistemi kurulıyor...")
                
                # Agent'ın step_callbacks listesine monitoring callback'ini ekle
                def monitoring_step_callback(step):
                    """Agent step callback'i için monitoring entegrasyonu"""
                    logger.info(f"Agent step callback çağrıldı: {step}")
                    
                    # Step verilerini detaylı monitoring formatına çevir
                    step_data = {
                        "type": "detailed_step",
                        "step_id": f"step_{getattr(step, 'step_number', 0)}",
                        "agent_name": getattr(self.current_agent, 'name', 'agent'),
                        "step_type": "step_progress",
                        "title": f"🔄 Adım {getattr(step, 'step_number', 0)}",
                        "description": getattr(step, 'action_output', 'İşlem devam ediyor'),
                        "details": {
                            "step_number": getattr(step, 'step_number', 0),
                            "duration": getattr(step, 'duration', 0),
                            "status": "completed" if hasattr(step, 'action_output') else "running"
                        },
                        "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
                        "time_iso": datetime.now().isoformat()
                    }
                    
                    # Monitoring sistemine ekle
                    self._handle_detailed_step(step_data)
                
                # Agent'ın mevcut step_callbacks listesini kontrol et
                if hasattr(self.current_agent, 'step_callbacks'):
                    logger.info(f"Agent step_callbacks listesi mevcut: {len(self.current_agent.step_callbacks)} callback")
                    self.current_agent.step_callbacks.append(monitoring_step_callback)
                else:
                    logger.warning("Agent step_callbacks listesi bulunamadı!")
                    # Eğer yoksa oluştur
                    self.current_agent.step_callbacks = [monitoring_step_callback]
                
                # Global monitor callback de ekle
                monitor.add_step_callback(self._handle_detailed_step)
                self.step_callback_added = True
                
                logger.info(f"Monitoring callback sistemi kuruldu!")
            
            return True
        except Exception as e:
            st.error(f"Agent başlatılırken hata oluştu: {str(e)}")
            return False
    
    def _handle_detailed_step(self, step_data):
        """Detaylı adım verilerini işle"""
        logger.info(f"Detaylı adım alındı: {step_data.get('title', 'Bilinmeyen')}")
        self.detailed_steps.append(step_data)
        
        # Step type'a göre genel adımları güncelle
        step_type = step_data.get('step_type', '')
        title = step_data.get('title', '')
        
        logger.info(f"Toplam detaylı adım sayısı: {len(self.detailed_steps)}")
        description = step_data.get('description', '')
        
        # Ana adım kategorilerine dönüştür
        if step_type in ['task_start', 'agent_start']:
            self.add_step("🚀 Görev Başlatıldı", description, "başlatıldı")
        elif step_type in ['planning']:
            self.add_step("🧠 Planlama", description, "çalışıyor")
        elif step_type in ['step_start', 'action_execution']:
            self.add_step("⚡ İşlem Yapılıyor", description, "çalışıyor")
        elif step_type in ['model_thinking', 'model_input', 'model_output']:
            self.add_step("🤖 Model İşlemi", description, "çalışıyor")
        elif step_type in ['tool_parsing', 'tool_found', 'tool_execution_start']:
            self.add_step("🔧 Tool Hazırlığı", description, "çalışıyor")
        elif step_type in ['tool_execution', 'tool_execution_detail', 'tool_prepare']:
            self.add_step("⚙️ Tool Çalışıyor", description, "çalışıyor")
        elif step_type in ['tool_result', 'tool_success', 'action_result']:
            self.add_step("📊 Tool Sonucu", description, "çalışıyor")
        elif step_type in ['step_complete']:
            self.add_step("✅ Adım Tamamlandı", description, "tamamlandı")
        elif step_type in ['final_answer', 'final_answer_processing', 'task_end']:
            self.add_step("🎯 Final Cevap", description, "tamamlandı")
        elif step_type in ['agent_error', 'step_error', 'model_error', 'parsing_error']:
            self.add_step("❌ Hata", description, "hata")
        elif step_type in ['tool_parameter_error', 'tool_execution_error', 'tool_not_found']:
            self.add_step("🔧❌ Tool Hatası", description, "hata")
        elif step_type in ['max_steps_reached']:
            self.add_step("⏰ Zaman Aşımı", description, "uyarı")
    
    async def run_task(self, task: str) -> str:
        """Görevi çalıştır ve adımları izle"""
        if not self.is_initialized or not self.current_agent:
            return "❌ **Agent henüz başlatılmamış!**\n\nLütfen önce sol panelden bir agent seçin ve başlatın."
        
        self.current_task_steps = []
        self.current_step_status = "running"
        self.step_progress = 0
        
        try:
            # Task başlangıcını kaydet
            self.add_step("🚀 Görev Başlatıldı", f"Görev: {task}", "başlatıldı")
            
            # Agent'ı çalıştır (bu kısımda gerçek zamanlı izleme eklenecek)
            result = await self._run_with_monitoring(task)
            
            self.add_step("✅ Görev Tamamlandı", "Tüm işlemler başarıyla tamamlandı", "tamamlandı")
            self.current_step_status = "completed"
            self.step_progress = 100
            
            # Sonucu markdown formatında düzenle
            formatted_result = self._format_result(result, task)
            return formatted_result
            
        except Exception as e:
            self.add_step("❌ Hata Oluştu", f"Hata: {str(e)}", "hata")
            self.current_step_status = "error" 
            return f"❌ **Görev çalıştırılırken hata oluştu:**\n\n```\n{str(e)}\n```\n\nLütfen tekrar deneyin."
    
    def _format_result(self, result: any, task: str) -> str:
        """Sonucu güzel formatlama"""
        formatted = f"## 🎯 Görev Sonucu\n\n"
        formatted += f"**📝 Görev:** {task}\n\n"
        formatted += f"**⏰ Tamamlanma Zamanı:** {datetime.now().strftime('%H:%M:%S')}\n\n"
        formatted += "---\n\n"
        
        # Result'ı string'e çevir ve formatlama
        result_str = str(result)
        
        # Eğer sonuç çok uzunsa bölümler halinde düzenle
        if len(result_str) > 1000:
            formatted += "### 📊 Detaylı Sonuçlar\n\n"
            
            # Paragrafları ayır
            paragraphs = result_str.split('\n\n')
            for i, paragraph in enumerate(paragraphs):
                if paragraph.strip():
                    formatted += f"{paragraph.strip()}\n\n"
        else:
            formatted += f"### 💡 Sonuç\n\n{result_str}\n\n"
        
        formatted += "---\n\n"
        formatted += f"✅ **Durum:** Başarıyla tamamlandı\n"
        formatted += f"📈 **İşlem Adımları:** {len(self.current_task_steps)} adım\n"
        
        return formatted
    
    def add_step(self, title: str, description: str, status: str):
        """Adım ekle"""
        step = {
            "title": title,
            "description": description,
            "status": status,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "time": datetime.now()
        }
        self.current_task_steps.append(step)
        
        # Progress güncelle
        if status == "tamamlandı":
            self.step_progress = min(100, self.step_progress + 20)
    
    async def _run_with_monitoring(self, task: str):
        """Görev çalıştırma ve izleme"""
        try:
            # Başlangıç adımı
            self.add_step("🚀 Görev Başlatılıyor", f"Görev: {task}", "başlatıldı")
            self.current_step_status = "running"
            
            # Debug: Agent durumunu kontrol et
            logger.info(f"Agent durumu: initialized={self.is_initialized}, agent={self.current_agent}")
            logger.info(f"Agent çalıştırılıyor: {task}")
            
            # Monitoring başlat
            monitor.start_task(f"webui_{int(time.time())}", task)
            
            # Agent'ı çalıştır
            self.add_step("🤖 Agent Çalışıyor", "Görev analiz ediliyor ve plan hazırlanıyor", "çalışıyor")
            
            # Agent'ın run metodunu await ile çağır
            logger.info(f"Agent.run() çağrılıyor...")
            result = await self.current_agent.run(task)
            logger.info(f"Agent.run() tamamlandı, sonuç uzunluğu: {len(str(result)) if result else 0}")
            
            # Başarı adımı
            self.add_step("✅ Görev Tamamlandı", "Agent görevi başarıyla tamamladı", "tamamlandı")
            self.current_step_status = "completed"
            
            # Monitoring bitir
            monitor.end_task(success=True, result=str(result)[:200])
            
            logger.info(f"Agent sonucu: {str(result)[:100]}...")
            
            return result
            
        except Exception as e:
            # Hata adımı
            self.add_step("❌ Hata Oluştu", f"Agent çalışırken hata: {str(e)}", "hata")
            self.current_step_status = "error"
            
            # Hata durumunda monitoring'i bitir
            monitor.end_task(success=False, result=f"Hata: {str(e)}")
            
            logger.error(f"Agent hatası: {e}")
            logger.error(f"Hata detayı: ", exc_info=True)
            raise e


class ToolManager:
    """Tool yönetimi için sınıf"""
    
    def __init__(self):
        self.tools = {}
        self.tools_loaded = False
    
    def load_tools(self):
        """Tool'ları config yüklendikten sonra yükle"""
        if self.tools_loaded:
            return
            
        try:
            # Temel araçları güvenli şekilde yükle
            from src.tools.web_searcher import WebSearcherTool
            from src.tools.web_fetcher import WebFetcherTool
            from src.tools.python_interpreter import PythonInterpreterTool
            
            self.tools["web_searcher"] = WebSearcherTool()
            self.tools["web_fetcher"] = WebFetcherTool()
            self.tools["python_interpreter"] = PythonInterpreterTool()
            
            # Gelişmiş araçları dikkatli yükle
            try:
                from src.tools.deep_researcher import DeepResearcherTool
                self.tools["deep_researcher"] = DeepResearcherTool()
                st.success("Deep Researcher Tool başarıyla yüklendi")
            except Exception as e:
                st.warning(f"Deep Researcher Tool yüklenemedi: {str(e)}")
            
            try:
                from src.tools.deep_analyzer import DeepAnalyzerTool  
                self.tools["deep_analyzer"] = DeepAnalyzerTool()
                st.success("Deep Analyzer Tool başarıyla yüklendi")
            except Exception as e:
                st.warning(f"Deep Analyzer Tool yüklenemedi: {str(e)}")
            
            try:
                from src.tools.auto_browser import AutoBrowserUseTool
                self.tools["auto_browser"] = AutoBrowserUseTool()
                st.success("Auto Browser Tool başarıyla yüklendi")
            except Exception as e:
                st.warning(f"Auto Browser Tool yüklenemedi: {str(e)}")
                
            self.tools_loaded = True
            
        except Exception as e:
            st.error(f"Araçlar yüklenirken genel hata: {str(e)}")
            # En azından boş araç listesi tut
            self.tools = {}
    
    async def run_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Tool'u çalıştır"""
        if tool_name not in self.tools:
            return f"Tool bulunamadı: {tool_name}"
        
        try:
            tool = self.tools[tool_name]
            result = await tool.forward(**parameters)
            if hasattr(result, 'output'):
                return str(result.output)
            return str(result)
        except Exception as e:
            return f"Tool çalıştırılırken hata oluştu: {str(e)}"


def init_session_state():
    """Session state'i başlat"""
    if 'ui_config' not in st.session_state:
        st.session_state.ui_config = WebUIConfig()
    
    if 'agent_manager' not in st.session_state:
        st.session_state.agent_manager = AgentManager()
    
    if 'tool_manager' not in st.session_state:
        st.session_state.tool_manager = ToolManager()
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'task_history' not in st.session_state:
        st.session_state.task_history = []
    
    if 'agent_steps_expanded' not in st.session_state:
        st.session_state.agent_steps_expanded = True
    
    if 'auto_scroll' not in st.session_state:
        st.session_state.auto_scroll = True
    
    if 'show_technical_details' not in st.session_state:
        st.session_state.show_technical_details = False
    
    if 'notification_sound' not in st.session_state:
        st.session_state.notification_sound = True
    
    if 'auto_refresh_enabled' not in st.session_state:
        st.session_state.auto_refresh_enabled = False
    
    if 'last_refresh_time' not in st.session_state:
        st.session_state.last_refresh_time = time.time()


def display_sidebar():
    """Yan panel menüsünü göster"""
    with st.sidebar:
        st.title("🧠 DeepResearchAgent")
        st.markdown("---")
        
        # API Anahtarı Durumu Kontrolü
        api_check_result = st.session_state.ui_config.check_api_keys()
        
        # En az bir API anahtarının olup olmadığını kontrol et
        has_any_api_key = any(api_check_result.values())
        
        if not has_any_api_key:
            st.error("⚠️ **API Hatası:** Hiç API anahtarı bulunamadı!")
            st.info("💡 **Çözüm:** En az bir API anahtarını ortam değişkenlerinizde ayarlayın.")
            
            # API anahtarı durumlarını göster
            with st.expander("🔑 API Anahtarları Durumu", expanded=True):
                for api_name, status in api_check_result.items():
                    status_icon = "✅" if status else "❌"
                    st.write(f"{status_icon} {api_name}: {'Var' if status else 'Yok'}")
                
                st.markdown("**Ortam değişkenlerinizi kontrol edin:**")
                st.code("""
export GOOGLE_API_KEY="your_google_api_key"
export OPENAI_API_KEY="your_openai_api_key"
export ANTHROPIC_API_KEY="your_anthropic_api_key"
export SERPER_API_KEY="your_serper_api_key"
                """)
            
            return  # API anahtarı yoksa diğer kontrolleri gösterme
        else:
            # Mevcut API anahtarlarını göster
            active_apis = [name for name, status in api_check_result.items() if status]
            st.success(f"✅ API Anahtarları: {', '.join(active_apis)}")
        
        # Konfigürasyon seçimi
        st.subheader("⚙️ Konfigürasyon")
        config_options = st.session_state.ui_config.available_configs
        selected_config = st.selectbox(
            "Konfigürasyon dosyası seçin:",
            options=config_options,
            index=0 if config_options else None,
            help="Kullanılacak konfigürasyon dosyasını seçin"
        )
        
        # Agent durumu
        st.subheader("🤖 Agent Durumu")
        is_initialized = st.session_state.agent_manager.is_initialized
        status_color = "🟢" if is_initialized else "🔴"
        st.write(f"{status_color} Durum: {'Hazır' if is_initialized else 'Başlatılmamış'}")
        
        # Agent başlat/durdur
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 Başlat", disabled=is_initialized):
                config_path = assemble_project_path(f"./configs/{selected_config}.toml")
                with st.spinner("Agent başlatılıyor..."):
                    success = asyncio.run(st.session_state.agent_manager.initialize_agent(config_path))
                    if success:
                        st.success("Agent başarıyla başlatıldı!")
                        st.rerun()
        
        with col2:
            if st.button("⏹️ Durdur", disabled=not is_initialized):
                st.session_state.agent_manager.is_initialized = False
                st.session_state.agent_manager.current_agent = None
                st.success("Agent durduruldu!")
                st.rerun()
        
        # Hızlı eylemler
        st.markdown("---")
        st.subheader("⚡ Hızlı Eylemler")
        
        if st.button("🧹 Geçmişi Temizle"):
            st.session_state.chat_history = []
            st.session_state.task_history = []
            st.success("Geçmiş temizlendi!")
            st.rerun()
        
        if st.button("📊 Sistem Bilgisi"):
            st.info(f"""
            **Mevcut Agentlar:** {len(st.session_state.ui_config.agent_types)}
            **Mevcut Araçlar:** {len(st.session_state.ui_config.tool_types)}
            **Konfigürasyonlar:** {len(st.session_state.ui_config.available_configs)}
            """)


def display_main_interface():
    """Ana arayüzü göster"""
    # Tab'lar oluştur
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💬 Sohbet", "🔧 Araçlar", "📊 Dashboard", "⚙️ Ayarlar", "📚 Dokümantasyon"
    ])
    
    with tab1:
        display_chat_interface()
    
    with tab2:
        display_tools_interface()
    
    with tab3:
        display_dashboard()
    
    with tab4:
        display_settings()
    
    with tab5:
        display_documentation()


def display_chat_interface():
    """Sohbet arayüzünü göster"""
    st.header("💬 AI Agent ile Sohbet")
    
    # Agent durumu kontrolü
    if not st.session_state.agent_manager.is_initialized:
        st.warning("⚠️ **Agent henüz başlatılmamış!** Sol panelden bir agent seçin ve başlatın.")
        st.info("💡 **Nasıl başlarım?**\n1. Sol panelden agent türünü seçin\n2. Konfigürasyon dosyasını seçin\n3. '🚀 Başlat' butonuna tıklayın")
        return
    
    # Tool'ları yükle (config yüklendikten sonra)
    if not st.session_state.tool_manager.tools_loaded:
        with st.spinner("Araçlar yükleniyor..."):
            st.session_state.tool_manager.load_tools()
    
    # Ana sohbet konteyneri
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Sohbet geçmişini göster
        st.subheader("💭 Sohbet Geçmişi")
        
        # Eğer henüz mesaj yoksa öneri göster
        if not st.session_state.chat_history:
            st.info("💬 **İlk mesajınızı gönderin!**\n\nAşağıdaki örnek görevlerden birini seçebilir veya kendi sorunuzu yazabilirsiniz.")
        
        chat_container = st.container()
        
        with chat_container:
            for i, message in enumerate(st.session_state.chat_history):
                with st.container():
                    if message['role'] == 'user':
                        st.markdown(f"""
                        <div style='background-color: #e3f2fd; padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 4px solid #2196f3;'>
                            <strong>👤 Kullanıcı:</strong> {message['content']}<br>
                            <small style='color: #666;'>🕒 {message['timestamp']}</small>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        # Agent cevabını daha güzel formatlama
                        content = message['content']
                        
                        # Uzun metinleri expander içinde göster
                        if len(content) > 500:
                            with st.expander(f"🤖 Agent Cevabı - {message['timestamp']}", expanded=True):
                                # Markdown formatında göster
                                st.markdown(content)
                                
                                # Eğer task history'de steps varsa göster
                                task_index = i // 2  # Her user-assistant çifti için index
                                if task_index < len(st.session_state.task_history):
                                    task_data = st.session_state.task_history[task_index]
                                    if 'steps' in task_data and task_data['steps']:
                                        with st.expander("🔍 İşlem Adımları", expanded=False):
                                            for step in task_data['steps']:
                                                step_title = step.get('title', 'Bilinmeyen')
                                                step_desc = step.get('description', '')
                                                step_status = step.get('status', 'unknown')
                                                
                                                # Status'a göre emoji
                                                if step_status == 'tamamlandı':
                                                    emoji = '✅'
                                                elif step_status == 'çalışıyor':
                                                    emoji = '⏳'
                                                elif step_status == 'hata':
                                                    emoji = '❌'
                                                else:
                                                    emoji = '🔄'
                                                
                                                st.markdown(f"**{emoji} {step_title}**")
                                                if step_desc:
                                                    st.caption(step_desc)
                        else:
                            st.markdown(f"""
                            <div style='background-color: #f3e5f5; padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 4px solid #9c27b0;'>
                                <strong>🤖 Agent:</strong><br>
                                <div style='margin-top: 10px;'>{content}</div>
                                <small style='color: #666;'>🕒 {message['timestamp']}</small>
                            </div>
                            """, unsafe_allow_html=True)
                st.divider()
    
    with col2:
        # Gerçek zamanlı agent durumu
        display_real_time_agent_status()
    
    # Yeni mesaj girişi
    st.subheader("✏️ Yeni Mesaj")
    with st.container():
        col1, col2 = st.columns([9, 1])
        
        with col1:
            # Örnek görev seçildiyse onu varsayılan değer olarak kullan
            default_value = ""
            if hasattr(st.session_state, 'selected_example_task'):
                default_value = st.session_state.selected_example_task
                # Görev kullanıldıktan sonra temizle
                del st.session_state.selected_example_task
            
            user_input = st.text_area(
                "Mesajınızı yazın:",
                value=default_value,
                placeholder="DeepResearchAgent'a ne sormak istiyorsunuz?",
                height=100,
                key="chat_input"
            )
        
        with col2:
            send_button = st.button("📤 Gönder", use_container_width=True)
    
    # Önceden tanımlı görevler
    st.subheader("📝 Örnek Görevler")
    example_tasks = [
        "AI Agent konusundaki en son makaleleri araştır ve özetle",
        "Python ile veri analizi yapma konusunda kapsamlı bir araştırma yap",
        "Machine Learning trendlerini araştır ve rapor hazırla",
        "Verilen bir web sitesini analiz et ve önemli bilgileri çıkar"
    ]
    
    col1, col2 = st.columns(2)
    for i, task in enumerate(example_tasks):
        column = col1 if i % 2 == 0 else col2
        with column:
            if st.button(f"📋 {task[:50]}...", key=f"example_{i}"):
                st.session_state.selected_example_task = task
                st.rerun()
    
    # Mesaj gönderme
    if send_button and user_input.strip():
        if not st.session_state.agent_manager.is_initialized:
            st.error("⚠️ Önce agent'ı başlatmanız gerekiyor!")
        else:
            # Kullanıcı mesajını ekle
            timestamp = datetime.now().strftime("%H:%M:%S")
            st.session_state.chat_history.append({
                'role': 'user',
                'content': user_input,
                'timestamp': timestamp
            })
            
            # Agent'dan cevap al - Gerçek zamanlı izleme ile
            with st.spinner("🤔 Agent düşünüyor..."):
                # Progress tracking için placeholders
                progress_container = st.container()
                
                with progress_container:
                    # Progress bar ve status
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    step_details = st.empty()
                    
                    # Task başlat
                    status_text.text("🚀 Görev başlatılıyor...")
                    progress_bar.progress(10)
                    
                    # Task çalıştır
                    response = asyncio.run(st.session_state.agent_manager.run_task(user_input))
                    
                    # Tamamlandı göstergesi
                    progress_bar.progress(100)
                    status_text.text("✅ Görev tamamlandı!")
                    
                    # Progress container'ı temizle
                    time.sleep(1)
                    progress_container.empty()
            
            # Agent cevabını ekle
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': response,
                'timestamp': datetime.now().strftime("%H:%M:%S")
            })
            
            # Görev geçmişine ekle
            st.session_state.task_history.append({
                'task': user_input,
                'result': response,
                'timestamp': datetime.now().isoformat(),
                'steps': st.session_state.agent_manager.current_task_steps.copy()
            })
            
            st.rerun()


def display_real_time_agent_status():
    """Gerçek zamanlı agent durumunu göster"""
    st.subheader("🔄 Agent Durumu")
    
    agent_manager = st.session_state.agent_manager
    
    # Agent durumu kartı
    if agent_manager.is_initialized:
        status_color = "🟢"
        status_text = "Hazır"
    else:
        status_color = "🔴" 
        status_text = "Başlatılmamış"
    
    st.markdown(f"""
    <div style='background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 4px solid #28a745;'>
        <strong>{status_color} Durum:</strong> {status_text}<br>
        <strong>🔄 İşlem:</strong> {agent_manager.current_step_status}<br>
    </div>
    """, unsafe_allow_html=True)
    
    # Progress bar
    if agent_manager.current_step_status == "running":
        st.progress(agent_manager.step_progress / 100)
        st.caption(f"İlerleme: %{agent_manager.step_progress}")
    
    # Detaylı adımlar
    if agent_manager.detailed_steps:
        st.subheader("🔍 Detaylı İşlem Adımları")
        st.caption(f"Toplam {len(agent_manager.detailed_steps)} adım")
        
        # Son 10 detaylı adımı göster
        recent_detailed_steps = agent_manager.detailed_steps[-10:]
        
        for step in reversed(recent_detailed_steps):
            step_type = step.get('step_type', 'unknown')
            title = step.get('title', 'Bilinmeyen Adım')
            description = step.get('description', '')
            timestamp = step.get('timestamp', '')
            details = step.get('details', {})
            agent_name = step.get('agent_name', 'agent')
            
            # API step'leri için özel durum
            if step_type == 'api_step':
                status = details.get('status', 'unknown')
                # Status'a göre renk ve icon belirleme
                if status == 'başlatıldı':
                    color = '#007bff'
                    icon = '🚀'
                elif status == 'çalışıyor':
                    color = '#ffc107'
                    icon = '⚡'
                elif status == 'tamamlandı':
                    color = '#28a745'
                    icon = '✅'
                else:
                    color = '#6c757d'
                    icon = '🔄'
                
                # API step'i için özel görüntüleme
                st.markdown(f"""
                <div style="border-left: 4px solid {color}; padding: 8px 12px; margin: 4px 0; 
                     background: rgba{tuple(list(bytes.fromhex(color[1:]))+[0.1])}; border-radius: 4px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong style="color: {color};">{icon} {title}</strong>
                        <small style="color: #666;">{timestamp}</small>
                    </div>
                    <div style="margin-top: 4px; color: #555;">{description}</div>
                    <small style="color: #888;">Durum: {status}</small>
                </div>
                """, unsafe_allow_html=True)
                continue
            
            # Step type'a göre renk belirleme (mevcut kodun devamı)
            type_colors = {
                'task_start': '#007bff',       # Mavi - Görev başlangıcı
                'agent_start': '#17a2b8',      # Cyan - Agent başlangıcı
                'planning': '#6f42c1',         # Mor - Planlama
                'step_start': '#fd7e14',       # Turuncu - Adım başlangıcı
                'action_execution': '#ffc107', # Sarı - Aksiyon
                'model_thinking': '#3d5afe',   # Indigo - Model düşünme
                'model_input': '#5c6bc0',      # Açık indigo - Model girdisi
                'model_output': '#7e57c2',     # Açık mor - Model çıktısı
                'tool_parsing': '#8bc34a',     # Açık yeşil - Tool parsing
                'tool_found': '#4caf50',       # Yeşil - Tool bulundu
                'tool_execution_start': '#26a69a', # Teal - Tool başlangıcı
                'tool_execution': '#6610f2',   # Mor - Tool çalışıyor
                'tool_execution_detail': '#673ab7', # Koyu mor - Tool detayı
                'tool_prepare': '#9c27b0',     # Pembe - Tool hazırlığı
                'tool_result': '#20c997',      # Turkuaz - Tool sonucu
                'tool_success': '#28a745',     # Yeşil - Tool başarılı
                'action_result': '#20c997',    # Turkuaz - Aksiyon sonucu
                'step_complete': '#28a745',    # Yeşil - Adım tamamlandı
                'final_answer': '#198754',     # Koyu yeşil - Final cevap
                'final_answer_processing': '#16A085', # Teal - Final cevap işleme
                'task_end': '#198754',         # Koyu yeşil - Görev sonu
                'agent_error': '#dc3545',      # Kırmızı - Agent hatası
                'step_error': '#fd7e14',       # Turuncu - Adım hatası
                'model_error': '#e74c3c',      # Açık kırmızı - Model hatası
                'parsing_error': '#ff5722',    # Koyu turuncu - Parsing hatası
                'tool_parameter_error': '#ff9800', # Amber - Tool parametre hatası
                'tool_execution_error': '#f44336', # Kırmızı - Tool execution hatası
                'tool_not_found': '#795548',   # Kahverengi - Tool bulunamadı
                'max_steps_reached': '#ff5722', # Koyu turuncu - Zaman aşımı
                'thinking': '#9e9e9e',         # Gri - Düşünme
                'decision': '#00bcd4',         # Cyan - Karar
                'sub_task': '#607d8b',         # Blue grey - Alt görev
                'custom': '#795548'            # Kahverengi - Özel
            }
            
            color = type_colors.get(step_type, '#6c757d')
            
            st.markdown(f"""
            <div style='border-left: 4px solid {color}; padding: 12px; margin: 8px 0; background: #f8f9fa; border-radius: 8px;'>
                <div style='font-weight: bold; margin-bottom: 4px; color: {color};'>
                    {title}
                </div>
                <div style='color: #333; margin-bottom: 8px; font-size: 14px;'>
                    {description}
                </div>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div style='font-size: 12px; color: #666;'>
                        🤖 {agent_name} | ⏰ {timestamp}
                    </div>
                    <div style='font-size: 11px; color: #999; background: #e9ecef; padding: 2px 8px; border-radius: 12px;'>
                        {step_type}
                    </div>
                </div>
                {f'''<div style='font-size: 11px; color: #666; margin-top: 8px; padding: 8px; background: #e7f3ff; border-radius: 4px;'>
                    <strong>Detaylar:</strong> {str(details)[:200]}{"..." if len(str(details)) > 200 else ""}
                </div>''' if details else ''}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("📄 Henüz detaylı adım bilgisi mevcut değil. Agent bir görev çalıştırdığında buradan takip edebilirsiniz.")
        # Debug: Session state kontrol et
        st.write(f"🔍 Debug: detailed_steps listesinin uzunluğu: {len(st.session_state.agent_manager.detailed_steps)}")
        if hasattr(st.session_state.agent_manager, 'detailed_steps'):
            st.write(f"🔍 Debug: detailed_steps mevcut: {st.session_state.agent_manager.detailed_steps[:2] if st.session_state.agent_manager.detailed_steps else 'Boş'}")
    
    # Genel adımlar (kısaltılmış görünüm)
    if agent_manager.current_task_steps:
        st.subheader("📋 Genel Adımlar")
        
        # Adım genişletme toggle
        show_all_steps = st.checkbox("Tüm genel adımları göster", value=st.session_state.agent_steps_expanded)
        st.session_state.agent_steps_expanded = show_all_steps
        
        # Adımları göster
        steps_to_show = agent_manager.current_task_steps if show_all_steps else agent_manager.current_task_steps[-3:]
        
        for step in reversed(steps_to_show):
            status_color = {
                "başlatıldı": "🔵",
                "çalışıyor": "🟡", 
                "tamamlandı": "🟢",
                "hata": "🔴",
                "uyarı": "🟠"
            }.get(step["status"], "⚪")
            
            st.markdown(f"""
            <div style='background-color: #f1f3f4; padding: 10px; border-radius: 8px; margin: 5px 0; border-left: 3px solid #4285f4;'>
                <strong>{status_color} {step['title']}</strong><br>
                <small>{step['description']}</small><br>
                <small style='color: #666;'>🕒 {step['timestamp']}</small>
            </div>
            """, unsafe_allow_html=True)
    
    # Otomatik yenileme
    if agent_manager.current_step_status == "running":
        time.sleep(1)
        st.rerun()


def display_tools_interface():
    """Araçlar arayüzünü göster"""
    st.header("🔧 Araç Yönetimi")
    
    # Araç seçimi
    tool_names = list(st.session_state.tool_manager.tools.keys())
    selected_tool = st.selectbox("Kullanılacak aracı seçin:", tool_names)
    
    if selected_tool:
        st.subheader(f"⚙️ {selected_tool.replace('_', ' ').title()}")
        
        # Deep Researcher Tool
        if selected_tool == "deep_researcher":
            query = st.text_area("Araştırma konusu:", placeholder="AI Agent konusundaki gelişmeler")
            
            if st.button("🔍 Araştırmayı Başlat"):
                if query.strip():
                    with st.spinner("Araştırma yapılıyor..."):
                        result = asyncio.run(st.session_state.tool_manager.run_tool(
                            "deep_researcher", {"query": query}
                        ))
                    st.success("Araştırma tamamlandı!")
                    st.markdown("### 📊 Sonuçlar")
                    st.write(result)
        
        # Deep Analyzer Tool
        elif selected_tool == "deep_analyzer":
            col1, col2 = st.columns(2)
            with col1:
                task = st.text_area("Analiz görevi:", placeholder="Verilen dosyayı analiz et")
            with col2:
                source = st.text_input("Kaynak (URL veya dosya):", placeholder="https://example.com")
            
            uploaded_file = st.file_uploader("Veya dosya yükleyin:", type=['txt', 'pdf', 'docx', 'md'])
            
            if st.button("📈 Analizi Başlat"):
                params = {}
                if task.strip():
                    params["task"] = task
                if source.strip():
                    params["source"] = source
                if uploaded_file:
                    # Dosyayı geçici olarak kaydet ve analiz et
                    temp_path = f"/tmp/{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    params["source"] = temp_path
                
                if params:
                    with st.spinner("Analiz yapılıyor..."):
                        result = asyncio.run(st.session_state.tool_manager.run_tool(
                            "deep_analyzer", params
                        ))
                    st.success("Analiz tamamlandı!")
                    st.markdown("### 📊 Sonuçlar")
                    st.write(result)
        
        # Auto Browser Tool
        elif selected_tool == "auto_browser":
            task = st.text_area("Tarayıcı görevi:", placeholder="Google'da AI konusunu ara ve ilk 3 sonucu özetle")
            
            if st.button("🌐 Tarayıcı Görevini Başlat"):
                if task.strip():
                    with st.spinner("Tarayıcı görevi çalıştırılıyor..."):
                        result = asyncio.run(st.session_state.tool_manager.run_tool(
                            "auto_browser", {"task": task}
                        ))
                    st.success("Tarayıcı görevi tamamlandı!")
                    st.markdown("### 📊 Sonuçlar")
                    st.write(result)
        
        # Python Interpreter Tool
        elif selected_tool == "python_interpreter":
            st.markdown("### 🐍 Python Kodu Çalıştır")
            code = st.text_area(
                "Python kodu:", 
                placeholder="print('Merhaba Dünya!')\nimport pandas as pd\ndf = pd.DataFrame({'A': [1, 2, 3]})\nprint(df)",
                height=200
            )
            
            if st.button("▶️ Kodu Çalıştır"):
                if code.strip():
                    with st.spinner("Kod çalıştırılıyor..."):
                        result = asyncio.run(st.session_state.tool_manager.run_tool(
                            "python_interpreter", {"code": code}
                        ))
                    st.success("Kod çalıştırıldı!")
                    st.markdown("### 📊 Sonuçlar")
                    st.code(result)


def display_dashboard():
    """Dashboard arayüzünü göster"""
    st.header("📊 Sistem Dashboard")
    
    # Sistem durumu kartları
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        agent_status = "Aktif" if st.session_state.agent_manager.is_initialized else "Pasif"
        agent_delta = "✅" if st.session_state.agent_manager.is_initialized else "❌"
        st.metric("Agent Durumu", agent_status, delta=agent_delta)
    
    with col2:
        st.metric("Toplam Görev", len(st.session_state.task_history))
    
    with col3:
        st.metric("Sohbet Mesajları", len(st.session_state.chat_history))
    
    with col4:
        st.metric("Mevcut Araçlar", len(st.session_state.tool_manager.tools))
    
    # Performans metrikleri
    st.subheader("📈 Performans Metrikleri")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Başarılı görevler
        successful_tasks = sum(1 for task in st.session_state.task_history 
                             if not task.get('result', '').startswith('❌'))
        success_rate = (successful_tasks / len(st.session_state.task_history) * 100) if st.session_state.task_history else 0
        st.metric("Başarı Oranı", f"{success_rate:.1f}%")
    
    with col2:
        # Ortalama görev süresi (yaklaşık)
        avg_steps = sum(len(task.get('steps', [])) for task in st.session_state.task_history) / len(st.session_state.task_history) if st.session_state.task_history else 0
        st.metric("Ort. Adım Sayısı", f"{avg_steps:.1f}")
    
    with col3:
        # Son 24 saat içindeki görevler
        recent_tasks = len([task for task in st.session_state.task_history 
                          if datetime.fromisoformat(task['timestamp']).date() == datetime.now().date()])
        st.metric("Bugünkü Görevler", recent_tasks)
    
    # Real-time Agent İzleme
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Detaylı görev geçmişi
        if st.session_state.task_history:
            st.subheader("📝 Son Görevler")
            
            # Sadece son 5 görevi göster
            recent_tasks = list(reversed(st.session_state.task_history[-5:]))
            
            for i, task in enumerate(recent_tasks):
                # Başarı durumunu kontrol et
                is_success = not task.get('result', '').startswith('❌')
                status_icon = "✅" if is_success else "❌"
                status_color = "#28a745" if is_success else "#dc3545"
                
                with st.expander(f"{status_icon} Görev {len(st.session_state.task_history) - i}: {task['task'][:60]}..."):
                    st.markdown(f"**📝 Görev:** {task['task']}")
                    
                    # Sonucu formatted şekilde göster
                    if len(task['result']) > 300:
                        st.markdown("**📊 Sonuç:**")
                        st.markdown(task['result'][:300] + "...")
                        if st.button(f"Tamamını Göster", key=f"show_full_{i}"):
                            st.markdown(task['result'])
                    else:
                        st.markdown("**📊 Sonuç:**")
                        st.markdown(task['result'])
                    
                    # Zaman bilgisi
                    timestamp = datetime.fromisoformat(task['timestamp'])
                    st.caption(f"🕒 {timestamp.strftime('%d/%m/%Y %H:%M:%S')}")
                    
                    # Adım detayları varsa göster
                    if 'steps' in task and task['steps']:
                        st.markdown("**🔄 İşlem Adımları:**")
                        for step in task['steps']:
                            status_icon = {
                                "başlatıldı": "🔵",
                                "çalışıyor": "🟡",
                                "tamamlandı": "🟢", 
                                "hata": "🔴"
                            }.get(step["status"], "⚪")
                            
                            st.markdown(f"""
                            **{status_icon} {step['title']}**  
                            {step['description']}  
                            *{step['timestamp']}*
                            """)

    with col2:
        # Anlık agent durumu
        st.subheader("🔄 Anlık Agent Durumu")
        agent_manager = st.session_state.agent_manager
        
        # Durum kartı
        current_status = agent_manager.current_step_status
        status_colors = {
            "idle": "#6c757d",
            "running": "#ffc107", 
            "completed": "#28a745",
            "error": "#dc3545"
        }
        
        st.markdown(f"""
        <div style='background: {status_colors.get(current_status, "#6c757d")}; color: white; padding: 15px; border-radius: 10px; text-align: center;'>
            <h3>{current_status.title()}</h3>
            <p>İlerleme: %{agent_manager.step_progress}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Aktif adımlar
        if agent_manager.current_task_steps:
            st.subheader("📋 Son Adımlar")
            for step in reversed(agent_manager.current_task_steps[-3:]):
                status_color = {
                    "başlatıldı": "#007bff",
                    "çalışıyor": "#ffc107",
                    "tamamlandı": "#28a745", 
                    "hata": "#dc3545"
                }.get(step["status"], "#6c757d")
                
                st.markdown(f"""
                <div style='border-left: 4px solid {status_color}; padding: 10px; margin: 5px 0; background: #f8f9fa;'>
                    <strong>{step['title']}</strong><br>
                    <small>{step['description']}</small><br>
                    <small style='color: #666;'>{step['timestamp']}</small>
                </div>
                """, unsafe_allow_html=True)
    
    # Sistem performans metrikleri
    st.subheader("📈 Sistem Performansı")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Başarı oranı hesapla
        completed_tasks = sum(1 for task in st.session_state.task_history 
                            if 'steps' in task and any(step['status'] == 'tamamlandı' for step in task['steps']))
        success_rate = (completed_tasks / len(st.session_state.task_history) * 100) if st.session_state.task_history else 0
        st.metric("Başarı Oranı", f"%{success_rate:.1f}")
    
    with col2:
        # Ortalama adım sayısı
        avg_steps = sum(len(task.get('steps', [])) for task in st.session_state.task_history) / len(st.session_state.task_history) if st.session_state.task_history else 0
        st.metric("Ort. Adım Sayısı", f"{avg_steps:.1f}")
    
    with col3:
        # Aktif tool sayısı
        active_tools = len([tool for tool in st.session_state.tool_manager.tools.values() if tool])
        st.metric("Aktif Tool", active_tools)
    
    # Sistem logları
    st.subheader("📋 Sistem Bilgileri")
    info_data = {
        "Kayıtlı Agentlar": list(REGISTED_AGENTS.keys()),
        "Kayıtlı Araçlar": list(REGISTED_TOOLS.keys()),
        "Mevcut Modeller": st.session_state.ui_config.available_models,
        "Konfigürasyonlar": st.session_state.ui_config.available_configs
    }
    
    for key, values in info_data.items():
        with st.expander(f"{key} ({len(values)})"):
            for value in values:
                st.write(f"• {value}")
    
    # Auto-refresh için
    if agent_manager.current_step_status == "running":
        time.sleep(2)
        st.rerun()


def display_settings():
    """Ayarlar arayüzünü göster"""
    st.header("⚙️ Sistem Ayarları")
    
    # Model ayarları
    st.subheader("🤖 Model Ayarları")
    col1, col2 = st.columns(2)
    
    with col1:
        selected_model = st.selectbox(
            "Varsayılan Model:",
            options=st.session_state.ui_config.available_models,
            help="Agentlar için kullanılacak varsayılan model"
        )
    
    with col2:
        use_local_proxy = st.checkbox("Yerel Proxy Kullan", help="Yerel proxy sunucusu kullanılsın mı?")
    
    # Agent ayarları
    st.subheader("🎛️ Agent Ayarları")
    col1, col2 = st.columns(2)
    
    with col1:
        max_steps = st.number_input("Maksimum Adım:", min_value=1, max_value=50, value=20)
    
    with col2:
        concurrency = st.number_input("Eşzamanlılık:", min_value=1, max_value=10, value=4)
    
    # Araç ayarları
    st.subheader("🔧 Araç Ayarları")
    
    # Deep Researcher ayarları
    with st.expander("🔍 Deep Researcher Ayarları"):
        col1, col2 = st.columns(2)
        with col1:
            max_depth = st.number_input("Maksimum Derinlik:", min_value=1, max_value=5, value=2)
            max_insights = st.number_input("Maksimum İçgörü:", min_value=5, max_value=50, value=10)
        with col2:
            time_limit = st.number_input("Zaman Limiti (saniye):", min_value=30, max_value=300, value=120)
            max_follow_ups = st.number_input("Maksimum Takip:", min_value=1, max_value=10, value=3)
    
    # Web Search ayarları
    with st.expander("🌐 Web Arama Ayarları"):
        col1, col2 = st.columns(2)
        with col1:
            search_engine = st.selectbox("Arama Motoru:", ["Google", "DuckDuckGo", "Bing", "Baidu"])
            num_results = st.number_input("Sonuç Sayısı:", min_value=1, max_value=20, value=5)
        with col2:
            language = st.selectbox("Dil:", ["tr", "en", "auto"])
            country = st.selectbox("Ülke:", ["tr", "us", "auto"])
    
    # Ayarları kaydet
    if st.button("💾 Ayarları Kaydet"):
        st.success("Ayarlar kaydedildi! (Bu özellik geliştirilecek)")


def display_documentation():
    """Dokümantasyon arayüzünü göster"""
    st.header("📚 Dokümantasyon")
    
    # Genel Bilgi
    with st.expander("🎯 DeepResearchAgent Nedir?", expanded=True):
        st.markdown("""
        **DeepResearchAgent**, karmaşık araştırma görevlerini otomatik olarak gerçekleştiren 
        hiyerarşik bir çoklu-agent sistemidir. Sistem, üst düzey bir planlama agenti ve 
        özelleşmiş alt agentlardan oluşur.
        
        ### 🏗️ Sistem Mimarisi
        - **Planlama Agent**: Görevleri planlar ve alt agentlara dağıtır
        - **Deep Researcher**: Web araştırması ve bilgi toplama
        - **Deep Analyzer**: Dosya ve veri analizi
        - **Browser Use**: Otomatik web tarayıcı işlemleri
        - **Python Interpreter**: Kod çalıştırma ve veri işleme
        """)
    
    # Agent Türleri
    with st.expander("🤖 Agent Türleri"):
        st.markdown("""
        ### 1. Deep Researcher Agent
        - Kapsamlı web araştırması yapar
        - Çoklu kaynaklardan bilgi toplar
        - Otomatik rapor oluşturur
        
        ### 2. Deep Analyzer Agent  
        - Dosya ve veri analizi
        - PDF, Word, Excel dosyalarını işler
        - Web sitelerini analiz eder
        
        ### 3. Browser Use Agent
        - Otomatik web tarayıcı kontrolü
        - Form doldurma ve veri çekme
        - Screenshot alma ve sayfa analizi
        
        ### 4. Planning Agent
        - Görev planlama ve koordinasyon
        - Alt agentlara görev dağıtımı
        - Sonuçları entegre etme
        """)
    
    # Araçlar
    with st.expander("🔧 Kullanılabilir Araçlar"):
        st.markdown("""
        ### 🔍 Deep Researcher
        ```python
        # Araştırma yapma
        query = "AI Agent gelişmeleri"
        result = await deep_researcher.forward(query=query)
        ```
        
        ### 📊 Deep Analyzer  
        ```python
        # Dosya analizi
        result = await deep_analyzer.forward(
            task="PDF'yi özetle", 
            source="file.pdf"
        )
        ```
        
        ### 🌐 Auto Browser
        ```python
        # Web tarayıcı görevi
        result = await auto_browser.forward(
            task="Google'da AI ara ve ilk 3 sonucu özetle"
        )
        ```
        
        ### 🐍 Python Interpreter
        ```python
        # Python kodu çalıştırma
        code = "import pandas as pd; print(pd.__version__)"
        result = await python_interpreter.forward(code=code)
        ```
        """)
    
    # API Kullanımı
    with st.expander("🔌 API Kullanımı"):
        st.markdown("""
        ### Temel Kullanım
        ```python
        import asyncio
        from src.agent import create_agent
        from src.config import config
        from src.models import model_manager
        
        # Konfigürasyonu başlat
        config.init_config("configs/config_gemini.toml")
        model_manager.init_models()
        
        # Agent oluştur
        agent = await create_agent()
        
        # Görev çalıştır
        result = await agent.run("AI Agent konusunu araştır")
        print(result)
        ```
        
        ### Özel Araç Kullanımı
        ```python
        from src.tools.deep_researcher import DeepResearcherTool
        
        researcher = DeepResearcherTool()
        result = await researcher.forward(query="Machine Learning trends")
        ```
        """)
    
    # Konfigürasyon
    with st.expander("⚙️ Konfigürasyon"):
        st.markdown("""
        ### TOML Konfigürasyon Örneği
        ```toml
        # Genel ayarlar
        tag = "production"
        concurrency = 4
        workdir = "workdir"
        log_path = "log.txt"
        
        # Web arama ayarları
        [web_search_tool]
        engine = "Google"
        num_results = 5
        lang = "tr"
        country = "tr"
        
        # Agent ayarları
        [agent]
        use_hierarchical_agent = true
        
        [agent.deep_researcher_agent_config]
        model_id = "gemini-1.5-pro"
        max_steps = 5
        tools = ["deep_researcher", "python_interpreter"]
        ```
        """)
    
    # Troubleshooting
    with st.expander("🚨 Sorun Giderme"):
        st.markdown("""
        ### Yaygın Sorunlar
        
        **1. Agent başlatılamıyor**
        - API anahtarlarınızı kontrol edin (.env dosyası)
        - Konfigürasyon dosyasının doğru olduğundan emin olun
        - Gerekli bağımlılıkların yüklü olduğunu kontrol edin
        
        **2. Browser agent çalışmıyor**
        ```bash
        pip install "browser-use[memory]"==0.1.48
        pip install playwright
        playwright install chromium --with-deps --no-shell
        ```
        
        **3. Model erişim hatası**
        - .env dosyasında API anahtarlarını kontrol edin
        - Model ID'lerinin doğru olduğundan emin olun
        - İnternet bağlantınızı kontrol edin
        
        **4. Python interpreter hatası**
        - Güvenlik kısıtlamaları aktif
        - Sadece izin verilen kütüphaneler kullanılabilir
        - Dosya sistemi erişimi sınırlı
        """)


def update_api_key(api_key: str) -> bool:
    """API anahtarını config dosyasına kaydet"""
    try:
        import toml
        config_path = assemble_project_path("./configs/config_webui.toml")
        
        # Mevcut config'i oku
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = toml.load(f)
        
        # API anahtarını güncelle
        if 'google' not in config_data:
            config_data['google'] = {}
        config_data['google']['api_key'] = api_key
        
        # Config'i kaydet
        with open(config_path, 'w', encoding='utf-8') as f:
            toml.dump(config_data, f)
        
        return True
    except Exception as e:
        logger.error(f"API anahtarı kaydedilemedi: {e}")
        return False


def main():
    """Ana uygulama fonksiyonu"""
    st.set_page_config(
        page_title="DeepResearchAgent Web UI",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
    }
    .stButton > button {
        border-radius: 20px;
        border: none;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .user-message {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Ana başlık
    st.markdown("""
    <div class="main-header">
        <h1>🧠 DeepResearchAgent Web UI</h1>
        <p>Gelişmiş AI araştırma ve analiz platformu</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Session state'i başlat
    init_session_state()
    
    # Auto-refresh sistemi - Agent çalışırken API'den güncel durumu al
    # Güvenli auto-refresh: 5 saniyede bir ve maksimum 10 kez
    current_time = time.time()
    should_refresh = False
    
    # Agent durumunu kontrol et
    try:
        import requests
        response = requests.get("http://localhost:8000/status", timeout=2)
        if response.status_code == 200:
            status_data = response.json()
            agent_status = status_data.get("agent_status", "idle")
            
            # Step'leri güncelle - önce /agent/steps endpoint'ini deneyelim
            try:
                steps_response = requests.get("http://localhost:8000/agent/steps", timeout=2)
                if steps_response.status_code == 200:
                    steps_data = steps_response.json()
                    if "steps" in steps_data:
                        new_steps = steps_data["steps"]
                        # API format'ından UI format'ına çevir
                        converted_steps = []
                        for step in new_steps:
                            converted_step = {
                                "step_type": "api_step",
                                "title": step.get("title", ""),
                                "description": step.get("description", ""),
                                "timestamp": step.get("timestamp", ""),
                                "details": {
                                    "status": step.get("status", ""),
                                },
                                "agent_name": "api"
                            }
                            converted_steps.append(converted_step)
                        
                        # Sadece step sayısı değiştiyse güncelle
                        if len(converted_steps) != len(st.session_state.agent_manager.detailed_steps):
                            st.session_state.agent_manager.detailed_steps = converted_steps
                            should_refresh = True
                            logger.info(f"UI: {len(converted_steps)} adet step güncellendi")
                            # Debug için step bilgisi göster
                            if converted_steps:
                                logger.info(f"UI Debug: İlk step - {converted_steps[0]['title']}: {converted_steps[0]['description']}")
            except Exception as e:
                logger.debug(f"UI: Steps endpoint hatası: {e}")
            
            # Fallback olarak status'daki current_task_steps'i kullan
            if not should_refresh and "current_task_steps" in status_data:
                new_steps = status_data["current_task_steps"]
                if len(new_steps) != len(st.session_state.agent_manager.detailed_steps):
                    st.session_state.agent_manager.detailed_steps = new_steps
                    should_refresh = True
                    logger.info(f"UI: Fallback ile {len(new_steps)} adet step güncellendi")
            
            # Agent çalışıyorsa ve son refresh'ten 5 saniye geçtiyse
            if (agent_status in ["running", "processing"] and 
                current_time - st.session_state.last_refresh_time > 5):
                
                st.session_state.last_refresh_time = current_time
                should_refresh = True
                
                # Auto-refresh göstergesi
                st.markdown("""
                <div style="position: fixed; top: 10px; right: 10px; background: #10b981; color: white; 
                            padding: 5px 10px; border-radius: 15px; font-size: 12px; z-index: 1000;">
                    🔄 Canlı İzleme Aktif
                </div>
                """, unsafe_allow_html=True)
            
            # Agent durumunu güncelle
            st.session_state.agent_manager.current_step_status = agent_status
            
    except Exception as e:
        # API bağlantı hatası - sessizce devam et
        pass
    
    # Manual refresh butonu
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 Durumu Yenile"):
            should_refresh = True
            st.success("✅ Durum güncellendi!")
    
    # Debug bilgisi
    with col2:
        if st.checkbox("🔍 Debug Modu", help="Session state ve API bilgilerini göster"):
            st.write(f"**Session State Debug:**")
            st.write(f"- detailed_steps sayısı: {len(st.session_state.agent_manager.detailed_steps)}")
            st.write(f"- current_step_status: {st.session_state.agent_manager.current_step_status}")
            st.write(f"- is_initialized: {st.session_state.agent_manager.is_initialized}")
            
            # API status test
            try:
                import requests
                api_response = requests.get("http://localhost:8000/status", timeout=1)
                if api_response.status_code == 200:
                    api_data = api_response.json()
                    st.write(f"**API Debug:**")
                    st.write(f"- Agent status: {api_data.get('agent_status')}")
                    st.write(f"- current_task_steps: {len(api_data.get('current_task_steps', []))}")
            except Exception as e:
                st.write(f"**API Debug:** Bağlantı hatası - {e}")
    
    # Refresh gerekiyorsa yap
    if should_refresh:
        st.rerun()
    
    # Yan panel
    display_sidebar()
    
    # Ana arayüz
    display_main_interface()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; padding: 1rem;'>"
        "DeepResearchAgent Web UI • Türkçe destekli AI araştırma platformu"
        "</div>", 
        unsafe_allow_html=True
    )

    # WebSocket JavaScript'i için HTML components ekle
    websocket_js = """
    <script>
    // WebSocket bağlantısı ve canlı monitoring
    let ws = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    
    function connectWebSocket() {
        try {
            ws = new WebSocket('ws://localhost:8000/ws');
            
            ws.onopen = function(event) {
                console.log('✅ WebSocket bağlantısı kuruldu');
                reconnectAttempts = 0;
                
                // Ping/pong mekanizması
                setInterval(() => {
                    if (ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({type: 'ping'}));
                    }
                }, 30000);
            };
            
            ws.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    console.log('📨 WebSocket mesajı alındı:', data);
                    
                    // Streamlit'e mesajı ileterek state'i güncelle
                    if (data.type === 'step_update' || data.type === 'detailed_step') {
                        // Custom event dispatch ederek Streamlit'i bilgilendir
                        window.dispatchEvent(new CustomEvent('webSocketStep', {
                            detail: data
                        }));
                        
                        // Streamlit sayfasını yeniden render etmek için
                        // Session state güncellemesi simüle et
                        document.body.setAttribute('data-ws-update', Date.now());
                    }
                } catch (error) {
                    console.error('WebSocket mesaj parse hatası:', error);
                }
            };
            
            ws.onclose = function(event) {
                console.log('❌ WebSocket bağlantısı kapandı');
                
                // Otomatik yeniden bağlanma
                if (reconnectAttempts < maxReconnectAttempts) {
                    setTimeout(() => {
                        reconnectAttempts++;
                        console.log(`🔄 WebSocket yeniden bağlanma denemesi ${reconnectAttempts}/${maxReconnectAttempts}`);
                        connectWebSocket();
                    }, 2000 * reconnectAttempts);
                }
            };
            
            ws.onerror = function(error) {
                console.error('❌ WebSocket hatası:', error);
            };
            
        } catch (error) {
            console.error('WebSocket bağlantı hatası:', error);
        }
    }
    
    // Sayfa yüklendiğinde WebSocket'i başlat
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', connectWebSocket);
    } else {
        connectWebSocket();
    }
    
    // Streamlit ile entegrasyon için event listener
    window.addEventListener('webSocketStep', function(event) {
        console.log('🔄 WebSocket step event alındı:', event.detail);
        
        // Sayfayı refresh etmek için Streamlit rerun simüle et
        // Bu, session state değişikliklerini tetikleyecek
        setTimeout(() => {
            window.parent.postMessage({
                type: 'streamlit:componentReady',
                apiVersion: 1,
            }, '*');
        }, 100);
    });
    </script>
    """
    
    # JavaScript'i HTML component olarak ekle
    st.components.v1.html(websocket_js, height=0)


if __name__ == "__main__":
    main()
