import streamlit as st
import pandas as pd
import os
import io
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Laboratorios Bagó - Conciliación Logística", layout="wide", page_icon="🧪")

# --- DISEÑO ESTÉTICO UI/UX PRO (RESTABLECIMIENTO TOTAL) ---
MAGENTA_BAGO = "#C7006A" 
MAGENTA_OSCURO = "#8A004A"

st.markdown(f"""
    <style>
    header, [data-testid="stHeader"] {{ display: none !important; }}
    .main {{ background: radial-gradient(circle at top right, #ffffff, #f0f2f6); }}
    .welcome-text {{ text-align: center; color: #888; font-size: 1.2rem; font-weight: 300; letter-spacing: 2px; text-transform: uppercase; margin-bottom: -10px; }}
    .main-title {{ color: {MAGENTA_BAGO}; font-size: 5rem !important; font-weight: 900 !important; text-align: center; margin-top: 0px; letter-spacing: -4px; filter: drop-shadow(0px 10px 15px rgba(199, 0, 106, 0.2)); line-height: 1; }}
    
    /* Botones de Inicio */
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
    
    /* Botones Secundarios */
    .stDownloadButton button, .nav-btn button {{
        height: 45px !important;
        border-radius: 12px !important;
        background-color: white !important;
        border: 1px solid #ddd !important;
        font-weight: 600 !important;
    }}

    [data-testid="stTable"] thead tr th {{ background-color: #2C3E50 !important; color: white !important; }}
    div[data-testid="stMetric"] {{ background: white !important; border-radius: 20px !important; padding: 20px !important; border-left: 8px solid {MAGENTA_BAGO} !important; box-shadow: 0 10px 20px rgba(0,0,0,0.04) !important; }}
    </style>
    """, unsafe_allow_html=True)

if 'pagina_actual' not in st.session_state:
    st.session_state['pagina_actual'] = "inicio"

# RUTAS
FILES = {
    "ex_gp": "master_gp.csv", "ex_cost": "master_costos.csv",
    "vv_gp": "master_gp_vv.csv", "vv_cost": "master_costos_vv.csv"
}

# --- FUNCIONES ---
def load_csv(path): return pd.read_csv(path) if os.path.exists(path) else None

def read_any(file):
    if file is None: return None
    return pd.read_excel(file) if file.name.endswith(('.xlsx', '.xls')) else pd.read_csv(file, encoding='latin-1')

def get_excel(df):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='openpyxl') as w:
        df.to_excel(w, index=False, sheet_name='Reporte')
    return out.getvalue()

