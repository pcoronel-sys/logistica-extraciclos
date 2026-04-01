import streamlit as st
import pandas as pd
from io import BytesIO
import os
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Bagó Logística Pro", layout="wide", page_icon="🧪")

# --- ESTILO CORPORATIVO ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .stButton>button {
        background: linear-gradient(90deg, #E10078 0%, #8E004C 100%);
        color: white; border-radius: 10px; font-weight: bold; width: 100%;
    }
    .status-box {
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
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

# --- NAVEGACIÓN ---
st.title("🚀 Gestión Logística Inteligente - Bagó")
tabs = st.tabs(["📊 Liquidación Mensual", "⚙️ Configurar Maestros", "🗄️ Historial"])

# --- PESTAÑA 2: CONFIGURAR MAESTROS (PUNTO 1) ---
with tabs[1]:
    st.header("Actualización de Maestros")
    st.write("Sube aquí tus archivos maestros. La App los recordará para futuras cargas.")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Maestro GP / Productos")
        u_gp = st.file_uploader("Subir Maestro GP", type=['xlsx', 'csv'], key="ugp")
        if u_gp:
            df_u_gp = pd.read_excel(u_gp) if u_gp.name.endswith('xlsx') else pd.read_csv(u_gp)
            df_u_gp.columns = df_u_gp.columns.str.strip().str.upper()
            guardar_maestro(df_u_gp, PATH_GP)
            st.success("Maestro GP actualizado.")

    with c2:
        st.subheader("Maestro de Costos / Zonas")
        u_costos = st.file_uploader("Subir Maestro Costos", type=['xlsx', 'csv'], key="ucostos")
        if u_costos:
            df_u_costos = pd.read_excel(u_costos) if u_costos.name.endswith('xlsx') else pd.read_csv(u_costos)
            df_u_costos.columns = df_u_costos.columns.str.strip().str.upper()
            guardar_maestro(df_u_costos, PATH_COSTOS)
            st.success("Maestro de Costos actualizado.")

# --- CARGAR MAESTROS EN MEMORIA ---
m_gp = cargar_maestro(PATH_GP)
m_costos = cargar_maestro(PATH_COSTOS)

# --- PESTAÑA 1: LIQUIDACIÓN (CON SEMÁFORO) ---
with tabs[0]:
    if m_gp is None or m_costos is None:
        st.warning("⚠️ Primero debes configurar los Maestros en la pestaña de Configuración.")
    else:
        col_m, col_f = st.columns([1, 2])
        with col_m:
            mes_sel = st.selectbox("Mes", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
        with col_f:
            archivo_carga = st.file_uploader("Subir archivo de Carga (Bultos)", type=['xlsx'])

        if archivo_carga:
            df_c = pd.read_excel(archivo_carga)
            df_c.columns = df_c.columns.str.strip().str.upper()
            
            # Normalización para validación
            df_c['CODIGO'] = df_c['CODIGO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            m_gp['CODIGO'] = m_gp[m_gp.columns[0]].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            df_c['DESCRIPCIÓN ZONA'] = df_c['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
            m_costos['DESCRIPCIÓN ZONA'] = m_costos['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()

            # --- SEMÁFORO DE VALIDACIÓN ---
            codigos_novedad = df_c[~df_c['CODIGO'].isin(m_gp['CODIGO'])]['CODIGO'].unique()
            zonas_novedad = df_c[~df_c['DESCRIPCIÓN ZONA'].isin(m_costos['DESCRIPCIÓN ZONA'])]['DESCRIPCIÓN ZONA'].unique()

            st.subheader("🚥 Semáforo de Validación")
            v1, v2 = st.columns(2)
            
            error_bloqueante = False
            
            with v1:
                if len(codigos_novedad) == 0:
                    st.success("✅ Productos: Todos encontrados")
                else:
                    st.error(f"❌ {len(codigos_novedad)} Productos nuevos no están en el Maestro")
                    st.write(codigos_novedad)
                    error_bloqueante = True
            
            with v2:
                if len(zonas_novedad) == 0:
                    st.success("✅ Zonas: Todas encontradas")
                else:
                    st.warning(f"⚠️ {len(zonas_novedad)} Zonas sin precio definido")
                    st.write(zonas_novedad)
                    error_bloqueante = True

            if error_bloqueante:
                st.info("💡 Por favor, actualiza los Maestros en la pestaña 'Configurar Maestros' para continuar.")
            else:
                # --- PROCESAMIENTO SI TODO ESTÁ OK ---
                res = pd.merge(df_c, m_gp[['CODIGO', 'GP', 'TIPO']], on='CODIGO', how='left')
                m_costos = m_costos.rename(columns={'PRECIO_PREP': 'PREPARACION', 'PRECIO_TRANS': 'TRANSPORTE'})
                res = pd.merge(res, m_costos[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')
                
                res['BULTOS'] = pd.to_numeric(res['BULTOS'], errors='coerce').fillna(0)
                res['VALOR_LOGISTICA'] = (pd.to_numeric(res['PREPARACION']) + pd.to_numeric(res['TRANSPORTE'])) * res['BULTOS']

                summary = res.groupby(['GP', 'TIPO'])['VALOR_LOGISTICA'].sum().unstack(fill_value=0).reset_index()
                for c in ['MM', 'MP']: 
                    if c not in summary.columns: summary[c] = 0.0
                summary['SUBTOTAL'] = summary['MM'] + summary['MP']
                summary['IVA 15%'] = summary['SUBTOTAL'] * 0.15
                summary['TOTAL'] = summary['SUBTOTAL'] + summary['IVA 15%']

                st.dataframe(summary.style.format(precision=2), use_container_width=True)
                
                if st.button("💾 Guardar en Histórico"):
                    res['MES_REPORTE'] = mes_sel
                    res['FECHA_SISTEMA'] = datetime.now()
                    if os.path.exists(HISTORICO_FILE):
                        pd.concat([pd.read_csv(HISTORICO_FILE), res]).to_csv(HISTORICO_FILE, index=False)
                    else:
                        res.to_csv(HISTORICO_FILE, index=False)
                    st.success("Guardado.")

# --- PESTAÑA 3: HISTORIAL ---
with tabs[2]:
    if os.path.exists(HISTORICO_FILE):
        h_df = pd.read_csv(HISTORICO_FILE)
        st.dataframe(h_df, use_container_width=True)
        st.download_button("Descargar Todo el Histórico", h_df.to_csv(index=False), "historico.csv")
    else:
        st.info("No hay datos históricos aún.")
