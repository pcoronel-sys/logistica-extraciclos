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

# --- NAVEGACIÓN ---
st.title("🚀 Gestión Logística Inteligente - Bagó")
tabs = st.tabs(["📊 Liquidación Mensual", "🔍 Detalle de Carga Actual", "⚙️ Configurar Maestros", "🗄️ Historial"])

with tabs[2]:
    st.header("⚙️ Actualización de Bases Maestras")
    c1, c2 = st.columns(2)
    with c1:
        u_gp = st.file_uploader("Subir Maestro GP", type=['xlsx', 'xls', 'csv'], key="ugp")
        if u_gp:
            df_u_gp = leer_archivo_protegido(u_gp)
            if df_u_gp is not None:
                df_u_gp.columns = df_u_gp.columns.str.strip().str.upper()
                guardar_maestro(df_u_gp, PATH_GP); st.success("✅ Maestro GP actualizado.")

    with c2:
        u_costos = st.file_uploader("Subir Maestro Costos", type=['xlsx', 'xls', 'csv'], key="ucostos")
        if u_costos:
            df_u_costos = leer_archivo_protegido(u_costos)
            if df_u_costos is not None:
                df_u_costos.columns = df_u_costos.columns.str.strip().str.upper()
                guardar_maestro(df_u_costos, PATH_COSTOS); st.success("✅ Maestro de Costos actualizado.")

m_gp = cargar_maestro(PATH_GP)
m_costos = cargar_maestro(PATH_COSTOS)

