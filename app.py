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

# --- FUNCIONES DE LIMPIEZA ---
def limpiar_maestro_serie(serie):
    return serie.astype(str).str.strip().str.upper().str.replace(r'\.0$', '', regex=True)

# --- PANTALLA INICIO ---
if st.session_state['pagina_actual'] == "inicio":
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<p class="welcome-text">Bienvenido,</p>', unsafe_allow_html=True)
    st.markdown('<p class="main-title">Laboratorios Bagó</p>', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:#555; font-weight:300; margin-bottom:60px;'>SISTEMA DE CONCILIACIÓN </h3>", unsafe_allow_html=True)
    
    _, col_l, col_r, _ = st.columns([6.5, 1.8, 1.8, 6.5])
    with col_l:
        if st.button("\n\n EXTRA CICLOS"):
            st.session_state['pagina_actual'] = "sistema" 
            st.rerun()
    with col_r:
        if st.button("\n REPROGRAMA"):
            st.toast("Módulo en desarrollo...", icon="⚠️")

# --- PANTALLA SISTEMA ---
elif st.session_state['pagina_actual'] == "sistema":
    if st.sidebar.button("⬅️ Volver al Menú Principal"):
        st.session_state['pagina_actual'] = "inicio"
        st.rerun()

    PATH_GP = "master_gp.csv"
    PATH_COSTOS = "master_costos.csv"

    st.title("📊 Control de Liquidación Logística")
    tabs = st.tabs(["🚀 Liquidación Mensual", "🔍 Detalle Actual", "⚙️ Configurar Maestros"])

    # CARGA DE MAESTROS CON ELIMINACIÓN DE DUPLICADOS DE RAÍZ
    m_gp = pd.read_csv(PATH_GP) if os.path.exists(PATH_GP) else None
    m_costos = pd.read_csv(PATH_COSTOS) if os.path.exists(PATH_COSTOS) else None

    with tabs[0]: 
        if m_gp is None or m_costos is None: 
            st.warning("⚠️ Cargue los maestros en la pestaña Configurar.")
        else:
            c1, c2 = st.columns([1, 2])
            with c1: mes_sel = st.selectbox("Mes", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
            with c2: archivo = st.file_uploader("Subir Carga Mensual", type=['xlsx', 'xls', 'csv'])

            if archivo:
                df_raw = pd.read_excel(archivo) if archivo.name.endswith(('.xlsx', '.xls')) else pd.read_csv(archivo, encoding='latin-1')
                if df_raw is not None:
                    # 1. LIMPIEZA DE CARGA Y CONSOLIDACIÓN PREVIA (Evita duplicados en la entrada)
                    df_raw.columns = df_raw.columns.str.strip().str.upper()
                    df_raw['CODIGO'] = limpiar_maestro_serie(df_raw['CODIGO'])
                    df_raw['DESCRIPCIÓN ZONA'] = limpiar_maestro_serie(df_raw['DESCRIPCIÓN ZONA'])
                    df_raw['BULTOS'] = pd.to_numeric(df_raw['BULTOS'], errors='coerce').fillna(0)
                    
                    # Agrupamos bultos antes del cruce
                    df_c = df_raw.groupby(['CODIGO', 'DESCRIPCIÓN ZONA'], as_index=False)['BULTOS'].sum()

                    # 2. LIMPIEZA DE MAESTRO GP (Asegura 1 registro por código)
                    m_gp.columns = m_gp.columns.str.strip().str.upper()
                    col_id_gp = [c for c in m_gp.columns if 'CODIGO' in c][0]
                    m_gp[col_id_gp] = limpiar_maestro_serie(m_gp[col_id_gp])
                    m_gp_clean = m_gp.drop_duplicates(subset=[col_id_gp])

                    # 3. LIMPIEZA DE MAESTRO COSTOS (Asegura 1 registro por zona)
                    m_costos.columns = m_costos.columns.str.strip().str.upper()
                    m_costos['DESCRIPCIÓN ZONA'] = limpiar_maestro_serie(m_costos['DESCRIPCIÓN ZONA'])
                    ren = {c: "P_PREP" for c in m_costos.columns if "PREP" in c}
                    ren.update({c: "P_TRANS" for c in m_costos.columns if "TRANS" in c})
                    m_costos_clean = m_costos.rename(columns=ren).drop_duplicates(subset=['DESCRIPCIÓN ZONA'])

                    # 4. CRUCE (MERGE) - Ahora es seguro porque no hay duplicados en maestros
                    res = pd.merge(df_c, m_gp_clean[[col_id_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_id_gp, how='left')
                    res = pd.merge(res, m_costos_clean[['DESCRIPCIÓN ZONA', 'P_PREP', 'P_TRANS']], on='DESCRIPCIÓN ZONA', how='left')

                    # 5. VERIFICACIÓN DE INTEGRIDAD
                    sin_gp = res[res['GP'].isna()]['CODIGO'].unique()
                    sin_tar = res[res['P_PREP'].isna()]['DESCRIPCIÓN ZONA'].unique()

                    if len(sin_gp) > 0 or len(sin_tar) > 0:
                        st.error("🛑 BLOQUEO: Hay datos en el Excel que no existen en los Maestros.")
                        if len(sin_gp) > 0: st.warning(f"Códigos sin GP: {list(sin_gp)}")
                        if len(sin_tar) > 0: st.warning(f"Zonas sin Tarifa: {list(sin_tar)}")
                    else:
                        # 6. CÁLCULOS
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
                        
                        st.session_state['res_actual'] = res

    with tabs[1]: # DETALLE ACTUAL (KPIs)
        if 'res_actual' in st.session_state:
            df_v = st.session_state['res_actual']
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Bultos", f"{df_v['BULTOS'].sum():,.0f}")
            k2.metric("Preparación", f"$ {df_v['TOTAL_PREPARACION'].sum():,.2f}")
            k3.metric("Transporte", f"$ {df_v['TOTAL_TRANSPORTE'].sum():,.2f}")
            k4.metric("Total Final", f"$ {df_v['TOTAL_FINAL'].sum():,.2f}")
            st.divider()
            st.dataframe(df_v, use_container_width=True)

    with tabs[2]: # CONFIG
        st.header("⚙️ Maestros")
        ca, cb = st.columns(2)
        with ca:
            ug = st.file_uploader("Cargar GP", type=['csv','xlsx'])
            if ug: d = pd.read_excel(ug) if ug.name.endswith(('.xlsx', '.xls')) else pd.read_csv(ug)
            d.to_csv(PATH_GP, index=False); st.success("GP OK")
        with cb:
            uc = st.file_uploader("Cargar Costos", type=['csv','xlsx'])
            if uc: d = pd.read_excel(uc) if uc.name.endswith(('.xlsx', '.xls')) else pd.read_csv(uc)
            d.to_csv(PATH_COSTOS, index=False); st.success("Costos OK")
