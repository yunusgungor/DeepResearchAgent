# DeepResearchAgent Web UI

Bu dizin, DeepResearchAgent projesi için geliştirilmiş modern web kullanıcı arayüzünü içerir.

## 🚀 Hızlı Başlangıç

```bash
# Web UI'yi başlat
cd web_ui
./start.sh
```

## 📋 İçerik

### 1. 🌟 Streamlit UI (`app.py`)
- **Önerilen seçenek** - Kullanımı kolay, hızlı kurulum
- Tüm agent yeteneklerini tek arayüzde kullanma
- Gerçek zamanlı sohbet ve araç yönetimi
- Görsel dashboard ve sistem izleme

**Özellikler:**
- 💬 **Sohbet Arayüzü**: AI agent ile doğal dil iletişimi
- 🔧 **Araç Yönetimi**: Tüm araçları tek yerden kullanma
- 📊 **Dashboard**: Sistem durumu ve görev geçmişi
- ⚙️ **Ayarlar**: Konfigürasyon ve parameter yönetimi
- 📚 **Dokümantasyon**: Kapsamlı kullanım kılavuzu

### 2. 🔧 FastAPI + React (`api.py` + `frontend.jsx`)
- **Gelişmiş seçenek** - API tabanlı mimari
- RESTful API ile backend/frontend ayrımı
- WebSocket desteği ile gerçek zamanlı iletişim
- Modern React bileşenleri

**API Endpoints:**
- `GET /` - Ana sayfa
- `GET /health` - Sistem durumu
- `GET /status` - Agent durumu
- `POST /agent/initialize` - Agent başlatma
- `POST /agent/task` - Görev çalıştırma
- `POST /tools/run` - Araç çalıştırma
- `GET /system/info` - Sistem bilgileri

### 3. 📜 Dosya Yapısı

```
web_ui/
├── app.py              # Streamlit ana uygulaması
├── api.py              # FastAPI backend servisi
├── frontend.jsx        # React frontend komponenti
├── requirements.txt    # Python bağımlılıkları
├── package.json        # Node.js bağımlılıkları
├── start.sh           # Otomatik başlatma scripti
└── README.md          # Bu dosya
```

## 🛠️ Kurulum ve Kullanım

### Gereksinimler
- Python 3.11+
- Node.js 16+ (React UI için)
- DeepResearchAgent ana projesi kurulu

### Manuel Kurulum

#### 1. Python Bağımlılıkları
```bash
cd web_ui
pip install -r requirements.txt
```

#### 2. Streamlit UI Başlatma
```bash
streamlit run app.py --server.port 8501
```

#### 3. FastAPI + React Başlatma
```bash
# Terminal 1 - API Server
python api.py

# Terminal 2 - React UI (opsiyonel)
npm install
npm start
```

### Otomatik Başlatma
```bash
./start.sh
```

## 🎯 Kullanım Senaryoları

### 1. Araştırma Görevleri
```
"AI Agent konusundaki en son gelişmeleri araştır ve özetle"
"Machine Learning trendlerini analiz et"
"Python ile veri analizi konusunda kapsamlı rapor hazırla"
```

### 2. Dosya Analizi
```
PDF dosyasını yükleyip önemli bilgileri çıkar
Web sitesini analiz et ve içerik özetini oluştur
Excel verilerini yorumla ve görselleştir
```

### 3. Web Otomasyonu
```
"Google'da belirtilen konuyu ara ve ilk 5 sonucu özetle"
"LinkedIn'de iş ilanlarını tarayıp uygun pozisyonları listele"
"E-ticaret sitesinden ürün bilgilerini topla"
```

### 4. Kod Geliştirme
```python
# Python kodu çalıştırma
import pandas as pd
data = pd.read_csv('data.csv')
print(data.describe())
```

## 🔧 Konfigürasyon

### Agent Ayarları
- **Model Seçimi**: Gemini, GPT-4, Claude, Qwen modelleri
- **Maksimum Adım**: Agent'ın alabileceği maksimum işlem sayısı
- **Eşzamanlılık**: Paralel çalışabilecek görev sayısı

### Araç Ayarları
- **Deep Researcher**: Araştırma derinliği, zaman limiti
- **Web Search**: Arama motoru, sonuç sayısı, dil ayarları
- **Browser Automation**: Tarayıcı ayarları, güvenlik seçenekleri

## 📊 Dashboard Özellikleri

### Sistem Durumu
- Agent aktiflik durumu
- Toplam çalıştırılan görev sayısı
- Sohbet mesaj sayısı
- Mevcut araç sayısı

### Görev Geçmişi
- Son çalıştırılan görevler
- Başarı/hata durumları
- Çalışma süreleri
- Sonuç özetleri

### Sistem Logları
- Gerçek zamanlı log takibi
- Hata ve uyarı mesajları
- Performance metrikleri

## 🔐 Güvenlik

### Python Interpreter Sandbox
- Güvenli kod çalıştırma ortamı
- Sınırlı kütüphane erişimi
- Dosya sistemi koruması
- Kaynak kullanım limitleri

### API Güvenliği
- CORS koruması
- Request validation
- Error handling
- Rate limiting (gelecek sürümde)

## 🐛 Sorun Giderme

### Port Çakışması
```bash
# Port 8501 kullanımda ise
streamlit run app.py --server.port 8502

# Port 8000 kullanımda ise
uvicorn api:app --port 8001
```

### Agent Başlatma Hatası
1. `.env` dosyasını kontrol edin
2. API anahtarlarının doğru olduğundan emin olun
3. Konfigürasyon dosyasını kontrol edin
4. Internet bağlantısını test edin

### Browser Use Hatası
```bash
pip install "browser-use[memory]"==0.1.48
pip install playwright
playwright install chromium --with-deps --no-shell
```

### Model Erişim Hatası
- API anahtarlarını `.env` dosyasında kontrol edin
- Model ID'lerinin doğru olduğundan emin olun
- API limitlerini kontrol edin

## 🔄 Güncellemeler

### v1.0.0
- ✅ Streamlit tabanlı temel UI
- ✅ FastAPI backend desteği
- ✅ Tüm agent türleri entegrasyonu
- ✅ Araç yönetimi arayüzü
- ✅ Dashboard ve izleme
- ✅ Türkçe dil desteği

### Gelecek Sürümler
- 🔄 React Native mobil uygulama
- 🔄 Desktop Electron uygulaması
- 🔄 Advanced analytics dashboard
- 🔄 Kullanıcı yetkilendirmesi
- 🔄 Çoklu workspace desteği

## 📞 Destek

Sorunlar için lütfen GitHub issues kullanın veya:
- 📧 E-posta: destek@deepresearchagent.com
- 📚 Dokümantasyon: `/docs` endpoint
- 💬 Discord: DeepResearchAgent topluluk kanalı

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.
