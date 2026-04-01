import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Acceso Seguro - Bagó Logística", layout="wide", page_icon="🔐")

# --- USUARIO Y CONTRASEÑA CONFIGURABLES ---
USUARIO_PRO = "admin"
CLAVE_PRO = "bago2024" # <-- Cámbiala aquí si lo deseas

# --- ESTILO CORPORATIVO INCLUYENDO EL LOGIN CENTRADO ---
st.markdown("""
    <style>
    /* Estilos globales */
    .stApp { background-color: #ffffff; }
    
    /* Estilos para las tablas y reportes */
    [data-testid="stTable"] thead tr th {
        background-color: #2C3E50 !important;
        color: white !important;
        font-weight: bold !important;
    }
    div[data-testid="stMetric"] {
        background-color: #fcfcfc;
        border-left: 6px solid #4CA1AF;
        border-radius: 10px;
        padding: 15px !important;
    }
    
    /* Estilo de botones */
    .stButton>button {
        background: linear-gradient(90deg, #2C3E50 0%, #4CA1AF 100%);
        color: white; border-radius: 10px; border: none;
        font-weight: bold; height: 3.5em; width: 100%;
    }

    /* --- ESTILO CSS PARA CENTRAR Y ACHICAR EL LOGIN --- */
    .login-container {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        margin-top: 10vh; /* Baja un poco el cuadro */
    }
    .login-box {
        padding: 40px;
        border-radius: 15px;
        background-color: #f8f9fa;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: 1px solid #e1e1e1;
        width: 100%;
        max-width: 450px; /* Ancho máximo del cuadro de login */
        text-align: center;
    }
    .stTextInput>div>div>input {
        text-align: center; /* Centra el texto dentro de los inputs */
    }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE GESTIÓN DE SESIÓN ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

# --- FUNCIÓN DE RENDERIZADO DEL LOGIN CENTRADO ---
def mostrar_login():
    # Usamos columnas para forzar el centrado horizontal en Streamlit
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        with st.container():
            st.markdown('<div class="login-box">', unsafe_allow_html=True)
            st.markdown("<h1>🧪</h1>", unsafe_allow_html=True) # Icono grande
            st.title("Bagó Logística")
            st.subheader("Panel de Control")
            st.write("Por favor, ingrese sus credenciales para continuar.")
            
            user = st.text_input("Usuario", placeholder="admin")
            password = st.text_input("Contraseña", type="password", placeholder="••••••••")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("Iniciar Sesión Segura"):
                if user == USUARIO_PRO and password == CLAVE_PRO:
                    st.session_state['autenticado'] = True
                    st.rerun() # Recarga la página para mostrar el sistema
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

# --- BARRA LATERAL (Solo visible si está logueado) ---
st.sidebar.image("https://www.bago.com.ar/wp-content/uploads/2021/05/logo-bago.png", width=150) # Logo Bagó opcional
st.sidebar.success(f"Usuario activo: {USUARIO_PRO}")
if st.sidebar.button("🔒 Cerrar Sesión"):
    st.session_state['autenticado'] = False
    st.rerun()

# ---------------------------------------------------------
# CÓDIGO DEL SISTEMA LOGÍSTICO (NO TOCADO)
# ---------------------------------------------------------

PATH_GP = "master_gp.csv"
PATH_COSTOS = "master_costos.csv"
HISTORICO_FILE = "base_historica_bago.csv"

def guardar_maestro(df, path): df.to_csv(path, index=False)
def cargar_maestro(path): return pd.read_csv(path) if os.path.exists(path) else None

def leer_archivo_protegido(archivo):
    try:
        nombre_lower = archivo.name.lower()
        if nombre_lower.endswith(('.xlsx', '.xls')): return pd.read_excel(archivo)
        else:
            try: return pd.read_csv(archivo, encoding='utf-8')
            except UnicodeDecodeError:
                archivo.seek(0)
                return pd.read_csv(archivo, encoding='latin-1')
    except Exception as e:
        st.error(f"Error crítico al leer {archivo.name}: {e}")
        return None

# Título principal del sistema
st.title("📊 Control de Liquidación Logística")
tabs = st.tabs(["🚀 Liquidación Mensual", "🔍 Detalle de Carga Actual", "⚙️ Configurar Maestros", "🗄️ Historial"])

m_gp = cargar_maestro(PATH_GP)
m_costos = cargar_maestro(PATH_COSTOS)

# --- PESTAÑA 1: LIQUIDACIÓN ---
with tabs[0]:
    if m_gp is None or m_costos is None: st.warning("⚠️ Cargue los maestros en la pestaña de Configuración.")
    else:
        col_m, col_f = st.columns([1, 2])
        with col_m: mes_sel = st.selectbox("Seleccionar Mes", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
        with col_f: archivo_carga = st.file_uploader("Subir Archivo de Carga Mensual", type=['xlsx', 'xls'])

        if archivo_carga:
            df_c = leer_archivo_protegido(archivo_carga)
            if df_c is not None:
                df_c.columns = df_c.columns.str.strip().str.upper()
                df_c['CODIGO'] = df_c['CODIGO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                col_id_gp = [c for c in m_gp.columns if 'CODIGO' in c][0]
                m_gp[col_id_gp] = m_gp[col_id_gp].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                df_c['DESCRIPCIÓN ZONA'] = df_c['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                m_costos['DESCRIPCIÓN ZONA'] = m_costos['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()

                if not df_c[~df_c['CODIGO'].isin(m_gp[col_id_gp])]['CODIGO'].empty or not df_c[~df_c['DESCRIPCIÓN ZONA'].isin(m_costos['DESCRIPCIÓN ZONA'])]['DESCRIPCIÓN ZONA'].empty:
                    st.error("🛑 Existen errores de validación. Revise los Maestros.")
                else:
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

                    busqueda = st.text_input("🔍 Filtrar por Gerente:", "")
                    summary_view = summary[summary['GP'].str.contains(busqueda.upper())] if busqueda else summary
                    tot = {'GP': '--- TOTAL GENERAL ---'}
                    for col in summary_view.columns[1:]: tot[col] = summary_view[col].sum()
                    summary_final = pd.concat([summary_view, pd.DataFrame([tot])], ignore_index=True)

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
                        st.success("Guardado en Base Histórica.")

# --- PESTAÑA 2: DETALLE ---
with tabs[1]:
    st.header("🔍 Detalle de Carga Procesada")
    if 'res_actual' in st.session_state:
        df_det_view = st.session_state['res_actual'].copy()
        
        # Filtros
        c_f1, c_f2 = st.columns(2)
        with c_f1: gps_sel = st.multiselect("Filtrar por GP:", options=sorted(df_det_view['GP'].unique()))
        with c_f2: tipos_sel = st.multiselect("Filtrar por Tipo:", options=sorted(df_det_view['TIPO'].unique()))
        
        df_view = df_det_view.copy()
        if gps_sel: df_view = df_view[df_view['GP'].isin(gps_sel)]
        if tipos_sel: df_view = df_view[df_view['TIPO'].isin(tipos_sel)]
        
        st.markdown("---")
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Bultos", f"{df_view['BULTOS'].sum():,.0f}")
        k2.metric("Prep.", f"$ {df_view['TOTAL PREPARACION'].sum():,.2f}")
        k3.metric("Trans.", f"$ {df_view['TOTAL TRANSPORTE'].sum():,.2f}")
        k4.metric("Neto", f"$ {df_view['VALOR_LOGISTICA'].sum():,.2f}")
        k5.metric("Total IVA", f"$ {df_view['TOTAL CON IVA'].sum():,.2f}")

        cols_orden = ['CODIGO', 'DESCRIPCIÓN ZONA', 'GP', 'TIPO', 'BULTOS', 'PREPARACION', 'TRANSPORTE', 'TOTAL PREPARACION', 'TOTAL TRANSPORTE', 'VALOR_LOGISTICA', 'IVA 15%', 'TOTAL CON IVA']
        tot_det = {'CODIGO': '--- TOTALES ---', 'BULTOS': df_view['BULTOS'].sum(), 'TOTAL PREPARACION': df_view['TOTAL PREPARACION'].sum(), 'TOTAL TRANSPORTE': df_view['TOTAL TRANSPORTE'].sum(), 'VALOR_LOGISTICA': df_view['VALOR_LOGISTICA'].sum(), 'IVA 15%': df_view['IVA 15%'].sum(), 'TOTAL CON IVA': df_view['TOTAL CON IVA'].sum()}
        df_final = pd.concat([df_view[cols_orden], pd.DataFrame([tot_det])], ignore_index=True)
        
        st.table(df_final.style.format({c: "{:,.2f}" for c in ['PREPARACION', 'TRANSPORTE', 'TOTAL PREPARACION', 'TOTAL TRANSPORTE', 'VALOR_LOGISTICA', 'IVA 15%', 'TOTAL CON IVA'] if c in df_final.columns}, na_rep="").set_properties(**{'background-color': '#2C3E50', 'color': 'white', 'font-weight': 'bold'}, subset=pd.IndexSlice[df_final.index[-1], :]))
    else: st.info("Procese un archivo primero.")

# --- PESTAÑA 3: CONFIG ---
with tabs[2]:
    st.header("⚙️ Configuración")
    c1, c2 = st.columns(2)
    with c1:
        u_gp = st.file_uploader("Actualizar Maestro GP", type=['xlsx', 'xls', 'csv'], key="ugp")
        if u_gp:
            df_u_gp = leer_archivo_protegido(u_gp)
            if df_u_gp is not None:
                df_u_gp.columns = df_u_gp.columns.str.strip().str.upper()
                guardar_maestro(df_u_gp, PATH_GP); st.success("✅ Maestro GP guardado.")
    with c2:
        u_costos = st.file_uploader("Actualizar Maestro Costos", type=['xlsx', 'xls', 'csv'], key="ucostos")
        if u_costos:
            df_u_costos = leer_archivo_protegido(u_costos)
            if df_u_costos is not None:
                df_u_costos.columns = df_u_costos.columns.str.strip().str.upper()
                guardar_maestro(df_u_costos, PATH_COSTOS); st.success("✅ Maestro de Costos guardado.")

with tabs[3]:
    st.header("🗄️ Historial")
    if os.path.exists(HISTORICO_FILE):
        h_df = pd.read_csv(HISTORICO_FILE)
        st.dataframe(h_df, use_container_width=True)
