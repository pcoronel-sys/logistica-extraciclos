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
    
    .stDownloadButton button {{
        height: 45px !important;
        width: auto !important;
        font-size: 1rem !important;
        padding: 0 25px !important;
        border-radius: 12px !important;
        background-color: white !important;
        border: 1px solid #ddd !important;
    }}

    [data-testid="stSidebar"] {{ background-color: white !important; border-right: 1px solid #eee; }}
    [data-testid="stTable"] thead tr th {{ background-color: #2C3E50 !important; color: white !important; font-weight: bold !important; }}
    div[data-testid="stMetric"] {{ background: white !important; border-radius: 20px !important; padding: 20px !important; border-left: 8px solid {MAGENTA_BAGO} !important; box-shadow: 0 10px 20px rgba(0,0,0,0.04) !important; }}
    </style>
    """, unsafe_allow_html=True)

if 'pagina_actual' not in st.session_state:
    st.session_state['pagina_actual'] = "inicio"

PATH_GP = "master_gp.csv"
PATH_COSTOS = "master_costos.csv"
PATH_GP_VV = "master_gp_vv.csv"
PATH_COSTOS_VV = "master_costos_vv.csv"

def cargar_maestro(path): return pd.read_csv(path) if os.path.exists(path) else None
def leer_archivo(archivo):
    try:
        if archivo.name.lower().endswith(('.xlsx', '.xls')): return pd.read_excel(archivo)
        return pd.read_csv(archivo, encoding='latin-1')
    except: return None

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Reporte')
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
    tabs = st.tabs(["🚀 Liquidación Mensual", "🔍 Detalle Actual", "⚙️ Configurar Maestros"])

    with tabs[0]: 
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
                    
                    col_id = [c for c in m_gp.columns if 'CODIGO' in c.upper()][0]
                    m_gp_clean = m_gp.copy(); m_gp_clean[col_id] = m_gp_clean[col_id].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    m_gp_clean = m_gp_clean.drop_duplicates(subset=[col_id])
                    
                    m_ct_c = m_costos.copy(); m_ct_c.columns = m_ct_c.columns.str.strip().str.upper()
                    rn = {c: "P_PREP" for c in m_ct_c.columns if "PREP" in c}; rn.update({c: "P_TRANS" for c in m_ct_c.columns if "TRANS" in c}); rn.update({c: "DESCRIPCIÓN ZONA" for c in m_ct_c.columns if "ZONA" in c})
                    m_ct_c = m_ct_c.rename(columns=rn).drop_duplicates(subset=['DESCRIPCIÓN ZONA'])
                    
                    res = pd.merge(df_c, m_gp_clean[[col_id, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_id, how='left')
                    res = pd.merge(res, m_ct_c[['DESCRIPCIÓN ZONA', 'P_PREP', 'P_TRANS']], on='DESCRIPCIÓN ZONA', how='left')
                    res['TOTAL_PREPARACION'] = res['P_PREP'] * res['BULTOS']
                    res['TOTAL_TRANSPORTE'] = res['P_TRANS'] * res['BULTOS']
                    res['SUBTOTAL_NETO'] = res['TOTAL_PREPARACION'] + res['TOTAL_TRANSPORTE']
                    res['IVA_15%'] = res['SUBTOTAL_NETO'] * 0.15
                    res['TOTAL_FINAL'] = res['SUBTOTAL_NETO'] + res['IVA_15%']

                    st.subheader(f"📋 Resumen Extra Ciclos: {mes_sel}")
                    summary = res.pivot_table(index='GP', columns='TIPO', values='SUBTOTAL_NETO', aggfunc='sum').fillna(0)
                    for col in ['MM', 'MP']:
                        if col not in summary.columns: summary[col] = 0.0
                    summary['SUBTOTAL'] = summary['MM'] + summary['MP']
                    summary['IVA 15%'] = summary['SUBTOTAL'] * 0.15
                    summary['TOTAL GENERAL'] = summary['SUBTOTAL'] + summary['IVA 15%']
                    summary_f = pd.concat([summary.reset_index(), pd.DataFrame([{'GP': '--- TOTALES ---', **summary.sum()}])], ignore_index=True)
                    st.table(summary_f.style.format(subset=summary_f.columns[1:], formatter="{:,.2f}"))
                    st.download_button("📥 Descargar Resumen (Excel)", to_excel(summary_f), f"Resumen_Extra_{mes_sel}.xlsx")
                    st.session_state['res_actual'] = res

    with tabs[1]:
        if 'res_actual' in st.session_state:
            df_v = st.session_state['res_actual']
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Bultos", f"{df_v['BULTOS'].sum():,.0f}"); k2.metric("Prep.", f"$ {df_v['TOTAL_PREPARACION'].sum():,.2f}"); k3.metric("Trans.", f"$ {df_v['TOTAL_TRANSPORTE'].sum():,.2f}"); k4.metric("Total Final", f"$ {df_v['TOTAL_FINAL'].sum():,.2f}")
            st.divider()
            st.download_button("📥 Descargar Detalle (Excel)", to_excel(df_v), "Detalle_ExtraCiclos.xlsx")
            st.dataframe(df_v, use_container_width=True)

    with tabs[2]: 
        st.header("⚙️ Configuración Maestros")
        ca, cb = st.columns(2)
        with ca:
            ug = st.file_uploader("Cargar GP", key="ug_ex")
            if ug: leer_archivo(ug).to_csv(PATH_GP, index=False); st.success("GP OK")
        with cb:
            uc = st.file_uploader("Cargar Costos", key="uc_ex")
            if uc: leer_archivo(uc).to_csv(PATH_COSTOS, index=False); st.success("Costos OK")

# ---------------------------------------------------------
# PANTALLA 3: VV / REPROGRAMA
# ---------------------------------------------------------
elif st.session_state['pagina_actual'] == "reprograma":
    if st.sidebar.button("⬅️ Volver al Menú Principal"):
        st.session_state['pagina_actual'] = "inicio"
        st.rerun()

    st.markdown(f'<p class="main-title" style="font-size: 3.5rem !important;">Módulo VV / Reprograma</p>', unsafe_allow_html=True)
    m_gp_vv = cargar_maestro(PATH_GP_VV)
    m_cost_vv = cargar_maestro(PATH_COSTOS_VV)
    tabs_v = st.tabs(["🚀 Liquidación VV", "🔍 Detalle VV", "⚙️ Configurar Maestros VV"])

    with tabs_v[0]:
        if m_gp_vv is None or m_cost_vv is None:
            st.warning("⚠️ Cargue maestros específicos para VV.")
        else:
            c1v, c2v = st.columns([1, 2])
            with c1v: mes_v = st.selectbox("Mes VV", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], key="mvv")
            with c2v: arch_vv = st.file_uploader("Subir Carga VV", key="avv")

            if arch_vv:
                df_vv = leer_archivo(arch_vv)
                if df_vv is not None:
                    df_vv.columns = df_vv.columns.str.strip().str.upper()
                    df_vv['CODIGO'] = df_vv['CODIGO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    df_vv['DESCRIPCIÓN ZONA'] = df_vv['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                    df_vv['BULTOS'] = pd.to_numeric(df_vv['BULTOS'], errors='coerce').fillna(0)
                    
                    id_v = [c for c in m_gp_vv.columns if 'CODIGO' in c.upper()][0]
                    mgp_v = m_gp_vv.copy(); mgp_v[id_v] = mgp_v[id_v].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    mgp_v = mgp_v.drop_duplicates(subset=[id_v])
                    
                    mct_v = m_cost_vv.copy(); mct_v.columns = mct_v.columns.str.strip().str.upper()
                    rn_v = {c: "P_PREP" for c in mct_v.columns if "PREP" in c}; rn_v.update({c: "P_TRANS" for c in mct_v.columns if "TRANS" in c}); rn_v.update({c: "DESCRIPCIÓN ZONA" for c in mct_v.columns if "ZONA" in c})
                    mct_v = mct_v.rename(columns=rn_v).drop_duplicates(subset=['DESCRIPCIÓN ZONA'])
                    
                    res_vv = pd.merge(df_vv, mgp_v[[id_v, 'GP', 'TIPO']], left_on='CODIGO', right_on=id_v, how='left')
                    res_vv = pd.merge(res_vv, mct_v[['DESCRIPCIÓN ZONA', 'P_PREP', 'P_TRANS']], on='DESCRIPCIÓN ZONA', how='left')
                    
                    res_vv['TOTAL_PREPARACION'] = res_vv['P_PREP'] * res_vv['BULTOS']
                    res_vv['TOTAL_TRANSPORTE'] = res_vv['P_TRANS'] * res_vv['BULTOS']
                    res_vv['SUBTOTAL_NETO'] = res_vv['TOTAL_PREPARACION'] + res_vv['TOTAL_TRANSPORTE']
                    res_vv['IVA_15%'] = res_vv['SUBTOTAL_NETO'] * 0.15
                    res_vv['TOTAL_FINAL'] = res_vv['SUBTOTAL_NETO'] + res_vv['IVA_15%']

                    st.subheader(f"📊 Resumen VV: {mes_v}")
                    sum_v = res_vv.groupby('GP')['SUBTOTAL_NETO'].sum().reset_index().rename(columns={'SUBTOTAL_NETO': 'SUBTOTAL'})
                    sum_v['IVA 15%'] = sum_v['SUBTOTAL'] * 0.15
                    sum_v['TOTAL GENERAL'] = sum_v['SUBTOTAL'] + sum_v['IVA 15%']
                    sum_v_f = pd.concat([sum_v, pd.DataFrame([{'GP': '--- TOTALES ---', **sum_v.sum()}])], ignore_index=True)
                    st.table(sum_v_f.style.format(subset=['SUBTOTAL', 'IVA 15%', 'TOTAL GENERAL'], formatter="{:,.2f}"))
                    
                    st.download_button("📥 Descargar Resumen VV", to_excel(sum_v_f), f"Resumen_VV_{mes_v}.xlsx")
                    st.session_state['res_vv'] = res_vv

    with tabs_v[1]:
        if 'res_vv' in st.session_state:
            dv = st.session_state['res_vv']
            kv1, kv2, kv3, kv4 = st.columns(4)
            kv1.metric("Bultos", f"{dv['BULTOS'].sum():,.0f}"); kv2.metric("Prep.", f"$ {dv['TOTAL_PREPARACION'].sum():,.2f}"); kv3.metric("Trans.", f"$ {dv['TOTAL_TRANSPORTE'].sum():,.2f}"); kv4.metric("Total Final", f"$ {dv['TOTAL_FINAL'].sum():,.2f}")
            st.divider()
            st.download_button("📥 Descargar Detalle VV", to_excel(dv), "Detalle_VV.xlsx")
            st.dataframe(dv, use_container_width=True)

    with tabs_v[2]: 
        st.header("⚙️ Maestros VV")
        cva, cvb = st.columns(2)
        with cva:
            ugv = st.file_uploader("Cargar GP VV", key="ugvv")
            if ugv: leer_archivo(ugv).to_csv(PATH_GP_VV, index=False); st.success("OK VV")
        with cvb:
            ucv = st.file_uploader("Cargar Costos VV", key="ucvv")
            if ucv: leer_archivo(ucv).to_csv(PATH_COSTOS_VV, index=False); st.success("OK VV")