def core_logic(df, m_gp, m_cost):
    # Limpieza de Carga
    df.columns = df.columns.str.strip().str.upper()
    df['CODIGO'] = df['CODIGO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    df['BULTOS'] = pd.to_numeric(df['BULTOS'], errors='coerce').fillna(0)
    df['DESCRIPCIÓN ZONA'] = df['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
    
    # Limpieza Maestros
    m_gp.columns = m_gp.columns.str.strip().str.upper()
    id_gp = [c for c in m_gp.columns if 'CODIGO' in c][0]
    m_gp[id_gp] = m_gp[id_gp].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    
    m_cost.columns = m_cost.columns.str.strip().str.upper()
    rename_map = {c: "P_PREP" for c in m_cost.columns if "PREP" in c}
    rename_map.update({c: "P_TRANS" for c in m_cost.columns if "TRANS" in c})
    rename_map.update({c: "DESCRIPCIÓN ZONA" for c in m_cost.columns if "ZONA" in c})
    m_cost = m_cost.rename(columns=rename_map)
    m_cost['P_PREP'] = pd.to_numeric(m_cost['P_PREP'], errors='coerce').fillna(0)
    m_cost['P_TRANS'] = pd.to_numeric(m_cost['P_TRANS'], errors='coerce').fillna(0)
    
    # Cruce y Cálculo
    res = pd.merge(df, m_gp[[id_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=id_gp, how='left')
    res = pd.merge(res, m_cost[['DESCRIPCIÓN ZONA', 'P_PREP', 'P_TRANS']], on='DESCRIPCIÓN ZONA', how='left')
    
    res['TOTAL_PREPARACION'] = res['P_PREP'].fillna(0) * res['BULTOS']
    res['TOTAL_TRANSPORTE'] = res['P_TRANS'].fillna(0) * res['BULTOS']
    res['SUBTOTAL_NETO'] = res['TOTAL_PREPARACION'] + res['TOTAL_TRANSPORTE']
    res['IVA'] = res['SUBTOTAL_NETO'] * 0.15
    res['TOTAL_GENERAL'] = res['SUBTOTAL_NETO'] + res['IVA']
    return res

# ---------------------------------------------------------
# PANTALLAS
# ---------------------------------------------------------
if st.session_state['pagina_actual'] == "inicio":
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<p class="welcome-text">Gestión Logística</p>', unsafe_allow_html=True)
    st.markdown('<p class="main-title">Laboratorios Bagó</p>', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:#555; font-weight:300; margin-bottom:60px;'>SISTEMA DE CONCILIACIÓN</h3>", unsafe_allow_html=True)
    
    _, col1, col2, _ = st.columns([6, 2, 2, 6])
    with col1:
        if st.button("\n\n EXTRA CICLOS"):
            st.session_state['pagina_actual'] = "ex"; st.rerun()
    with col2:
        if st.button("\n\n VV / REPROGRAMA"):
            st.session_state['pagina_actual'] = "vv"; st.rerun()

elif st.session_state['pagina_actual'] in ["ex", "vv"]:
    mode = st.session_state['pagina_actual']
    if st.sidebar.button("⬅️ Volver al Inicio"):
        st.session_state['pagina_actual'] = "inicio"; st.rerun()
    
    m_gp = load_csv(FILES[f"{mode}_gp"])
    m_ct = load_csv(FILES[f"{mode}_cost"])
    
    t1, t2, t3 = st.tabs(["🚀 Liquidación", "🔍 Detalle Actual", "⚙️ Configuración"])
    
    with t1:
        if m_gp is not None and m_ct is not None:
            archivo = st.file_uploader("Subir Carga", key=f"file_{mode}")
            if archivo:
                res = core_logic(read_any(archivo), m_gp, m_ct)
                st.subheader("📋 Resumen Ejecutivo")
                if mode == "ex":
                    pivot = res.pivot_table(index='GP', columns='TIPO', values='SUBTOTAL_NETO', aggfunc='sum').fillna(0)
                    for c in ['MM','MP']: 
                        if c not in pivot.columns: pivot[c] = 0.0
                    pivot['SUBTOTAL'] = pivot['MM'] + pivot['MP']
                else:
                    pivot = res.groupby('GP')['SUBTOTAL_NETO'].sum().reset_index().rename(columns={'SUBTOTAL_NETO':'SUBTOTAL'})
                
                pivot['IVA 15%'] = pivot['SUBTOTAL'] * 0.15
                pivot['TOTAL GENERAL'] = pivot['SUBTOTAL'] + pivot['IVA 15%']
                st.table(pivot.style.format("{:,.2f}"))
                st.download_button("📥 Descargar Resumen", get_excel(pivot), f"Resumen_{mode}.xlsx")
                st.session_state[f"res_{mode}"] = res
        else: st.warning("Cargue los maestros en la pestaña Configuración.")

    with t2:
        if f"res_{mode}" in st.session_state:
            df_v = st.session_state[f"res_{mode}"]
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Bultos Total", f"{df_v['BULTOS'].sum():,.0f}")
            k2.metric("Preparación", f"$ {df_v['TOTAL_PREPARACION'].sum():,.2f}")
            k3.metric("Transporte", f"$ {df_v['TOTAL_TRANSPORTE'].sum():,.2f}")
            k4.metric("Total Neto", f"$ {df_v['SUBTOTAL_NETO'].sum():,.2f}")
            st.divider()
            st.download_button("📥 Descargar Detalle Completo", get_excel(df_v), f"Detalle_{mode}.xlsx")
            st.dataframe(df_v, use_container_width=True)

    with t3:
        st.subheader("⚙️ Gestión de Maestros")
        c1, c2 = st.columns(2)
        with c1:
            u1 = st.file_uploader("Cargar Maestro GP", key=f"ugp_{mode}")
            if u1: read_any(u1).to_csv(FILES[f"{mode}_gp"], index=False); st.success("GP OK")
        with c2:
            u2 = st.file_uploader("Cargar Maestro Costos", key=f"uct_{mode}")
            if u2: read_any(u2).to_csv(FILES[f"{mode}_cost"], index=False); st.success("Costos OK")
