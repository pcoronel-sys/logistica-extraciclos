import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Gestión Bagó", layout="wide", page_icon="🧪")

# --- CSS AGRESIVO PARA ELIMINAR CUADROS Y ESPACIOS SUPERIORES ---
st.markdown("""
    <style>
    /* 1. ELIMINA EL HEADER, EL MENÚ Y EL ESPACIADO SUPERIOR DE RAÍZ */
    header, [data-testid="stHeader"], .st-emotion-cache-18ni7ap, .st-emotion-cache-z5fcl4 {
        display: none !important;
        height: 0px !important;
    }
    
    /* 2. QUITA EL RELLENO (PADDING) DEL CONTENEDOR PRINCIPAL */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        margin-top: -5rem !important; /* Empuja el contenido hacia arriba */
    }

    .stApp { background-color: #ffffff; }
    
    /* 3. DISEÑO DE TABLAS CON ENCABEZADO COLOR */
    [data-testid="stTable"] thead tr th {
        background-color: #2C3E50 !important;
        color: white !important;
        font-weight: bold !important;
        text-align: center !important;
    }
    
    /* 4. LOGIN TOTALMENTE LIMPIO Y CENTRADO */
    .login-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh; /* Usa todo el alto de la pantalla */
        margin-top: 5rem;
    }
    
    .login-box {
        padding: 30px;
        border-radius: 12px;
        background-color: #f8f9fa;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        border: 1px solid #dee2e6;
        width: 340px;
        text-align: center;
    }

    .stButton>button {
        background: linear-gradient(90deg, #2C3E50 0%, #4CA1AF 100%);
        color: white; border-radius: 8px; border: none;
        font-weight: bold; height: 3em; width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CREDENCIALES ---
USUARIO_PRO = "admin"
CLAVE_PRO = "bago2024"

if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

# --- PANTALLA DE LOGIN ---
if not st.session_state['autenticado']:
    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown("<h2 style='color: #2C3E50; margin-bottom: 5px;'>Bagó Logística</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #7f8c8d; font-size: 14px;'>Acceso Protegido</p>", unsafe_allow_html=True)
        
        user = st.text_input("User", label_visibility="collapsed", placeholder="Usuario")
        password = st.text_input("Pass", type="password", label_visibility="collapsed", placeholder="Contraseña")
        
        if st.button("INGRESAR"):
            if user == USUARIO_PRO and password == CLAVE_PRO:
                st.session_state['autenticado'] = True
                st.rerun()
            else:
                st.error("Acceso Denegado")
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- BARRA LATERAL ---
st.sidebar.write(f"👤 Usuario: **{USUARIO_PRO}**")
if st.sidebar.button("Cerrar Sesión"):
    st.session_state['autenticado'] = False
    st.rerun()

# --- SISTEMA LOGÍSTICO (TODAS LAS FUNCIONES ACTIVAS) ---
PATH_GP = "master_gp.csv"
PATH_COSTOS = "master_costos.csv"
HISTORICO_FILE = "base_historica_bago.csv"

def guardar_maestro(df, path): df.to_csv(path, index=False)
def cargar_maestro(path): return pd.read_csv(path) if os.path.exists(path) else None
def leer_archivo(archivo):
    try:
        if archivo.name.lower().endswith(('.xlsx', '.xls')): return pd.read_excel(archivo)
        return pd.read_csv(archivo, encoding='latin-1')
    except: return None

# Título y Navegación
st.title("📊 Control de Liquidación Logística")
tabs = st.tabs(["🚀 Liquidación Mensual", "🔍 Detalle de Carga Actual", "⚙️ Configurar Maestros", "🗄️ Historial"])

m_gp = cargar_maestro(PATH_GP)
m_costos = cargar_maestro(PATH_COSTOS)

# --- PESTAÑA 1: LIQUIDACIÓN ---
with tabs[0]:
    if m_gp is None or m_costos is None: st.warning("⚠️ Cargue los maestros en la pestaña Configurar.")
    else:
        c1, c2 = st.columns([1, 2])
        with c1: mes_sel = st.selectbox("Mes", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
        with c2: archivo = st.file_uploader("Subir Carga Mensual", type=['xlsx', 'xls', 'csv'])

        if archivo:
            df_c = leer_archivo(archivo)
            if df_c is not None:
                df_c.columns = df_c.columns.str.strip().str.upper()
                df_c['CODIGO'] = df_c['CODIGO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                col_id_gp = [c for c in m_gp.columns if 'CODIGO' in c][0]
                m_gp[col_id_gp] = m_gp[col_id_gp].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                
                res = pd.merge(df_c, m_gp.drop_duplicates(subset=[col_id_gp])[[col_id_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_id_gp, how='left')
                m_c = m_costos.rename(columns={'PRECIO_PREP': 'PREPARACION', 'PRECIO_TRANS': 'TRANSPORTE'}).drop_duplicates(subset=['DESCRIPCIÓN ZONA'])
                res = pd.merge(res, m_c[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')
                
                for col in ['BULTOS', 'PREPARACION', 'TRANSPORTE']: res[col] = pd.to_numeric(res[col], errors='coerce').fillna(0)
                res['TOTAL PREPARACION'] = res['PREPARACION'] * res['BULTOS']
                res['TOTAL TRANSPORTE'] = res['TRANSPORTE'] * res['BULTOS']
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

                st.table(summary_f.style.format(precision=2).set_properties(**{'background-color': '#2C3E50', 'color': 'white', 'font-weight': 'bold'}, subset=pd.IndexSlice[summary_f.index[-1], :]))
                st.session_state['res_actual'] = res
                st.session_state['mes_actual'] = mes_sel
                if st.button("💾 Guardar Periodo"):
                    res['MES_REPORTE'] = mes_sel
                    res['FECHA_REGISTRO'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    pd.concat([pd.read_csv(HISTORICO_FILE) if os.path.exists(HISTORICO_FILE) else pd.DataFrame(), res], ignore_index=True).to_csv(HISTORICO_FILE, index=False)
                    st.success("Guardado.")

# --- PESTAÑA 2: DETALLE ---
with tabs[1]:
    if 'res_actual' in st.session_state:
        df_det = st.session_state['res_actual']
        st.subheader(f"📑 Detalle - {st.session_state['mes_actual']}")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Bultos", f"{df_det['BULTOS'].sum():,.0f}")
        k2.metric("Preparación", f"$ {df_det['TOTAL PREPARACION'].sum():,.2f}")
        k3.metric("Transporte", f"$ {df_det['TOTAL TRANSPORTE'].sum():,.2f}")
        k4.metric("Total Final", f"$ {df_det['TOTAL CON IVA'].sum():,.2f}")
        st.dataframe(df_det, use_container_width=True)
    else: st.info("Procese un archivo primero.")

# --- PESTAÑA 3: CONFIGURACIÓN ---
with tabs[2]:
    st.header("⚙️ Configuración")
    ca, cb = st.columns(2)
    with ca:
        ug = st.file_uploader("Actualizar Maestro GP", type=['xlsx', 'xls', 'csv'], key="ug")
        if ug:
            d = leer_archivo(ug)
            if d is not None:
                d.columns = d.columns.str.strip().str.upper()
                guardar_maestro(d, PATH_GP); st.success("GP Guardado.")
    with cb:
        uc = st.file_uploader("Actualizar Maestro Costos", type=['xlsx', 'xls', 'csv'], key="uc")
        if uc:
            d = leer_archivo(uc)
            if d is not None
