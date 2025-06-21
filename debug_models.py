#!/usr/bin/env python3
"""
Model kayıt durumunu kontrol etmek için debug script
"""

import sys
from pathlib import Path

# Add project root to path
root = str(Path(__file__).resolve().parent)
sys.path.append(root)

from src.config import config
from src.models import model_manager
from src.utils import assemble_project_path

def debug_models():
    print("🔍 Model Debug Scripti")
    print("=" * 50)
    
    # Config yükle
    config_path = assemble_project_path("./configs/config_webui.toml")
    print(f"📁 Config dosyası: {config_path}")
    config.init_config(config_path=config_path)
    
    # Model manager'ı başlat
    try:
        model_manager.init_models(use_local_proxy=config.use_local_proxy)
        print(f"✅ Model manager başlatıldı")
        print(f"🔧 Local proxy kullanımı: {config.use_local_proxy}")
    except Exception as e:
        print(f"❌ Model manager başlatılamadı: {e}")
        return
    
    # Kayıtlı modelleri listele
    print(f"\n📊 Kayıtlı Model Sayısı: {len(model_manager.registed_models)}")
    print("\n🤖 Tüm Kayıtlı Modeller:")
    print("-" * 30)
    
    for i, model_name in enumerate(sorted(model_manager.registed_models.keys()), 1):
        model = model_manager.registed_models[model_name]
        print(f"{i:2d}. {model_name} ({type(model).__name__})")
    
    # LangChain modelleri kontrol et
    print(f"\n🔗 LangChain Modelleri:")
    print("-" * 25)
    langchain_models = [name for name in model_manager.registed_models.keys() if name.startswith('langchain-')]
    
    if langchain_models:
        for model_name in sorted(langchain_models):
            print(f"✅ {model_name}")
    else:
        print("❌ Hiç LangChain modeli bulunamadı!")
    
    # Gemini modelleri kontrol et
    print(f"\n🧠 Gemini Modelleri:")
    print("-" * 20)
    gemini_models = [name for name in model_manager.registed_models.keys() if 'gemini' in name.lower()]
    
    if gemini_models:
        for model_name in sorted(gemini_models):
            print(f"✅ {model_name}")
    else:
        print("❌ Hiç Gemini modeli bulunamadı!")
    
    # Spesifik model kontrolü
    target_model = "langchain-gemini-2.5-flash"
    print(f"\n🎯 Hedef Model Kontrolü: {target_model}")
    print("-" * 35)
    
    if target_model in model_manager.registed_models:
        print(f"✅ {target_model} mevcut!")
        model = model_manager.registed_models[target_model]
        print(f"   Tip: {type(model).__name__}")
    else:
        print(f"❌ {target_model} bulunamadı!")
        
        # Benzer modelleri öner
        similar = [name for name in model_manager.registed_models.keys() if 'gemini' in name]
        if similar:
            print(f"   Benzer modeller: {similar}")

if __name__ == "__main__":
    debug_models()
