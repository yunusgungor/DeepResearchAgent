# 🧠 DeepResearchAgent Web UI

Bu proje için eksiksiz bir kullanıcı arayüzü geliştirilmiştir. Projenin tüm kabiliyetlerini modern ve kullanıcı dostu bir web arayüzü ile kullanabilirsiniz.

## 🌟 Özellikler

### 💬 Akıllı Sohbet Arayüzü
- **Doğal Dil İletişimi**: AI agent ile Türkçe sohbet
- **Gerçek Zamanlı Yanıtlar**: WebSocket destekli hızlı iletişim  
- **Sohbet Geçmişi**: Tüm konuşmaları kaydetme ve görüntüleme
- **Örnek Görevler**: Hızlı başlangıç için hazır görev şablonları

### 🔧 Kapsamlı Araç Yönetimi
- **Deep Researcher**: Web araştırması ve rapor hazırlama
- **Deep Analyzer**: Dosya analizi ve veri işleme
- **Browser Automation**: Otomatik web tarayıcı işlemleri
- **Python Interpreter**: Güvenli kod çalıştırma ortamı

### 📊 Gelişmiş Dashboard
- **Sistem Durumu**: Agent ve araç durumlarını izleme
- **Görev Geçmişi**: Çalıştırılan görevlerin detaylı kayıtları
- **Performance Metrikleri**: Kullanım istatistikleri ve grafikler
- **Sistem Logları**: Gerçek zamanlı log takibi

### ⚙️ Esnek Konfigürasyon
- **Model Seçimi**: GPT-4, Claude, Gemini, Qwen modelleri
- **Agent Ayarları**: Maksimum adım, eşzamanlılık, timeout
- **Araç Parametreleri**: Her araç için özelleştirilebilir ayarlar
- **Güvenlik Ayarları**: Sandbox ve erişim kontrolü

## 🚀 Hızlı Başlangıç

### 1. Kurulum
```bash
# Web UI'yi kur
./install_webui.sh

# Veya manuel kurulum
pip install -r requirements_webui.txt
```

### 2. Konfigürasyon
```bash
# .env dosyasını düzenleyin (API anahtarları)
nano .env
```

### 3. Başlatma
```bash
# Otomatik başlatıcı (önerilen)
cd web_ui
python launcher.py

# Veya manuel
./start.sh
```

## 🎯 Kullanım Senaryoları

### 📚 Araştırma ve Analiz
```
"AI Agent konusundaki 2024 gelişmelerini araştır ve detaylı rapor hazırla"
"Yapay zeka etiği konusunda kapsamlı bir analiz yap"
"Blockchain teknolojisinin sağlık sektöründeki uygulamalarını araştır"
```

### 📄 Dosya İşleme
- PDF, Word, Excel dosyalarını yükleyip analiz etme
- Web sitelerini otomatik analiz etme
- Veri görselleştirme ve rapor oluşturma

### 🌐 Web Otomasyonu
```
"Google'da 'machine learning trends' ara ve ilk 10 sonucu özetle"
"LinkedIn'de AI Engineer pozisyonlarını tara ve analiz et"
"E-ticaret sitesinden ürün bilgilerini topla ve karşılaştır"
```

### 💻 Kod Geliştirme
```python
# Güvenli Python ortamında kod çalıştırma
import pandas as pd
import matplotlib.pyplot as plt

# Veri analizi yapma
data = pd.read_csv('data.csv')
analysis = data.describe()
print(analysis)
```

## 🔧 Teknik Detaylar

### 🏗️ Mimari
- **Frontend**: Streamlit (Ana UI) + React (Gelişmiş UI)
- **Backend**: FastAPI + WebSocket desteği
- **Agent System**: Hiyerarşik multi-agent mimari
- **Security**: Sandbox Python interpreter, input validation

### 📱 UI Seçenekleri

#### 1. Streamlit UI (Önerilen)
- **Port**: 8501
- **Avantajlar**: Hızlı kurulum, kullanımı kolay
- **Ideal için**: Günlük kullanım, araştırma görevleri

#### 2. FastAPI + React  
- **Port**: 8000 (API) + 3000 (React)
- **Avantajlar**: Modern UI, API erişimi
- **Ideal için**: Geliştiriciler, özelleştirme

#### 3. API Only
- **Port**: 8000
- **Avantajlar**: RESTful API, entegrasyon
- **Ideal için**: Programatik kullanım

### 🔌 API Endpoints

