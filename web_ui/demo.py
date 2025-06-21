#!/usr/bin/env python3
"""
DeepResearchAgent Web UI Demo
Hızlı test ve demo için
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
root = str(Path(__file__).resolve().parents[1])
sys.path.append(root)

def test_imports():
    """Gerekli modüllerin yüklendiğini test et"""
    print("🧪 Modül importları test ediliyor...")
    
    try:
        # Ana proje modülleri
        from src.config import config
        from src.models import model_manager
        from src.agent import create_agent
        from src.registry import REGISTED_AGENTS, REGISTED_TOOLS
        print("✅ Ana proje modülleri yüklendi")
        
        # Web UI modülleri
        import streamlit
        import fastapi
        import uvicorn
        print("✅ Web UI modülleri yüklendi")
        
        # Araç modülleri
        from src.tools.deep_researcher import DeepResearcherTool
        from src.tools.deep_analyzer import DeepAnalyzerTool
        from src.tools.auto_browser import AutoBrowserUseTool
        from src.tools.python_interpreter import PythonInterpreterTool
        print("✅ Araç modülleri yüklendi")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import hatası: {e}")
        return False

def test_agent_creation():
    """Agent oluşturma testi"""
    print("\n🤖 Agent oluşturma test ediliyor...")
    
    try:
        from src.utils import assemble_project_path
        config_path = assemble_project_path("./configs/config_gemini.toml")
        
        # Konfigürasyon dosyasının varlığını kontrol et
        if not Path(config_path).exists():
            print(f"⚠️  Konfigürasyon dosyası bulunamadı: {config_path}")
            return False
        
        print("✅ Konfigürasyon dosyası bulundu")
        return True
        
    except Exception as e:
        print(f"❌ Agent oluşturma hatası: {e}")
        return False

def test_tools():
    """Araç oluşturma testi"""
    print("\n🔧 Araçlar test ediliyor...")
    
    try:
        from src.tools.deep_researcher import DeepResearcherTool
        from src.tools.deep_analyzer import DeepAnalyzerTool
        from src.tools.python_interpreter import PythonInterpreterTool
        
        # Tool örnekleri oluştur
        researcher = DeepResearcherTool()
        analyzer = DeepAnalyzerTool()
        interpreter = PythonInterpreterTool()
        
        print(f"✅ Deep Researcher: {researcher.name}")
        print(f"✅ Deep Analyzer: {analyzer.name}")
        print(f"✅ Python Interpreter: {interpreter.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Araç testi hatası: {e}")
        return False

def show_system_info():
    """Sistem bilgilerini göster"""
    print("\n📊 Sistem Bilgileri:")
    print("=" * 40)
    
    try:
        from src.registry import REGISTED_AGENTS, REGISTED_TOOLS
        
        print(f"🤖 Kayıtlı Agentlar ({len(REGISTED_AGENTS)}):")
        for agent_id in REGISTED_AGENTS:
            print(f"   • {agent_id}")
        
        print(f"\n🔧 Kayıtlı Araçlar ({len(REGISTED_TOOLS)}):")
        for tool_id in REGISTED_TOOLS:
            print(f"   • {tool_id}")
        
        # Konfigürasyon dosyalarını listele
        config_dir = Path(root) / "configs"
        configs = []
        if config_dir.exists():
            configs = [f.stem for f in config_dir.glob("*.toml")]
        
        print(f"\n⚙️  Mevcut Konfigürasyonlar ({len(configs)}):")
        for config in configs:
            print(f"   • {config}")
        
        # Web UI dosyalarını kontrol et
        webui_dir = Path(root) / "web_ui"
        webui_files = ['app.py', 'api.py', 'launcher.py', 'start.sh']
        
        print(f"\n🌐 Web UI Dosyaları:")
        for file in webui_files:
            file_path = webui_dir / file
            status = "✅" if file_path.exists() else "❌"
            print(f"   {status} {file}")
        
    except Exception as e:
        print(f"❌ Sistem bilgisi hatası: {e}")

def main():
    """Ana demo fonksiyonu"""
    print("🧠 DeepResearchAgent Web UI Demo")
    print("=" * 50)
    
    # Test sırası
    tests = [
        ("Modül İmportları", test_imports),
        ("Agent Oluşturma", test_agent_creation),
        ("Araç Testi", test_tools)
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}...")
        if not test_func():
            all_passed = False
    
    # Sistem bilgilerini göster
    show_system_info()
    
    # Sonuç
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 Tüm testler başarılı!")
        print("\n🚀 Web UI'yi başlatmak için:")
        print("   cd web_ui")
        print("   python launcher.py")
        print("\n📱 Tarayıcınızda: http://localhost:8501")
    else:
        print("❌ Bazı testler başarısız!")
        print("\n🔧 Sorun giderme:")
        print("   ./install_webui.sh")
        print("   pip install -r requirements.txt")
        print("   pip install -r requirements_webui.txt")
    
    print("\n📚 Detaylı bilgi için: WEB_UI_README.md")

if __name__ == "__main__":
    main()
