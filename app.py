import streamlit as st
import pandas as pd
import os
import io
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Laboratorios Bagó - Conciliación Logística", layout="wide", page_icon="🧪")

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

# RUTAS DE ARCHIVOS
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
# PANTALLA 2: EXTRA CICLOS (SISTEMA)
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
            with c2: archivo = st.file_uploader("Subir Carga Mensual", type=['xlsx', 'xls', 'csv'], key="up_ex")

            if archivo:
                df_c = leer_archivo(archivo)
                if df_c is not None:
                    df_c.columns = df_c.columns.str.strip().str.upper()
                    df_c['CODIGO'] = df_c['CODIGO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    df_c['DESCRIPCIÓN ZONA'] = df_c['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                    df_c['BULTOS'] = pd.to_numeric(df_c['BULTOS'], errors='coerce').fillna(0)
                    
                    col_id_gp = [c for c in m_gp.columns if 'CODIGO' in c.upper()][0]
                    m_gp_clean = m_gp.copy(); m_gp_clean[col_id_gp] = m_gp_clean[col_id_gp].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    m_gp_clean = m_gp_clean.drop_duplicates(subset=[col_id_gp])
                    
                    m_costos_clean = m_costos.copy(); m_costos_clean.columns = m_costos_clean.columns.str.strip().str.upper()
                    rn_map = {c: "P_PREP" for c in m_costos_clean.columns if "PREP" in c}; rn_map.update({c: "P_TRANS" for c in m_costos_clean.columns if "TRANS" in c}); rn_map.update({c: "DESCRIPCIÓN ZONA" for c in m_costos_clean.columns if "ZONA" in c})
                    m_costos_clean = m_costos_clean.rename(columns=rn_map); m_costos_clean['DESCRIPCIÓN ZONA'] = m_costos_clean['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                    m_costos_clean = m_costos_clean.drop_duplicates(subset=['DESCRIPCIÓN ZONA'])
                    
                    res = pd.merge(df_c, m_gp_clean[[col_id_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_id_gp, how='left')
                    res = pd.merge(res, m_costos_clean[['DESCRIPCIÓN ZONA', 'P_PREP', 'P_TRANS']], on='DESCRIPCIÓN ZONA', how='left')

                    res['TOTAL_PREPARACION'] = res['P_PREP'] * res['BULTOS']
                    res['TOTAL_TRANSPORTE'] = res['P_TRANS'] * res['BULTOS']
                    res['SUBTOTAL_NETO'] = res['TOTAL_PREPARACION'] + res['TOTAL_TRANSPORTE']
                    res['IVA_15'] = res['SUBTOTAL_NETO'] * 0.15
                    res['TOTAL_FINAL'] = res['SUBTOTAL_NETO'] + res['IVA_15']

                    st.subheader(f"📋 Resumen: {mes_sel}")
                    summary = res.pivot_table(index='GP', columns='TIPO', values='SUBTOTAL_NETO', aggfunc='sum').fillna(0)
                    for col in ['MM', 'MP']:
                        if col not in summary.columns: summary[col] = 0.0
                    summary['SUBTOTAL'] = summary['MM'] + summary['MP']
                    summary['IVA 15%'] = summary['SUBTOTAL'] * 0.15
                    summary['TOTAL GENERAL'] = summary['SUBTOTAL'] + summary['IVA 15%']
                    summary_f = pd.concat([summary.reset_index(), pd.DataFrame([{'GP': '--- TOTALES ---', **summary.sum()}])], ignore_index=True)
                    st.table(summary_f.style.format(subset=summary_f.columns[1:], formatter="{:,.2f}"))
                    st.download_button("📥 Descargar Resumen", format_excel(summary_f), f"Resumen_Extra_{mes_sel}.xlsx")
                    st.session_state['res_actual'] = res

    with tabs[1]:
        if 'res_actual' in st.session_state:
            df_v = st.session_state['res_actual']
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Bultos", f"{df_v['BULTOS'].sum():,.0f}"); k2.metric("Prep.", f"$ {df_v['TOTAL_PREPARACION'].sum():,.2f}"); k3.metric("Trans.", f"$ {df_v['TOTAL_TRANSPORTE'].sum():,.2f}"); k4.metric("Total Final", f"$ {df_v['TOTAL_FINAL'].sum():,.2f}")
            st.dataframe(df_v, use_container_width=True)

    with tabs[2]:
        ca, cb = st.columns(2)
        with ca:
            ug = st.file_uploader("Cargar GP Extra", key="ug_ex")
            if ug: leer_archivo(ug).to_csv(PATH_GP, index=False); st.success("GP OK")
        with cb:
            uc = st.file_uploader("Cargar Costos Extra", key="uc_ex")
            if uc: leer_archivo(uc).to_csv(PATH_COSTOS, index=False); st.success("Costos OK")

# ---------------------------------------------------------
# PANTALLA 3: VV / REPROGRAMA (ESPEJO EXACTO)
# ---------------------------------------------------------
elif st.session_state['pagina_actual'] == "reprograma":
    if st.sidebar.button("⬅️ Volver al Menú Principal"):
        st.session_state['pagina_actual'] = "inicio"
        st.rerun()

    st.markdown(f'<p class="main-title" style="font-size: 3.5rem !important;">Módulo VV / Reprograma</p>', unsafe_allow_html=True)
    m_gp_vv = cargar_maestro(PATH_GP_VV)
    m_cost_vv = cargar_maestro(PATH_COSTOS_VV)
    
    tabs_v = st.tabs(["🚀 Liquidación Mensual", "🔍 Detalle Actual", "⚙️ Configurar Maestros", "🗄️ Historial"])

    with tabs_v[0]: # LIQUIDACIÓN VV
        if m_gp_vv is None or m_cost_vv is None:
            st.warning("⚠️ Cargue los maestros específicos para VV en la pestaña Configurar.")
        else:
            c1v, c2v = st.columns([1, 2])
            with c1v: mes_vv = st.selectbox("Mes", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], key="mvv")
            with c2v: arch_vv = st.file_uploader("Subir Carga Mensual", type=['xlsx', 'xls', 'csv'], key="avv")

            if arch_vv:
                df_vv = leer_archivo(arch_vv)
                if df_vv is not None:
                    df_vv.columns = df_vv.columns.str.strip().str.upper()
                    df_vv['CODIGO'] = df_vv['CODIGO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    df_vv['DESCRIPCIÓN ZONA'] = df_vv['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                    df_vv['BULTOS'] = pd.to_numeric(df_vv['BULTOS'], errors='coerce').fillna(0)

                    col_id_v = [c for c in m_gp_vv.columns if 'CODIGO' in c.upper()][0]
                    mgp_v_c = m_gp_vv.copy(); mgp_v_c[col_id_v] = mgp_v_c[col_id_v].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    mgp_v_c = mgp_v_c.drop_duplicates(subset=[col_id_v])
                    
                    mct_v_c = m_cost_vv.copy(); mct_v_c.columns = mct_v_c.columns.str.strip().str.upper()
                    rn_v = {c: "P_PREP" for c in mct_v_c.columns if "PREP" in c}; rn_v.update({c: "P_TRANS" for c in mct_v_c.columns if "TRANS" in c}); rn_v.update({c: "DESCRIPCIÓN ZONA" for c in mct_v_c.columns if "ZONA" in c})
                    mct_v_c = mct_v_c.rename(columns=rn_v); mct_v_c['DESCRIPCIÓN ZONA'] = mct_v_c['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                    mct_v_c = mct_v_c.drop_duplicates(subset=['DESCRIPCIÓN ZONA'])

                    res_v = pd.merge(df_vv, mgp_v_c[[col_id_v, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_id_v, how='left')
                    res_v = pd.merge(res_v, mct_v_c[['DESCRIPCIÓN ZONA', 'P_PREP', 'P_TRANS']], on='DESCRIPCIÓN ZONA', how='left')
                    
                    res_v['TOTAL_PREPARACION'] = res_v['P_PREP'] * res_v['BULTOS']
                    res_v['TOTAL_TRANSPORTE'] = res_v['P_TRANS'] * res_v['BULTOS']
                    res_v['SUBTOTAL_NETO'] = res_v['TOTAL_PREPARACION'] + res_v['TOTAL_TRANSPORTE']
                    res_v['IVA_15'] = res_v['SUBTOTAL_NETO'] * 0.15
                    res_v['TOTAL_FINAL'] = res_v['SUBTOTAL_NETO'] + res_v['IVA_15']

                    st.subheader(f"📋 Resumen: {mes_vv}")
                    summary_v = res_v.pivot_table(index='GP', columns='TIPO', values='SUBTOTAL_NETO', aggfunc='sum').fillna(0)
                    for col in ['MM', 'MP']:
                        if col not in summary_v.columns: summary_v[col] = 0.0
                    summary_v['SUBTOTAL'] = summary_v['MM'] + summary_v['MP']
                    summary_v['IVA 15%'] = summary_v['SUBTOTAL'] * 0.15
                    summary_v['TOTAL GENERAL'] = summary_v['SUBTOTAL'] + summary_v['IVA 15%']
                    summary_vf = pd.concat([summary_v.reset_index(), pd.DataFrame([{'GP': '--- TOTALES ---', **summary_v.sum()}])], ignore_index=True)
                    st.table(summary_vf.style.format(subset=summary_vf.columns[1:], formatter="{:,.2f}"))
                    st.download_button("📥 Descargar Resumen VV", format_excel(summary_vf), f"Resumen_VV_{mes_vv}.xlsx")
                    st.session_state['res_vv'] = res_v

    with tabs_v[1]: # DETALLE VV
        if 'res_vv' in st.session_state:
            dv = st.session_state['res_vv']
            kv1, kv2, kv3, kv4 = st.columns(4)
            kv1.metric("Bultos", f"{dv['BULTOS'].sum():,.0f}"); kv2.metric("Prep.", f"$ {dv['TOTAL_PREPARACION'].sum():,.2f}"); kv3.metric("Trans.", f"$ {dv['TOTAL_TRANSPORTE'].sum():,.2f}"); kv4.metric("Total Final", f"$ {dv['TOTAL_FINAL'].sum():,.2f}")
            st.dataframe(dv, use_container_width=True)

    with tabs_v[2]: # CONFIG VV
        cva, cvb = st.columns(2)
        with cva:
            ugv = st.file_uploader("Cargar GP VV", key="ugvv")
            if ugv: leer_archivo(ugv).to_csv(PATH_GP_VV, index=False); st.success("GP VV OK")
        with cvb:
            ucv = st.file_uploader("Cargar Costos VV", key="ucvv")
            if ucv: leer_archivo(ucv).to_csv(PATH_COSTOS_VV, index=False); st.success("Costos VV OK")
