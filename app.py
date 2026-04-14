import streamlit as st
import pandas as pd
import os
import io
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Laboratorios Bagó - Conciliación", layout="wide", page_icon="🧪")

# --- DISEÑO ESTÉTICO UI/UX PRO ---
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
    </style>
    """, unsafe_allow_html=True)

if 'pagina_actual' not in st.session_state:
    st.session_state['pagina_actual'] = "inicio"

# --- RUTAS ---
PATH_GP = "master_gp.csv"
PATH_COSTOS = "master_costos.csv"
PATH_GP_VV = "master_gp_vv.csv"
PATH_COSTOS_VV = "master_costos_vv.csv"
HISTORICO_FILE = "base_historica_bago.csv"

# --- FUNCIONES ---
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
    st.markdown("<h3 style='text-align:center; color:#555; font-weight:300; margin-bottom:60px;'>SISTEMA DE CONCILIACIÓN LOGÍSTICA</h3>", unsafe_allow_html=True)
    
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
# PANTALLA 2: EXTRA CICLOS
# ---------------------------------------------------------
elif st.session_state['pagina_actual'] == "sistema":
    if st.sidebar.button("⬅️ Volver al Menú Principal"):
        st.session_state['pagina_actual'] = "inicio"
        st.rerun()

    m_gp = cargar_maestro(PATH_GP)
    m_costos = cargar_maestro(PATH_COSTOS)

    tabs = st.tabs(["🚀 Liquidación Mensual", "🔍 Detalle Actual", "⚙️ Configurar Maestros", "🗄️ Historial"])

    with tabs[0]: # LIQUIDACIÓN
        if m_gp is None or m_costos is None: 
            st.warning("⚠️ Cargue maestros en la pestaña Configurar.")
        else:
            c1, c2 = st.columns([1, 2])
            with c1: mes_sel = st.selectbox("Mes", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
            with c2: archivo = st.file_uploader("Subir Carga Extra Ciclos", type=['xlsx', 'xls', 'csv'])

            if archivo:
                df_c = leer_archivo(archivo)
                if df_c is not None:
                    df_c.columns = df_c.columns.str.strip().str.upper()
                    df_c['CODIGO'] = df_c['CODIGO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    df_c['DESCRIPCIÓN ZONA'] = df_c['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                    df_c['BULTOS'] = pd.to_numeric(df_c['BULTOS'], errors='coerce').fillna(0)
                    
                    # PROCESAMIENTO
                    col_id = [c for c in m_gp.columns if 'CODIGO' in c.upper()][0]
                    res = pd.merge(df_c, m_gp[[col_id, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_id, how='left')
                    
                    m_cost_c = m_costos.copy()
                    m_cost_c.columns = m_cost_c.columns.str.strip().str.upper()
                    rn = {c: "P_PREP" for c in m_cost_c.columns if "PREP" in c}
                    rn.update({c: "P_TRANS" for c in m_cost_c.columns if "TRANS" in c})
                    rn.update({c: "DESCRIPCIÓN ZONA" for c in m_cost_c.columns if "ZONA" in c})
                    m_cost_c = m_cost_c.rename(columns=rn)
                    
                    res = pd.merge(res, m_cost_c[['DESCRIPCIÓN ZONA', 'P_PREP', 'P_TRANS']], on='DESCRIPCIÓN ZONA', how='left')
                    
                    res['TOTAL_PREPARACION'] = res['P_PREP'] * res['BULTOS']
                    res['TOTAL_TRANSPORTE'] = res['P_TRANS'] * res['BULTOS']
                    res['SUBTOTAL_NETO'] = res['TOTAL_PREPARACION'] + res['TOTAL_TRANSPORTE']
                    res['IVA_15'] = res['SUBTOTAL_NETO'] * 0.15
                    res['TOTAL_FINAL'] = res['SUBTOTAL_NETO'] + res['IVA_15']

                    # RESUMEN Y KPIs
                    st.subheader(f"📋 Resumen: {mes_sel}")
                    k1, k2, k3 = st.columns(3)
                    k1.metric("Bultos Totales", f"{res['BULTOS'].sum():,.0f}")
                    k2.metric("Subtotal Neto", f"$ {res['SUBTOTAL_NETO'].sum():,.2f}")
                    k3.metric("Total c/ IVA", f"$ {res['TOTAL_FINAL'].sum():,.2f}")
                    
                    summary = res.pivot_table(index='GP', columns='TIPO', values='SUBTOTAL_NETO', aggfunc='sum').fillna(0)
                    summary['TOTAL'] = summary.sum(axis=1)
                    st.table(summary.style.format("{:,.2f}"))
                    st.session_state['res_extra'] = res

    with tabs[2]: # CONFIGURACIÓN EXTRA
        st.header("⚙️ Maestros Extra Ciclos")
        ca, cb = st.columns(2)
        with ca:
            ug = st.file_uploader("Maestro GP", key="ug1")
            if ug: cargar_maestro(PATH_GP) # Solo para activar el guardado
            if ug: leer_archivo(ug).to_csv(PATH_GP, index=False); st.success("GP OK")
        with cb:
            uc = st.file_uploader("Maestro Costos", key="uc1")
            if uc: leer_archivo(uc).to_csv(PATH_COSTOS, index=False); st.success("Costos OK")

# ---------------------------------------------------------
# PANTALLA 3: VV / REPROGRAMA (RESTAURADA CON DISEÑO COMPLETO)
# ---------------------------------------------------------
elif st.session_state['pagina_actual'] == "reprograma":
    if st.sidebar.button("⬅️ Volver al Menú Principal"):
        st.session_state['pagina_actual'] = "inicio"
        st.rerun()

    st.markdown(f'<p class="main-title" style="font-size: 3.5rem !important;">Módulo VV / Reprograma</p>', unsafe_allow_html=True)
    
    m_gp_vv = cargar_maestro(PATH_GP_VV)
    m_costos_vv = cargar_maestro(PATH_COSTOS_VV)
    
    tabs_v = st.tabs(["🚀 Liquidación VV", "🔍 Detalle VV", "⚙️ Configurar Maestros VV"])

    with tabs_v[0]: # LIQUIDACIÓN VV
        if m_gp_vv is None or m_costos_vv is None:
            st.warning("⚠️ Cargue los maestros específicos de VV en la pestaña Configurar.")
        else:
            c1v, c2v = st.columns([1, 2])
            with c1v: mes_v = st.selectbox("Mes VV", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], key="m_vv")
            with c2v: arch_v = st.file_uploader("Subir Carga Mensual VV", type=['xlsx', 'xls', 'csv'], key="a_vv")

            if arch_v:
                df_v = leer_archivo(arch_v)
                if df_v is not None:
                    df_v.columns = df_v.columns.str.strip().str.upper()
                    df_v['CODIGO'] = df_v['CODIGO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    df_v['DESCRIPCIÓN ZONA'] = df_v['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                    df_v['BULTOS'] = pd.to_numeric(df_v['BULTOS'], errors='coerce').fillna(0)
                    
                    # PROCESAMIENTO VV
                    col_id_v = [c for c in m_gp_vv.columns if 'CODIGO' in c.upper()][0]
                    res_v = pd.merge(df_v, m_gp_vv[[col_id_v, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_id_v, how='left')
                    
                    m_ct_v = m_costos_vv.copy()
                    m_ct_v.columns = m_ct_v.columns.str.strip().str.upper()
                    rn_v = {c: "P_PREP" for c in m_ct_v.columns if "PREP" in c}
                    rn_v.update({c: "P_TRANS" for c in m_ct_v.columns if "TRANS" in c})
                    rn_v.update({c: "DESCRIPCIÓN ZONA" for c in m_ct_v.columns if "ZONA" in c})
                    m_ct_v = m_ct_v.rename(columns=rn_v)
                    
                    res_v = pd.merge(res_v, m_ct_v[['DESCRIPCIÓN ZONA', 'P_PREP', 'P_TRANS']], on='DESCRIPCIÓN ZONA', how='left')
                    
                    res_v['TOTAL_PREPARACION'] = res_v['P_PREP'] * res_v['BULTOS']
                    res_v['TOTAL_TRANSPORTE'] = res_v['P_TRANS'] * res_v['BULTOS']
                    res_v['SUBTOTAL_NETO'] = res_v['TOTAL_PREPARACION'] + res_v['TOTAL_TRANSPORTE']
                    res_v['IVA_15%'] = res_v['SUBTOTAL_NETO'] * 0.15
                    res_v['TOTAL_FINAL'] = res_v['SUBTOTAL_NETO'] + res_v['IVA_15%']

                    # DISEÑO RESTAURADO (KPIs Y TABLAS)
                    st.subheader(f"📊 Resumen VV: {mes_v}")
                    kv1, kv2, kv3 = st.columns(3)
                    kv1.metric("Bultos VV", f"{res_v['BULTOS'].sum():,.0f}")
                    kv2.metric("Subtotal VV", f"$ {res_v['SUBTOTAL_NETO'].sum():,.2f}")
                    kv3.metric("Total VV c/ IVA", f"$ {res_v['TOTAL_FINAL'].sum():,.2f}")
                    
                    summary_v = res_v.pivot_table(index='GP', columns='TIPO', values='SUBTOTAL_NETO', aggfunc='sum').fillna(0)
                    summary_v['TOTAL'] = summary_v.sum(axis=1)
                    st.table(summary_v.style.format("{:,.2f}"))
                    
                    st.session_state['res_vv_final'] = res_v

    with tabs_v[1]: # DETALLE VV
        if 'res_vv_final' in st.session_state:
            st.dataframe(st.session_state['res_vv_final'], use_container_width=True)

    with tabs_v[2]: # CONFIGURACIÓN VV
        st.header("⚙️ Maestros Exclusivos VV")
        cva, cvb = st.columns(2)
        with cva:
            ugv = st.file_uploader("Maestro GP (VV)", key="ugv")
            if ugv: leer_archivo(ugv).to_csv(PATH_GP_VV, index=False); st.success("GP VV OK")
        with cvb:
            ucv = st.file_uploader("Maestro Costos (VV)", key="ucv")
            if ucv: leer_archivo(ucv).to_csv(PATH_COSTOS_VV, index=False); st.success("Costos VV OK")
