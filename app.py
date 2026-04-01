import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Bagó Intel-Stock | Extra Ciclos", layout="wide", page_icon="🧪")

# --- 🎨 MOTOR DE ESTILOS RADICAL (COLORES VIVOS Y CENTRADO TOTAL) ---
st.markdown("""
    <style>
    header, [data-testid="stHeader"], footer { display: none !important; }
    
    /* FONDO DINÁMICO */
    .stApp {
        background: radial-gradient(circle at top right, #fdfcfb, #e2e5e7);
    }

    /* ELIMINAR CUADROS VACÍOS Y CENTRAR TODO EL CONTENIDO */
    .block-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        padding: 0 !important;
    }

    /* TARJETA DE CRISTAL (GLASSMORPHISM) */
    .glass-card {
        background: rgba(255, 255, 255, 0.3);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 40px;
        border: 1px solid rgba(255, 255, 255, 0.7);
        box-shadow: 0 30px 60px rgba(0,0,0,0.1);
        padding: 60px;
        text-align: center;
        max-width: 900px;
        width: 90%;
        animation: fadeIn 1.2s ease-out;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* TEXTOS DE COLORES */
    .hero-title {
        background: linear-gradient(90deg, #FF0066 0%, #FF8000 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 75px; font-weight: 900; line-height: 1.1; margin-bottom: 10px;
    }
    .hero-sub {
        color: #2C3E50; font-size: 24px; font-weight: 400; opacity: 0.8; margin-bottom: 50px;
    }

    /* BOTONES ESTILO NEÓN/ESPEJO */
    .stButton>button {
        background: linear-gradient(135deg, #FF0066 0%, #CC0052 100%) !important;
        color: white !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        height: 80px !important;
        width: 100% !important;
        border-radius: 25px !important;
        border: none !important;
        box-shadow: 0 10px 25px rgba(255, 0, 102, 0.3) !important;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    }
    .stButton>button:hover {
        transform: scale(1.05) translateY(-5px);
        box-shadow: 0 20px 40px rgba(255, 0, 102, 0.5) !important;
        filter: brightness(1.2);
    }

    /* ETIQUETAS DE ALMACÉN */
    .tag-label {
        color: #FF0066; font-size: 14px; font-weight: 800; letter-spacing: 3px; margin-bottom: 15px;
    }

    /* ESTILOS INTERNOS DE TABLAS */
    [data-testid="stTable"] thead tr th {
        background-color: #2C3E50 !important; color: white !important; font-weight: bold !important;
    }
    div[data-testid="stMetric"] {
        background: white !important; border-radius: 20px !important; 
        box-shadow: 0 10px 20px rgba(0,0,0,0.03) !important; padding: 20px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- NAVEGACIÓN ---
if 'pagina_actual' not in st.session_state:
    st.session_state['pagina_actual'] = "inicio"

# ---------------------------------------------------------
# PANTALLA DE INICIO (CENTRADA Y SIN CUADROS VACÍOS)
# ---------------------------------------------------------
if st.session_state['pagina_actual'] == "inicio":
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    st.markdown("<p style='color:#7f8c8d; font-weight:700; letter-spacing:4px; margin-bottom:0;'>BAGÓ ECUADOR</p>", unsafe_allow_html=True)
    st.markdown("<h1 class='hero-title'>Laboratorios Bagó</h1>", unsafe_allow_html=True)
    st.markdown("<p class='hero-sub'>Auditoría & Cálculo de Extra Ciclos</p>", unsafe_allow_html=True)

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
# SISTEMA DE CÁLCULO (TU CÓDIGO ORIGINAL INTACTO)
# ---------------------------------------------------------
elif st.session_state['pagina_actual'] == "sistema":
    
    with st.sidebar:
        st.markdown("<h3 style='color:#FF0066;'>Menú de Control</h3>", unsafe_allow_html=True)
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

    with tabs[0]: # PESTAÑA LIQUIDACIÓN
        if m_gp is None or m_costos is None: st.warning("⚠️ Cargue los maestros en la pestaña Maestros.")
        else:
            c1, c2 = st.columns([1, 2])
            with c1: mes_sel = st.selectbox("Mes de reporte", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
            with c2: archivo = st.file_uploader("Subir Archivo Excel", type=['xlsx', 'xls', 'csv'])

            if archivo:
                df_c = leer_archivo(archivo)
                if df_c is not None:
                    df_c.columns = df_c.columns.str.strip().str.upper()
                    df_c['CODIGO'] = df_c['CODIGO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    df_c['DESCRIPCIÓN ZONA'] = df_c['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                    
                    # Normalización GP
                    m_gp_clean = m_gp.copy()
                    col_id = [c for c in m_gp_clean.columns if 'CODIGO' in c.upper()][0]
                    m_gp_clean[col_id] = m_gp_clean[col_id].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    m_gp_clean = m_gp_clean.drop_duplicates(subset=[col_id])
                    
                    # Normalización Costos
                    m_costos_clean = m_costos.copy()
                    m_costos_clean.columns = m_costos_clean.columns.str.strip().str.upper()
                    renames = {c: "PREP" for c in m_costos_clean.columns if "PREP" in c}
                    renames.update({c: "TRANS" for c in m_costos_clean.columns if "TRANS" in c})
                    m_costos_clean = m_costos_clean.rename(columns=renames)
                    m_costos_clean['DESCRIPCIÓN ZONA'] = m_costos_clean['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                    m_costos_clean = m_costos_clean.drop_duplicates(subset=['DESCRIPCIÓN ZONA'])
                    
                    res = pd.merge(df_c, m_gp_clean[[col_id, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_id, how='left')
                    res = pd.merge(res, m_costos_clean[['DESCRIPCIÓN ZONA', 'PREP', 'TRANS']], on='DESCRIPCIÓN ZONA', how='left')
                    
                    for col in ['BULTOS', 'PREP', 'TRANS']: res[col] = pd.to_numeric(res[col], errors='coerce').fillna(0)
                    
                    res['TOTAL PREPARACION'] = res['PREP'] * res['BULTOS']
                    res['TOTAL TRANSPORTE'] = res['TRANS'] * res['BULTOS']
                    res['VALOR_LOGISTICA'] = res['TOTAL PREPARACION'] + res['TOTAL TRANSPORTE']
                    res['IVA 15%'] = res['VALOR_LOGISTICA'] * 0.15
                    res['TOTAL CON IVA'] = res['VALOR_LOGISTICA'] + res['IVA 15%']

                    st.subheader(f"📈 Resumen Consolidado: {mes_sel}")
                    summary = res.groupby(['GP', 'TIPO'])['VALOR_LOGISTICA'].sum().unstack(fill_value=0).reset_index()
                    for c in ['MM', 'MP']: 
                        if c not in summary.columns: summary[c] = 0.0
                    summary['SUBTOTAL'] = summary['MM'] + summary['MP']
                    summary['IVA 15%'] = summary['SUBTOTAL'] * 0.15
                    summary['TOTAL GENERAL'] = summary['SUBTOTAL'] + summary['IVA 15%']

                    tot = {'GP': '--- TOTALES ---'}
                    for col in summary.columns[1:]: tot[col] = summary[col].sum()
                    summary_f = pd.concat([summary, pd.DataFrame([tot])], ignore_index=True)
                    st.table(summary_f.style.format(precision=2))
                    
                    st.session_state['res_actual'] = res
                    st.session_state['mes_actual'] = mes_sel

    with tabs[1]: # PESTAÑA DETALLE
        if 'res_actual' in st.session_state:
            df_d = st.session_state['res_actual']
            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric("Bultos", f"{df_d['BULTOS'].sum():,.0f}")
            k2.metric("Preparación", f"$ {df_d['TOTAL PREPARACION'].sum():,.2f}")
            k3.metric("Transporte", f"$ {df_d['TOTAL TRANSPORTE'].sum():,.2f}")
            k4.metric("Valor Neto", f"$ {df_d['VALOR_LOGISTICA'].sum():,.2f}")
            k5.metric("Total c/ IVA", f"$ {df_d['TOTAL CON IVA'].sum():,.2f}")
            st.divider()
            st.dataframe(df_d, use_container_width=True, height=450)

    with tabs[2]: # PESTAÑA CONFIG
        ca, cb = st.columns(2)
        with ca:
            ug = st.file_uploader("Actualizar Maestro GP", type=['xlsx', 'xls', 'csv'])
            if ug:
                d = leer_archivo(ug); d.to_csv(PATH_GP, index=False); st.success("GP Guardado.")
        with cb:
            uc = st.file_uploader("Actualizar Maestro Costos", type=['xlsx', 'xls', 'csv'])
            if uc:
                d = leer_archivo(uc); d.to_csv(PATH_COSTOS, index=False); st.success("Costos Guardado.")

    with tabs[3]: # PESTAÑA HISTORIAL
        if os.path.exists(HISTORICO_FILE):
            h = pd.read_csv(HISTORICO_FILE)
            st.dataframe(h, use_container_width=True)
