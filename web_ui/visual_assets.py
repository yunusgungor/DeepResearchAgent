"""
DeepResearchAgent Web UI İkonları ve Görseller
Streamlit ve API için görsel öğeler
"""

import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import streamlit as st

def create_logo(size=(200, 200), bg_color="#667eea", text_color="white"):
    """DeepResearchAgent logosu oluştur"""
    img = Image.new('RGB', size, bg_color)
    draw = ImageDraw.Draw(img)
    
    # Gradyan efekt için basit renk geçişi
    for i in range(size[1]):
        gradient_color = (
            int(102 + (118 - 102) * i / size[1]),  # R
            int(126 + (186 - 126) * i / size[1]),  # G  
            int(234 + (162 - 234) * i / size[1])   # B
        )
        draw.line([(0, i), (size[0], i)], fill=gradient_color)
    
    # Merkeze brain emoji ve text
    try:
        # Büyük font dene
        font_large = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 60)
        font_small = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 20)
    except:
        # Varsayılan font
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Brain emoji
    brain_emoji = "🧠"
    bbox = draw.textbbox((0, 0), brain_emoji, font=font_large)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size[0] - text_width) // 2
    y = (size[1] - text_height) // 2 - 20
    draw.text((x, y), brain_emoji, font=font_large)
    
    # Alt metin
    text = "DeepResearchAgent"
    bbox = draw.textbbox((0, 0), text, font=font_small)
    text_width = bbox[2] - bbox[0]
    x = (size[0] - text_width) // 2
    y = y + 80
    draw.text((x, y), text, fill=text_color, font=font_small)
    
    return img

def create_favicon(size=(32, 32)):
    """Favicon oluştur"""
    img = Image.new('RGB', size, "#667eea")
    draw = ImageDraw.Draw(img)
    
    # Basit brain emoji
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    brain_emoji = "🧠"
    bbox = draw.textbbox((0, 0), brain_emoji, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size[0] - text_width) // 2
    y = (size[1] - text_height) // 2
    draw.text((x, y), brain_emoji, font=font)
    
    return img

def get_logo_base64():
    """Logo'yu base64 formatında getir"""
    logo = create_logo()
    buffer = BytesIO()
    logo.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

def get_favicon_base64():
    """Favicon'u base64 formatında getir"""
    favicon = create_favicon()
    buffer = BytesIO()
    favicon.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

def add_logo_to_sidebar():
    """Streamlit sidebar'a logo ekle"""
    logo_base64 = get_logo_base64()
    st.sidebar.markdown(
        f"""
        <div style="text-align: center; padding: 20px;">
            <img src="{logo_base64}" width="150" style="border-radius: 10px;">
        </div>
        """,
        unsafe_allow_html=True
    )

def add_custom_css():
    """Özel CSS stilleri ekle"""
    favicon_base64 = get_favicon_base64()
    
    st.markdown(
        f"""
        <style>
        /* Favicon */
        .main .block-container {{
            max-width: 1200px;
            padding-top: 2rem;
        }}
        
        /* Header styling */
        .main-header {{
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        /* Button styling */
        .stButton > button {{
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 20px;
            padding: 0.5rem 1rem;
            font-weight: bold;
            transition: all 0.3s ease;
        }}
        
        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }}
        
        /* Sidebar styling */
        .css-1d391kg {{
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        }}
        
        /* Chat message styling */
        .chat-message {{
            padding: 1rem;
            border-radius: 10px;
            margin: 0.5rem 0;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        
        .user-message {{
            background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
            border-left: 4px solid #2196f3;
        }}
        
        .assistant-message {{
            background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
            border-left: 4px solid #9c27b0;
        }}
        
        /* Card styling */
        .metric-card {{
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 1rem;
            border-radius: 10px;
            border-left: 4px solid #667eea;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        
        /* Status indicators */
        .status-active {{
            color: #28a745;
            font-weight: bold;
        }}
        
        .status-inactive {{
            color: #dc3545;
            font-weight: bold;
        }}
        
        /* Animations */
        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
            100% {{ opacity: 1; }}
        }}
        
        .loading {{
            animation: pulse 2s infinite;
        }}
        
        /* Custom scrollbar */
        .main::-webkit-scrollbar {{
            width: 8px;
        }}
        
        .main::-webkit-scrollbar-track {{
            background: #f1f1f1;
            border-radius: 10px;
        }}
        
        .main::-webkit-scrollbar-thumb {{
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
        }}
        
        .main::-webkit-scrollbar-thumb:hover {{
            background: linear-gradient(180deg, #5a6fd8 0%, #6a4190 100%);
        }}
        
        /* Typography */
        .big-font {{
            font-size: 24px !important;
            font-weight: bold;
            color: #667eea;
        }}
        
        .medium-font {{
            font-size: 18px !important;
            color: #495057;
        }}
        
        .small-font {{
            font-size: 14px !important;
            color: #6c757d;
        }}
        
        /* Success/Error alerts */
        .alert-success {{
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            border: 1px solid #28a745;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }}
        
        .alert-error {{
            background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
            border: 1px solid #dc3545;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }}
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 8px;
            padding: 8px 16px;
            border: 1px solid #dee2e6;
        }}
        
        .stTabs [aria-selected="true"] {{
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        
        /* Footer */
        .footer {{
            text-align: center;
            padding: 2rem;
            color: #6c757d;
            border-top: 1px solid #dee2e6;
            margin-top: 3rem;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

def show_loading_animation(text="Yükleniyor..."):
    """Yükleme animasyonu göster"""
    return st.markdown(
        f"""
        <div style="text-align: center; padding: 2rem;">
            <div class="loading">
                <h3>🔄 {text}</h3>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def show_success_message(message):
    """Başarı mesajı göster"""
    return st.markdown(
        f"""
        <div class="alert-success">
            <strong>✅ Başarılı!</strong> {message}
        </div>
        """,
        unsafe_allow_html=True
    )

def show_error_message(message):
    """Hata mesajı göster"""
    return st.markdown(
        f"""
        <div class="alert-error">
            <strong>❌ Hata!</strong> {message}
        </div>
        """,
        unsafe_allow_html=True
    )

# Logo dosyalarını oluştur ve kaydet
if __name__ == "__main__":
    print("🎨 DeepResearchAgent logoları oluşturuluyor...")
    
    # Logo oluştur ve kaydet
    logo = create_logo()
    logo.save("static/logo.png")
    print("✅ Logo kaydedildi: static/logo.png")
    
    # Favicon oluştur ve kaydet
    favicon = create_favicon()
    favicon.save("static/favicon.png")
    print("✅ Favicon kaydedildi: static/favicon.png")
    
    # Büyük logo
    big_logo = create_logo((400, 400))
    big_logo.save("static/logo_big.png")
    print("✅ Büyük logo kaydedildi: static/logo_big.png")
    
    print("🎉 Tüm görseller oluşturuldu!")
