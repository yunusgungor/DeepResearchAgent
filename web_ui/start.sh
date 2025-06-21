#!/bin/bash

# DeepResearchAgent Web UI Başlatma Scripti

echo "🧠 DeepResearchAgent Web UI Başlatılıyor..."

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

# Python sanal ortamını kontrol et
echo -e "${BLUE}📋 Python sanal ortamını kontrol ediliyor...${NC}"
if [ ! -d "../.venv" ] && [ ! -d "../venv" ]; then
    echo -e "${YELLOW}⚠️  Sanal ortam bulunamadı. Yeni sanal ortam oluşturuluyor...${NC}"
    cd ..
    python -m venv .venv
    check_error "Sanal ortam oluşturulamadı"
    cd web_ui
fi

# Sanal ortamı aktifleştir
echo -e "${BLUE}🔄 Sanal ortam aktifleştiriliyor...${NC}"
if [ -d "../.venv" ]; then
    source ../.venv/bin/activate
elif [ -d "../venv" ]; then
    source ../venv/bin/activate
fi
check_error "Sanal ortam aktifleştirilemedi"

# Python bağımlılıklarını kontrol et
echo -e "${BLUE}📦 Python bağımlılıkları kontrol ediliyor...${NC}"
pip install -r requirements.txt
check_error "Python bağımlılıkları yüklenemedi"

# Ana proje bağımlılıklarını kontrol et
echo -e "${BLUE}📦 Ana proje bağımlılıkları kontrol ediliyor...${NC}"
cd ..
pip install -r requirements.txt
check_error "Ana proje bağımlılıkları yüklenemedi"
cd web_ui

# Port kontrolü
check_port() {
    local port=$1
    local service=$2
    if lsof -i :$port >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Port $port zaten kullanımda ($service). Devam etmek istiyor musunuz? (y/n)${NC}"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo -e "${RED}❌ İşlem iptal edildi.${NC}"
            exit 1
        fi
    fi
}

# Portları kontrol et
echo -e "${BLUE}🔍 Portlar kontrol ediliyor...${NC}"
check_port 8000 "API Server"
check_port 8501 "Streamlit"

# Konfigürasyon dosyasını kontrol et
echo -e "${BLUE}⚙️  Konfigürasyon kontrol ediliyor...${NC}"
if [ ! -f "../.env" ]; then
    echo -e "${YELLOW}⚠️  .env dosyası bulunamadı. Örnek dosya kopyalanıyor...${NC}"
    if [ -f "../.env.example" ]; then
        cp ../.env.example ../.env
        echo -e "${YELLOW}📝 .env dosyasını düzenlemeyi unutmayın!${NC}"
    else
        echo -e "${RED}❌ .env.example dosyası bulunamadı!${NC}"
        exit 1
    fi
fi

# Başlatma seçenekleri
echo -e "${GREEN}🚀 Web UI başlatma seçenekleri:${NC}"
echo "1) 🌟 Streamlit UI (Önerilen - Basit)"
echo "2) 🔧 FastAPI + React (Gelişmiş)"
echo "3) 🐍 Sadece API Server"
echo "4) 📊 Sadece Streamlit"
echo "5) ❌ İptal"

read -p "Seçiminizi yapın (1-5): " choice

case $choice in
    1)
        echo -e "${GREEN}🌟 Streamlit UI başlatılıyor...${NC}"
        echo -e "${BLUE}📱 UI: http://localhost:8501${NC}"
        streamlit run app.py --server.port 8501 --server.address 0.0.0.0
        ;;
    2)
        echo -e "${GREEN}🔧 FastAPI + React başlatılıyor...${NC}"
        echo -e "${BLUE}🔗 API: http://localhost:8000${NC}"
        echo -e "${BLUE}📱 React UI: http://localhost:3000${NC}"
        
        # Arka planda API'yi başlat
        python api.py &
        API_PID=$!
        
        # Node.js bağımlılıklarını kontrol et
        if [ ! -d "node_modules" ]; then
            echo -e "${BLUE}📦 Node.js bağımlılıkları yükleniyor...${NC}"
            npm install
            check_error "Node.js bağımlılıkları yüklenemedi"
        fi
        
        # React uygulamasını başlat
        npm start
        
        # API'yi durdur
        kill $API_PID 2>/dev/null
        ;;
    3)
        echo -e "${GREEN}🐍 API Server başlatılıyor...${NC}"
        echo -e "${BLUE}🔗 API: http://localhost:8000${NC}"
        echo -e "${BLUE}📚 Docs: http://localhost:8000/docs${NC}"
        python api.py
        ;;
    4)
        echo -e "${GREEN}📊 Streamlit başlatılıyor...${NC}"
        echo -e "${BLUE}📱 UI: http://localhost:8501${NC}"
        streamlit run app.py --server.port 8501
        ;;
    5)
        echo -e "${YELLOW}❌ İşlem iptal edildi.${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}❌ Geçersiz seçim!${NC}"
        exit 1
        ;;
esac
