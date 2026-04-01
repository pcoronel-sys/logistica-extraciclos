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
    div[data-testid="stMetric"] {
        background: #ffffff;
        border-radius: 12px;
        border: 1px solid #f0f0f0;
        border-top: 5px solid #E10078;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        padding: 20px !important;
    }
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
    try:
        nombre_lower = archivo.name.lower()
        if nombre_lower.endswith(('.xlsx', '.xls')):
            return pd.read_excel(archivo)
        else:
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
tabs = st.tabs(["📊 Liquidación Mensual", "🔍 Detalle de Carga Actual", "⚙️ Configurar Maestros", "🗄️ Historial"])

# --- PESTAÑA 3: CONFIGURAR MAESTROS ---
with tabs[2]:
    st.header("⚙️ Actualización de Bases Maestras")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Maestro GP (Productos y Tipos)")
        u_gp = st.file_uploader("Subir Maestro GP", type=['xlsx', 'xls', 'csv'], key="ugp")
        if u_gp:
            df_u_gp = leer_archivo_protegido(u_gp)
            if df_u_gp is not None:
                df_u_gp.columns = df_u_gp.columns.str.strip().str.upper()
                guardar_maestro(df_u_gp, PATH_GP)
                st.success(f"✅ Maestro GP actualizado.")

    with c2:
        st.subheader("Maestro Costos (Zonas y Precios)")
        u_costos = st.file_uploader("Subir Maestro Costos", type=['xlsx', 'xls', 'csv'], key="ucostos")
        if u_costos:
            df_u_costos = leer_archivo_protegido(u_costos)
            if df_u_costos is not None:
                df_u_costos.columns = df_u_costos.columns.str.strip().str.upper()
                guardar_maestro(df_u_costos, PATH_COSTOS)
                st.success(f"✅ Maestro de Costos actualizado.")

m_gp = cargar_maestro(PATH_GP)
m_costos = cargar_maestro(PATH_COSTOS)

