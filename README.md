# 🌴 PalmCity: Panoramik SVI, Semantik Segmentasyon ve SHAP Analizi

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-red)
![GeoPandas](https://img.shields.io/badge/GeoPandas-Spatial_Analysis-green)
![SHAP](https://img.shields.io/badge/SHAP-Explainable_AI-orange)

**PalmCity Projesi**, Mersin kent merkezinde toplanan 360° Panoramik Sokak Görünümü (SVI) verilerini, kentsel morfolojileri, piksel tabanlı semantik segmentasyon etiketlerini ve makine öğrenmesi destekli mikro-klima (sıcaklık anomalisi) analizlerini etkileşimli olarak sunan kapsamlı bir veri bilimi arayüzüdür.

## 📖 Proje Hakkında

Bu proje, kentsel çevrenin görsel ve yapısal unsurlarının yüzey sıcaklıkları üzerindeki etkisini anlamak amacıyla geliştirilmiştir. Toplam **5.232 adet 360° panoramik görüntü** toplanmış, bunlardan **830 tanesi** Supervisely platformu kullanılarak **32 farklı semantik sınıfta** piksel düzeyinde etiketlenmiştir.

Uygulama, ağır makine öğrenmesi (XGBoost, Random Forest, LightGBM) ve mekânsal analiz süreçlerini son kullanıcıya anında sunabilmek için **önbelleklenmiş veriler (.npz, .json) ve GeoPackage (.gpkg)** formatlarını kullanır.

## ✨ Temel Özellikler (Uygulama Sekmeleri)

Uygulama 7 ana modülden oluşmaktadır:

1. **📚 Literatürdeki Mevcut Veri Setleri:** Cityscapes, ADE20K, MS COCO, BDD100K ve Mapillary Vistas gibi öne çıkan küresel veri setlerinin PalmCity ile karşılaştırmalı analizi.
2. **🗺️ Arazi Çalışmaları & Veri Toplama:** 13 farklı saha seferinin GPS metaverileri, GoPro Max 360 donanım düzenekleri ve mevsimsel/konumsal dağılım istatistikleri.
3. **🏙️ Kentsel & Mimari Tipolojiler:** Mersin'in 5 temel kentsel tipolojisinin (Çarşı, Planlı Rezidans, Planlı Apartman, Plansız Yerleşim, Sahil) SVI örnekleri ve mekânsal kırılımları.
4. **🏷️ Semantik Etiketleme:** 32 sınıflık (Yol, Kaldırım, Bina, Ağaç, Gökyüzü vb.) detaylı etiket hiyerarşisi ve renk paleti matrisi.
5. **📊 İstatistik & Analiz:** Etiketlenmiş piksellerin sınıflara, mevsimlere ve kentsel tipolojilere göre dağılımını gösteren özet panosu.
6. **📈 Çevresel İndisler (Mekânsal Haritalar):** 8 temel kentsel indisin (GVI, SVF, BVI vb.) ESRI uydu haritaları (Contextily) üzerinde ve istatistiksel kutu grafikleriyle (Plotly) etkileşimli dağılımı.
7. **🧠 SHAP Analizi:** Makine öğrenmesi modelleri kullanılarak hesaplanan sıcaklık anomalilerinin (Delta T), kentsel indislerle olan karmaşık ilişkisini açıklayan **Explainable AI (XAI)** modülü (Bar Plot ve Yönlü Dot Plot).

## 🛠️ Kullanılan Teknolojiler

* **Arayüz:** [Streamlit](https://streamlit.io/)
* **Veri İşleme:** Pandas, NumPy
* **Mekânsal Analiz (GIS):** GeoPandas, Contextily (ESRI Basemaps), Mapclassify
* **Makine Öğrenmesi Yorumlama:** SHAP (SHapley Additive exPlanations)
* **Veri Görselleştirme:** Plotly Express, Matplotlib

## 🚀 Kurulum ve Çalıştırma (Lokal Ortam)

Projeyi kendi bilgisayarınızda çalıştırmak için aşağıdaki adımları izleyin:

### 1. Depoyu Klonlayın
```bash
git clone [https://github.com/KULLANICI_ADINIZ/PalmCity-Tanitim.git](https://github.com/KULLANICI_ADINIZ/PalmCity-Tanitim.git)
cd PalmCity-Tanitim

PalmCity-Tanitim/
│
├── app.py                  # Streamlit ana uygulama dosyası
├── requirements.txt        # Gerekli Python kütüphaneleri
├── images/                 # SVI örnekleri, logolar ve statik analiz grafikleri
└── files/                  # İnteraktif modüller için işlenmiş veri dosyaları
    ├── gdf5_final.gpkg     # Çevresel indislerin coğrafi veritabanı (Haritalar için)
    ├── gdf5_final.xlsx     # Çevresel indislerin tablosal formatı
    ├── anomaly_summer_temp/# Yaz mevsimi model JSON metrikleri
    ├── anomaly_summer_temp.npz # Yaz mevsimi SHAP önbellek dizileri
    └── ...                 # Diğer mevsimlere ait veri setleri