import streamlit as st
import pandas as pd
import os
import io
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Laboratorios Bagó - Conciliación Logística", layout="wide", page_icon="🧪")

# --- DISEÑO ESTÉTICO UI/UX PRO (RESTAURACIÓN TOTAL) ---
MAGENTA_BAGO = "#C7006A" 
MAGENTA_OSCURO = "#8A004A"

st.markdown(f"""
    <style>
    header, [data-testid="stHeader"] {{ display: none !important; }}
    .main {{ background: radial-gradient(circle at top right, #ffffff, #f0f2f6); }}
    .welcome-text {{ text-align: center; color: #888; font-size: 1.2rem; font-weight: 300; letter-spacing: 2px; text-transform: uppercase; margin-bottom: -10px; }}
    .main-title {{ color: {MAGENTA_BAGO}; font-size: 5rem !important; font-weight: 900 !important; text-align: center; margin-top: 0px; letter-spacing: -4px; filter: drop-shadow(0px 10px 15px rgba(199, 0, 106, 0.2)); line-height: 1; }}
    
    /* Botones Grandes del Menú Principal */
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
    
    /* Estilo para Botones de Descarga y Navegación Pequeños */
    .stDownloadButton button, .nav-btn button {{
        height: 45px !important;
        width: auto !important;
        font-size: 0.9rem !important;
        padding: 0 20px !important;
        border-radius: 12px !important;
        background-color: white !important;
        border: 1px solid #ddd !important;
        box-shadow: none !important;
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

# --- UTILITARIOS ---
def cargar_maestro(path): return pd.read_csv(path) if os.path.exists(path) else None
def leer_archivo(archivo):
    try:
        if archivo.name.lower().endswith(('.xlsx', '.xls')): return pd.read_excel(archivo)
        return pd.read_csv(archivo, encoding='latin-1')
    except: return None
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultados')
    return output.getvalue()

# Lógica de procesamiento (Blindada para multiplicaciones exactas)
def procesar_logica(df_carga, m_gp, m_costos):
    df_carga.columns = df_carga.columns.str.strip().str.upper()
    df_carga['CODIGO'] = df_carga['CODIGO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    df_carga['BULTOS'] = pd.to_numeric(df_carga['BULTOS'], errors='coerce').fillna(0)
    df_carga['DESCRIPCIÓN ZONA'] = df_carga['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
    
    m_gp.columns = m_gp.columns.str.strip().str.upper()
    id_col = [c for c in m_gp.columns if 'CODIGO' in c][0]
    m_gp[id_col] = m_gp[id_col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    
    m_costos.columns = m_costos.columns.str.strip().str.upper()
    rn = {c: "P_PREP" for c in m_costos.columns if "PREP" in c}
    rn.update({c: "P_TRANS" for c in m_costos.columns if "TRANS" in c})
    rn.update({c: "DESCRIPCIÓN ZONA" for c in m_costos.columns if "ZONA" in c})
    m_costos = m_costos.rename(columns=rn)
    m_costos['P_PREP'] = pd.to_numeric(m_costos['P_PREP'], errors='coerce').fillna(0)
    m_costos['P_TRANS'] = pd.to_numeric(m_costos['P_TRANS'], errors='coerce').fillna(0)

    res = pd.merge(df_carga, m_gp[[id_col, 'GP', 'TIPO']], left_on='CODIGO', right_on=id_col, how='left')
    res = pd.merge(res, m_costos[['DESCRIPCIÓN ZONA', 'P_PREP', 'P_TRANS']], on='DESCRIPCIÓN ZONA', how='left')
    
    res['TOTAL_PREPARACION'] = res['P_PREP'].fillna(0) * res['BULTOS']
    res['TOTAL_TRANSPORTE'] = res['P_TRANS'].fillna(0) * res['BULTOS']
    res['SUBTOTAL_NETO'] = res['TOTAL_PREPARACION'] + res['TOTAL_TRANSPORTE']
    res['IVA_15'] = res['SUBTOTAL_NETO'] * 0.15
    res['TOTAL_FINAL'] = res['SUBTOTAL_NETO'] + res['IVA_15']
    return res

# ---------------------------------------------------------
# PANTALLA 1: INICIO
# ---------------------------------------------------------
if st.session_state['pagina_actual'] == "inicio":
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<p class="welcome-text">Bienvenido al Sistema de</p>', unsafe_allow_html=True)
    st.markdown('<p class="main-title">Laboratorios Bagó</p>', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:#555; font-weight:300; margin-bottom:60px;'>CONCILIACIÓN LOGÍSTICA</h3>", unsafe_allow_html=True)
    
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
    st.sidebar.markdown(f"### Módulo Extra Ciclos")
    if st.sidebar.button("⬅️ Menú Principal"): st.session_state['pagina_actual'] = "inicio"; st.rerun()
    
    m_gp = cargar_maestro(PATH_GP); m_costos = cargar_maestro(PATH_COSTOS)
    tabs = st.tabs(["🚀 Liquidación", "🔍 Detalle Actual", "⚙️ Configurar Maestros"])

    with tabs[0]:
        if m_gp is not None and m_costos is not None:
            c1, c2 = st.columns([1, 2])
            with c1: mes_sel = st.selectbox("Mes", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
            with c2: archivo = st.file_uploader("Cargar Archivo Mensual", key="u_ex")
            
            if archivo:
                res = procesar_logica(leer_archivo(archivo), m_gp, m_costos)
                st.subheader(f"📋 Resumen: {mes_sel}")
                pivot = res.pivot_table(index='GP', columns='TIPO', values='SUBTOTAL_NETO', aggfunc='sum').fillna(0)
                for c in ['MM','MP']: 
                    if c not in pivot.columns: pivot[c] = 0.0
                pivot['SUBTOTAL'] = pivot['MM'] + pivot['MP']
                pivot['IVA 15%'] = pivot['SUBTOTAL'] * 0.15
                pivot['TOTAL'] = pivot['SUBTOTAL'] + pivot['IVA 15%']
                st.table(pivot.style.format("{:,.2f}"))
                st.download_button("📥 Descargar Resumen", to_excel(pivot), f"Resumen_Extra_{mes_sel}.xlsx")
                st.session_state['res_ex'] = res
        else: st.warning("Por favor, cargue los maestros en la pestaña Configurar.")

    with tabs[1]:
        if 'res_ex' in st.session_state:
            d = st.session_state['res_ex']
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Bultos", f"{d['BULTOS'].sum():,.0f}")
            k2.metric("Prep.", f"$ {d['TOTAL_PREPARACION'].sum():,.2f}")
            k3.metric("Trans.", f"$ {d['TOTAL_TRANSPORTE'].sum():,.2f}")
            k4.metric("Total Final", f"$ {d['TOTAL_FINAL'].sum():,.2f}")
            st.divider()
            st.dataframe(d, use_container_width=True)

    with tabs[2]:
        st.header("⚙️ Maestros Extra Ciclos")
        c1, c2 = st.columns(2)
        with c1: 
            u1 = st.file_uploader("Subir GP", key="ug1")
            if u1: leer_archivo(u1).to_csv(PATH_GP, index=False); st.success("Guardado")
        with c2:
            u2 = st.file_uploader("Subir Costos", key="uc1")
            if u2: leer_archivo(u2).to_csv(PATH_COSTOS, index=False); st.success("Guardado")

# ---------------------------------------------------------
# PANTALLA 3: VV / REPROGRAMA
# ---------------------------------------------------------
elif st.session_state['pagina_actual'] == "reprograma":
    st.sidebar.markdown(f"### Módulo VV / Reprograma")
    if st.sidebar.button("⬅️ Menú Principal"): st.session_state['pagina_actual'] = "inicio"; st.rerun()
    
    m_gp_v = cargar_maestro(PATH_GP_VV); m_cost_v = cargar_maestro(PATH_COSTOS_VV)
    tabs_v = st.tabs(["🚀 Liquidación VV", "🔍 Detalle VV", "⚙️ Maestros VV"])

    with tabs_v[0]:
        if m_gp_v is not None and m_cost_v is not None:
            c1v, c2v = st.columns([1, 2])
            with c1v: mes_vv = st.selectbox("Mes VV", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], key="mesvv")
            with c2v: arch_vv = st.file_uploader("Cargar Archivo VV", key="u_vv")
            
            if arch_vv:
                res_v = procesar_logica(leer_archivo(arch_vv), m_gp_v, m_cost_v)
                st.subheader(f"📊 Resumen VV: {mes_vv}")
                sum_v = res_v.groupby('GP')['SUBTOTAL_NETO'].sum().reset_index().rename(columns={'SUBTOTAL_NETO':'SUBTOTAL'})
                sum_v['IVA 15%'] = sum_v['SUBTOTAL'] * 0.15
                sum_v['TOTAL'] = sum_v['SUBTOTAL'] + sum_v['IVA 15%']
                st.table(sum_v.style.format(subset=['SUBTOTAL','IVA 15%','TOTAL'], formatter="{:,.2f}"))
                st.download_button("📥 Descargar Resumen VV", to_excel(sum_v), f"Resumen_VV_{mes_vv}.xlsx")
                st.session_state['res_vv'] = res_v
        else: st.warning("Cargue maestros de VV.")

    with tabs_v[1]:
        if 'res_vv' in st.session_state:
            dv = st.session_state['res_vv']
            kv1, kv2, kv3, kv4 = st.columns(4)
            kv1.metric("Bultos", f"{dv['BULTOS'].sum():,.0f}")
            kv2.metric("Prep.", f"$ {dv['TOTAL_PREPARACION'].sum():,.2f}")
            kv3.metric("Trans.", f"$ {dv['TOTAL_TRANSPORTE'].sum():,.2f}")
            kv4.metric("Total Final", f"$ {dv['TOTAL_FINAL'].sum():,.2f}")
            st.divider()
            st.dataframe(dv, use_container_width=True)

    with tabs_v[2]:
        st.header("⚙️ Maestros VV")
        c3, c4 = st.columns(2)
        with c3:
            u3 = st.file_uploader("GP VV", key="ug2")
            if u3: leer_archivo(u3).to_csv(PATH_GP_VV, index=False); st.success("Guardado")
        with c4:
            u4 = st.file_uploader("Costos VV", key="uc2")
            if u4: leer_archivo(u4).to_csv(PATH_COSTOS_VV, index=False); st.success("Guardado")
