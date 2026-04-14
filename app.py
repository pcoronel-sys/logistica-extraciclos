import streamlit as st
import pandas as pd
import os
import io
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Laboratorios Bagó - Conciliación Extra Ciclos", layout="wide", page_icon="🧪")

# --- DISEÑO ESTÉTICO UI/UX PRO (ESTILOS BAGO) ---
MAGENTA_BAGO = "#C7006A" 
MAGENTA_OSCURO = "#8A004A"

st.markdown(f"""
    <style>
    header, [data-testid="stHeader"] {{ display: none !important; }}
    .main {{ background: radial-gradient(circle at top right, #ffffff, #f0f2f6); }}
    .welcome-text {{ text-align: center; color: #888; font-size: 1.2rem; font-weight: 300; letter-spacing: 2px; text-transform: uppercase; margin-bottom: -10px; }}
    .main-title {{ color: {MAGENTA_BAGO}; font-size: 5rem !important; font-weight: 900 !important; text-align: center; margin-top: 0px; letter-spacing: -4px; filter: drop-shadow(0px 10px 15px rgba(199, 0, 106, 0.2)); line-height: 1; }}
    
    div.stButton > button {{ 
        background: rgba(250, 255, 255, 0.7) !important; 
        backdrop-filter: blur(15px) !important; 
        color: #333 !important; 
        border: 1px solid rgba(200, 200, 200, 0.3) !important; 
        border-radius: 20px !important; 
        height: 150px !important; 
        width: 100% !important; 
        box-shadow: 0 20px 40px rgba(0,0,0,0.05) !important; 
        transition: all 0.6s cubic-bezier(0.165, 0.84, 0.44, 1.0) !important; 
        font-size: 1.4rem !important; 
        font-weight: 800 !important; 
    }}
    div.stButton > button:hover {{ 
        background: linear-gradient(135deg, {MAGENTA_BAGO} 0%, {MAGENTA_OSCURO} 100%) !important; 
        color: white !important; 
        transform: translateY(-15px) scale(1.03) !important; 
    }}
    
    [data-testid="stSidebar"] {{ background-color: white !important; border-right: 1px solid #eee; }}
    [data-testid="stTable"] thead tr th {{ background-color: #2C3E50 !important; color: white !important; font-weight: bold !important; }}
    div[data-testid="stMetric"] {{ background: white !important; border-radius: 20px !important; padding: 20px !important; border-left: 8px solid {MAGENTA_BAGO} !important; box-shadow: 0 10px 20px rgba(0,0,0,0.04) !important; }}
    
    .small-btn button {{
        height: auto !important;
        padding: 5px 15px !important;
        font-size: 0.8rem !important;
        background: #ff4b4b22 !important;
        color: #ff4b4b !important;
        border: 1px solid #ff4b4b !important;
    }}
    </style>
    """, unsafe_allow_html=True)

if 'pagina_actual' not in st.session_state:
    st.session_state['pagina_actual'] = "inicio"

PATH_GP = "master_gp.csv"
PATH_COSTOS = "master_costos.csv"
PATH_GP_VV = "master_gp_vv.csv"
PATH_COSTOS_VV = "master_costos_vv.csv"
HISTORICO_FILE = "base_historica_bago.csv"

# --- FUNCIONES DE SOPORTE ---
def cargar_maestro(path): return pd.read_csv(path) if os.path.exists(path) else None

def leer_archivo(archivo):
    try:
        if archivo.name.lower().endswith(('.xlsx', '.xls')): return pd.read_excel(archivo)
        return pd.read_csv(archivo, encoding='latin-1')
    except: return None

def format_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos')
    return output.getvalue()

hora_ajustada = (datetime.now() - timedelta(hours=5)).hour
saludo_txt = "☀️ Buenos días" if 5 <= hora_ajustada < 12 else "🌤️ Buenas tardes" if 12 <= hora_ajustada < 19 else "🌙 Buenas noches"