# --- PESTAÑA 1: LIQUIDACIÓN ---
with tabs[0]:
    if m_gp is None or m_costos is None:
        st.warning("⚠️ Configura los Maestros primero en la pestaña correspondiente.")
    else:
        col_m, col_f = st.columns([1, 2])
        with col_m:
            mes_sel = st.selectbox("Mes de Carga", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
        with col_f:
            archivo_carga = st.file_uploader("📂 Subir archivo de Bultos", type=['xlsx', 'xls'])

        if archivo_carga:
            df_c = leer_archivo_protegido(archivo_carga)
            if df_c is not None:
                df_c.columns = df_c.columns.str.strip().str.upper()
                df_c['CODIGO'] = df_c['CODIGO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                col_id_gp = [c for c in m_gp.columns if 'CODIGO' in c][0]
                m_gp[col_id_gp] = m_gp[col_id_gp].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                df_c['DESCRIPCIÓN ZONA'] = df_c['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                m_costos['DESCRIPCIÓN ZONA'] = m_costos['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()

                # SEMÁFORO
                cod_nov = df_c[~df_c['CODIGO'].isin(m_gp[col_id_gp])]['CODIGO'].unique()
                zon_nov = df_c[~df_c['DESCRIPCIÓN ZONA'].isin(m_costos['DESCRIPCIÓN ZONA'])]['DESCRIPCIÓN ZONA'].unique()

                st.subheader("🚥 Validación")
                v1, v2 = st.columns(2)
                err = False
                with v1:
                    if len(cod_nov) == 0: st.success("✅ Productos OK")
                    else: st.error(f"❌ {len(cod_nov)} Códigos faltantes"); st.write(cod_nov); err = True
                with v2:
                    if len(zon_nov) == 0: st.success("✅ Zonas OK")
                    else: st.warning(f"⚠️ {len(zon_nov)} Zonas sin precio"); st.write(zon_nov); err = True

                if not err:
                    # PROCESAMIENTO
                    res = pd.merge(df_c, m_gp.drop_duplicates(subset=[col_id_gp])[[col_id_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_id_gp, how='left')
                    m_c_c = m_costos.rename(columns={'PRECIO_PREP': 'PREPARACION', 'PRECIO_TRANS': 'TRANSPORTE'}).drop_duplicates(subset=['DESCRIPCIÓN ZONA'])
                    res = pd.merge(res, m_c_c[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')
                    
                    for col in ['BULTOS', 'PREPARACION', 'TRANSPORTE']:
                        res[col] = pd.to_numeric(res[col], errors='coerce').fillna(0)
                    
                    # CÁLCULOS ADICIONALES PARA EL DETALLE
                    res['TOTAL PREPARACION'] = res['PREPARACION'] * res['BULTOS']
                    res['TOTAL TRANSPORTE'] = res['TRANSPORTE'] * res['BULTOS']
                    res['VALOR_LOGISTICA'] = res['TOTAL PREPARACION'] + res['TOTAL TRANSPORTE']

                    # --- REPORTE CONSOLIDADO ---
                    st.markdown("---")
                    st.subheader(f"📋 Reporte de Liquidación: {mes_sel}")
                    
                    summary = res.groupby(['GP', 'TIPO'])['VALOR_LOGISTICA'].sum().unstack(fill_value=0).reset_index()
                    for c in ['MM', 'MP']: 
                        if c not in summary.columns: summary[c] = 0.0
                    summary['SUBTOTAL'] = summary['MM'] + summary['MP']
                    summary['IVA 15%'] = summary['SUBTOTAL'] * 0.15
                    summary['TOTAL'] = summary['SUBTOTAL'] + summary['IVA 15%']

                    # BUSCADOR DINÁMICO
                    busqueda = st.text_input("🔍 Buscar por nombre de Gerente (GP):", "")
                    summary_view = summary[summary['GP'].str.contains(busqueda.upper())] if busqueda else summary

                    # Fila de Totales para el resumen
                    tot = {'GP': '--- TOTAL GENERAL ---'}
                    for col in summary_view.columns[1:]: tot[col] = summary_view[col].sum()
                    summary_final = pd.concat([summary_view, pd.DataFrame([tot])], ignore_index=True)

                    st.dataframe(summary_final.style.format(precision=2), use_container_width=True)
                    
                    # Guardar el procesamiento en el estado de la sesión
                    st.session_state['res_actual'] = res
                    st.session_state['mes_actual'] = mes_sel
                    
                    if st.button(f"💾 Guardar datos de {mes_sel}"):
                        res['MES_REPORTE'] = mes_sel
                        res['FECHA_REGISTRO'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        pd.concat([pd.read_csv(HISTORICO_FILE) if os.path.exists(HISTORICO_FILE) else pd.DataFrame(), res], ignore_index=True).to_csv(HISTORICO_FILE, index=False)
                        st.success("Guardado en Histórico.")

# --- PESTAÑA 2: DETALLE DE CARGA ACTUAL ---
with tabs[1]:
    st.header("🔍 Detalle de la Carga Procesada")
    if 'res_actual' in st.session_state:
        df_detalle = st.session_state['res_actual']
        st.write(f"Mostrando el detalle para el mes de **{st.session_state['mes_actual']}**")
        
        bus_det = st.text_input("🔍 Filtrar detalle:", "", key="bus_det")
        df_det_view = df_detalle[df_detalle.astype(str).apply(lambda x: x.str.contains(bus_det.upper())).any(axis=1)] if bus_det else df_detalle

        # Fila de totales para el detalle (Añadiendo las nuevas columnas multiplicadas)
        tot_det = {
            'CODIGO': 'TOTALES', 
            'BULTOS': df_det_view['BULTOS'].sum(),
            'TOTAL PREPARACION': df_det_view['TOTAL PREPARACION'].sum(),
            'TOTAL TRANSPORTE': df_det_view['TOTAL TRANSPORTE'].sum(),
            'VALOR_LOGISTICA': df_det_view['VALOR_LOGISTICA'].sum()
        }
        df_det_final = pd.concat([df_det_view, pd.DataFrame([tot_det])], ignore_index=True).fillna("")
        
        # Formatear columnas de dinero
        cols_dinero = ['PREPARACION', 'TRANSPORTE', 'TOTAL PREPARACION', 'TOTAL TRANSPORTE', 'VALOR_LOGISTICA']
        st.dataframe(df_det_final.style.format({c: "{:.2f}" for c in cols_dinero if c in df_det_final.columns}), use_container_width=True)
    else:
        st.info("Primero sube y procesa un archivo en la pestaña 'Liquidación Mensual'.")

# --- PESTAÑA 4: HISTORIAL ---
with tabs[3]:
    st.header("🗄️ Histórico de Movimientos")
    if os.path.exists(HISTORICO_FILE):
        h_df = pd.read_csv(HISTORICO_FILE)
        st.dataframe(h_df, use_container_width=True)
        st.download_button("📥 Descargar Todo el Histórico", h_df.to_csv(index=False).encode('utf-8'), "historico_completo.csv", "text/csv")
    else: st.info("Sin datos históricos.")
