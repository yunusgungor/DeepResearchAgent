#!/usr/bin/env python3
"""
DeepResearchAgent Web UI Launcher
Geliştirilmiş gerçek zamanlı izleme özellikleri ile
"""

import argparse
import subprocess
import sys
import webbrowser
from pathlib import Path
import time
import signal
import os
import threading

def check_dependencies():
    """Gerekli bağımlılıkları kontrol et"""
    try:
        import streamlit
        import fastapi
        import uvicorn
    except ImportError as e:
        print(f"❌ Gerekli bağımlılık eksik: {e}")
        print("🔧 Kurulum için çalıştırın: pip install -r requirements_webui.txt")
        return False
    return True

def check_main_project():
    """Ana proje bağımlılıklarını kontrol et"""
    parent_dir = Path(__file__).parent.parent
    sys.path.append(str(parent_dir))
    
    try:
        from src.config import config
        from src.models import model_manager
        from src.agent import create_agent
        return True
    except ImportError as e:
        print(f"❌ Ana proje modülleri yüklenemedi: {e}")
        print("🔧 Ana proje dizininde requirements.txt'i yükleyin")
        return False

def start_streamlit(port=8501, host="localhost"):
    """Streamlit UI'yi başlat - Gerçek zamanlı izleme ile"""
    print(f"🌟 Streamlit UI başlatılıyor...")
    print(f"📱 URL: http://{host}:{port}")
    print(f"🔄 Gerçek zamanlı agent izleme aktif!")
    
    # Web UI için özel config dosyasını ayarla
    os.environ['CONFIG_PATH'] = 'configs/config_webui.toml'
    
    cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.port", str(port),
        "--server.address", host,
        "--server.headless", "true",
        "--server.runOnSave", "true",
        "--theme.primaryColor", "#667eea",
        "--theme.backgroundColor", "#ffffff",
        "--theme.secondaryBackgroundColor", "#f0f2f6"
    ]
    
    try:
        process = subprocess.Popen(cmd, cwd=Path(__file__).parent)
        time.sleep(3)  # UI'nin başlaması için bekle
        webbrowser.open(f"http://{host}:{port}")
        process.wait()
    except KeyboardInterrupt:
        print("\\n🛑 Streamlit UI durduruldu")
        process.terminate()

def start_api(port=8000, host="0.0.0.0"):
    """FastAPI backend'i başlat - WebSocket desteği ile"""
    print(f"🔗 FastAPI backend başlatılıyor...")
    print(f"📡 API URL: http://{host}:{port}")
    print(f"📚 Docs: http://{host}:{port}/docs")
    print(f"🔌 WebSocket: ws://{host}:{port}/ws")
    
    cmd = [
        sys.executable, "-m", "uvicorn", "api:app",
        "--host", host,
        "--port", str(port),
        "--reload",
        "--log-level", "info"
    ]
    
    try:
        process = subprocess.Popen(cmd, cwd=Path(__file__).parent)
        time.sleep(2)  # API'nin başlaması için bekle
        webbrowser.open(f"http://{host}:{port}")
        process.wait()
    except KeyboardInterrupt:
        print("\\n🛑 FastAPI backend durduruldu")
        process.terminate()

def start_both(streamlit_port=8501, api_port=8000, host="localhost"):
    """Hem Streamlit hem FastAPI'yi başlat"""
    print("🚀 Her iki arayüz de başlatılıyor...")
    print(f"📱 Streamlit: http://{host}:{streamlit_port}")
    print(f"📡 FastAPI: http://{host}:{api_port}")
    print(f"🔄 Gerçek zamanlı izleme aktif!")
    
    # API'yi arka planda başlat
    api_cmd = [
        sys.executable, "-m", "uvicorn", "api:app",
        "--host", "0.0.0.0",
        "--port", str(api_port),
        "--reload"
    ]
    
    # Streamlit'i ön planda başlat
    streamlit_cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.port", str(streamlit_port),
        "--server.address", host,
        "--server.headless", "true"
    ]
    
    try:
        # API process'ini başlat
        api_process = subprocess.Popen(api_cmd, cwd=Path(__file__).parent)
        time.sleep(2)
        
        # Streamlit process'ini başlat
        streamlit_process = subprocess.Popen(streamlit_cmd, cwd=Path(__file__).parent)
        time.sleep(3)
        
        # Tarayıcıları aç
        webbrowser.open(f"http://{host}:{streamlit_port}")
        time.sleep(1)
        webbrowser.open(f"http://{host}:{api_port}")
        
        # Her iki process'i de bekle
        streamlit_process.wait()
        
    except KeyboardInterrupt:
        print("\\n🛑 Tüm servisler durduruldu")
        api_process.terminate()
        streamlit_process.terminate()

