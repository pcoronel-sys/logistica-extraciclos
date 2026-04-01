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
    """Lee Excel o CSV detectando la extensión y codificación correctamente"""
    try:
        # Convertimos a minúsculas para reconocer .XLSX o .xlsx por igual
        nombre_lower = archivo.name.lower()
        
        if nombre_lower.endswith(('.xlsx', '.xls')):
            return pd.read_excel(archivo)
        else:
            # Es un CSV, probamos codificaciones comunes
            try:
                return pd.read_csv(archivo, encoding='utf-8')
            except UnicodeDecodeError:
                archivo.seek(0)
                return pd.read_csv(archivo, encoding='latin-1')
    except Exception as e:
        st.error(f"Error crítico al leer {archivo.name}: {e}")
        return None

# --- NAVEGACIÓN ---
st.title("🚀 Gestión Logística Inteligente - Bagó")
st.caption("Sistema de Liquidación con Validación de Maestros y Memoria Local")
tabs = st.tabs(["📊 Liquidación Mensual", "⚙️ Configurar Maestros", "🗄️ Historial"])

# --- PESTAÑA 2: CONFIGURAR MAESTROS ---
with tabs[1]:
    st.header("⚙️ Actualización de Bases Maestras")
    st.info("Sube tus archivos aquí. La App los recordará para procesar los bultos mensuales.")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Maestro GP (Productos y Tipos)")
        u_gp = st.file_uploader("Subir Maestro GP (.xlsx o .csv)", type=['xlsx', 'xls', 'csv'], key="ugp")
        if u_gp:
            df_u_gp = leer_archivo_protegido(u_gp)
            if df_u_gp is not None:
                df_u_gp.columns = df_u_gp.columns.str.strip().str.upper()
                guardar_maestro(df_u_gp, PATH_GP)
                st.success(f"✅ Maestro GP actualizado con {len(df_u_gp)} productos.")

    with c2:
        st.subheader("Maestro Costos (Zonas y Precios)")
        u_costos = st.file_uploader("Subir Maestro Costos (.xlsx o .xls)", type=['xlsx', 'xls', 'csv'], key="ucostos")
        if u_costos:
            df_u_costos = leer_archivo_protegido(u_costos)
            if df_u_costos is not None:
                df_u_costos.columns = df_u_costos.columns.str.strip().str.upper()
                guardar_maestro(df_u_costos, PATH_COSTOS)
                st.success(f"✅ Maestro de Costos actualizado con {len(df_u_costos)} zonas.")

# CARGAR MAESTROS EXISTENTES DESDE MEMORIA
m_gp = cargar_maestro(PATH_GP)
m_costos = cargar_maestro(PATH_COSTOS)