```bash
# Agent yönetimi
POST /agent/initialize    # Agent başlatma
POST /agent/task         # Görev çalıştırma
GET  /agent/status       # Durum kontrolü
DELETE /agent/reset      # Agent sıfırlama

# Araç yönetimi  
POST /tools/run          # Araç çalıştırma

# Sistem
GET /system/info         # Sistem bilgisi
GET /health             # Sağlık kontrolü
GET /logs               # Log görüntüleme

# Dosya işlemleri
POST /upload            # Dosya yükleme
```

## 🛡️ Güvenlik

### Python Interpreter Sandbox
- ✅ Güvenli kod çalıştırma ortamı
- ✅ Sınırlı kütüphane erişimi (`pandas`, `numpy`, `requests`)
- ✅ Dosya sistemi koruması
- ✅ Kaynak kullanım limitleri
- ✅ Zararlı kod tespiti

### API Güvenliği
- ✅ CORS koruması
- ✅ Input validation
- ✅ Error handling
- ✅ Request size limits

## 📈 Performance

### Optimizasyonlar
- **Async/Await**: Eşzamansız işlem desteği
- **WebSocket**: Gerçek zamanlı iletişim
- **Caching**: Model ve config önbellekleme
- **Streaming**: Büyük yanıtlar için stream desteği

### Kaynak Yönetimi
- **Memory**: Automatic cleanup, session management
- **CPU**: Multi-threading, background tasks
- **Network**: Connection pooling, retry logic

## 🎨 Özelleştirme

### UI Temaları
```python
# config.py içinde
UI_THEME = {
    'primary_color': '#1890ff',
    'background_color': '#ffffff', 
    'text_color': '#262626',
    'sidebar_background': '#f0f2f6'
}
```

### Custom Agents
```python
# Yeni agent ekleme
@register_agent("custom_agent")
class CustomAgent(AsyncMultiStepAgent):
    def __init__(self, config, tools, model, **kwargs):
        super().__init__(tools=tools, model=model, **kwargs)
```

### Custom Tools
```python
# Yeni araç ekleme
@register_tool("custom_tool")
class CustomTool(AsyncTool):
    async def forward(self, **kwargs):
        # Araç işlevi
        return result
```

## 🐛 Sorun Giderme

### Yaygın Sorunlar

#### 1. Agent Başlatma Hatası
```bash
# Çözüm
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
export GOOGLE_API_KEY="your-key"
```

#### 2. Port Çakışması
```bash
# Farklı port kullanma
streamlit run app.py --server.port 8502
python launcher.py --port 8502
```

#### 3. Browser Agent Hatası
```bash
# Playwright yeniden kurulum
pip uninstall playwright
pip install playwright
playwright install chromium --with-deps --no-shell
```

#### 4. Module Import Hatası
```bash
# Python path kontrolü
export PYTHONPATH="${PYTHONPATH}:/path/to/DeepResearchAgent"
```

### Log Analizi
```bash
# Detaylı log için
export PYTHONPATH=DEBUG
streamlit run app.py

# Log dosyası kontrolü
tail -f log.txt
```

## 📞 Destek

### Dokümantasyon
- 📚 **API Docs**: `http://localhost:8000/docs`
- 📖 **Kullanım Kılavuzu**: UI içinde `/docs` sekmesi
- 🔧 **Örnekler**: `examples/` dizini

### Topluluk
- 💬 **GitHub Issues**: Hata raporları ve özellik istekleri
- 📧 **E-posta**: deepresearchagent@support.com
- 🌐 **Website**: https://deepresearchagent.com

## 🔄 Güncellemeler

### v1.0.0 (Mevcut)
- ✅ Streamlit tabanlı kapsamlı UI
- ✅ FastAPI backend desteği
- ✅ Tüm agent türleri entegrasyonu
- ✅ Araç yönetimi sistemi
- ✅ Dashboard ve monitoring
- ✅ Türkçe dil desteği
- ✅ Güvenli Python interpreter
- ✅ WebSocket gerçek zamanlı iletişim

### Planlanan Özellikler
- 🔄 Mobil responsive tasarım
- 🔄 Kullanıcı yetkilendirme sistemi
- 🔄 Çoklu workspace desteği
- 🔄 Advanced analytics dashboard
- 🔄 Export/import functionality
- 🔄 Plugin architecture
- 🔄 Voice interface
- 🔄 Collaborative features

## 📝 Lisans

Bu Web UI, ana DeepResearchAgent projesi ile aynı lisans (MIT) altında lisanslanmıştır.

---

**🧠 DeepResearchAgent Web UI - Gelişmiş AI araştırma ve analiz platformunun modern web arayüzü**
