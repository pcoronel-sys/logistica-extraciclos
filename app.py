import streamlit as st
import pandas as pd
import os
import io
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Laboratorios Bagó - Conciliación", layout="wide", page_icon="🧪")

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

# --- RUTAS DE ARCHIVOS ---
PATH_GP = "master_gp.csv"
PATH_COSTOS = "master_costos.csv"
PATH_GP_VV = "master_gp_vv.csv"      # Maestro GP exclusivo para VV
PATH_COSTOS_VV = "master_costos_vv.csv" # Maestro Costos exclusivo para VV
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
# PANTALLA 2: EXTRA CICLOS (CÓDIGO ORIGINAL INTACTO)
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
            st.warning("⚠️ Cargue los maestros en la pestaña Configurar.")
        else:
            c1, c2 = st.columns([1, 2])
            with c1: mes_sel = st.selectbox("Mes", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
            with c2: archivo = st.file_uploader("Subir Carga Mensual", type=['xlsx', 'xls', 'csv'], key="up_exc")

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
                        for col in ['MM', 'MP']:
                            if col not in summary.columns: summary[col] = 0.0
                        summary['SUBTOTAL'] = summary['MM'] + summary['MP']
                        summary['IVA 15%'] = summary['SUBTOTAL'] * 0.15
                        summary['TOTAL GENERAL'] = summary['SUBTOTAL'] + summary['IVA 15%']
                        st.table(summary.style.format("{:,.2f}"))
                        st.session_state['res_actual'] = res

    with tabs[2]: # CONFIGURACIÓN EXTRA CICLOS
        st.header("⚙️ Maestros Extra Ciclos")
        ca, cb = st.columns(2)
        with ca:
            if st.file_uploader("Cargar Maestro GP", type=['csv','xlsx'], key="up_gp_exc"):
                d = leer_archivo(st.session_state.up_gp_exc); d.to_csv(PATH_GP, index=False); st.success("GP OK")
        with cb:
            if st.file_uploader("Cargar Maestro Costos", type=['csv','xlsx'], key="up_cost_exc"):
                d = leer_archivo(st.session_state.up_cost_exc); d.to_csv(PATH_COSTOS, index=False); st.success("Costos OK")

# ---------------------------------------------------------
# PANTALLA 3: MÓDULO VV / REPROGRAMA (INDEPENDIENTE)
# ---------------------------------------------------------
elif st.session_state['pagina_actual'] == "reprograma":
    if st.sidebar.button("⬅️ Volver al Menú Principal"):
        st.session_state['pagina_actual'] = "inicio"
        st.rerun()

    st.markdown(f'<p class="main-title" style="font-size: 3.5rem !important;">Módulo VV / Reprograma</p>', unsafe_allow_html=True)
    
    # Cargamos maestros específicos de VV
    m_gp_vv = cargar_maestro(PATH_GP_VV)
    m_costos_vv = cargar_maestro(PATH_COSTOS_VV)
    
    t_vv = st.tabs(["🚀 Liquidación VV", "🔍 Detalle VV", "⚙️ Configurar Maestros VV"])

    with t_vv[0]: # LIQUIDACIÓN VV
        if m_gp_vv is None or m_costos_vv is None:
            st.warning("⚠️ Por favor, cargue los maestros GP y Costos específicos para VV en la pestaña Configurar Maestros VV.")
        else:
            c1_v, c2_v = st.columns([1, 2])
            with c1_v: mes_vv = st.selectbox("Mes de Proceso VV", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], key="sel_mes_vv")
            with c2_v: arch_vv = st.file_uploader("Subir Carga Mensual VV", type=['xlsx', 'xls', 'csv'], key="up_vv_mensual")

            if arch_vv:
                df_v = leer_archivo(arch_vv)
                if df_v is not None:
                    df_v.columns = df_v.columns.str.strip().str.upper()
                    df_v['CODIGO'] = df_v['CODIGO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    df_v['DESCRIPCIÓN ZONA'] = df_v['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                    df_v['BULTOS'] = pd.to_numeric(df_v['BULTOS'], errors='coerce').fillna(0)
                    
                    # Limpieza Maestro GP VV
                    m_gp_vv_c = m_gp_vv.copy()
                    col_id_v = [c for c in m_gp_vv_c.columns if 'CODIGO' in c.upper()][0]
                    m_gp_vv_c[col_id_v] = m_gp_vv_c[col_id_v].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    
                    # Limpieza Maestro Costos VV
                    m_cost_vv_c = m_costos_vv.copy()
                    m_cost_vv_c.columns = m_cost_vv_c.columns.str.strip().str.upper()
                    rn_v = {c: "P_PREP" for c in m_cost_vv_c.columns if "PREP" in c}
                    rn_v.update({c: "P_TRANS" for c in m_cost_vv_c.columns if "TRANS" in c})
                    rn_v.update({c: "DESCRIPCIÓN ZONA" for c in m_cost_vv_c.columns if "ZONA" in c})
                    m_cost_vv_c = m_cost_vv_c.rename(columns=rn_v)
                    
                    # Cruce de datos (Merge)
                    res_vv = pd.merge(df_v, m_gp_vv_c[[col_id_v, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_id_v, how='left')
                    res_vv = pd.merge(res_vv, m_cost_vv_c[['DESCRIPCIÓN ZONA', 'P_PREP', 'P_TRANS']], on='DESCRIPCIÓN ZONA', how='left')
                    
                    # Cálculos
                    res_vv['TOTAL_PREPARACION'] = res_vv['P_PREP'] * res_vv['BULTOS']
                    res_vv['TOTAL_TRANSPORTE'] = res_vv['P_TRANS'] * res_vv['BULTOS']
                    res_vv['SUBTOTAL_NETO'] = res_vv['TOTAL_PREPARACION'] + res_vv['TOTAL_TRANSPORTE']
                    res_vv['IVA_15'] = res_vv['SUBTOTAL_NETO'] * 0.15
                    res_vv['TOTAL_FINAL'] = res_vv['SUBTOTAL_NETO'] + res_vv['IVA_15']

                    st.subheader(f"📊 Resumen VV: {mes_vv}")
                    # Pivot Table para el resumen igual a la otra pestaña
                    sum_vv = res_vv.pivot_table(index='GP', columns='TIPO', values='SUBTOTAL_NETO', aggfunc='sum').fillna(0).reset_index()
                    # Aseguramos que la columna VV exista
                    if 'VV' not in sum_vv.columns: sum_vv['VV'] = 0.0
                    
                    sum_vv['SUBTOTAL'] = sum_vv.iloc[:, 1:].sum(axis=1)
                    sum_vv['IVA 15%'] = sum_vv['SUBTOTAL'] * 0.15
                    sum_vv['TOTAL GENERAL'] = sum_vv['SUBTOTAL'] + sum_vv['IVA 15%']
                    
                    st.table(sum_vv.style.format(subset=sum_vv.columns[1:], formatter="{:,.2f}"))
                    st.session_state['res_vv_final'] = res_vv

    with t_vv[1]: # DETALLE VV
        if 'res_vv_final' in st.session_state:
            st.dataframe(st.session_state['res_vv_final'], use_container_width=True)
        else: st.info("Procese una liquidación en la pestaña anterior para ver el detalle.")

    with t_vv[2]: # CONFIGURAR MAESTROS VV (INDIVIDUAL)
        st.header("⚙️ Configuración de Maestros EXCLUSIVOS VV")
        st.info("Los archivos que suba aquí solo afectarán a los cálculos de la pestaña VV.")
        
        cv1, cv2 = st.columns(2)
        with cv1:
            u_gp_v = st.file_uploader("Cargar Maestro GP (VV)", type=['csv','xlsx'], key="up_gp_v")
            if u_gp_v:
                d = leer_archivo(u_gp_v)
                if d is not None: d.to_csv(PATH_GP_VV, index=False); st.success("Maestro GP VV guardado.")
        
        with cv2:
            u_ct_v = st.file_uploader("Cargar Maestro Costos (VV)", type=['csv','xlsx'], key="up_ct_v")
            if u_ct_v:
                d = leer_archivo(u_ct_v)
                if d is not None: d.to_csv(PATH_COSTOS_VV, index=False); st.success("Maestro Costos VV guardado.")
        
        st.divider()
        if st.button("🗑️ Borrar todos los Maestros VV"):
            for p in [PATH_GP_VV, PATH_COSTOS_VV]:
                if os.path.exists(p): os.remove(p)
            st.rerun()
