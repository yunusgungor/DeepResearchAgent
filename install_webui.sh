#!/bin/bash

# DeepResearchAgent Web UI Kurulum Scripti

echo "🧠 DeepResearchAgent Web UI Kuruluyor..."

# Renk kodları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Hata kontrol fonksiyonu
check_error() {
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Hata: $1${NC}"
        exit 1
    fi
}

# Gerekli dizinleri oluştur
echo -e "${BLUE}📁 Dizinler oluşturuluyor...${NC}"
mkdir -p web_ui/exports
mkdir -p web_ui/uploads
mkdir -p web_ui/static
mkdir -p web_ui/templates

# Ana proje bağımlılıklarını yükle
echo -e "${BLUE}📦 Ana proje bağımlılıkları yükleniyor...${NC}"
pip install -r requirements.txt
check_error "Ana proje bağımlılıkları yüklenemedi"

# Web UI bağımlılıklarını yükle
echo -e "${BLUE}📦 Web UI bağımlılıkları yükleniyor...${NC}"
pip install -r requirements_webui.txt
check_error "Web UI bağımlılıkları yüklenemedi"

# Playwright kurulumu (browser_use için)
echo -e "${BLUE}🌐 Playwright kuruluyor...${NC}"
pip install playwright
playwright install chromium --with-deps --no-shell
check_error "Playwright kurulamadı"

# .env dosyasını kontrol et
echo -e "${BLUE}⚙️  Konfigürasyon kontrol ediliyor...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env dosyası bulunamadı.${NC}"
    echo "Lütfen aşağıdaki API anahtarlarını .env dosyasına ekleyin:"
    echo ""
    echo "OPENAI_API_KEY=your_openai_key_here"
    echo "ANTHROPIC_API_KEY=your_anthropic_key_here"
    echo "GOOGLE_API_KEY=your_google_key_here"
    echo ""
    
    read -p "Şimdi .env dosyası oluşturmak ister misiniz? (y/n): " create_env
    if [[ "$create_env" =~ ^[Yy]$ ]]; then
        cat > .env << EOL
# DeepResearchAgent Konfigürasyonu
PYTHONWARNINGS=ignore
ANONYMIZED_TELEMETRY=false

# OpenAI API
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_API_KEY=your_openai_key_here

# Anthropic API  
ANTHROPIC_API_BASE=https://api.anthropic.com
ANTHROPIC_API_KEY=your_anthropic_key_here

# Google API
GOOGLE_API_BASE=https://generativelanguage.googleapis.com
GOOGLE_API_KEY=your_google_key_here

# Hugging Face (opsiyonel)
HUGGINGFACE_API_KEY=your_hf_key_here

# Arama API'leri (opsiyonel)
SERPAPI_API_KEY=your_serpapi_key_here
EOL
        echo -e "${GREEN}✅ .env dosyası oluşturuldu. Lütfen API anahtarlarınızı güncelleyin.${NC}"
    fi
fi

# Test koşusu
echo -e "${BLUE}🧪 Sistem testi yapılıyor...${NC}"
cd web_ui
python -c "
import sys
sys.path.append('..')
try:
    from src.config import config
    from src.models import model_manager
    print('✅ Ana proje modülleri yüklendi')
except ImportError as e:
    print(f'❌ Modül yüklenemedi: {e}')
    sys.exit(1)

try:
    import streamlit
    import fastapi
    import uvicorn
    print('✅ Web UI bağımlılıkları yüklendi')
except ImportError as e:
    print(f'❌ Web UI bağımlılığı eksik: {e}')
    sys.exit(1)
"
check_error "Sistem testi başarısız"

echo -e "${GREEN}🎉 Kurulum başarıyla tamamlandı!${NC}"
echo ""
echo -e "${BLUE}🚀 Web UI'yi başlatmak için:${NC}"
echo "cd web_ui"
echo "./start.sh"
echo ""
echo -e "${BLUE}veya direkt:${NC}"
echo "python web_ui/launcher.py"
echo ""
echo -e "${YELLOW}📝 Önemli:${NC}"
echo "- .env dosyasındaki API anahtarlarını güncelleyin"
echo "- İlk çalıştırmada model indirme işlemi olabilir"
echo "- Browser kullanımı için Chrome/Chromium gerekli"
echo ""
echo -e "${GREEN}✅ Kurulum tamamlandı!${NC}"
