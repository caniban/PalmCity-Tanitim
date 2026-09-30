import os
import glob
import re
import pandas as pd
import plotly.express as px
from PIL import Image
import streamlit as st

# ==========================================
# 1. SAYFA YAPILANDIRMASI VE ÖZEL CSS
# ==========================================
st.set_page_config(
    page_title="PalmCity SVI & Semantik Segmentasyon Sunumu",
    page_icon="🌴",
    layout="wide"
)

# Sunum Kartları ve Modern Temalama İçin Özel CSS
st.markdown(
    """
    <style>
    .main {
        background-color: #F8F9FA;
    }
    .header-card {
        background: linear-gradient(135deg, #38BDF8 0%, #0EA5E9 100%);
        padding: 24px;
        border-radius: 12px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-card {
        background-color: #FFFFFF;
        border-left: 5px solid #2A5298;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: center;
    }
    .metric-value {
        font-size: 26px;
        font-weight: bold;
        color: #1E3C72;
    }
    .metric-label {
        font-size: 13px;
        color: #6C757D;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .info-box {
        background-color: #EEF2F7;
        border-left: 4px solid #1E3C72;
        padding: 12px 16px;
        border-radius: 4px;
        margin-bottom: 15px;
        font-size: 14px;
    }
    .class-badge {
        display: inline-block;
        padding: 4px 10px;
        margin: 3px;
        border-radius: 4px;
        color: white;
        font-weight: 600;
        font-size: 12px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #E9ECEF;
        border-radius: 6px 6px 0px 0px;
        padding: 10px 20px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #38BDF8 !important;
        color: white !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# ==========================================
# 2. YARDIMCI GÖRSEL YÜKLEME FONKSİYONU
# ==========================================
def get_image_path(base_name):
  """Görsel adının sonunda ' (1)' takısı olsa da olmasa da doğru dosyayı arar ve döndürür."""
  name_no_ext, ext = os.path.splitext(base_name)
  if not ext:
    ext = ".png"

  candidates = [
      os.path.join("images", f"{name_no_ext} (1){ext}"),
      os.path.join("images", f"{name_no_ext}{ext}"),
      f"{name_no_ext} (1){ext}",
      f"{name_no_ext}{ext}",
      os.path.join("images", base_name),
      base_name,
  ]

  for path in candidates:
    if os.path.exists(path):
      return path
  return None


def show_image(base_name, caption=None, use_container_width=True):
  """Görseli yükler, yoksa hata vermeden uyarı kartı gösterir."""
  img_path = get_image_path(base_name)
  if img_path:
    image = Image.open(img_path)
    st.image(image, caption=caption, use_container_width=use_container_width)
  else:
    st.warning(
        f"⚠️ Görsel bulunamadı: `{base_name}` (Beklenen Yol: `images/{base_name}`"
        ' veya ` (1)` takılı versiyonu)'
    )


# ==========================================
# 3. VERİ VERİTABANI & TABLOLAR
# ==========================================

# 1. Cityscapes Sınıfları
df_cityscapes = pd.DataFrame([
    {
        "Kategori": "Düz yüzey (flat)",
        "Sınıflar": "yol, kaldırım, park alanı, ray hattı",
        "Açıklama": (
            "Taşıt ve yaya hareketinin gerçekleştiği yatay yüzeyleri ifade"
            " eder."
        ),
    },
    {
        "Kategori": "İnşa edilmiş yapılar (construction)",
        "Sınıflar": "bina, duvar, çit, korkuluk, köprü, tünel",
        "Açıklama": "Kentsel çevredeki yapısal elemanları kapsar.",
    },
    {
        "Kategori": "Nesneler (object)",
        "Sınıflar": "direk, direk grubu, trafik ışığı, trafik levhası",
        "Açıklama": (
            "Yol çevresinde konumlanan, yönlendirme ve aydınlatma sağlayan kent"
            " mobilyaları."
        ),
    },
    {
        "Kategori": "Doğa (nature)",
        "Sınıflar": "bitki örtüsü, arazi",
        "Açıklama": "Ağaç, çalı, çim ve doğal yüzeyleri kapsar.",
    },
    {
        "Kategori": "Gökyüzü (sky)",
        "Sınıflar": "gökyüzü",
        "Açıklama": "Açık gökyüzü bölgesini temsil eder.",
    },
    {
        "Kategori": "İnsan (human)",
        "Sınıflar": "kişi, sürücü/binici",
        "Açıklama": "Yayalar ile araç üzerindeki bireyleri ayırır.",
    },
    {
        "Kategori": "Taşıt (vehicle)",
        "Sınıflar": (
            "otomobil, kamyon, otobüs, tren, motosiklet, bisiklet, karavan,"
            " römork"
        ),
        "Açıklama": "Karayolu ve raylı sistem taşıtlarını kapsar.",
    },
    {
        "Kategori": "Boş/geçersiz alan (void)",
        "Sınıflar": (
            "zemin, dinamik, statik, ego araç, etiketsiz, ilgi alanı dışı,"
            " düzeltme sınırı"
        ),
        "Açıklama": (
            "Değerlendirme dışı bırakılan veya belirsiz kalan bölgeleri ifade"
            " eder."
        ),
    },
])

# 2. ADE20K Karşılaştırması
df_ade20k = pd.DataFrame([
    {
        "Özellik": "Sınıf Sayısı",
        "SceneParse150": "150",
        "ADE20K Tam Sürüm": "3.169",
    },
    {
        "Özellik": "Eğitim Seti",
        "SceneParse150": "20.210 Görüntü",
        "ADE20K Tam Sürüm": "~25.000+ Görüntü",
    },
    {
        "Özellik": "Doğrulama / Test",
        "SceneParse150": "2.000 / 3.000 Görüntü",
        "ADE20K Tam Sürüm": "2.000 / 3.000 Görüntü",
    },
    {
        "Özellik": "Etiket Yapısı",
        "SceneParse150": "Standart Etiketleme",
        "ADE20K Tam Sürüm": "Nesne-Parça Hiyerarşisi",
    },
    {
        "Özellik": "Odak Noktası",
        "SceneParse150": "Standart Performans Ölçümü",
        "ADE20K Tam Sürüm": "Geniş Spektrumlu Sahne Analizi",
    },
])

# 3. Arazi Çalışmaları Dağılımı Tablosu
df_arazi = pd.DataFrame([
    {
        "No": 1,
        "Tarih": "12.11.2024",
        "Mahalle / İlçe": "Çiftlikköy / Yenişehir",
        "Arazi Kullanımı & Mimari Tipoloji": (
            "Plansız Yerleşim ve Planlı Apartman"
        ),
        "Görüntü Sayısı": 163,
    },
    {
        "No": 2,
        "Tarih": "25.11.2024",
        "Mahalle / İlçe": "Çiftlikköy / Yenişehir",
        "Arazi Kullanımı & Mimari Tipoloji": (
            "Planlı Apartman ve Planlı Rezidans"
        ),
        "Görüntü Sayısı": 148,
    },
    {
        "No": 3,
        "Tarih": "26.11.2024",
        "Mahalle / İlçe": "Viranşehir / Mezitli",
        "Arazi Kullanımı & Mimari Tipoloji": "Planlı Apartman ve Sahil",
        "Görüntü Sayısı": 224,
    },
    {
        "No": 4,
        "Tarih": "28.11.2024",
        "Mahalle / İlçe": "Çiftlikköy / Yenişehir",
        "Arazi Kullanımı & Mimari Tipoloji": (
            "Planlı Apartman ve Planlı Rezidans"
        ),
        "Görüntü Sayısı": 247,
    },
    {
        "No": 5,
        "Tarih": "29.11.2024",
        "Mahalle / İlçe": "İnönü-Gazi-Palmiye / Yenişehir",
        "Arazi Kullanımı & Mimari Tipoloji": "Çarşı ve Planlı Apartman",
        "Görüntü Sayısı": 365,
    },
    {
        "No": 6,
        "Tarih": "05.12.2024",
        "Mahalle / İlçe": "Mersin Ana Arterler",
        "Arazi Kullanımı & Mimari Tipoloji": "Tüm Tipolojiler (Motosiklet)",
        "Görüntü Sayısı": 607,
    },
    {
        "No": 7,
        "Tarih": "12.01.2025",
        "Mahalle / İlçe": "Hürriyet / Yenişehir",
        "Arazi Kullanımı & Mimari Tipoloji": (
            "Planlı Apartman ve Plansız Yerleşim"
        ),
        "Görüntü Sayısı": 391,
    },
    {
        "No": 8,
        "Tarih": "08.03.2025",
        "Mahalle / İlçe": "Çankaya / Akdeniz",
        "Arazi Kullanımı & Mimari Tipoloji": "Çarşı ve Plansız Yerleşim",
        "Görüntü Sayısı": 655,
    },
    {
        "No": 9,
        "Tarih": "27.04.2025",
        "Mahalle / İlçe": "Sağlık / Toroslar",
        "Arazi Kullanımı & Mimari Tipoloji": "Plansız Yerleşim",
        "Görüntü Sayısı": 714,
    },
    {
        "No": 10,
        "Tarih": "30.07.2025",
        "Mahalle / İlçe": "Çukurova / Toroslar",
        "Arazi Kullanımı & Mimari Tipoloji": "Plansız Yerleşim",
        "Görüntü Sayısı": 746,
    },
    {
        "No": 11,
        "Tarih": "24.08.2025",
        "Mahalle / İlçe": "Akdeniz / Mezitli",
        "Arazi Kullanımı & Mimari Tipoloji": (
            "Planlı Apartman ve Planlı Rezidans"
        ),
        "Görüntü Sayısı": 393,
    },
    {
        "No": 12,
        "Tarih": "02.09.2025",
        "Mahalle / İlçe": "Güvenevler / Yenişehir",
        "Arazi Kullanımı & Mimari Tipoloji": "Çarşı ve Planlı Apartman",
        "Görüntü Sayısı": 310,
    },
    {
        "No": 13,
        "Tarih": "28.09.2025",
        "Mahalle / İlçe": "Menderes / Mezitli",
        "Arazi Kullanımı & Mimari Tipoloji": "Planlı Apartman ve Sahil",
        "Görüntü Sayısı": 271,
    },
])

# 4. PalmCity 32 Semantik Sınıf Listesi
df_classes = pd.DataFrame([
    {
        "ID": 1,
        "İngilizce Ad": "Road",
        "Türkçe Ad": "Yol",
        "Kategori": "Düz Yüzey",
        "RGB Renk koda": "rgb(128, 64, 128)",
        "HEX": "#804080",
    },
    {
        "ID": 2,
        "İngilizce Ad": "Sidewalk",
        "Türkçe Ad": "Kaldırım",
        "Kategori": "Düz Yüzey",
        "RGB Renk koda": "rgb(244, 35, 232)",
        "HEX": "#F423E8",
    },
    {
        "ID": 3,
        "İngilizce Ad": "Parking Lot",
        "Türkçe Ad": "Otopark Alanı",
        "Kategori": "Düz Yüzey",
        "RGB Renk koda": "rgb(250, 170, 160)",
        "HEX": "#FAAAA0",
    },
    {
        "ID": 4,
        "İngilizce Ad": "Parking Barrier",
        "Türkçe Ad": "Otopark Bariyeri",
        "Kategori": "Kent Mobilyası",
        "RGB Renk koda": "rgb(255, 129, 0)",
        "HEX": "#FF8100",
    },
    {
        "ID": 5,
        "İngilizce Ad": "Soil",
        "Türkçe Ad": "Toprak / Zemin",
        "Kategori": "Doğa",
        "RGB Renk koda": "rgb(192, 182, 154)",
        "HEX": "#C0B69A",
    },
    {
        "ID": 6,
        "İngilizce Ad": "Pedestrian",
        "Türkçe Ad": "Yaya",
        "Kategori": "İnsan",
        "RGB Renk koda": "rgb(220, 20, 60)",
        "HEX": "#DC143C",
    },
    {
        "ID": 7,
        "İngilizce Ad": "Driver",
        "Türkçe Ad": "Sürücü / Binici",
        "Kategori": "İnsan",
        "RGB Renk koda": "rgb(255, 0, 0)",
        "HEX": "#FF0000",
    },
    {
        "ID": 8,
        "İngilizce Ad": "Car",
        "Türkçe Ad": "Otomobil",
        "Kategori": "Taşıt",
        "RGB Renk koda": "rgb(0, 0, 142)",
        "HEX": "#00008E",
    },
    {
        "ID": 9,
        "İngilizce Ad": "Truck",
        "Türkçe Ad": "Kamyon",
        "Kategori": "Taşıt",
        "RGB Renk koda": "rgb(0, 0, 70)",
        "HEX": "#000046",
    },
    {
        "ID": 10,
        "İngilizce Ad": "Bus",
        "Türkçe Ad": "Otobüs",
        "Kategori": "Taşıt",
        "RGB Renk koda": "rgb(0, 60, 100)",
        "HEX": "#003C64",
    },
    {
        "ID": 11,
        "İngilizce Ad": "Motorbike",
        "Türkçe Ad": "Motosiklet",
        "Kategori": "Taşıt",
        "RGB Renk koda": "rgb(0, 0, 230)",
        "HEX": "#0000E6",
    },
    {
        "ID": 12,
        "İngilizce Ad": "Bicycle",
        "Türkçe Ad": "Bisiklet",
        "Kategori": "Taşıt",
        "RGB Renk koda": "rgb(119, 11, 32)",
        "HEX": "#770B20",
    },
    {
        "ID": 13,
        "İngilizce Ad": "Traffic Light",
        "Türkçe Ad": "Trafik Işığı",
        "Kategori": "Nesne",
        "RGB Renk koda": "rgb(250, 170, 30)",
        "HEX": "#FAAA1E",
    },
    {
        "ID": 14,
        "İngilizce Ad": "Traffic Sign",
        "Türkçe Ad": "Trafik Levhası",
        "Kategori": "Nesne",
        "RGB Renk koda": "rgb(220, 220, 0)",
        "HEX": "#DCDC00",
    },
    {
        "ID": 15,
        "İngilizce Ad": "Pole",
        "Türkçe Ad": "Direk",
        "Kategori": "Nesne",
        "RGB Renk koda": "rgb(153, 153, 153)",
        "HEX": "#999999",
    },
    {
        "ID": 16,
        "İngilizce Ad": "Garbage Box",
        "Türkçe Ad": "Çöp Kutusu / Konteyner",
        "Kategori": "Kent Mobilyası",
        "RGB Renk koda": "rgb(137, 145, 169)",
        "HEX": "#8991A9",
    },
    {
        "ID": 17,
        "İngilizce Ad": "Sitting Bench",
        "Türkçe Ad": "Oturma Bankı",
        "Kategori": "Kent Mobilyası",
        "RGB Renk koda": "rgb(145, 161, 153)",
        "HEX": "#91A199",
    },
    {
        "ID": 18,
        "İngilizce Ad": "Infrastructure Cover",
        "Türkçe Ad": "Altyapı Kapağı (Rögar)",
        "Kategori": "Altyapı",
        "RGB Renk koda": "rgb(74, 68, 42)",
        "HEX": "#4A442A",
    },
    {
        "ID": 19,
        "İngilizce Ad": "Infrastructure Box",
        "Türkçe Ad": "Altyapı Kutusu / Pano",
        "Kategori": "Altyapı",
        "RGB Renk koda": "rgb(54, 95, 145)",
        "HEX": "#365F91",
    },
    {
        "ID": 20,
        "İngilizce Ad": "Building",
        "Türkçe Ad": "Bina",
        "Kategori": "İnşa Edilmiş",
        "RGB Renk koda": "rgb(70, 70, 70)",
        "HEX": "#464646",
    },
    {
        "ID": 21,
        "İngilizce Ad": "Wall",
        "Türkçe Ad": "Duvar",
        "Kategori": "İnşa Edilmiş",
        "RGB Renk koda": "rgb(102, 102, 156)",
        "HEX": "#66669C",
    },
    {
        "ID": 22,
        "İngilizce Ad": "Fence",
        "Türkçe Ad": "Çit",
        "Kategori": "İnşa Edilmiş",
        "RGB Renk koda": "rgb(190, 153, 153)",
        "HEX": "#BE9999",
    },
    {
        "ID": 23,
        "İngilizce Ad": "Guardrail",
        "Türkçe Ad": "Korkuluk / Otobariyer",
        "Kategori": "İnşa Edilmiş",
        "RGB Renk koda": "rgb(180, 165, 180)",
        "HEX": "#B4A5B4",
    },
    {
        "ID": 24,
        "İngilizce Ad": "Bridge / Tunnel",
        "Türkçe Ad": "Köprü / Tünel",
        "Kategori": "İnşa Edilmiş",
        "RGB Renk koda": "rgb(150, 100, 100)",
        "HEX": "#966464",
    },
    {
        "ID": 25,
        "İngilizce Ad": "Vegetation",
        "Türkçe Ad": "Bitki Örtüsü / Ağaç",
        "Kategori": "Doğa",
        "RGB Renk koda": "rgb(107, 142, 35)",
        "HEX": "#6B8E23",
    },
    {
        "ID": 26,
        "İngilizce Ad": "Terrain",
        "Türkçe Ad": "Arazi / Çim",
        "Kategori": "Doğa",
        "RGB Renk koda": "rgb(152, 251, 152)",
        "HEX": "#98FB98",
    },
    {
        "ID": 27,
        "İngilizce Ad": "Sky",
        "Türkçe Ad": "Gökyüzü",
        "Kategori": "Gökyüzü",
        "RGB Renk koda": "rgb(70, 130, 180)",
        "HEX": "#4682B4",
    },
    {
        "ID": 28,
        "İngilizce Ad": "Water",
        "Türkçe Ad": "Deniz / Su Yüzeyi",
        "Kategori": "Doğa",
        "RGB Renk koda": "rgb(0, 100, 200)",
        "HEX": "#0064C8",
    },
    {
        "ID": 29,
        "İngilizce Ad": "Operator Shadow",
        "Türkçe Ad": "Operatör Gölgesi",
        "Kategori": "Ego / Özel",
        "RGB Renk koda": "rgb(60, 60, 60)",
        "HEX": "#3C3C3C",
    },
    {
        "ID": 30,
        "İngilizce Ad": "Operator Body",
        "Türkçe Ad": "Operatör Vücudu",
        "Kategori": "Ego / Özel",
        "RGB Renk koda": "rgb(40, 40, 40)",
        "HEX": "#282828",
    },
    {
        "ID": 31,
        "İngilizce Ad": "Stairs",
        "Türkçe Ad": "Merdiven",
        "Kategori": "İnşa Edilmiş",
        "RGB Renk koda": "rgb(200, 200, 150)",
        "HEX": "#C8C896",
    },
    {
        "ID": 32,
        "İngilizce Ad": "Void / Unlabeled",
        "Türkçe Ad": "Boş / Etiketsiz",
        "Kategori": "Void",
        "RGB Renk koda": "rgb(0, 0, 0)",
        "HEX": "#000000",
    },
])


# ==========================================
# 4. BAŞLIK VE ÜST BİLGİ PANELİ
# ==========================================
col_logo, col_title = st.columns([1, 5])

with col_logo:
  logo_path = get_image_path("palmcity_logo.png")
  if logo_path:
    st.image(logo_path, use_container_width=True)
  else:
    st.markdown("### 🌴 PalmCity")

with col_title:
  st.markdown(
      """
        <div class="header-card">
            <h1 style='margin:0; font-size: 30px;'>PalmCity Projesi: Yerel ve Panoramik Sokak Görünümü Veri Seti</h1>
            <p style='margin-top:8px; opacity:0.9; font-size: 15px;'>Mersin Kent Merkezinde Elde Edilen 360° Panoramik SVI Görüntüleri, Kent Morfolojileri ve Semantik Analiz</p>
        </div>
    """,
      unsafe_allow_html=True,
  )

# KPI Metrik Kartları
m1, m2, m3, m4, m5 = st.columns(5)
with m1:
  st.markdown(
      """<div class="metric-card"><div class="metric-value">5.232</div><div class="metric-label">Toplam Panoramik SVI Görüntüsü</div></div>""",
      unsafe_allow_html=True,
  )
with m2:
  st.markdown(
      """<div class="metric-card"><div class="metric-value">830</div><div class="metric-label">Etiketli Panoramik SVI</div></div>""",
      unsafe_allow_html=True,
  )
with m3:
  st.markdown(
      """<div class="metric-card"><div class="metric-value">32</div><div class="metric-label">Semantik Sınıf</div></div>""",
      unsafe_allow_html=True,
  )
with m4:
  st.markdown(
      """<div class="metric-card"><div class="metric-value">5</div><div class="metric-label">Kentsel Tipoloji</div></div>""",
      unsafe_allow_html=True,
  )
with m5:
  st.markdown(
      """<div class="metric-card"><div class="metric-value">4</div><div class="metric-label">Merkez İlçe (Mersin)</div></div>""",
      unsafe_allow_html=True,
  )

st.write("")

# ==========================================
# 5. ANA SUNUM TAB'LERİ
# ==========================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📚 1. Literatürdeki Mevcut Veri Setleri",
    "🗺️ 2. Arazi Çalışmaları & Veri Toplama",
    "🏙️ 3. Kentsel & Mimari Tipolojiler",
    "🏷️ 4. PalmCity Semantik Etiketleme",
    "📊 5. İstatistik & Analiz",
])


# ------------------------------------------
# TAB 1: LİTERATÜR VERİ SETLERİ (Hızlandırılmış ve Güncellenmiş)
# ------------------------------------------
with tab1:
  st.subheader("📚 Literatürde Öne Çıkan Sokak Görünümü Veri Setleri")

  # Metin, tablo ve seçim elemanlarını tam siyah ve yüksek kontrastlı yapan CSS
  st.markdown(
      """
        <style>
        /* Tüm metinleri net siyah ve okunaklı yap */
        .stMarkdown, p, span, label, li, h1, h2, h3, h4, h5, h6 {
            color: #000000 !important;
            font-weight: 500;
        }
        /* Tablo yazılarını tam siyah yap */
        [data-testid="stDataFrame"] *, div[data-testid="stTable"] * {
            color: #000000 !important;
            font-weight: 600 !important;
        }
        /* Seçim butonlarını (pills) modern ve hızlı hale getir */
        div[role="radiogroup"] {
            flex-direction: row;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 15px;
        }
        div[role="radiogroup"] > label {
            background-color: #E2E8F0 !important;
            border: 1px solid #CBD5E1 !important;
            padding: 8px 16px !important;
            border-radius: 8px !important;
            cursor: pointer !important;
            font-weight: 600 !important;
        }
        div[role="radiogroup"] > label:hover {
            background-color: #CBD5E1 !important;
        }
        div[role="radiogroup"] label[data-baseweb="radio"] > div:first-child {
            display: none; /* Yuvarlak radio ikonunu gizle, buton görünümü ver */
        }
        </style>
    """,
      unsafe_allow_html=True,
  )

  # Tek tıkla anında yüklenen yatay buton dizilimi
  ds_option = st.radio(
      "Veri Seti Seçin:",
      [
          "Cityscapes",
          "ADE20K",
          "MS COCO & COCO-Stuff",
          "PASCAL VOC",
          "BDD100K",
          "Mapillary Vistas",
          "PASS, DensePASS & SynPASS",
      ],
      horizontal=True,
      label_visibility="collapsed",
  )

  st.markdown("---")

  if ds_option == "Cityscapes":
    c1, c2 = st.columns([1, 1])
    with c1:
      st.markdown("### 🏙️ Cityscapes Veri Seti")
      st.write(
          "TU Darmstadt, Max Planck Enformatik Enstitüsü ve Daimler"
          " tarafından otonom sürüş algısını geliştirmek amacıyla Almanya ve"
          " çevresindeki 50 kentten toplanmıştır. 5.000 yüksek"
          " hassasiyetli, 20.000 kaba etiketli perspektif görüntü içerir."
          " Standardize değerlendirmede 19 semantik sınıf kullanılır."
      )
      st.info(
          "💡 **Sınırlılık:** Sabit perspektif kameralar kullanıldığından 360°"
          " panoramik görüntülerdeki radyal distorsiyonları ve yan/arka çevre"
          " bağlamını temsil edemez."
      )
    with c2:
      show_image(
          "cityscapes_demo.png",
          caption=(
              "Şekil 1: Cityscapes Veri Seti Örnek Etiketli Görüntüleri"
              " (Cordts vd., 2016)"
          ),
      )

  elif ds_option == "ADE20K":
    c1, c2 = st.columns([1, 1])
    with c1:
      st.markdown("### 🏛️ ADE20K Veri Seti")
      st.write(
          "MIT CSAIL tarafından geliştirilen ADE20K, iç ve dış mekanları bir"
          " arada sunan en kapsamlı veri kaynaklarından biridir. Tam"
          " sürümünde 3.169 sınıf bulunurken, standart kıyaslamada"
          " SceneParse150 (150 sınıf) kullanılır."
      )
      st.markdown("""
            * **SceneParse150:** 150 Sınıf | 20.210 Eğitim | 2.000 Doğrulama Görüntüsü
            * **ADE20K Tam Sürüm:** 3.169 Sınıf | ~25.000+ Görüntü | Nesne-Parça Hiyerarşisi
            """)
      st.info(
          "💡 **Sınırlılık:** Yüksek sınıf karmaşıklığı nedeniyle aşırı veri"
          " dengesizliği (class imbalance) barındırır ve doğrudan kent içi sokak"
          " perspektifine odaklanmamıştır."
      )
    with c2:
      show_image(
          "ade20k_demo.png",
          caption=(
              "Şekil 2: ADE20K Veri Seti Örnek Segmentasyon Haritaları (Zhou"
              " vd., 2017)"
          ),
      )

  elif ds_option == "MS COCO & COCO-Stuff":
    c1, c2 = st.columns([1, 1])
    with c1:
      st.markdown("### 🖼️ MS COCO & COCO-Stuff")
      st.write(
          "Microsoft COCO, nesnelerin doğal çevreleri ve bağlamlarıyla"
          " birlikte değerlendirilmesini amaçlar. 80 nesne sınıfına ek olarak"
          " COCO-Stuff ile 91 arka plan sınıfı eklenerek toplam 171 sınıfa"
          " ulaştırılmıştır."
      )
      st.info(
          "💡 **Sınırlılık:** Genel odaklı nesne sahnelerinden oluştuğu için"
          " otonom sürüş ve kent mekânı geometrisine özgü dinamikleri doğrudan"
          " modellemekte yetersiz kalır."
      )
    with c2:
      show_image(
          "mscoco_demo.png",
          caption=(
              "Şekil 3: MS COCO Veri Setinden Örnek Bağlamsal Etiketler"
              " (Fleet vd., 2014)"
          ),
      )

  elif ds_option == "PASCAL VOC":
    c1, c2 = st.columns([1, 1])
    with c1:
      st.markdown("### 🏷️ PASCAL VOC")
      st.write(
          "Erken dönem derin öğrenme (FCN, DeepLab) mimarilerinin gelişiminde"
          " test alanı oluşturan tarihsel veri setidir. 20 nesne sınıfı içerir."
      )
      st.info(
          "💡 **Sınırlılık:** Kısıtlı sınıf sayısı (20 sınıf), düşük görüntü"
          " çözünürlüğü ve kentsel alan karmaşıklığını tam yansıtamaması"
          " nedeniyle güncel uygulamalarda yetersiz kalmaktadır."
      )
    with c2:
      show_image(
          "pascalvoc_demo.png",
          caption=(
              "Şekil 4: PASCAL VOC Segmentasyon ve Void Etiket Örnekleri"
              " (Everingham vd., 2010)"
          ),
      )

  elif ds_option == "BDD100K":
    c1, c2 = st.columns([1, 1])
    with c1:
      st.markdown("### 🚗 BDD100K Veri Seti")
      st.write(
          "Berkeley Deep Drive tarafından geliştirilen 100.000 sürüş videosu"
          " içeren devasa veri kaynağıdır. Gece, sis, yağmur ve kar gibi"
          " olumsuz çevre koşullarında model dayanıklılığını ölçmek için"
          " kullanılır."
      )
      st.info(
          "💡 **Sınırlılık:** Standart araç ön camı (perspektif) açılarıyla"
          " sınırlı olduğundan 360° kesintisiz çevresel görüş ve mekânsal alan"
          " analizlerini kapsayamaz."
      )
    with c2:
      show_image(
          "bdd100k_demo.png",
          caption=(
              "Şekil 5: BDD100K Farklı Hava ve Zaman Koşulları Sürüş Kareleri"
              " (Yu vd., 2020)"
          ),
      )

  elif ds_option == "Mapillary Vistas":
    c1, c2 = st.columns([1, 1])
    with c1:
      st.markdown("### 🌐 Mapillary Vistas")
      st.write(
          "6 kıtadan kitle kaynaklı toplanan 25.000 yüksek çözünürlüklü görüntü"
          " ve 66 semantik sınıf içerir. Farklı sensör ve kameralardan"
          " toplandığı için oldukça heterojendir."
      )
      st.info(
          "💡 **Sınırlılık:** Farklı mobil cihazlardan kitle kaynaklı"
          " toplanması nedeniyle görüntü kalitesi, çekim yüksekliği ve"
          " aydınlatma standartlarında belirgin tutarsızlıklar görülür."
      )
    with c2:
      show_image(
          "mapillary_vistas_demo.png",
          caption=(
              "Şekil 6: Mapillary Vistas Kitle Kaynaklı Etiket Örnekleri"
              " (Neuhold vd., 2017)"
          ),
      )

  elif ds_option == "PASS, DensePASS & SynPASS":
    c1, c2 = st.columns(2)
    with c1:
      st.markdown("#### 🔄 DensePASS (Panoramik Aktarım)")
      st.write(
          "Perspektif etiketlerin matematiksel projeksiyonla panoramik düzleme"
          " aktarıldığı veri setidir. Projeksiyon hataları ve üst/alt"
          " distorsiyonlar içerir."
      )
      st.info(
          "💡 **Sınırlılık:** Dönüşüm esnasında kutup bölgelerinde oluşan"
          " matematiksel bükülmeler ve piksel bozulmaları etiket kaymalarına yol"
          " açabilir."
      )
      show_image(
          "densepass_demo.png",
          caption=(
              "Şekil 7: DensePASS Panoramik Segmentasyon Aktarımı (Ma vd.,"
              " 2021)"
          ),
      )
    with c2:
      st.markdown("#### 🎮 SynPASS (Sentetik Panoramik)")
      st.write(
          "Sanal motorlar üzerinde 9.080 sentetik panoramik görüntü ve"
          " kusursuz etiketler üretilmiştir. Sentetik-gerçek alan kayması"
          " bulunmaktadır."
      )
      st.info(
          "💡 **Sınırlılık:** Oyun/simülasyon motoru çıktısı olduğundan gerçek"
          " dünya dokuları, ışık kırılmaları ve karmaşık hava koşulları ile"
          " arasında sentetik-gerçek (domain gap) farkı bulunur."
      )
      show_image(
          "synpass_demo.png",
          caption=(
              "Şekil 8: SynPASS Sentetik Panoramik Segmentasyon (Zhang vd.,"
              " 2024)"
          ),
      )


# ------------------------------------------
# TAB 2: ARAZİ ÇALIŞMALARI & VERİ TOPLAMA
# ------------------------------------------
with tab2:
  st.subheader("🗺️ Mersin Saha Arazi Çalışmaları & Veri Toplama Protokolü")

  col_left, col_right = st.columns([1, 1])

  with col_left:
    st.markdown("### 📷 Görüntüleme Donanımı & Yöntem")
    st.write(
        "Saha çekimlerinde **GoPro Max 360** aksiyon kamerası kullanılmıştır"
        " 5760 × 2880 piksel (16 MP) çözünürlükte 360° panoramik"
        " görüntüler insan göz hizasında sabitlenerek toplanmıştır."
    )

    st.markdown("#### Yaya ve Motosiklet Çekim Düzenekleri")
    sub_c1, sub_c2 = st.columns(2)
    with sub_c1:
      show_image(
          "goruntu_eldesi_duzenegi.png",
          caption="Yaya Saha Çalışması Düzeneği",
      )
    with sub_c2:
      show_image(
          "motorsiklet.png",
          caption="Ana Arter Motosiklet Düzeneği",
      )

  with col_right:
    st.markdown("### 📍 GPS Konumlandırma & GIS Üretimi")
    st.write(
        "Çekim sırasında akıllı telefon GPS entegrasyonuyla EXIF"
        " metaverilerine koordinatlar işlenmiştir. GPS sinyalinin"
        " bozulduğu 118 görüntü **GeoSetter** yazılımı ile manuel"
        " konumlandırılmıştır."
    )

    sub_g1, sub_g2 = st.columns(2)
    with sub_g1:
      show_image("metaveri.png", caption="Görüntü GPS Metaverisi")
    with sub_g2:
      show_image("geosetter.png", caption="GeoSetter Konum Düzeltme")

  st.divider()

  st.markdown("### 📅 Arazi Çalışmaları Dağılım Tablosu (13 Saha Seferi)")
  st.dataframe(df_arazi, use_container_width=True)

  st.divider()

  st.markdown("### 🌍 Konumsal Dağılım, Mevsimsellik & Mesafe Analizleri")
  r1, r2= st.columns(2)
  with r1:
    show_image(
        "goruntu_alim_tarihleri_konumsal_dagilim.png",
        caption="SVI Görüntülerinin Konumsal Haritası",
    )
  with r2:
    show_image(
        "seasonal_distribution.png",
        caption="Mevsimsel Örnekleme Dağılımı",
    )


  st.divider()

  st.markdown("### 🌐 Mapillary Açık Erişim Platformu Entegrasyonu")
  m1_col, m2_col = st.columns(2)
  with m1_col:
    show_image(
        "mapillary_account.png",
        caption="PalmCity Mapillary Hesap Portalı",
    )
  with m2_col:
    show_image(
        "mapillary_navigation.png",
        caption="Mapillary 360° İnteraktif Navigasyon Arayüzü",
    )


# ------------------------------------------
# TAB 3: KENTSEL & MİMARİ TİPOLOJİLER
# ------------------------------------------
with tab3:
  st.subheader("🏙️ Mersin Kent Merkezi Kentsel ve Mimari Tipolojileri")
  st.write(
      "PalmCity veri seti, Mersin kent dokusunu temsil eden 5 temel kentsel"
      " tipolojiyi kapsar:"
  )

  t_gallery = st.radio(
      "İncelemek İstediğiniz Tipolojiyi Seçin:",
      [
          "Çarşı (Bazaar)",
          "Planlı Rezidans",
          "Planlı Apartman",
          "Plansız Yerleşim",
          "Sahil",
      ],
      horizontal=True,
  )

  if t_gallery == "Çarşı (Bazaar)":
    c1, c2 = st.columns([1, 1])
    with c1:
      st.markdown("### 🏪 Çarşı Tipolojisi")
      st.write(
          "Ticarethanelerin, tabela yoğunluğunun, yaya hareketliliğinin ve dar"
          " sokakların hakim olduğu kentsel alanlardır."
      )
    with c2:
      show_image(
          "bazaar_typology.png", caption="Çarşı Tipolojisi SVI Örneği"
      )

  elif t_gallery == "Planlı Rezidans":
    c1, c2 = st.columns([1, 1])
    with c1:
      st.markdown("### 🏢 Planlı Rezidans Tipolojisi")
      st.write(
          "Yüksek katlı modern yapılar, düzenli peyzaj, geniş yollar ve açık"
          " otopark alanlarını barındıran tipolojidir."
      )
    with c2:
      show_image(
          "planned_residential_typology.png",
          caption="Planlı Rezidans Tipolojisi Örneği",
      )

  elif t_gallery == "Planlı Apartman":
    c1, c2 = st.columns([1, 1])
    with c1:
      st.markdown("### 🏙️ Planlı Apartman Tipolojisi")
      st.write(
          "Orta-yüksek katlı konut blokları, kaldırımlar, düzenli sokak"
          " ızgarası ve dikili kent ağaçlarını içerir."
      )
    with c2:
      show_image(
          "planned_apartment_typology.png",
          caption="Planlı Apartman Tipolojisi Örneği",
      )

  elif t_gallery == "Plansız Yerleşim":
    c1, c2 = st.columns([1, 1])
    with c1:
      st.markdown("### 🏚️ Plansız Yerleşim Tipolojisi")
      st.write(
          "Düşük katlı, düzensiz yapılaşma, dar sokaklar, karmaşık kablo ve"
          " altyapı elemanlarının öne çıktığı alanlardır."
      )
    with c2:
      show_image(
          "unplanned_typology.png",
          caption="Plansız Yerleşim Tipolojisi Örneği",
      )

  elif t_gallery == "Sahil":
    c1, c2 = st.columns([1, 1])
    with c1:
      st.markdown("### 🏖️ Sahil Tipolojisi")
      st.write(
          "Deniz yüzeyi, geniş yürüyüş yolları, palmiye ağaçları ve açık ufuk"
          " çizgisinin egemen olduğu kıyı şerididir."
      )
    with c2:
      show_image(
          "coastal_typology.png", caption="Sahil Tipolojisi Örneği"
      )

  st.divider()

  st.markdown("### 📊 Tipoloji Dağılım Grafikleri & İlçe/Mahalle Analizleri")
  g1, g2 = st.columns(2)
  with g1:
    show_image(
        "typology_distribution.png",
        caption="Genel Tipoloji Oranları",
    )
    show_image(
        "typology_district_distribution.png",
        caption="İlçelere Göre Tipoloji Dağılımı",
    )
  with g2:
    show_image(
        "typology_spatial_distribution.png",
        caption="Tipolojilerin Konumsal Haritası",
    )
    show_image(
        "typology_neighborhood_distribution.png",
        caption="Mahallelere Göre Tipoloji Kırılımı",
    )


# ------------------------------------------
# TAB 4: PALMCITY SEMANTİK ETİKETLEME
# ------------------------------------------

with tab4:
  st.subheader("🏷️ PalmCity Semantik Etiketleme Protokolü & Sınıf Hiyerarşisi")
  st.write(
      "Etiketlemeler **Supervisely** platformu üzerinde poligon tabanlı piksel"
      " düzeyinde manuel olarak gerçekleştirilmiştir. 830 panoramik"
      " görüntü üzerinde 32 semantik sınıf tanımlanmıştır."
  )

  st.markdown("### 🎨 32 Semantik Sınıf ve Renk Paleti Matrisi")

  # İnteraktif Sınıf Arama Filtresi
  search_term = st.text_input(
      "🔍 Sınıf Ara (Örn: Road, Bina, Yaya, Sky...):", ""
  )

  filtered_df = df_classes[
      df_classes["İngilizce Ad"]
      .str.contains(search_term, case=False)
      | df_classes["Türkçe Ad"].str.contains(search_term, case=False)
      | df_classes["Kategori"].str.contains(search_term, case=False)
  ]
  

  # Renk Rozetleri Görünümü
  cols = st.columns(4)
  for idx, row in filtered_df.reset_index().iterrows():
    col_target = cols[idx % 4]
    with col_target:
      st.markdown(
          f"""
            <div style='background-color: white; border: 1px solid #DDD; padding: 10px; border-radius: 8px; margin-bottom: 10px;'>
                <div style='display: flex; align-items: center; justify-content: space-between;'>
                    <span style='font-weight: bold; font-size: 14px;'>{row['ID']}. {row['Türkçe Ad']}</span>
                    <span style='background-color: {row['HEX']}; width: 22px; height: 22px; border-radius: 50%; display: inline-block; border: 1px solid #888;'></span>
                </div>
                <div style='font-size: 12px; color: #555; margin-top: 4px;'>{row['İngilizce Ad']}</div>
                <div style='font-size: 11px; color: #888;'>Kategori: {row['Kategori']} | {row['RGB Renk koda']}</div>
            </div>
            """,
          unsafe_allow_html=True,
      )

  st.divider()
  st.markdown("### 📋 Detaylı Sınıf Tablosu")
  st.dataframe(filtered_df, use_container_width=True)


# ------------------------------------------
# TAB 5: İSTATİSTİK & ANALİZ PANELİ (Görsel Odaklı)
# ------------------------------------------
with tab5:
    st.subheader("📊 Etkileşimli İstatistik ve Veri Analizi Paneli (Görseller)")

    # 2x2 görsel ızgarası
    st.markdown("#### 📌 Labelled Görsel Özetleri")
    grid_cols = st.columns(2)
    img_names_2x2 = [
        "Labelled_Image_Locations (1).png",
        "Labelled_Images_Districts (1).png",
        "Labelled_Image_Typology (1).png",
        "Labelled_Image_Seasons (1).png",
    ]
    # Render 2x2
    for idx, img_name in enumerate(img_names_2x2):
        col = grid_cols[idx % 2]
        with col:
            caption = img_name.replace(" (1).png", "").replace(".png", "")
            show_image(img_name, caption=caption, use_container_width=True)

    st.markdown("---")

    # Tek sütun: Labelled_Pixel_Counts
    st.markdown("#### 📈 Piksel Dağılımı / Labelled Pixel Counts")
    show_image("Labelled_Pixel_Counts (1).png", caption="Labelled Pixel Counts", use_container_width=True)

    st.markdown("---")

    # Tek sütun: Labelled_Pixel_Counts
    st.markdown("#### 🖼️ Örnek Etiketlenmiş Görüntüler")
    show_image("etiket_ornekleri.png", caption="Etiketlenmiş Örnek Görüntüler", use_container_width=True)

    
    st.markdown("---")
    # İsteğe bağlı: mevcut istatistik kartlarını koru (kısa özet)
    s1, s2, s3 = st.columns(3)
    s1.metric("Toplam Çekimi Yapılan Panoramik SVI", int(df_arazi["Görüntü Sayısı"].sum()))
    s2.metric("Toplam Semantik Sınıf", int(df_classes.shape[0]))
    s3.metric("Etiketli Panoramik SVI", "830")


    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #888; font-size: 13px;'>PalmCity Veri Seti & Semantik Segmentasyon Projesi</div>",
        unsafe_allow_html=True,
    )