# ---------------------------------------------------------
# PANTALLA 1: INICIO
# ---------------------------------------------------------
if st.session_state['pagina_actual'] == "inicio":
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f'<p class="welcome-text">{saludo_txt},</p>', unsafe_allow_html=True)
    st.markdown('<p class="main-title">Laboratorios Bagó</p>', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:#555; font-weight:300; margin-bottom:60px;'>SISTEMA DE CONCILIACION DE EXTRA CICLOS </h3>", unsafe_allow_html=True)
    
    _, col_l, col_r, _ = st.columns([6.5, 1.8, 1.8, 6.5])
    with col_l:
        if st.button("\n\n EXTRA CICLOS"):
            st.session_state['pagina_actual'] = "sistema" 
            st.rerun()
    with col_r:
        if st.button("\n\n VV / REPROGRAMA"):
            st.session_state['pagina_actual'] = "reprograma"
            st.rerun()

# ---------------------------------------------------------
# PANTALLA 2: SISTEMA PRINCIPAL (EXTRA CICLOS)
# ---------------------------------------------------------
elif st.session_state['pagina_actual'] == "sistema":
    if st.sidebar.button("⬅️ Volver al Menú Principal"):
        st.session_state['pagina_actual'] = "inicio"
        st.rerun()

    m_gp = cargar_maestro(PATH_GP)
    m_costos = cargar_maestro(PATH_COSTOS)

    tabs = st.tabs(["🚀 Liquidación Mensual", "🔍 Detalle Actual", "⚙️ Configurar Maestros", "🗄️ Historial"])

    with tabs[0]: 
        if m_gp is None or m_costos is None: 
            st.warning("⚠️ Cargue los maestros en la pestaña Configurar.")
        else:
            c1, c2 = st.columns([1, 2])
            with c1: mes_sel = st.selectbox("Mes", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
            with c2: archivo = st.file_uploader("Subir Carga Mensual", type=['xlsx', 'xls', 'csv'], key="up1")

            if archivo:
                df_c = leer_archivo(archivo)
                if df_c is not None:
                    df_c.columns = df_c.columns.str.strip().str.upper()
                    df_c['CODIGO'] = df_c['CODIGO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    df_c['DESCRIPCIÓN ZONA'] = df_c['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                    df_c['BULTOS'] = pd.to_numeric(df_c['BULTOS'], errors='coerce').fillna(0)
                    
                    col_id_gp = [c for c in m_gp.columns if 'CODIGO' in c.upper()][0]
                    m_gp_clean = m_gp.copy()
                    m_gp_clean[col_id_gp] = m_gp_clean[col_id_gp].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    m_gp_clean = m_gp_clean.drop_duplicates(subset=[col_id_gp])
                    
                    m_costos_clean = m_costos.copy()
                    m_costos_clean.columns = m_costos_clean.columns.str.strip().str.upper()
                    renames = {c: "P_PREP" for c in m_costos_clean.columns if "PREP" in c}
                    renames.update({c: "P_TRANS" for c in m_costos_clean.columns if "TRANS" in c})
                    renames.update({c: "DESCRIPCIÓN ZONA" for c in m_costos_clean.columns if "ZONA" in c})
                    m_costos_clean = m_costos_clean.rename(columns=renames)
                    m_costos_clean['DESCRIPCIÓN ZONA'] = m_costos_clean['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                    m_costos_clean['P_PREP'] = pd.to_numeric(m_costos_clean['P_PREP'], errors='coerce').fillna(0)
                    m_costos_clean['P_TRANS'] = pd.to_numeric(m_costos_clean['P_TRANS'], errors='coerce').fillna(0)
                    m_costos_clean = m_costos_clean.drop_duplicates(subset=['DESCRIPCIÓN ZONA'])
                    
                    res = pd.merge(df_c, m_gp_clean[[col_id_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_id_gp, how='left')
                    res = pd.merge(res, m_costos_clean[['DESCRIPCIÓN ZONA', 'P_PREP', 'P_TRANS']], on='DESCRIPCIÓN ZONA', how='left')

                    if res['GP'].isna().any() or res['P_PREP'].isna().any():
                        st.error("🛑 BLOQUEO: Hay códigos o zonas sin registro.")
                    else:
                        res['TOTAL_PREPARACION'] = res['P_PREP'] * res['BULTOS']
                        res['TOTAL_TRANSPORTE'] = res['P_TRANS'] * res['BULTOS']
                        res['SUBTOTAL_NETO'] = res['TOTAL_PREPARACION'] + res['TOTAL_TRANSPORTE']
                        res['IVA_15'] = res['SUBTOTAL_NETO'] * 0.15
                        res['TOTAL_FINAL'] = res['SUBTOTAL_NETO'] + res['IVA_15']

                        st.subheader(f"📋 Resumen: {mes_sel}")
                        summary = res.pivot_table(index='GP', columns='TIPO', values='SUBTOTAL_NETO', aggfunc='sum').fillna(0)
                        summary['TOTAL'] = summary.sum(axis=1)
                        st.table(summary.style.format("{:,.2f}"))
                        st.session_state['res_actual'] = res

    with tabs[2]: # CONFIG
        ca, cb = st.columns(2)
        with ca:
            ug = st.file_uploader("Cargar GP", key="ug1")
            if ug: leer_archivo(ug).to_csv(PATH_GP, index=False); st.success("GP OK")
        with cb:
            uc = st.file_uploader("Cargar Costos", key="uc1")
            if uc: leer_archivo(uc).to_csv(PATH_COSTOS, index=False); st.success("Costos OK")

# ---------------------------------------------------------
# PANTALLA 3: VV / REPROGRAMA (COPIA EXACTA INDEPENDIENTE)
# ---------------------------------------------------------
elif st.session_state['pagina_actual'] == "reprograma":
    if st.sidebar.button("⬅️ Volver al Menú Principal"):
        st.session_state['pagina_actual'] = "inicio"
        st.rerun()

    st.markdown(f'<p class="main-title" style="font-size: 3.5rem !important;">Módulo VV / Reprograma</p>', unsafe_allow_html=True)
    m_gp_v = cargar_maestro(PATH_GP_VV)
    m_cost_v = cargar_maestro(PATH_COSTOS_VV)
    
    tabs_v = st.tabs(["🚀 Liquidación VV", "🔍 Detalle VV", "⚙️ Configurar Maestros VV"])

    with tabs_v[0]: 
        if m_gp_v is None or m_cost_v is None:
            st.warning("⚠️ Cargue los maestros específicos para VV.")
        else:
            c1v, c2v = st.columns([1, 2])
            with c1v: mes_v = st.selectbox("Mes VV", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], key="mvv")
            with c2v: arch_v = st.file_uploader("Subir Carga VV", key="avv")

            if arch_v:
                df_vv = leer_archivo(arch_v)
                if df_vv is not None:
                    df_vv.columns = df_vv.columns.str.strip().str.upper()
                    df_vv['CODIGO'] = df_vv['CODIGO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    df_vv['DESCRIPCIÓN ZONA'] = df_vv['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                    df_vv['BULTOS'] = pd.to_numeric(df_vv['BULTOS'], errors='coerce').fillna(0)
                    
                    # PROCESO MAESTROS VV (ORDEN CORRECTO)
                    mct_v = m_cost_v.copy()
                    mct_v.columns = mct_v.columns.str.strip().str.upper()
                    rn_v = {c: "P_PREP" for c in mct_v.columns if "PREP" in c}
                    rn_v.update({c: "P_TRANS" for c in mct_v.columns if "TRANS" in c})
                    rn_v.update({c: "DESCRIPCIÓN ZONA" for c in mct_v.columns if "ZONA" in c})
                    mct_v = mct_v.rename(columns=rn_v)
                    mct_v['DESCRIPCIÓN ZONA'] = mct_v['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                    mct_v = mct_v.drop_duplicates(subset=['DESCRIPCIÓN ZONA'])
                    
                    id_v = [c for c in m_gp_v.columns if 'CODIGO' in c.upper()][0]
                    mgp_v = m_gp_v.copy()
                    mgp_v[id_v] = mgp_v[id_v].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    mgp_v = mgp_v.drop_duplicates(subset=[id_v])
                    
                    # MERGE Y CÁLCULOS
                    rv = pd.merge(df_vv, mgp_v[[id_v, 'GP', 'TIPO']], left_on='CODIGO', right_on=id_v, how='left')
                    rv = pd.merge(rv, mct_v[['DESCRIPCIÓN ZONA', 'P_PREP', 'P_TRANS']], on='DESCRIPCIÓN ZONA', how='left')
                    
                    rv['TOTAL_PREPARACION'] = rv['P_PREP'] * rv['BULTOS']
                    rv['TOTAL_TRANSPORTE'] = rv['P_TRANS'] * rv['BULTOS']
                    rv['SUBTOTAL_NETO'] = rv['TOTAL_PREPARACION'] + rv['TOTAL_TRANSPORTE']
                    rv['IVA'] = rv['SUBTOTAL_NETO'] * 0.15
                    rv['TOTAL_FINAL'] = rv['SUBTOTAL_NETO'] + rv['IVA']

                    st.subheader(f"📊 Resumen VV: {mes_v}")
                    kv1, kv2, kv3, kv4 = st.columns(4)
                    kv1.metric("Bultos", f"{rv['BULTOS'].sum():,.0f}")
                    kv2.metric("Prep.", f"$ {rv['TOTAL_PREPARACION'].sum():,.2f}")
                    kv3.metric("Trans.", f"$ {rv['TOTAL_TRANSPORTE'].sum():,.2f}")
                    kv4.metric("Total Final", f"$ {rv['TOTAL_FINAL'].sum():,.2f}")
                    
                    sv = rv.pivot_table(index='GP', columns='TIPO', values='SUBTOTAL_NETO', aggfunc='sum').fillna(0)
                    sv['TOTAL'] = sv.sum(axis=1)
                    st.table(sv.style.format("{:,.2f}"))
                    st.session_state['res_vv'] = rv

    with tabs_v[2]:
        cva, cvb = st.columns(2)
        with cva:
            ugv = st.file_uploader("Maestro GP VV", key="ugv")
            if ugv: leer_archivo(ugv).to_csv(PATH_GP_VV, index=False); st.success("OK")
        with cvb:
            ucv = st.file_uploader("Maestro Costos VV", key="ucv")
            if ucv: leer_archivo(ucv).to_csv(PATH_COSTOS_VV, index=False); st.success("OK")