with tabs[0]:
    if m_gp is None or m_costos is None: st.warning("⚠️ Configura los Maestros primero.")
    else:
        col_m, col_f = st.columns([1, 2])
        with col_m: mes_sel = st.selectbox("Mes", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
        with col_f: archivo_carga = st.file_uploader("📂 Subir Bultos", type=['xlsx', 'xls'])

        if archivo_carga:
            df_c = leer_archivo_protegido(archivo_carga)
            if df_c is not None:
                df_c.columns = df_c.columns.str.strip().str.upper()
                df_c['CODIGO'] = df_c['CODIGO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                col_id_gp = [c for c in m_gp.columns if 'CODIGO' in c][0]
                m_gp[col_id_gp] = m_gp[col_id_gp].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                df_c['DESCRIPCIÓN ZONA'] = df_c['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                m_costos['DESCRIPCIÓN ZONA'] = m_costos['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()

                cod_nov = df_c[~df_c['CODIGO'].isin(m_gp[col_id_gp])]['CODIGO'].unique()
                zon_nov = df_c[~df_c['DESCRIPCIÓN ZONA'].isin(m_costos['DESCRIPCIÓN ZONA'])]['DESCRIPCIÓN ZONA'].unique()

                st.subheader("🚥 Validación")
                v1, v2 = st.columns(2)
                err = False
                with v1:
                    if len(cod_nov) == 0: st.success("✅ Productos OK")
                    else: st.error(f"❌ {len(cod_nov)} Faltantes"); st.write(cod_nov); err = True
                with v2:
                    if len(zon_nov) == 0: st.success("✅ Zonas OK")
                    else: st.warning(f"⚠️ {len(zon_nov)} Sin precio"); st.write(zon_nov); err = True

                if not err:
                    res = pd.merge(df_c, m_gp.drop_duplicates(subset=[col_id_gp])[[col_id_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_id_gp, how='left')
                    m_c_c = m_costos.rename(columns={'PRECIO_PREP': 'PREPARACION', 'PRECIO_TRANS': 'TRANSPORTE'}).drop_duplicates(subset=['DESCRIPCIÓN ZONA'])
                    res = pd.merge(res, m_c_c[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')
                    
                    for col in ['BULTOS', 'PREPARACION', 'TRANSPORTE']: res[col] = pd.to_numeric(res[col], errors='coerce').fillna(0)
                    
                    res['TOTAL PREPARACION'] = res['PREPARACION'] * res['BULTOS']
                    res['TOTAL TRANSPORTE'] = res['TRANSPORTE'] * res['BULTOS']
                    res['VALOR_LOGISTICA'] = res['TOTAL PREPARACION'] + res['TOTAL TRANSPORTE']
                    res['IVA 15%'] = res['VALOR_LOGISTICA'] * 0.15
                    res['TOTAL CON IVA'] = res['VALOR_LOGISTICA'] + res['IVA 15%']

                    st.markdown("---")
                    st.subheader(f"📋 Reporte de Liquidación: {mes_sel}")
                    
                    summary = res.groupby(['GP', 'TIPO'])['VALOR_LOGISTICA'].sum().unstack(fill_value=0).reset_index()
                    for c in ['MM', 'MP']: 
                        if c not in summary.columns: summary[c] = 0.0
                    summary['SUBTOTAL'] = summary['MM'] + summary['MP']
                    summary['IVA 15%'] = summary['SUBTOTAL'] * 0.15
                    summary['TOTAL'] = summary['SUBTOTAL'] + summary['IVA 15%']

                    busqueda = st.text_input("🔍 Buscar Gerente:", "")
                    summary_view = summary[summary['GP'].str.contains(busqueda.upper())] if busqueda else summary

                    tot = {'GP': '--- TOTAL GENERAL ---'}
                    for col in summary_view.columns[1:]: tot[col] = summary_view[col].sum()
                    summary_final = pd.concat([summary_view, pd.DataFrame([tot])], ignore_index=True)

                    # TABLA BONITA SIN LIBRERÍAS EXTERNAS
                    st.dataframe(
                        summary_final.style.format(precision=2)
                        .set_properties(**{'background-color': '#fdf2f8', 'color': '#E10078', 'font-weight': 'bold'}, subset=['TOTAL'])
                        .set_properties(**{'background-color': '#E10078', 'color': 'white', 'font-weight': 'bold'}, subset=pd.IndexSlice[summary_final.index[-1], :])
                        , use_container_width=True
                    )
                    
                    st.session_state['res_actual'] = res
                    st.session_state['mes_actual'] = mes_sel
                    
                    if st.button(f"💾 Guardar datos"):
                        res['MES_REPORTE'] = mes_sel
                        res['FECHA_REGISTRO'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        pd.concat([pd.read_csv(HISTORICO_FILE) if os.path.exists(HISTORICO_FILE) else pd.DataFrame(), res], ignore_index=True).to_csv(HISTORICO_FILE, index=False)
                        st.success("Guardado.")

with tabs[1]:
    st.header("🔍 Detalle de Carga Actual")
    if 'res_actual' in st.session_state:
        df_det_view = st.session_state['res_actual'].copy()
        
        tot_det = {'CODIGO': 'TOTALES', 'BULTOS': df_det_view['BULTOS'].sum(), 'TOTAL PREPARACION': df_det_view['TOTAL PREPARACION'].sum(), 'TOTAL TRANSPORTE': df_det_view['TOTAL TRANSPORTE'].sum(), 'VALOR_LOGISTICA': df_det_view['VALOR_LOGISTICA'].sum(), 'IVA 15%': df_det_view['IVA 15%'].sum(), 'TOTAL CON IVA': df_det_view['TOTAL CON IVA'].sum()}
        df_det_final = pd.concat([df_det_view, pd.DataFrame([tot_det])], ignore_index=True)
        
        # Formato de dinero manual para evitar errores
        cols_m = ['PREPARACION', 'TRANSPORTE', 'TOTAL PREPARACION', 'TOTAL TRANSPORTE', 'VALOR_LOGISTICA', 'IVA 15%', 'TOTAL CON IVA']
        
        st.dataframe(
            df_det_final.style.format({c: "{:.2f}" for c in cols_m if c in df_det_final.columns}, na_rep="")
            .set_properties(**{'background-color': '#fdf2f8', 'font-weight': 'bold'}, subset=['TOTAL CON IVA'])
            .set_properties(**{'background-color': '#E10078', 'color': 'white', 'font-weight': 'bold'}, subset=pd.IndexSlice[df_det_final.index[-1], :])
            , use_container_width=True
        )
    else: st.info("Procesa un archivo primero.")

with tabs[3]:
    st.header("🗄️ Histórico")
    if os.path.exists(HISTORICO_FILE):
        h_df = pd.read_csv(HISTORICO_FILE)
        st.dataframe(h_df, use_container_width=True)
        st.download_button("📥 Descargar", h_df.to_csv(index=False).encode('utf-8'), "historico.csv", "text/csv")
    else: st.info("Sin datos.")