# --- PESTAÑA 1: LIQUIDACIÓN ---
with tabs[0]:
    if m_gp is None or m_costos is None:
        st.warning("⚠️ No hay maestros configurados. Ve a la pestaña 'Configurar Maestros' y sube los archivos iniciales.")
    else:
        col_m, col_f = st.columns([1, 2])
        with col_m:
            mes_sel = st.selectbox("Mes de Carga", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
        with col_f:
            archivo_carga = st.file_uploader("📂 Subir archivo de Bultos (Carga)", type=['xlsx', 'xls'])

        if archivo_carga:
            df_c = leer_archivo_protegido(archivo_carga)
            if df_c is not None:
                df_c.columns = df_c.columns.str.strip().str.upper()
                
                # Normalización de datos para cruce
                df_c['CODIGO'] = df_c['CODIGO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                col_id_gp = [c for c in m_gp.columns if 'CODIGO' in c][0]
                m_gp[col_id_gp] = m_gp[col_id_gp].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                
                df_c['DESCRIPCIÓN ZONA'] = df_c['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                m_costos['DESCRIPCIÓN ZONA'] = m_costos['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()

                # --- SEMÁFORO DE VALIDACIÓN ---
                codigos_novedad = df_c[~df_c['CODIGO'].isin(m_gp[col_id_gp])]['CODIGO'].unique()
                zonas_novedad = df_c[~df_c['DESCRIPCIÓN ZONA'].isin(m_costos['DESCRIPCIÓN ZONA'])]['DESCRIPCIÓN ZONA'].unique()

                st.subheader("🚥 Semáforo de Validación")
                v1, v2 = st.columns(2)
                error_bloqueante = False
                
                with v1:
                    if len(codigos_novedad) == 0:
                        st.success("✅ Productos: Todos encontrados en Maestro GP.")
                    else:
                        st.error(f"❌ {len(codigos_novedad)} Códigos nuevos NO registrados.")
                        st.write(codigos_novedad)
                        error_bloqueante = True
                
                with v2:
                    if len(zonas_novedad) == 0:
                        st.success("✅ Zonas: Todas tienen precio definido.")
                    else:
                        st.warning(f"⚠️ {len(zonas_novedad)} Zonas sin precio en Maestro Costos.")
                        st.write(zonas_novedad)
                        error_bloqueante = True

                if error_bloqueante:
                    st.error("🛑 Liquidación detenida. Actualiza los Maestros para continuar.")
                else:
                    # --- PROCESAMIENTO ---
                    m_gp_clean = m_gp.drop_duplicates(subset=[col_id_gp])
                    res = pd.merge(df_c, m_gp_clean[[col_id_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_id_gp, how='left')
                    
                    m_costos_clean = m_costos.rename(columns={'PRECIO_PREP': 'PREPARACION', 'PRECIO_TRANS': 'TRANSPORTE'}).drop_duplicates(subset=['DESCRIPCIÓN ZONA'])
                    res = pd.merge(res, m_costos_clean[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')
                    
                    # Cálculos
                    for col in ['BULTOS', 'PREPARACION', 'TRANSPORTE']:
                        res[col] = pd.to_numeric(res[col], errors='coerce').fillna(0)
                    
                    res['VALOR_LOGISTICA'] = (res['PREPARACION'] + res['TRANSPORTE']) * res['BULTOS']

                    # Tabla resumen
                    summary = res.groupby(['GP', 'TIPO'])['VALOR_LOGISTICA'].sum().unstack(fill_value=0).reset_index()
                    for col_t in ['MM', 'MP']:
                        if col_t not in summary.columns: summary[col_t] = 0.0
                    
                    summary['SUBTOTAL'] = summary['MM'] + summary['MP']
                    summary['IVA 15%'] = summary['SUBTOTAL'] * 0.15
                    summary['TOTAL'] = summary['SUBTOTAL'] + summary['IVA 15%']

                    # Fila de Totales
                    tot_row = {'GP': '--- TOTAL GENERAL ---'}
                    for col in summary.columns[1:]: tot_row[col] = summary[col].sum()
                    summary_final = pd.concat([summary, pd.DataFrame([tot_row])], ignore_index=True)

                    st.subheader(f"📋 Liquidación Consolidada: {mes_sel}")
                    st.dataframe(summary_final.style.format(precision=2), use_container_width=True)
                    
                    if st.button(f"💾 Guardar Detalle de {mes_sel} en Histórico"):
                        res['MES_REPORTE'] = mes_sel
                        res['FECHA_REGISTRO'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        if os.path.exists(HISTORICO_FILE):
                            pd.concat([pd.read_csv(HISTORICO_FILE), res], ignore_index=True).to_csv(HISTORICO_FILE, index=False)
                        else:
                            res.to_csv(HISTORICO_FILE, index=False)
                        st.success(f"✅ Datos de {mes_sel} añadidos a la base histórica.")

# --- PESTAÑA 3: HISTORIAL ---
with tabs[2]:
    st.header("🗄️ Base de Datos Histórica")
    if os.path.exists(HISTORICO_FILE):
        h_df = pd.read_csv(HISTORICO_FILE)
        st.dataframe(h_df, use_container_width=True)
        csv_bin = h_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Base Completa (CSV)", csv_bin, "historico_bago_completo.csv", "text/csv")
        
        if st.sidebar.button("🗑️ Vaciar Histórico"):
            os.remove(HISTORICO_FILE)
            st.rerun()
    else:
        st.info("No hay registros históricos almacenados.")
