import streamlit as st
import pandas as pd
from io import BytesIO
import os
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Bagó Logística Pro", layout="wide", page_icon="🧪")

# --- ESTILO CORPORATIVO MAGENTA Y BLANCO ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    
    /* Métricas */
    div[data-testid="stMetric"] {
        background: #ffffff;
        border-radius: 12px;
        border: 1px solid #f0f0f0;
        border-top: 5px solid #E10078;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        padding: 20px !important;
    }

    /* Botones Magenta */
    .stButton>button {
        background: linear-gradient(90deg, #E10078 0%, #8E004C 100%);
        color: white; border-radius: 10px; border: none;
        font-weight: bold; height: 3em; width: 100%;
        transition: 0.3s;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 5px 15px rgba(225, 0, 120, 0.4);
    }
    </style>
    """, unsafe_allow_html=True)

# ARCHIVOS DE MEMORIA LOCAL
PATH_GP = "master_gp.csv"
PATH_COSTOS = "master_costos.csv"
HISTORICO_FILE = "base_historica_bago.csv"

# --- FUNCIONES DE PERSISTENCIA ---
def guardar_maestro(df, path):
    df.to_csv(path, index=False)

def cargar_maestro(path):
    if os.path.exists(path):
        return pd.read_csv(path)
    return None

def leer_archivo_protegido(archivo):
    """Lee Excel o CSV con detección de codificación para evitar errores de decode"""
    try:
        if archivo.name.endswith(('xlsx', 'xls')):
            return pd.read_excel(archivo)
        else:
            try:
                return pd.read_csv(archivo, encoding='utf-8')
            except UnicodeDecodeError:
                archivo.seek(0)
                return pd.read_csv(archivo, encoding='latin-1')
    except Exception as e:
        st.error(f"Error al leer el archivo {archivo.name}: {e}")
        return None

# --- NAVEGACIÓN ---
st.title("🚀 Gestión Logística Inteligente - Bagó")
st.caption("Procesador de Extra-ciclos con Validación Automática")
tabs = st.tabs(["📊 Liquidación Mensual", "⚙️ Configurar Maestros", "🗄️ Historial"])

# --- PESTAÑA 2: CONFIGURAR MAESTROS ---
with tabs[1]:
    st.header("⚙️ Actualización de Bases Maestras")
    st.info("Sube tus archivos aquí para que la App aprenda los códigos de productos y precios de zonas.")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Maestro GP (Productos y Tipos)")
        u_gp = st.file_uploader("Subir Maestro GP (.xlsx o .csv)", type=['xlsx', 'csv'], key="ugp")
        if u_gp:
            df_u_gp = leer_archivo_protegido(u_gp)
            if df_u_gp is not None:
                df_u_gp.columns = df_u_gp.columns.str.strip().str.upper()
                guardar_maestro(df_u_gp, PATH_GP)
                st.success(f"✅ Maestro GP actualizado con {len(df_u_gp)} productos.")

    with c2:
        st.subheader("Maestro Costos (Zonas y Precios)")
        u_costos = st.file_uploader("Subir Maestro Costos (.xlsx o .csv)", type=['xlsx', 'csv'], key="ucostos")
        if u_costos:
            df_u_costos = leer_archivo_protegido(u_costos)
            if df_u_costos is not None:
                df_u_costos.columns = df_u_costos.columns.str.strip().str.upper()
                guardar_maestro(df_u_costos, PATH_COSTOS)
                st.success(f"✅ Maestro de Costos actualizado con {len(df_u_costos)} zonas.")

# CARGAR MAESTROS EXISTENTES
m_gp = cargar_maestro(PATH_GP)
m_costos = cargar_maestro(PATH_COSTOS)

# --- P
