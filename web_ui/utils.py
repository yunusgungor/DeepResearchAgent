"""
DeepResearchAgent Web UI Yardımcı Fonksiyonları
Ortak kullanılan fonksiyonlar ve sınıflar
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import streamlit as st
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


class UIUtils:
    """UI yardımcı fonksiyonları"""
    
    @staticmethod
    def format_timestamp(timestamp: str) -> str:
        """Timestamp'i Türkçe formatta formatla"""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime("%d/%m/%Y %H:%M:%S")
        except:
            return timestamp
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100) -> str:
        """Metni belirtilen uzunlukta kes"""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """Süreyi insan okunabilir formatta göster"""
        if seconds < 60:
            return f"{seconds:.1f} saniye"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f} dakika"
        else:
            hours = seconds / 3600
            return f"{hours:.1f} saat"
    
    @staticmethod
    def get_status_color(status: str) -> str:
        """Durum rengini getir"""
        status_colors = {
            "success": "#52c41a",
            "completed": "#52c41a", 
            "error": "#ff4d4f",
            "failed": "#ff4d4f",
            "running": "#1890ff",
            "pending": "#faad14",
            "warning": "#faad14"
        }
        return status_colors.get(status.lower(), "#d9d9d9")
    
    @staticmethod
    def format_bytes(bytes_value: int) -> str:
        """Byte değerini insan okunabilir formatta göster"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"


class ChartUtils:
    """Grafik yardımcı fonksiyonları"""
    
    @staticmethod
    def create_task_timeline(task_history: List[Dict]) -> go.Figure:
        """Görev zaman çizelgesi oluştur"""
        if not task_history:
            fig = go.Figure()
            fig.add_annotation(
                text="Henüz görev geçmişi yok",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        df = pd.DataFrame(task_history)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['task_short'] = df['task'].apply(lambda x: UIUtils.truncate_text(x, 30))
        
        fig = px.timeline(
            df, 
            x_start="timestamp", 
            x_end="timestamp",
            y="task_short",
            color="status",
            title="Görev Zaman Çizelgesi"
        )
        
        fig.update_layout(
            height=400,
            showlegend=True,
            xaxis_title="Zaman",
            yaxis_title="Görevler"
        )
        
        return fig
    
    @staticmethod
    def create_status_pie_chart(task_history: List[Dict]) -> go.Figure:
        """Görev durum pasta grafiği"""
        if not task_history:
            return go.Figure()
        
        status_counts = {}
        for task in task_history:
            status = task.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        fig = go.Figure(data=[go.Pie(
            labels=list(status_counts.keys()),
            values=list(status_counts.values()),
            hole=0.3
        )])
        
        fig.update_layout(
            title="Görev Durum Dağılımı",
            height=300
        )
        
        return fig
    
    @staticmethod
    def create_agent_usage_chart(chat_history: List[Dict]) -> go.Figure:
        """Agent kullanım grafiği"""
        if not chat_history:
            return go.Figure()
        
        # Saatlik mesaj sayısını hesapla
        hourly_counts = {}
        for message in chat_history:
            if message['type'] == 'user':
                timestamp = datetime.fromisoformat(message['timestamp'])
                hour = timestamp.strftime("%H:00")
                hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
        
        hours = sorted(hourly_counts.keys())
        counts = [hourly_counts[hour] for hour in hours]
        
        fig = go.Figure(data=[
            go.Bar(x=hours, y=counts, name="Mesaj Sayısı")
        ])
        
        fig.update_layout(
            title="Saatlik Agent Kullanımı",
            xaxis_title="Saat",
            yaxis_title="Mesaj Sayısı",
            height=300
        )
        
        return fig


class FileUtils:
    """Dosya yardımcı fonksiyonları"""
    
    @staticmethod
    def save_chat_history(chat_history: List[Dict], filename: str = None) -> str:
        """Sohbet geçmişini dosyaya kaydet"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chat_history_{timestamp}.json"
        
        filepath = Path("exports") / filename
        filepath.parent.mkdir(exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(chat_history, f, ensure_ascii=False, indent=2)
        
        return str(filepath)
    
    @staticmethod
    def load_chat_history(filepath: str) -> List[Dict]:
        """Sohbet geçmişini dosyadan yükle"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Dosya yüklenirken hata oluştu: {str(e)}")
            return []
    
    @staticmethod
    def export_task_results(task_history: List[Dict], format: str = "json") -> str:
        """Görev sonuçlarını dışa aktar"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format.lower() == "json":
            filename = f"task_results_{timestamp}.json"
            filepath = Path("exports") / filename
            filepath.parent.mkdir(exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(task_history, f, ensure_ascii=False, indent=2)
        
        elif format.lower() == "csv":
            filename = f"task_results_{timestamp}.csv"
            filepath = Path("exports") / filename
            filepath.parent.mkdir(exist_ok=True)
            
            df = pd.DataFrame(task_history)
            df.to_csv(filepath, index=False, encoding='utf-8')
        
        else:
            raise ValueError(f"Desteklenmeyen format: {format}")
        
        return str(filepath)


class ConfigManager:
    """Konfigürasyon yönetimi"""
    
    def __init__(self):
        self.config_dir = Path("configs")
        self.user_config_file = Path("user_config.json")
    
    def load_user_config(self) -> Dict[str, Any]:
        """Kullanıcı ayarlarını yükle"""
        if self.user_config_file.exists():
            try:
                with open(self.user_config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Varsayılan ayarlar
        return {
            "default_model": "gemini-1.5-pro",
            "default_config": "config_gemini",
            "max_steps": 20,
            "concurrency": 4,
            "ui_theme": "light",
            "auto_save": True,
            "show_timestamps": True,
            "language": "tr"
        }
    
    def save_user_config(self, config: Dict[str, Any]) -> bool:
        """Kullanıcı ayarlarını kaydet"""
        try:
            with open(self.user_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            st.error(f"Ayarlar kaydedilemedi: {str(e)}")
            return False
    
    def get_available_configs(self) -> List[str]:
        """Mevcut konfigürasyon dosyalarını listele"""
        if not self.config_dir.exists():
            return []
        
        configs = []
        for file in self.config_dir.glob("*.toml"):
            if file.name != "config_example.toml":
                configs.append(file.stem)
        
        return sorted(configs)


class SessionManager:
    """Session yönetimi"""
    
    @staticmethod
    def init_session_state(key: str, default_value: Any) -> None:
        """Session state değerini başlat"""
        if key not in st.session_state:
            st.session_state[key] = default_value
    
    @staticmethod
    def get_session_value(key: str, default_value: Any = None) -> Any:
        """Session state değerini getir"""
        return st.session_state.get(key, default_value)
    
    @staticmethod
    def set_session_value(key: str, value: Any) -> None:
        """Session state değerini ayarla"""
        st.session_state[key] = value
    
    @staticmethod
    def clear_session() -> None:
        """Session state'i temizle"""
        for key in list(st.session_state.keys()):
            del st.session_state[key]


class NotificationManager:
    """Bildirim yönetimi"""
    
    @staticmethod
    def show_success(message: str, duration: int = 3) -> None:
        """Başarı bildirimi göster"""
        st.success(f"✅ {message}")
        if duration > 0:
            time.sleep(duration)
    
    @staticmethod
    def show_error(message: str, duration: int = 5) -> None:
        """Hata bildirimi göster"""
        st.error(f"❌ {message}")
        if duration > 0:
            time.sleep(duration)
    
    @staticmethod
    def show_warning(message: str, duration: int = 4) -> None:
        """Uyarı bildirimi göster"""
        st.warning(f"⚠️ {message}")
        if duration > 0:
            time.sleep(duration)
    
    @staticmethod
    def show_info(message: str, duration: int = 3) -> None:
        """Bilgi bildirimi göster"""
        st.info(f"ℹ️ {message}")
        if duration > 0:
            time.sleep(duration)


class ValidationUtils:
    """Doğrulama yardımcı fonksiyonları"""
    
    @staticmethod
    def validate_task_input(task: str) -> tuple[bool, str]:
        """Görev girişini doğrula"""
        if not task or not task.strip():
            return False, "Görev boş olamaz"
        
        if len(task.strip()) < 3:
            return False, "Görev en az 3 karakter olmalıdır"
        
        if len(task) > 5000:
            return False, "Görev çok uzun (maksimum 5000 karakter)"
        
        return True, ""
    
    @staticmethod
    def validate_file_upload(file) -> tuple[bool, str]:
        """Dosya yükleme doğrulaması"""
        if file is None:
            return False, "Dosya seçilmedi"
        
        # Dosya boyutu kontrolü (10MB)
        max_size = 10 * 1024 * 1024
        if file.size > max_size:
            return False, f"Dosya çok büyük (maksimum {UIUtils.format_bytes(max_size)})"
        
        # Dosya uzantısı kontrolü
        allowed_extensions = ['.txt', '.pdf', '.docx', '.xlsx', '.md', '.json', '.csv']
        file_extension = Path(file.name).suffix.lower()
        
        if file_extension not in allowed_extensions:
            return False, f"Desteklenmeyen dosya formatı: {file_extension}"
        
        return True, ""
    
    @staticmethod
    def validate_url(url: str) -> tuple[bool, str]:
        """URL doğrulaması"""
        if not url or not url.strip():
            return False, "URL boş olamaz"
        
        url = url.strip()
        
        if not (url.startswith('http://') or url.startswith('https://')):
            return False, "URL http:// veya https:// ile başlamalıdır"
        
        if len(url) > 2000:
            return False, "URL çok uzun"
        
        return True, ""


# Ortak sabitler
EXAMPLE_TASKS = [
    "AI Agent konusundaki en son gelişmeleri araştır ve özetle",
    "Python ile veri analizi yapma konusunda kapsamlı bir rehber hazırla",
    "Machine Learning trendlerini araştır ve 2024 tahminlerini yap",
    "Blockchain teknolojisinin gelecekteki uygulamalarını analiz et",
    "Sürdürülebilir enerji çözümlerini araştır ve karşılaştır",
    "Uzaktan çalışma trendlerini analiz et ve öneriler sun",
    "Yapay zeka etiği konusunda kapsamlı bir rapor hazırla",
    "Siber güvenlik tehditlerini araştır ve korunma yöntemlerini listele"
]

SUPPORTED_FILE_TYPES = {
    'text/plain': '.txt',
    'application/pdf': '.pdf', 
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
    'text/markdown': '.md',
    'application/json': '.json',
    'text/csv': '.csv'
}

UI_COLORS = {
    'primary': '#1890ff',
    'success': '#52c41a',
    'warning': '#faad14',
    'error': '#ff4d4f',
    'text': '#262626',
    'text_secondary': '#8c8c8c',
    'background': '#ffffff',
    'background_secondary': '#fafafa'
}
