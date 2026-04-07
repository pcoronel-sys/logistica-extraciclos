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

def clean_val(val):
    return str(val).strip().upper().replace(".0", "")

# --- PANTALLA INICIO ---
if st.session_state['pagina_actual'] == "inicio":
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<p class="welcome-text">Bienvenido,</p>', unsafe_allow_html=True)
    st.markdown('<p class="main-title">Laboratorios Bagó</p>', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:#555; font-weight:300; margin-bottom:60px;'>CONCILIACIÓN DE EXTRA CICLOS </h3>", unsafe_allow_html=True)
    
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
    tabs = st.tabs(["🚀 Proceso de Liquidación", "⚙️ Configurar Maestros"])

    m_gp_raw = pd.read_csv(PATH_GP) if os.path.exists(PATH_GP) else None
    m_costos_raw = pd.read_csv(PATH_COSTOS) if os.path.exists(PATH_COSTOS) else None

    with tabs[0]: 
        if m_gp_raw is None or m_costos_raw is None: 
            st.warning("⚠️ Primero cargue los maestros en la pestaña Configurar.")
        else:
            c1, c2 = st.columns([1, 2])
            with c1: mes_sel = st.selectbox("Mes de Proceso", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
            with c2: archivo = st.file_uploader("Subir Archivo de Carga Mensual", type=['xlsx', 'xls', 'csv'])

            if archivo:
                df_c_raw = pd.read_excel(archivo) if archivo.name.endswith(('.xlsx', '.xls')) else pd.read_csv(archivo, encoding='latin-1')
                if df_c_raw is not None:
                    # 1. Limpieza de Carga
                    df_c_raw.columns = df_c_raw.columns.str.strip().str.upper()
                    df_c_raw['CODIGO'] = df_c_raw['CODIGO'].apply(clean_val)
                    df_c_raw['DESCRIPCIÓN ZONA'] = df_c_raw['DESCRIPCIÓN ZONA'].apply(clean_val)
                    df_c_raw['BULTOS'] = pd.to_numeric(df_c_raw['BULTOS'], errors='coerce').fillna(0)
                    df_c = df_c_raw.groupby(['CODIGO', 'DESCRIPCIÓN ZONA'], as_index=False)['BULTOS'].sum()

                    # 2. Diccionarios de Maestros (Cero Duplicados)
                    m_gp_raw.columns = m_gp_raw.columns.str.strip().str.upper()
                    col_id_gp = [c for c in m_gp_raw.columns if 'CODIGO' in c][0]
                    m_gp_raw[col_id_gp] = m_gp_raw[col_id_gp].apply(clean_val)
                    dict_gp = m_gp_raw.drop_duplicates(col_id_gp).set_index(col_id_gp)['GP'].to_dict()
                    dict_tipo = m_gp_raw.drop_duplicates(col_id_gp).set_index(col_id_gp)['TIPO'].to_dict()

                    m_costos_raw.columns = m_costos_raw.columns.str.strip().str.upper()
                    m_costos_raw['DESCRIPCIÓN ZONA'] = m_costos_raw['DESCRIPCIÓN ZONA'].apply(clean_val)
                    ren = {c: "P_PREP" for c in m_costos_raw.columns if "PREP" in c}
                    ren.update({c: "P_TRANS" for c in m_costos_raw.columns if "TRANS" in c})
                    m_costos_ren = m_costos_raw.rename(columns=ren).drop_duplicates('DESCRIPCIÓN ZONA')
                    dict_prep = m_costos_ren.set_index('DESCRIPCIÓN ZONA')['P_PREP'].to_dict()
                    dict_trans = m_costos_ren.set_index('DESCRIPCIÓN ZONA')['P_TRANS'].to_dict()

                    # 3. Mapeado de Datos
                    res = df_c.copy()
                    res['GP'] = res['CODIGO'].map(dict_gp)
                    res['TIPO'] = res['CODIGO'].map(dict_tipo)
                    res['P_PREP'] = res['DESCRIPCIÓN ZONA'].map(dict_prep)
                    res['P_TRANS'] = res['DESCRIPCIÓN ZONA'].map(dict_trans)

                    # 4. Validación de Errores Críticos
                    sin_gp = res[res['GP'].isna()]['CODIGO'].unique()
                    sin_costo = res[res['P_PREP'].isna()]['DESCRIPCIÓN ZONA'].unique()

                    if len(sin_gp) > 0 or len(sin_costo) > 0:
                        st.error("🛑 BLOQUEO: Faltan registros en los Maestros.")
                        if len(sin_gp) > 0: st.warning(f"❌ Códigos sin GP en Maestro: {list(sin_gp)}")
                        if len(sin_costo) > 0: st.warning(f"❌ Zonas sin Tarifa en Maestro: {list(sin_costo)}")
                    else:
                        # 5. Cálculos Finales
                        res['TOTAL_PREPARACION'] = res['P_PREP'] * res['BULTOS']
                        res['TOTAL_TRANSPORTE'] = res['P_TRANS'] * res['BULTOS']
                        res['SUBTOTAL_NETO'] = res['TOTAL_PREPARACION'] + res['TOTAL_TRANSPORTE']
                        res['IVA_15'] = res['SUBTOTAL_NETO'] * 0.15
                        res['TOTAL_FINAL'] = res['SUBTOTAL_NETO'] + res['IVA_15']

                        # KPIs Superiores
                        k1, k2, k3, k4 = st.columns(4)
                        k1.metric("Bultos Totales", f"{res['BULTOS'].sum():,.0f}")
                        k2.metric("Preparación", f"$ {res['TOTAL_PREPARACION'].sum():,.2f}")
                        k3.metric("Transporte", f"$ {res['TOTAL_TRANSPORTE'].sum():,.2f}")
                        k4.metric("Total Final", f"$ {res['TOTAL_FINAL'].sum():,.2f}")

                        st.divider()

                        # Tabla de Resumen
                        st.subheader(f"📋 Resumen de Liquidación - {mes_sel}")
                        summary = res.pivot_table(index='GP', columns='TIPO', values='SUBTOTAL_NETO', aggfunc='sum').fillna(0)
                        for col in ['MM', 'MP']: 
                            if col not in summary.columns: summary[col] = 0.0
                        
                        summary['SUBTOTAL'] = summary['MM'] + summary['MP']
                        summary['IVA 15%'] = summary['SUBTOTAL'] * 0.15
                        summary['TOTAL FINAL'] = summary['SUBTOTAL'] + summary['IVA 15%']
                        
                        summary_f = pd.concat([summary.reset_index(), pd.DataFrame([{'GP': '--- TOTALES ---', **summary.sum()}])], ignore_index=True)
                        st.table(summary_f.style.format(subset=summary_f.columns[1:], formatter="{:,.2f}"))

                        # Descargas
                        d_col1, d_col2 = st.columns(2)
                        with d_col1:
                            out_sum = io.BytesIO()
                            with pd.ExcelWriter(out_sum, engine='openpyxl') as wr: summary_f.to_excel(wr, index=False)
                            st.download_button("📥 Descargar Resumen (Excel)", out_sum.getvalue(), f"Resumen_Bago_{mes_sel}.xlsx")
                        with d_col2:
                            out_det = io.BytesIO()
                            with pd.ExcelWriter(out_det, engine='openpyxl') as wr: res.to_excel(wr, index=False)
                            st.download_button("📥 Descargar Detalle Completo (Excel)", out_det.getvalue(), f"Detalle_Bago_{mes_sel}.xlsx")

    with tabs[1]: # CONFIGURACIÓN DE MAESTROS
        st.header("⚙️ Gestión de Maestros")
        ca, cb = st.columns(2)
        with ca:
            ug = st.file_uploader("Cargar Maestro GP (Productos)", type=['csv','xlsx'])
            if ug:
                d = pd.read_excel(ug) if ug.name.endswith(('.xlsx', '.xls')) else pd.read_csv(ug)
                d.to_csv(PATH_GP, index=False); st.success("Maestro GP Actualizado.")
        with cb:
            uc = st.file_uploader("Cargar Maestro Costos (Tarifas)", type=['csv','xlsx'])
            if uc:
                d = pd.read_excel(uc) if uc.name.endswith(('.xlsx', '.xls')) else pd.read_csv(uc)
                d.to_csv(PATH_COSTOS, index=False); st.success("Maestro Costos Actualizado.")
