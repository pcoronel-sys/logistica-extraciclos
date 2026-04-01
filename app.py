import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Gestión Bagó Pro", layout="wide", page_icon="🧪")

# --- CSS: LOGIN LIMPIO Y TABLAS BAGO ---
st.markdown("""
    <style>
    header, [data-testid="stHeader"] { display: none !important; }
    .block-container { padding-top: 2rem !important; }
    .stApp { background-color: #ffffff; }
    
    /* ENCABEZADOS DE TABLAS AZUL PROFUNDO */
    [data-testid="stTable"] thead tr th {
        background-color: #2C3E50 !important;
        color: white !important;
        font-weight: bold !important;
        text-align: center !important;
    }
    
    /* TARJETAS DE MÉTRICAS */
    div[data-testid="stMetric"] {
        background-color: #fcfcfc;
        border-left: 6px solid #4CA1AF;
        border-radius: 10px;
        padding: 15px !important;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }

    .login-box {
        margin: auto; padding: 30px; border-radius: 10px;
        background-color: #f8f9fa; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: 1px solid #eeeeee; width: 320px; text-align: center; margin-top: 10vh;
    }

    .stTextInput input { height: 35px !important; text-align: center !important; }
    .stButton>button { background: #2C3E50 !important; color: white !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# --- SEGURIDAD ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    _, col_cent, _ = st.columns([1, 1, 1])
    with col_cent:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown("<h3 style='color: #2C3E50; margin-bottom: 5px;'>Bagó Logística</h3>", unsafe_allow_html=True)
        u = st.text_input("Usuario", label_visibility="collapsed", placeholder="Usuario")
        p = st.text_input("Clave", type="password", label_visibility="collapsed", placeholder="Contraseña")
        if st.button("ENTRAR"):
            if u == "admin" and p == "bago2024":
                st.session_state['autenticado'] = True
                st.rerun()
            else: st.error("Acceso denegado")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- RUTAS ---
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

# --- APP PRINCIPAL ---
st.title("📊 Control de Liquidación Logística")
tabs = st.tabs(["🚀 Liquidación Mensual", "🔍 Detalle de Carga Actual", "⚙️ Configurar Maestros", "🗄️ Historial"])

m_gp = cargar_maestro(PATH_GP)
m_costos = cargar_maestro(PATH_COSTOS)

with tabs[0]:
    if m_gp is None or m_costos is None: st.warning("⚠️ Cargue los maestros.")
    else:
        c1, c2 = st.columns([1, 2])
        with c1: mes_sel = st.selectbox("Mes", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
        with c2: archivo = st.file_uploader("Subir Carga", type=['xlsx', 'xls', 'csv'])

        if archivo:
            df_c = leer_archivo(archivo)
            if df_c is not None:
                df_c.columns = df_c.columns.str.strip().str.upper()
                df_c['CODIGO'] = df_c['CODIGO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                col_id_gp = [c for c in m_gp.columns if 'CODIGO' in c][0]
                m_gp[col_id_gp] = m_gp[col_id_gp].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                
                # CRUCE DE DATOS
                res = pd.merge(df_c, m_gp.drop_duplicates(subset=[col_id_gp])[[col_id_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_id_gp, how='left')
                m_c = m_costos.rename(columns={'PRECIO_PREP': 'PREPARACION', 'PRECIO_TRANS': 'TRANSPORTE'}).drop_duplicates(subset=['DESCRIPCIÓN ZONA'])
                res = pd.merge(res, m_c[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')
                
                # CÁLCULOS
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

                # FILA DE TOTALES GENERALES
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

with tabs[1]:
    if 'res_actual' in st.session_state:
        df_d = st.session_state['res_actual']
        st.subheader(f"📑 Detalle - {st.session_state['mes_actual']}")
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Bultos", f"{df_d['BULTOS'].sum():,.0f}")
        k2.metric("Prep.", f"$ {df_d['TOTAL PREPARACION'].sum():,.2f}")
        k3.metric("Trans.", f"$ {df_d['TOTAL TRANSPORTE'].sum():,.2f}")
        k4.metric("Neto", f"$ {df_d['VALOR_LOGISTICA'].sum():,.2f}")
        k5.metric("Total IVA", f"$ {df_d['TOTAL CON IVA'].sum():,.2f}")
        
        bus = st.text_input("🔍 Buscar en el detalle:", "").upper()
        df_v = df_d[df_d.astype(str).apply(lambda x: x.str.contains(bus)).any(axis=1)] if bus else df_d
        st.dataframe(df_v, use_container_width=True)

with tabs[2]:
    st.header("⚙️ Configuración")
    ca, cb = st.columns(2)
    with ca:
        ug = st.file_uploader("Maestro GP", type=['xlsx', 'xls', 'csv'], key="ug")
        if ug:
            d = leer_archivo(ug)
            if d is not None:
                d.columns = d.columns.str.strip().str.upper()
                guardar_maestro(d, PATH_GP); st.success("GP Guardado.")
    with cb:
        uc = st.file_uploader("Maestro Costos", type=['xlsx', 'xls', 'csv'], key="uc")
        if uc:
            d = leer_archivo(uc)
            if d is not None:
                d.columns = d.columns.str.strip().str.upper()
                guardar_maestro(d, PATH_COSTOS); st.success("Costos Guardado.")

with tabs[3]:
    if os.path.exists(HISTORICO_FILE):
        h = pd.read_csv(HISTORICO_FILE)
        with st.expander("🗑️ Borrar Mes Específico"):
            m = st.selectbox("Mes a borrar:", sorted(h['MES_REPORTE'].unique()))
            if st.button("Eliminar"):
                h[h['MES_REPORTE'] != m].to_csv(HISTORICO_FILE, index=False)
                st.rerun()
        st.dataframe(h, use_container_width=True)
