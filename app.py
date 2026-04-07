import streamlit as st
import pandas as pd
import os
import io
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
    
    div.stButton > button {{ 
        background: rgba(250, 255, 255, 0.7) !important; 
        backdrop-filter: blur(15px) !important; 
        color: #333 !important; 
        border: 1px solid rgba(200, 200, 200, 0.3) !important; 
        border-radius: 20px !important; 
        height: 100px !important; 
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

# PANTALLA INICIO
if st.session_state['pagina_actual'] == "inicio":
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<p class="main-title">Laboratorios Bagó</p>', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:#555;'>SISTEMA DE CONCILIACIÓN</h3>", unsafe_allow_html=True)
    
    _, col_l, col_r, _ = st.columns([6.5, 1.8, 1.8, 6.5])
    with col_l:
        if st.button("\n\n EXTRA CICLOS"):
            st.session_state['pagina_actual'] = "sistema" 
            st.rerun()

# PANTALLA SISTEMA
elif st.session_state['pagina_actual'] == "sistema":
    if st.sidebar.button("⬅️ Volver"):
        st.session_state['pagina_actual'] = "inicio"
        st.rerun()

    PATH_GP = "master_gp.csv"
    PATH_COSTOS = "master_costos.csv"

    def limpiar_str(serie):
        return serie.astype(str).str.strip().str.upper().str.replace(r'\.0$', '', regex=True)

    tabs = st.tabs(["🚀 Liquidación", "🔍 Detalle", "⚙️ Configurar"])

    m_gp = pd.read_csv(PATH_GP) if os.path.exists(PATH_GP) else None
    m_costos = pd.read_csv(PATH_COSTOS) if os.path.exists(PATH_COSTOS) else None

    with tabs[0]:
        if m_gp is None or m_costos is None:
            st.warning("Cargue los maestros en Configurar.")
        else:
            archivo = st.file_uploader("Subir Carga Mensual", type=['xlsx', 'csv'])
            if archivo:
                df_raw = pd.read_excel(archivo) if archivo.name.endswith('.xlsx') else pd.read_csv(archivo, encoding='latin-1')
                
                # 1. EVITAR DUPLICADOS EN CARGA
                df_raw.columns = df_raw.columns.str.strip().str.upper()
                df_raw['CODIGO'] = limpiar_str(df_raw['CODIGO'])
                df_raw['DESCRIPCIÓN ZONA'] = limpiar_str(df_raw['DESCRIPCIÓN ZONA'])
                df_c = df_raw.groupby(['CODIGO', 'DESCRIPCIÓN ZONA'], as_index=False)['BULTOS'].sum()

                # 2. EVITAR DUPLICADOS EN MAESTROS
                m_gp.columns = m_gp.columns.str.strip().str.upper()
                cid = [c for c in m_gp.columns if 'CODIGO' in c][0]
                m_gp[cid] = limpiar_str(m_gp[cid])
                m_gp_clean = m_gp.drop_duplicates(subset=[cid])

                m_costos.columns = m_costos.columns.str.strip().str.upper()
                m_costos['DESCRIPCIÓN ZONA'] = limpiar_str(m_costos['DESCRIPCIÓN ZONA'])
                ren = {c: "P_PREP" for c in m_costos.columns if "PREP" in c}
                ren.update({c: "P_TRANS" for c in m_costos.columns if "TRANS" in c})
                m_costos_clean = m_costos.rename(columns=ren).drop_duplicates(subset=['DESCRIPCIÓN ZONA'])

                # 3. CRUCE Y VALIDACIÓN
                res = pd.merge(df_c, m_gp_clean[[cid, 'GP', 'TIPO']], left_on='CODIGO', right_on=cid, how='left')
                res = pd.merge(res, m_costos_clean[['DESCRIPCIÓN ZONA', 'P_PREP', 'P_TRANS']], on='DESCRIPCIÓN ZONA', how='left')

                if res['GP'].isna().any() or res['P_PREP'].isna().any():
                    st.error("Datos faltantes en maestros. Revise códigos y zonas.")
                    st.write("Faltan GP:", res[res['GP'].isna()]['CODIGO'].unique())
                    st.write("Faltan Tarifas:", res[res['P_PREP'].isna()]['DESCRIPCIÓN ZONA'].unique())
                else:
                    res['SUBTOTAL'] = (res['P_PREP'] + res['P_TRANS']) * res['BULTOS']
                    res['TOTAL'] = res['SUBTOTAL'] * 1.15
                    st.success("Procesado sin duplicados.")
                    st.session_state['res'] = res
                    st.table(res.pivot_table(index='GP', columns='TIPO', values='SUBTOTAL', aggfunc='sum').fillna(0))

    with tabs[1]:
        if 'res' in st.session_state:
            st.dataframe(st.session_state['res'], use_container_width=True)

    with tabs[2]:
        st.header("Configuración")
        u1 = st.file_uploader("Actualizar Maestro GP", type=['xlsx', 'csv'])
        if u1:
            d_gp = pd.read_excel(u1) if u1.name.endswith('.xlsx') else pd.read_csv(u1)
            d_gp.to_csv(PATH_GP, index=False)
            st.success("GP actualizado.")
            
        u2 = st.file_uploader("Actualizar Maestro Costos", type=['xlsx', 'csv'])
        if u2:
            d_costos = pd.read_excel(u2) if u2.name.endswith('.xlsx') else pd.read_csv(u2)
            d_costos.to_csv(PATH_COSTOS, index=False)
            st.success("Costos actualizados.")
