#!/usr/bin/env python3
"""
DeepResearchAgent Web UI Ana Başlatıcı
Tüm UI seçeneklerini tek yerden yönetir
"""

import argparse
import subprocess
import sys
import webbrowser
from pathlib import Path
import time
import signal
import os

def check_dependencies():
    """Gerekli bağımlılıkları kontrol et"""
    try:
        import streamlit
        import fastapi
        import uvicorn
    except ImportError as e:
        print(f"❌ Gerekli bağımlılık eksik: {e}")
        print("🔧 Kurulum için çalıştırın: pip install -r requirements.txt")
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
    """Streamlit UI'yi başlat"""
    print(f"🌟 Streamlit UI başlatılıyor...")
    print(f"📱 URL: http://{host}:{port}")
    
    # Web UI için özel config dosyasını ayarla
    os.environ['CONFIG_PATH'] = 'configs/config_webui.toml'
    
    cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.port", str(port),
        "--server.address", host,
        "--browser.gatherUsageStats", "false"
    ]
    
    try:
        process = subprocess.Popen(cmd, cwd=Path(__file__).parent)
        time.sleep(3)  # UI'nin başlaması için bekle
        webbrowser.open(f"http://{host}:{port}")
        process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Streamlit UI durduruldu")
        process.terminate()

def start_api(port=8000, host="0.0.0.0"):
    """FastAPI backend'i başlat"""
    print(f"🔗 FastAPI backend başlatılıyor...")
    print(f"📡 API URL: http://{host}:{port}")
    print(f"📚 Docs: http://{host}:{port}/docs")
    
    cmd = [
        sys.executable, "-m", "uvicorn", "api:app",
        "--host", host,
        "--port", str(port),
        "--reload"
    ]
    
    try:
        process = subprocess.Popen(cmd, cwd=Path(__file__).parent)
        time.sleep(2)  # API'nin başlaması için bekle
        webbrowser.open(f"http://{host}:{port}")
        process.wait()
    except KeyboardInterrupt:
        print("\n🛑 FastAPI backend durduruldu")
        process.terminate()

def start_full_stack(api_port=8000, ui_port=8501):
    """Full-stack uygulamayı başlat (API + Streamlit)"""
    print(f"🚀 Full-stack uygulama başlatılıyor...")
    
    # API'yi arka planda başlat
    api_cmd = [
        sys.executable, "-m", "uvicorn", "api:app",
        "--host", "0.0.0.0",
        "--port", str(api_port)
    ]
    
    # Streamlit'i başlat
    ui_cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.port", str(ui_port),
        "--server.address", "localhost",
        "--browser.gatherUsageStats", "false"
    ]
    
    processes = []
    
    try:
        # API'yi başlat
        print(f"📡 API başlatılıyor (port {api_port})...")
        api_process = subprocess.Popen(api_cmd, cwd=Path(__file__).parent)
        processes.append(api_process)
        time.sleep(3)
        
        # Streamlit'i başlat  
        print(f"📱 UI başlatılıyor (port {ui_port})...")
        ui_process = subprocess.Popen(ui_cmd, cwd=Path(__file__).parent)
        processes.append(ui_process)
        time.sleep(3)
        
        # Tarayıcıları aç
        webbrowser.open(f"http://localhost:{ui_port}")
        webbrowser.open(f"http://localhost:{api_port}")
        
        print(f"\n✅ Uygulama başarıyla başlatıldı!")
        print(f"📱 Streamlit UI: http://localhost:{ui_port}")
        print(f"📡 FastAPI: http://localhost:{api_port}")
        print(f"📚 API Docs: http://localhost:{api_port}/docs")
        print(f"\n⌨️  Durdurmak için Ctrl+C tuşlayın")
        
        # İşlemlerin bitmesini bekle
        for process in processes:
            process.wait()
            
    except KeyboardInterrupt:
        print("\n🛑 Uygulama durduruldu")
        for process in processes:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

def main():
    """Ana fonksiyon"""
    parser = argparse.ArgumentParser(
        description="DeepResearchAgent Web UI Başlatıcı",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Kullanım örnekleri:
  python launcher.py                          # Interaktif mod
  python launcher.py --streamlit              # Sadece Streamlit UI
  python launcher.py --api                    # Sadece FastAPI backend  
  python launcher.py --full-stack             # API + Streamlit
  python launcher.py --streamlit --port 8502  # Özel port ile Streamlit
        """
    )
    
    parser.add_argument(
        "--streamlit", 
        action="store_true", 
        help="Sadece Streamlit UI'yi başlat"
    )
    
    parser.add_argument(
        "--api", 
        action="store_true", 
        help="Sadece FastAPI backend'i başlat"
    )
    
    parser.add_argument(
        "--full-stack", 
        action="store_true", 
        help="Full-stack uygulamayı başlat (API + UI)"
    )
    
    parser.add_argument(
        "--port", 
        type=int, 
        default=None,
        help="Port numarası (varsayılan: 8501 Streamlit, 8000 API için)"
    )
    
    parser.add_argument(
        "--host", 
        default=None,
        help="Host adresi (varsayılan: localhost Streamlit, 0.0.0.0 API için)"
    )
    
    parser.add_argument(
        "--no-browser", 
        action="store_true",
        help="Tarayıcıyı otomatik açma"
    )
    
    args = parser.parse_args()
    
    # Banner
    print("🧠 DeepResearchAgent Web UI Launcher")
    print("=" * 50)
    
    # Bağımlılık kontrolü
    if not check_dependencies():
        return 1
        
    if not check_main_project():
        return 1
    
    # Tarayıcı ayarı
    if args.no_browser:
        def no_op_open(url):
            print(f"🌐 URL: {url}")
        webbrowser.open = no_op_open
    
    # Mod seçimi
    if args.streamlit:
        port = args.port or 8501
        host = args.host or "localhost"
        start_streamlit(port, host)
        
    elif args.api:
        port = args.port or 8000
        host = args.host or "0.0.0.0"
        start_api(port, host)
        
    elif args.full_stack:
        api_port = 8000
        ui_port = args.port or 8501
        start_full_stack(api_port, ui_port)
        
    else:
        # Interaktif mod
        print("\n🚀 Hangi modu başlatmak istiyorsunuz?")
        print("1) 🌟 Streamlit UI (Önerilen)")
        print("2) 🔗 FastAPI Backend")
        print("3) 🚀 Full-Stack (API + UI)")
        print("4) ❌ Çıkış")
        
        while True:
            try:
                choice = input("\nSeçiminizi yapın (1-4): ").strip()
                
                if choice == "1":
                    start_streamlit()
                    break
                elif choice == "2":
                    start_api()
                    break
                elif choice == "3":
                    start_full_stack()
                    break
                elif choice == "4":
                    print("👋 Çıkış yapılıyor...")
                    break
                else:
                    print("❌ Geçersiz seçim! Lütfen 1-4 arası bir sayı girin.")
                    
            except KeyboardInterrupt:
                print("\n👋 Çıkış yapılıyor...")
                break
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
