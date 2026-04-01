import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Bagó - Intel Stock Premium", layout="wide", page_icon="🧪")

# --- 🎨 ESTILOS PREMIUM (ESPEJO Y RELIEVE) ---
st.markdown("""
    <style>
    header, [data-testid="stHeader"] { display: none !important; }
    .stApp { background-color: #f8f9fa; }
    div[data-testid="stMetric"], .stTable, .stDataFrame, .login-box {
        background: rgba(255, 255, 255, 0.8) !important;
        backdrop-filter: blur(10px);
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.5) !important;
        box-shadow: 10px 10px 20px #d1d1d1, -10px -10px 20px #ffffff !important;
        padding: 20px !important;
    }
    .stButton>button {
        background: linear-gradient(145deg, #e91e63, #c2185b) !important;
        color: white !important; font-weight: bold !important;
        border-radius: 15px !important; border: none !important;
        box-shadow: 5px 5px 15px #d1d1d1, -5px -5px 15px #ffffff !important;
        height: 3.5em !important; transition: 0.3s;
    }
    [data-testid="stTable"] thead tr th {
        background-color: #2C3E50 !important; color: white !important; font-weight: bold !important;
    }
    .main-title { color: #E91E63; font-size: 50px; font-weight: bold; text-align: center; margin: 0; }
    .almacen-tag { color: #E91E63; font-weight: bold; letter-spacing: 1px; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- SEGURIDAD Y NAVEGACIÓN ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'pagina' not in st.session_state: st.session_state['pagina'] = "login"

if not st.session_state['autenticado']:
    _, col_cent, _ = st.columns([1, 1, 1])
    with col_cent:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown("<h2 style='text-align:center; color:#E91E63;'>Ingreso Seguro</h2>", unsafe_allow_html=True)
        u = st.text_input("Usuario", placeholder="admin", label_visibility="collapsed")
        p = st.text_input("Clave", type="password", placeholder="••••", label_visibility="collapsed")
        if st.button("ACCEDER AL PORTAL"):
            if u == "admin" and p == "bago2024":
                st.session_state['autenticado'] = True
                st.session_state['pagina'] = "menu"
                st.rerun()
            else: st.error("Acceso denegado")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- RUTAS ---
PATH_GP = "master_gp.csv"
PATH_COSTOS = "master_costos.csv"
HISTORICO_FILE = "base_historica_bago.csv"

def leer_archivo(archivo):
    try:
        if archivo.name.lower().endswith(('.xlsx', '.xls')): return pd.read_excel(archivo)
        return pd.read_csv(archivo, encoding='latin-1')
    except: return None

# --- PANTALLA DE MENÚ ---
if st.session_state['pagina'] == "menu":
    st.markdown("<p style='text-align:center; color:#bdc3c7; margin-top:30px;'>👋 BUENAS TARDES, EQUIPO BAGÓ</p>", unsafe_allow_html=True)
    st.markdown("<h1 class='main-title'>Laboratorios Bagó</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#7f8c8d; font-size:18px;'>Intel-Stock Management</p>", unsafe_allow_html=True)
    
    col_s1, col_b1, col_b2, col_s2 = st.columns([1, 2, 2, 1])
    with col_b1:
        st.markdown("<p class='almacen-tag' style='text-align:center;'>ALMACÉN 1010</p>", unsafe_allow_html=True)
        if st.button("📦 MATERIAL DE EMPAQUE"):
            st.session_state['pagina'] = "app"
            st.rerun()
    with col_b2:
        st.markdown("<p class='almacen-tag' style='text-align:center;'>ALMACÉN 1070</p>", unsafe_allow_html=True)
        if st.button("🔢 MATERIAL PROMOCIONAL"):
            st.session_state['pagina'] = "app"
            st.rerun()

# --- SISTEMA DE LIQUIDACIÓN ---
if st.session_state['pagina'] == "app":
    if st.sidebar.button("⬅️ VOLVER AL MENÚ"):
        st.session_state['pagina'] = "menu"
        st.rerun()

    st.title("📊 Control de Liquidación Logística")
    tabs = st.tabs(["🚀 Liquidación", "🔍 Detalle", "⚙️ Configuración", "🗄️ Historial"])
    
    # Cargar Maestros
    m_gp = pd.read_csv(PATH_GP) if os.path.exists(PATH_GP) else None
    m_costos = pd.read_csv(PATH_COSTOS) if os.path.exists(PATH_COSTOS) else None

    with tabs[0]: # LIQUIDACIÓN
        if m_gp is None or m_costos is None: st.warning("⚠️ Cargue los archivos maestros en la pestaña Configuración.")
        else:
            c1, c2 = st.columns([1, 2])
            with c1: mes_sel = st.selectbox("Mes", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
            with c2: archivo = st.file_uploader("Subir Carga Mensual", type=['xlsx', 'xls', 'csv'])

            if archivo:
                df_c = leer_archivo(archivo)
                if df_c is not None:
                    # NORMALIZACIÓN DE CARGA
                    df_c.columns = df_c.columns.str.strip().str.upper()
                    # Convertimos CODIGO a String y quitamos el .0 si es flotante
                    df_c['CODIGO'] = df_c['CODIGO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    df_c['DESCRIPCIÓN ZONA'] = df_c['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()

                    # NORMALIZACIÓN MAESTRO GP
                    m_gp_c = m_gp.copy()
                    m_gp_c.columns = m_gp_c.columns.str.strip().str.upper()
                    col_id = [c for c in m_gp_c.columns if 'CODIGO' in c][0]
                    # Forzamos CODIGO a String para evitar el ValueError
                    m_gp_c[col_id] = m_gp_c[col_id].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    m_gp_c = m_gp_c.drop_duplicates(subset=[col_id])

                    # NORMALIZACIÓN MAESTRO COSTOS
                    m_costos_c = m_costos.copy()
                    m_costos_c.columns = m_costos_c.columns.str.strip().str.upper()
                    renames = {c: "PREP" for c in m_costos_c.columns if "PREP" in c}
                    renames.update({c: "TRANS" for c in m_costos_c.columns if "TRANS" in c})
                    m_costos_c = m_costos_c.rename(columns=renames)
                    m_costos_c['DESCRIPCIÓN ZONA'] = m_costos_c['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                    m_costos_c = m_costos_c.drop_duplicates(subset=['DESCRIPCIÓN ZONA'])

                    # CRUCE DE DATOS (MERGE SEGURO)
                    res = pd.merge(df_c, m_gp_c[[col_id, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_id, how='left')
                    res = pd.merge(res, m_costos_c[['DESCRIPCIÓN ZONA', 'PREP', 'TRANS']], on='DESCRIPCIÓN ZONA', how='left')

                    # CÁLCULOS
                    for c in ['BULTOS', 'PREP', 'TRANS']: res[c] = pd.to_numeric(res[c], errors='coerce').fillna(0)
                    
                    res['TOTAL PREPARACION'] = res['PREP'] * res['BULTOS']
                    res['TOTAL TRANSPORTE'] = res['TRANS'] * res['BULTOS']
                    res['VALOR_LOGISTICA'] = res['TOTAL PREPARACION'] + res['TOTAL TRANSPORTE']
                    res['IVA 15%'] = res['VALOR_LOGISTICA'] * 0.15
                    res['TOTAL CON IVA'] = res['VALOR_LOGISTICA'] + res['IVA 15%']

                    st.subheader(f"📋 Reporte Consolidado: {mes_sel}")
                    summary = res.groupby(['GP', 'TIPO'])['VALOR_LOGISTICA'].sum().unstack(fill_value=0).reset_index()
                    for c in ['MM', 'MP']: 
                        if c not in summary.columns: summary[c] = 0.0
                    summary['SUBTOTAL'] = summary['MM'] + summary['MP']
                    summary['IVA 15%'] = summary['SUBTOTAL'] * 0.15
                    summary['TOTAL'] = summary['SUBTOTAL'] + summary['IVA 15%']

                    tot = {'GP': '--- TOTAL GENERAL ---'}
                    for col in summary.columns[1:]: tot[col] = summary[col].sum()
                    summary_f = pd.concat([summary, pd.DataFrame([tot])], ignore_index=True)
                    st.table(summary_f.style.format(precision=2))
                    
                    st.session_state['res_actual'] = res
                    st.session_state['mes_actual'] = mes_sel
                    
                    if st.button("💾 Guardar en Historial"):
                        res['MES_REPORTE'] = mes_sel
                        res['FECHA_REGISTRO'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        hist_existente = pd.read_csv(HISTORICO_FILE) if os.path.exists(HISTORICO_FILE) else pd.DataFrame()
                        pd.concat([hist_existente, res], ignore_index=True).to_csv(HISTORICO_FILE, index=False)
                        st.success("Guardado en Historial.")

    with tabs[1]: # DETALLE
        if 'res_actual' in st.session_state:
            df_d = st.session_state['res_actual']
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Bultos", f"{df_d['BULTOS'].sum():,.0f}")
            k2.metric("Neto", f"$ {df_d['VALOR_LOGISTICA'].sum():,.2f}")
            k3.metric("IVA 15%", f"$ {df_d['IVA 15%'].sum():,.2f}")
            k4.metric("Total", f"$ {df_d['TOTAL CON IVA'].sum():,.2f}")
            st.dataframe(df_d, use_container_width=True, height=450)

    with tabs[2]: # CONFIGURACIÓN
        ca, cb = st.columns(2)
        with ca:
            ug = st.file_uploader("Actualizar Maestro GP", type=['xlsx', 'xls', 'csv'])
            if ug:
                d = leer_archivo(ug)
                if d is not None:
                    d.to_csv(PATH_GP, index=False)
                    st.success("GP Guardado. Refresque la app.")
        with cb:
            uc = st.file_uploader("Actualizar Maestro Costos", type=['xlsx', 'xls', 'csv'])
            if uc:
                d = leer_archivo(uc)
                if d is not None:
                    d.to_csv(PATH_COSTOS, index=False)
                    st.success("Costos Guardado. Refresque la app.")

    with tabs[3]: # HISTORIAL
        if os.path.exists(HISTORICO_FILE):
            h = pd.read_csv(HISTORICO_FILE)
            m_del = st.selectbox("Eliminar mes:", sorted(h['MES_REPORTE'].unique()))
            if st.button("Eliminar"):
                h[h['MES_REPORTE'] != m_del].to_csv(HISTORICO_FILE, index=False)
                st.rerun()
            st.dataframe(h, use_container_width=True)
        else:
            st.info("No hay datos en el historial aún.")
