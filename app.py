import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS
st.set_page_config(page_title="Gestión Bagó", layout="wide", page_icon="🧪")

# --- ESTILO CORPORATIVO AJUSTADO ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    
    /* Configuración Global de Encabezados de Tablas */
    [data-testid="stTable"] thead tr th, 
    thead tr th {
        background-color: #2C3E50 !important;
        color: white !important;
        font-weight: bold !important;
        text-align: center !important;
    }
    
    /* Estilo de Tarjetas de Métricas */
    div[data-testid="stMetric"] {
        background-color: #fcfcfc;
        border-left: 6px solid #4CA1AF;
        border-radius: 10px;
        padding: 15px !important;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }

    /* Estilo de Botones */
    .stButton>button {
        background: linear-gradient(90deg, #2C3E50 0%, #4CA1AF 100%);
        color: white; border-radius: 10px; border: none;
        font-weight: bold; height: 3.5em; width: 100%;
        transition: 0.3s ease;
    }
    .stButton>button:hover { opacity: 0.9; }

    /* CSS AJUSTADO PARA CENTRAR Y ACHICAR EL LOGIN (SIN CUADROS FANTASMAS) */
    .login-container {
        display: flex;
        justify-content: center;
        width: 100%;
        margin-top: 15vh; /* Baja un poco el cuadro */
    }
    .login-box {
        padding: 30px 40px;
        border-radius: 15px;
        background-color: #f8f9fa;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: 1px solid #e1e1e1;
        width: 100%;
        max-width: 380px; /* Ancho máximo reducido para que sea compacto */
        text-align: left; /* Títulos a la izquierda */
    }
    .login-header {
        text-align: center;
        margin-bottom: 25px;
    }
    .stTextInput>div>div>input { text-align: left; }
    </style>
    """, unsafe_allow_html=True)

# --- USUARIO Y CONTRASEÑA CONFIGURABLES ---
USUARIO_PRO = "admin"
CLAVE_PRO = "bago2024" # <-- Cámbiala aquí

# --- LÓGICA DE GESTIÓN DE SESIÓN ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

# --- FUNCIÓN DE RENDERIZADO DEL LOGIN CENTRADO Y LIMPIO ---
def mostrar_login():
    col1, col2, col3 = st.columns([1.5, 2, 1.5])
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        
        # Cabecera limpia y centrada
        st.markdown('<div class="login-header">', unsafe_allow_html=True)
        st.markdown("<h2>🧪 Bagó Logística</h2>", unsafe_allow_html=True)
        st.markdown("<p>Control Logístico Extraciclos</p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Formulario de Streamlit directo
        user = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Ingresar al Sistema"):
            if user == USUARIO_PRO and password == CLAVE_PRO:
                st.session_state['autenticado'] = True
                st.rerun()
            elif user == "" and password == "":
                 st.warning("⚠️ Por favor complete los campos.")
            else:
                st.error("❌ Credenciales incorrectas.")
        
        st.markdown('</div>', unsafe_allow_html=True) # Cierra login-box
        st.markdown('</div>', unsafe_allow_html=True) # Cierra login-container

# --- VERIFICACIÓN DE ACCESO ---
if not st.session_state['autenticado']:
    mostrar_login()
    st.stop() # Detiene la ejecución aquí si no está logueado

# --- BARRA LATERAL LIMPIA ---
st.sidebar.success(f"Usuario activo: {USUARIO_PRO}")
if st.sidebar.button("🔒 Cerrar Sesión"):
    st.session_state['autenticado'] = False
    st.rerun()

# ---------------------------------------------------------
# SISTEMA LOGÍSTICO (NO TOCADO, CON MAESTROS Y SUBTOTALES)
# ---------------------------------------------------------

PATH_GP = "master_gp.csv"
PATH_COSTOS = "master_costos.csv"
HISTORICO_FILE = "base_historica_bago.csv"

def guardar_maestro(df, path): df.to_csv(path, index=False)
def cargar_maestro(path): return pd.read_csv(path) if os.path.exists(path) else None

def leer_archivo_protegido(archivo):
    try:
        if archivo.name.lower().endswith(('.xlsx', '.xls')): return pd.read_excel(archivo)
        else:
            try: return pd.read_csv(archivo, encoding='utf-8')
            except: return pd.read_csv(archivo, encoding='latin-1')
    except: return None

# Título principal del sistema
st.title("📊 Control de Liquidación Logística")
tabs = st.tabs(["🚀 Liquidación Mensual", "🔍 Detalle de Carga Actual", "⚙️ Configurar Maestros", "🗄️ Historial"])

m_gp = cargar_maestro(PATH_GP)
m_costos = cargar_maestro(PATH_COSTOS)

# --- PESTAÑA 1: LIQUIDACIÓN (CON SUBTOTALES Y TÍTULOS EN COLOR) ---
with tabs[0]:
    if m_gp is None or m_costos is None: st.warning("⚠️ Cargue los maestros.")
    else:
        col_m, col_f = st.columns([1, 2])
        with col_m: mes_sel = st.selectbox("Mes", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
        with col_f: archivo_carga = st.file_uploader("📂 Subir Carga Mensual", type=['xlsx', 'xls', 'csv'])

        if archivo_carga:
            df_c = leer_archivo_protegido(archivo_carga)
            if df_c is not None:
                df_c.columns = df_c.columns.str.strip().str.upper()
                df_c['CODIGO'] = df_c['CODIGO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                col_id_gp = [c for c in m_gp.columns if 'CODIGO' in c][0]
                m_gp[col_id_gp] = m_gp[col_id_gp].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                df_c['DESCRIPCIÓN ZONA'] = df_c['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                m_costos['DESCRIPCIÓN ZONA'] = m_costos['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()

                res = pd.merge(df_c, m_gp.drop_duplicates(subset=[col_id_gp])[[col_id_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_id_gp, how='left')
                m_c_c = m_costos.rename(columns={'PRECIO_PREP': 'PREPARACION', 'PRECIO_TRANS': 'TRANSPORTE'}).drop_duplicates(subset=['DESCRIPCIÓN ZONA'])
                res = pd.merge(res, m_c_c[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')
                
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
                summary_final = pd.concat([summary, pd.DataFrame([tot])], ignore_index=True)

                st.table(
                    summary_final.style.format(precision=2)
                    .set_properties(**{'background-color': '#E8F6F3', 'color': '#16A085', 'font-weight': 'bold'}, subset=['TOTAL'])
                    .set_properties(**{'background-color': '#2C3E50', 'color': 'white', 'font-weight': 'bold'}, subset=pd.IndexSlice[summary_final.index[-1], :])
                )
                st.session_state['res_actual'] = res
                if st.button(f"💾 Guardar Periodo {mes_sel}"):
                    res['MES_REPORTE'] = mes_sel
                    res['FECHA_REGISTRO'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    pd.concat([pd.read_csv(HISTORICO_FILE) if os.path.exists(HISTORICO_FILE) else pd.DataFrame(), res], ignore_index=True).to_csv(HISTORICO_FILE, index=False)
                    st.success("Guardado.")

# --- PESTAÑA 2: DETALLE (SIN CAMBIOS) ---
with tabs[1]:
    if 'res_actual' in st.session_state:
        df_det_view = st.session_state['res_actual'].copy()
        st.subheader(f"📑 Auditoría - {st.session_state['mes_actual']}")
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Bultos", f"{df_det_view['BULTOS'].sum():,.0f}")
        k2.metric("Prep.", f"$ {df_det_view['TOTAL PREPARACION'].sum():,.2f}")
        k3.metric("Trans.", f"$ {df_det_view['TOTAL TRANSPORTE'].sum():,.2f}")
        k4.metric("Neto", f"$ {df_det_view['VALOR_LOGISTICA'].sum():,.2f}")
        k5.metric("Total IVA", f"$ {df_det_view['TOTAL CON IVA'].sum():,.2f}")
        st.dataframe(df_det_view, use_container_width=True)
    else: st.info("Procese un archivo primero.")

# --- PESTAÑA 3: CONFIGURACIÓN (CON CARGA DE MAESTROS) ---
with tabs[2]:
    st.header("⚙️ Configuración de Bases Maestras")
    col_a, col_b = st.columns(2)
    with col_a:
        u_gp = st.file_uploader("Actualizar Maestro GP", type=['xlsx', 'xls', 'csv'], key="ugp")
        if u_gp:
            df_ugp = leer_archivo_protegido(u_gp)
            if df_ugp is not None:
                df_ugp.columns = df_ugp.columns.str.strip().str.upper()
                guardar_maestro(df_ugp, PATH_GP); st.success("✅ Maestro GP guardado.")
    with col_b:
        u_costos = st.file_uploader("Actualizar Maestro Costos", type=['xlsx', 'xls', 'csv'], key="ucostos")
        if u_costos:
            df_ucostos = leer_archivo_protegido(u_costos)
            if df_ucostos is not None:
                df_ucostos.columns = df_ucostos.columns.str.strip().str.upper()
                guardar_maestro(df_ucostos, PATH_COSTOS); st.success("✅ Maestro de Costos guardado.")

# --- PESTAÑA 4: HISTORIAL (CON BORRADO POR MES) ---
with tabs[3]:
    if os.path.exists(HISTORICO_FILE):
        h_df = pd.read_csv(HISTORICO_FILE)
        with st.expander("🗑️ Zona de Peligro: Eliminar Periodo"):
            m_del = st.selectbox("Seleccionar Mes a borrar:", sorted(h_df['MES_REPORTE'].unique()))
            if st.button("Eliminar permanentemente"):
                h_df[h_df['MES_REPORTE'] != m_del].to_csv(HISTORICO_FILE, index=False)
                st.rerun()
        st.dataframe(h_df, use_container_width=True)
    else: st.info("Sin historial.")