def start_realtime_demo():
    """Gerçek zamanlı demo sayfasını başlat"""
    print("🔄 Gerçek zamanlı demo sayfası açılıyor...")
    
    # Demo HTML dosyasının yolunu al
    demo_path = Path(__file__).parent / "real_time_demo.html"
    
    if demo_path.exists():
        # Demo sayfasını tarayıcıda aç
        webbrowser.open(f"file://{demo_path.absolute()}")
        print(f"📱 Demo sayfa açıldı: {demo_path}")
        print("🔌 API'nin http://localhost:8000 adresinde çalıştığından emin olun")
    else:
        print("❌ Demo HTML dosyası bulunamadı!")

def show_monitoring_info():
    """İzleme özelliklerini göster"""
    print("""
🔄 GERÇEK ZAMANLI İZLEME ÖZELLİKLERİ

📊 Yeni Özellikler:
  • Gerçek zamanlı agent adım takibi
  • WebSocket tabanlı canlı güncelleme
  • Progress bar ile ilerleme göstergesi  
  • Detaylı adım logları
  • Otomatik sayfa yenileme
  • Renk kodlu durum göstergeleri

🎯 Sohbet Arayüzü:
  • Agent çalışırken anlık adım görme
  • Tool seçimi ve kullanımı izleme
  • Hata durumlarında detaylı bilgi
  • Görev geçmişinde adım detayları

🔌 API Özellikleri:
  • WebSocket endpoint: /ws
  • Gerçek zamanlı adım broadcast
  • Task durumu endpoint: /agent/steps
  • Çoklu client desteği

💡 Kullanım İpuçları:
  • Sohbet sırasında sağ paneli izleyin
  • Dashboard'da detaylı istatistikleri görün
  • Demo sayfasında pure JavaScript örneği test edin
    """)

def main():
    parser = argparse.ArgumentParser(
        description="DeepResearchAgent Web UI Launcher - Gerçek Zamanlı İzleme ile"
    )
    parser.add_argument(
        "mode", 
        choices=["streamlit", "api", "both", "demo", "info"],
        help="Başlatma modu: streamlit, api, both, demo (gerçek zamanlı demo), info"
    )
    parser.add_argument("--streamlit-port", type=int, default=8501, help="Streamlit port")
    parser.add_argument("--api-port", type=int, default=8000, help="FastAPI port")
    parser.add_argument("--host", default="localhost", help="Host adresi")
    
    args = parser.parse_args()
    
    # Header
    print("="*60)
    print("🧠 DeepResearchAgent Web UI Launcher")
    print("🔄 Gerçek Zamanlı Agent İzleme Sistemi")
    print("="*60)
    
    # Özel komutlar
    if args.mode == "info":
        show_monitoring_info()
        return
    
    if args.mode == "demo":
        start_realtime_demo()
        return
    
    # Bağımlılık kontrolü
    if not check_dependencies():
        sys.exit(1)
    
    if not check_main_project():
        sys.exit(1)
    
    print("✅ Tüm bağımlılıklar mevcut")
    
    # Mode'a göre başlat
    if args.mode == "streamlit":
        start_streamlit(args.streamlit_port, args.host)
    elif args.mode == "api":
        start_api(args.api_port, args.host)
    elif args.mode == "both":
        start_both(args.streamlit_port, args.api_port, args.host)

if __name__ == "__main__":
    main()
