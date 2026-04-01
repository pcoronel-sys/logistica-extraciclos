import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Bagó Intel-Stock | Extra Ciclos", layout="wide", page_icon="🧪")

# --- 🎨 MOTOR DE ESTILOS RADICAL (BORRADO DE CONTENEDORES Y CENTRADO) ---
st.markdown("""
    <style>
    /* 1. ELIMINAR TODO EL NAVBAR Y ESPACIOS SUPERIORES */
    header, [data-testid="stHeader"], footer { display: none !important; }
    
    /* 2. FORZAR FONDO LIMPIO EN TODA LA APP */
    .stApp {
        background: radial-gradient(circle at center, #ffffff 0%, #f0f2f6 100%);
    }

    /* 3. CENTRADO ABSOLUTO DEL CONTENIDO (ELIMINA EL CUADRO IZQUIERDO) */
    [data-testid="stAppViewContainer"] > section:nth-child(2) > div:nth-child(1) {
        padding: 0 !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }

    .block-container {
        max-width: 100% !important;
        padding: 0 !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        min-height: 100vh !important;
    }

    /* 4. TARJETA DE CRISTAL REAL (SIN BORDES EXTRAÑOS) */
    .glass-card {
        background: rgba(255, 255, 255, 0.4);
        backdrop-filter: blur(25px);
        -webkit-backdrop-filter: blur(25px);
        border-radius: 50px;
        border: 1px solid rgba(255, 255, 255, 0.6);
        box-shadow: 0 40px 100px rgba(0,0,0,0.08);
        padding: 80px;
        text-align: center;
        width: 850px; /* Ancho fijo para control total */
        margin: auto;
    }

    /* 5. TÍTULOS Y COLORES VIVOS */
    .hero-title {
        background: linear-gradient(90deg, #FF0066 0%, #8E2DE2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 80px; font-weight: 900; line-height: 1; margin-bottom: 5px;
    }
    .hero-sub {
        color: #455A64; font-size: 26px; font-weight: 300; margin-bottom: 60px;
    }

    /* 6. BOTONES PREMIUM TIPO ESPEJO */
    .stButton>button {
        background: linear-gradient(135deg, #FF0066 0%, #D81B60 100%) !important;
        color: white !important;
        font-size: 20px !important;
        font-weight: 800 !important;
        height: 90px !important;
        width: 100% !important;
        border-radius: 30px !important;
        border: none !important;
        box-shadow: 0 15px 35px rgba(255, 0, 102, 0.25) !important;
        transition: all 0.4s ease !important;
    }
    .stButton>button:hover {
        transform: scale(1.03) translateY(-5px);
        box-shadow: 0 25px 50px rgba(255, 0, 102, 0.4) !important;
    }

    .tag-label {
        color: #FF0066; font-size: 13px; font-weight: 900; letter-spacing: 4px; margin-bottom: 10px;
    }

    /* Ajustes para el sistema interno para que no se dañen las tablas */
    .internal-mode .block-container {
        display: block !important;
        padding: 2rem 5rem !important;
        min-height: auto !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- NAVEGACIÓN ---
if 'pagina_actual' not in st.session_state:
    st.session_state['pagina_actual'] = "inicio"

# ---------------------------------------------------------
# PANTALLA DE INICIO (ESTO ELIMINA EL CUADRO Y CENTRA)
# ---------------------------------------------------------
if st.session_state['pagina_actual'] == "inicio":
    
    # Este div contenedor asegura el centrado real
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    st.markdown("<p style='color:#78909C; font-weight:800; letter-spacing:5px; margin-bottom:10px;'>BAGÓ ECUADOR</p>", unsafe_allow_html=True)
    st.markdown("<h1 class='hero-title'>Laboratorios Bagó</h1>", unsafe_allow_html=True)
    st.markdown("<p class='hero-sub'>Cálculo de Extra Ciclos • Intel-Stock</p>", unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown("<p class='tag-label'>ALMACÉN 1010</p>", unsafe_allow_html=True)
        if st.button("📦 MATERIAL EMPAQUE"):
            st.session_state['pagina_actual'] = "sistema"
            st.rerun()

    with col2:
        st.markdown("<p class='tag-label'>ALMACÉN 1070</p>", unsafe_allow_html=True)
        if st.button("🔢 PROMOCIONALES"):
            st.session_state['pagina_actual'] = "sistema"
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# SISTEMA DE CÁLCULO (TU CÓDIGO INTACTO)
# ---------------------------------------------------------
elif st.session_state['pagina_actual'] == "sistema":
    # Agregamos una clase para que el CSS sepa que aquí NO debe centrar todo
    st.markdown('<div class="internal-mode">', unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("<h2 style='color:#FF0066;'>Opciones</h2>", unsafe_allow_html=True)
        if st.button("⬅️ VOLVER AL INICIO"):
            st.session_state['pagina_actual'] = "inicio"
            st.rerun()
        st.divider()

    # --- LÓGICA DE DATOS ---
    PATH_GP = "master_gp.csv"
    PATH_COSTOS = "master_costos.csv"
    HISTORICO_FILE = "base_historica_bago.csv"

    def cargar_maestro(path): return pd.read_csv(path) if os.path.exists(path) else None
    def leer_archivo(archivo):
        try:
            if archivo.name.lower().endswith(('.xlsx', '.xls')): return pd.read_excel(archivo)
            return pd.read_csv(archivo, encoding='latin-1')
        except: return None

    st.title("📊 Auditoría de Extra Ciclos")
    tabs = st.tabs(["🚀 Proceso", "🔍 Auditoría", "⚙️ Maestros", "🗄️ Historial"])

    m_gp = cargar_maestro(PATH_GP)
    m_costos = cargar_maestro(PATH_COSTOS)

    with tabs[0]: # LIQUIDACIÓN
        if m_gp is None or m_costos is None: st.warning("⚠️ Cargue maestros en la pestaña correspondiente.")
        else:
            c1, c2 = st.columns([1, 2])
            with c1: mes_sel = st.selectbox("Mes", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
            with c2: archivo = st.file_uploader("Subir Archivo", type=['xlsx', 'xls', 'csv'])

            if archivo:
                df_c = leer_archivo(archivo)
                if df_c is not None:
                    df_c.columns = df_c.columns.str.strip().str.upper()
                    df_c['CODIGO'] = df_c['CODIGO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    df_c['DESCRIPCIÓN ZONA'] = df_c['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                    
                    m_gp_clean = m_gp.copy()
                    cid = [c for c in m_gp_clean.columns if 'CODIGO' in c.upper()][0]
                    m_gp_clean[cid] = m_gp_clean[cid].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    m_gp_clean = m_gp_clean.drop_duplicates(subset=[cid])
                    
                    m_costos_clean = m_costos.copy()
                    m_costos_clean.columns = m_costos_clean.columns.str.strip().str.upper()
                    ren = {c: "PREP" for c in m_costos_clean.columns if "PREP" in c}
                    ren.update({c: "TRANS" for c in m_costos_clean.columns if "TRANS" in c})
                    m_costos_clean = m_costos_clean.rename(columns=ren)
                    m_costos_clean['DESCRIPCIÓN ZONA'] = m_costos_clean['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                    m_costos_clean = m_costos_clean.drop_duplicates(subset=['DESCRIPCIÓN ZONA'])
                    
                    res = pd.merge(df_c, m_gp_clean[[cid, 'GP', 'TIPO']], left_on='CODIGO', right_on=cid, how='left')
                    res = pd.merge(res, m_costos_clean[['DESCRIPCIÓN ZONA', 'PREP', 'TRANS']], on='DESCRIPCIÓN ZONA', how='left')
                    
                    for col in ['BULTOS', 'PREP', 'TRANS']: res[col] = pd.to_numeric(res[col], errors='coerce').fillna(0)
                    res['TOTAL PREPARACION'] = res['PREP'] * res['BULTOS']
                    res['TOTAL TRANSPORTE'] = res['TRANS'] * res['BULTOS']
                    res['VALOR_LOGISTICA'] = res['TOTAL PREPARACION'] + res['TOTAL TRANSPORTE']
                    res['IVA 15%'] = res['VALOR_LOGISTICA'] * 0.15
                    res['TOTAL CON IVA'] = res['VALOR_LOGISTICA'] + res['IVA 15%']

                    st.table(res.groupby(['GP', 'TIPO'])['VALOR_LOGISTICA'].sum().unstack(fill_value=0))
                    st.session_state['res_actual'] = res

    with tabs[1]: # AUDITORÍA
        if 'res_actual' in st.session_state:
            st.dataframe(st.session_state['res_actual'], use_container_width=True)

    with tabs[2]: # MAESTROS
        ca, cb = st.columns(2)
        with ca:
            ug = st.file_uploader("Maestro GP", type=['xlsx', 'xls', 'csv'])
            if ug: leer_archivo(ug).to_csv(PATH_GP, index=False); st.success("OK")
        with cb:
            uc = st.file_uploader("Maestro Costos", type=['xlsx', 'xls', 'csv'])
            if uc: leer_archivo(uc).to_csv(PATH_COSTOS, index=False); st.success("OK")
