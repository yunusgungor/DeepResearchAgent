"""
DeepResearchAgent Web UI
Modern web arayüzü ile tüm agent yeteneklerini kullanabilir.
"""

import asyncio
import json
import os
import sys
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


class AgentManager:
    """Agent yönetimi için sınıf"""
    
    def __init__(self):
        self.current_agent = None
        self.is_initialized = False
    
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
            return True
        except Exception as e:
            st.error(f"Agent başlatılırken hata oluştu: {str(e)}")
            return False
    
    async def run_task(self, task: str) -> str:
        """Görevi çalıştır"""
        if not self.is_initialized or not self.current_agent:
            return "Agent henüz başlatılmamış!"
        
        try:
            result = await self.current_agent.run(task)
            return str(result)
        except Exception as e:
            return f"Görev çalıştırılırken hata oluştu: {str(e)}"


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


def display_sidebar():
    """Yan panel menüsünü göster"""
    with st.sidebar:
        st.title("🧠 DeepResearchAgent")
        st.markdown("---")
        
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
    
    # Tool'ları yükle (config yüklendikten sonra)
    if not st.session_state.tool_manager.tools_loaded:
        with st.spinner("Araçlar yükleniyor..."):
            st.session_state.tool_manager.load_tools()
    
    # Sohbet geçmişini göster
    for i, message in enumerate(st.session_state.chat_history):
        with st.container():
            col1, col2 = st.columns([1, 10])
            with col1:
                if message['role'] == 'user':
                    st.write("👤")
                else:
                    st.write("🤖")
            with col2:
                st.write(f"**{message['role'].title()}:** {message['content']}")
                st.caption(f"Zaman: {message['timestamp']}")
        st.divider()
    
    # Yeni mesaj girişi
    with st.container():
        col1, col2 = st.columns([9, 1])
        
        with col1:
            user_input = st.text_area(
                "Mesajınızı yazın:",
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
                st.session_state.chat_input = task
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
            
            # Agent'dan cevap al
            with st.spinner("🤔 Agent düşünüyor..."):
                response = asyncio.run(st.session_state.agent_manager.run_task(user_input))
            
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
                'timestamp': datetime.now().isoformat()
            })
            
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
        st.metric(
            "Agent Durumu",
            "Aktif" if st.session_state.agent_manager.is_initialized else "Pasif",
            delta="✅" if st.session_state.agent_manager.is_initialized else "❌"
        )
    
    with col2:
        st.metric("Toplam Görev", len(st.session_state.task_history))
    
    with col3:
        st.metric("Sohbet Mesajları", len(st.session_state.chat_history))
    
    with col4:
        st.metric("Mevcut Araçlar", len(st.session_state.tool_manager.tools))
    
    # Görev geçmişi
    if st.session_state.task_history:
        st.subheader("📝 Son Görevler")
        for i, task in enumerate(reversed(st.session_state.task_history[-5:])):
            with st.expander(f"Görev {len(st.session_state.task_history) - i}: {task['task'][:50]}..."):
                st.write(f"**Görev:** {task['task']}")
                st.write(f"**Sonuç:** {task['result'][:200]}...")
                st.caption(f"Zaman: {task['timestamp']}")
    
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


if __name__ == "__main__":
    main()
