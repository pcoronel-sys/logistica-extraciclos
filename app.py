import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Laboratorios Bagó - Conciliación Extra Ciclos", layout="wide", page_icon="🧪")

# --- DISEÑO ESTÉTICO UI/UX PRO ---
MAGENTA_BAGO = "#C7006A" 
MAGENTA_OSCURO = "#8A004A"

st.markdown(f"""
    <style>
    header, [data-testid="stHeader"] {{ display: none !important; }}
    .main {{ background: radial-gradient(circle at top right, #ffffff, #f0f2f6); }}
    .welcome-text {{ text-align: center; color: #888; font-size: 1.2rem; font-weight: 300; letter-spacing: 2px; text-transform: uppercase; margin-bottom: -10px; }}
    .main-title {{ color: {MAGENTA_BAGO}; font-size: 5rem !important; font-weight: 900 !important; text-align: center; margin-top: 0px; letter-spacing: -4px; filter: drop-shadow(0px 10px 15px rgba(199, 0, 106, 0.2)); line-height: 1; }}
    
    /* Botones de Almacén */
    div.stButton > button {{ 
        background: rgba(250, 255, 255, 0.7) !important; 
        backdrop-filter: blur(15px) !important; 
        color: #333 !important; 
        border: 1px solid rgba(200, 200, 200, 0.3) !important; 
        border-radius: 20px !important; 
        height: 50px !important; 
        width: 100% !important; 
        box-shadow: 0 20px 40px rgba(0,0,0,0.05) !important; 
        transition: all 0.6s cubic-bezier(0.165, 0.84, 0.44, 1.0) !important; 
        font-size: 1.4rem !important; 
        font-weight: 800 !important; 
        display: flex; 
        flex-direction: column; 
        justify-content: center; 
    }}
    div.stButton > button:hover {{ 
        background: linear-gradient(135deg, {MAGENTA_BAGO} 0%, {MAGENTA_OSCURO} 100%) !important; 
        color: white !important; 
        transform: translateY(-15px) scale(1.03) !important; 
        box-shadow: 0 30px 60px rgba(199, 0, 106, 0.3) !important; 
        border: 1px solid {MAGENTA_BAGO} !important; 
    }}
    
    .almacen-tag {{ text-align: center; color: {MAGENTA_BAGO}; font-weight: 800; font-size: 1rem; margin-bottom: 10px; letter-spacing: 1px; }}
    
    /* Estilos del Sistema Interno */
    [data-testid="stSidebar"] {{ background-color: white !important; border-right: 1px solid #eee; }}
    [data-testid="stTable"] thead tr th {{ background-color: #2C3E50 !important; color: white !important; font-weight: bold !important; }}
    div[data-testid="stMetric"] {{ background: white !important; border-radius: 20px !important; padding: 20px !important; border-left: 8px solid {MAGENTA_BAGO} !important; box-shadow: 0 10px 20px rgba(0,0,0,0.04) !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE NAVEGACIÓN ---
if 'pagina_actual' not in st.session_state:
    st.session_state['pagina_actual'] = "inicio"

# Ajuste de saludo según hora
hora_ajustada = (datetime.now() - timedelta(hours=5)).hour
if 5 <= hora_ajustada < 12:
    saludo_txt = "☀️ Buenos días"
elif 12 <= hora_ajustada < 19:
    saludo_txt = "🌤️ Buenas tardes"
else:
    saludo_txt = "🌙 Buenas noches"

# ---------------------------------------------------------
# PANTALLA 1: INICIO (UI/UX PRO)
# ---------------------------------------------------------
if st.session_state['pagina_actual'] == "inicio":
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f'<p class="welcome-text">{saludo_txt},</p>', unsafe_allow_html=True)
    st.markdown('<p class="main-title">Laboratorios Bagó</p>', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:#555; font-weight:300; margin-bottom:60px;'>SISTEMA DE CONCILIACION DE EXTRA CICLOS </h3>", unsafe_allow_html=True)
    
    _, col_l, col_r, _ = st.columns([6.5, 1.8, 1.8, 6.5])
    
    with col_l:
        st.markdown(f'<p class="almacen-tag"></p>', unsafe_allow_html=True)
        if st.button("\n\n EXTRA CICLOS"):
            st.session_state['pagina_actual'] = "sistema" # Dirige al sistema funcional
            st.rerun()
            
    with col_r:
        st.markdown(f'<p class="almacen-tag"></p>', unsafe_allow_html=True)
        if st.button("\n REPROGRAMA"):
            # NO CAMBIA DE PÁGINA - Se queda en el inicio
            st.toast("Módulo en desarrollo...", icon="⚠️")
            pass 

# ---------------------------------------------------------
# PANTALLA 2: SISTEMA PRINCIPAL (FUNCIONALIDAD INTACTA)
# ---------------------------------------------------------
elif st.session_state['pagina_actual'] == "sistema":
    
    # Botón lateral para regresar
    if st.sidebar.button("⬅️ Volver al Menú Principal"):
        st.session_state['pagina_actual'] = "inicio"
        st.rerun()

    # --- RUTAS ---
    PATH_GP = "master_gp.csv"
    PATH_COSTOS = "master_costos.csv"
    HISTORICO_FILE = "base_historica_bago.csv"

    def cargar_maestro(path): return pd.read_csv(path) if os.path.exists(path) else None
    def leer_archivo(archivo):
        try:
            if archivo.name.lower().endswith(('.xlsx', '.xls')): return pd.read_excel(archivo)
            return pd.read_csv(archivo, encoding='latin-1')
        except: return None

    st.title("📊 Control de Liquidación Logística")
    tabs = st.tabs(["🚀 Liquidación Mensual", "🔍 Detalle Actual", "⚙️ Configurar Maestros", "🗄️ Historial"])

    m_gp = cargar_maestro(PATH_GP)
    m_costos = cargar_maestro(PATH_COSTOS)

    with tabs[0]: # LIQUIDACIÓN
        if m_gp is None or m_costos is None: 
            st.warning("⚠️ Cargue los maestros en la pestaña Configurar.")
        else:
            c1, c2 = st.columns([1, 2])
            with c1: mes_sel = st.selectbox("Mes", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
            with c2: archivo = st.file_uploader("Subir Carga Mensual", type=['xlsx', 'xls', 'csv'])

            if archivo:
                df_c = leer_archivo(archivo)
                if df_c is not None:
                    df_c.columns = df_c.columns.str.strip().str.upper()
                    df_c['CODIGO'] = df_c['CODIGO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    df_c['DESCRIPCIÓN ZONA'] = df_c['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                    
                    # Normalización GP
                    col_id_gp = [c for c in m_gp.columns if 'CODIGO' in c.upper()][0]
                    m_gp_clean = m_gp.copy()
                    m_gp_clean[col_id_gp] = m_gp_clean[col_id_gp].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    m_gp_clean = m_gp_clean.drop_duplicates(subset=[col_id_gp])
                    
                    # Normalización Costos
                    m_costos_clean = m_costos.copy()
                    m_costos_clean.columns = m_costos_clean.columns.str.strip().str.upper()
                    renames = {}
                    for col in m_costos_clean.columns:
                        if "PREP" in col: renames[col] = "PRECIO_PREP"
                        elif "TRANS" in col: renames[col] = "PRECIO_TRANS"
                        elif "ZONA" in col: renames[col] = "DESCRIPCIÓN ZONA"
                    
                    m_costos_clean = m_costos_clean.rename(columns=renames)
                    m_costos_clean['DESCRIPCIÓN ZONA'] = m_costos_clean['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                    m_costos_clean = m_costos_clean.drop_duplicates(subset=['DESCRIPCIÓN ZONA'])
                    
                    # Cruce y Cálculos
                    res = pd.merge(df_c, m_gp_clean[[col_id_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_id_gp, how='left')
                    res = pd.merge(res, m_costos_clean[['DESCRIPCIÓN ZONA', 'PRECIO_PREP', 'PRECIO_TRANS']], on='DESCRIPCIÓN ZONA', how='left')
                    
                    for col in ['BULTOS', 'PRECIO_PREP', 'PRECIO_TRANS']:
                        res[col] = pd.to_numeric(res[col], errors='coerce').fillna(0)
                    
                    res['TOTAL PREPARACION'] = res['PRECIO_PREP'] * res['BULTOS']
                    res['TOTAL TRANSPORTE'] = res['PRECIO_TRANS'] * res['BULTOS']
                    res['VALOR_LOGISTICA'] = res['TOTAL PREPARACION'] + res['TOTAL TRANSPORTE']
                    res['IVA 15%'] = res['VALOR_LOGISTICA'] * 0.15
                    res['TOTAL CON IVA'] = res['VALOR_LOGISTICA'] + res['IVA 15%']

                    st.subheader(f"📋 Resumen: {mes_sel}")
                    tipo_f = st.radio("Ver por Tipo:", ["Todos", "Solo MM", "Solo MP"], horizontal=True)
                    summary = res.groupby(['GP', 'TIPO'])['VALOR_LOGISTICA'].sum().unstack(fill_value=0).reset_index()
                    for c in ['MM', 'MP']: 
                        if c not in summary.columns: summary[c] = 0.0
                    
                    if tipo_f == "Solo MM": summary = summary[['GP', 'MM']]
                    elif tipo_f == "Solo MP": summary = summary[['GP', 'MP']]
                    
                    summary['SUBTOTAL'] = summary.iloc[:, 1:].sum(axis=1)
                    summary['IVA 15%'] = summary['SUBTOTAL'] * 0.15
                    summary['TOTAL GENERAL'] = summary['SUBTOTAL'] + summary['IVA 15%']

                    tot = {'GP': '--- TOTALES ---'}
                    for col in summary.columns[1:]: tot[col] = summary[col].sum()
                    summary_f = pd.concat([summary, pd.DataFrame([tot])], ignore_index=True)

                    st.table(summary_f.style.format(precision=2))
                    st.session_state['res_actual'] = res
                    st.session_state['mes_actual'] = mes_sel

    with tabs[1]: # DETALLE
        if 'res_actual' in st.session_state:
            df_d = st.session_state['res_actual']
            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric("Bultos", f"{df_d['BULTOS'].sum():,.0f}")
            k2.metric("Total Prep.", f"$ {df_d['TOTAL PREPARACION'].sum():,.2f}")
            k3.metric("Total Trans.", f"$ {df_d['TOTAL TRANSPORTE'].sum():,.2f}")
            k4.metric("Valor Neto", f"$ {df_d['VALOR_LOGISTICA'].sum():,.2f}")
            k5.metric("Total c/ IVA", f"$ {df_d['TOTAL CON IVA'].sum():,.2f}")
            st.dataframe(df_d, use_container_width=True)

    with tabs[2]: # CONFIG
        st.header("⚙️ Configuración de Maestros")
        c_a, c_b = st.columns(2)
        with c_a:
            ug = st.file_uploader("Maestro GP", type=['xlsx', 'xls', 'csv'])
            if ug:
                d = leer_archivo(ug); d.columns = d.columns.str.strip().str.upper()
                d.to_csv(PATH_GP, index=False); st.success("GP Guardado.")
        with c_b:
            uc = st.file_uploader("Maestro Costos", type=['xlsx', 'xls', 'csv'])
            if uc:
                d = leer_archivo(uc); d.columns = d.columns.str.strip().str.upper()
                d.to_csv(PATH_COSTOS, index=False); st.success("Costos Guardado.")
