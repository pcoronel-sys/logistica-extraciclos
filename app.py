import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Bagó Logística - Auditoría", layout="wide", page_icon="🧪")

# --- ESTILO CORPORATIVO ---
st.markdown("""
    <style>
    header, [data-testid="stHeader"] { display: none !important; }
    .block-container { padding-top: 1rem !important; }
    .stApp { background-color: #ffffff; }
    [data-testid="stTable"] thead tr th {
        background-color: #2C3E50 !important; color: white !important; font-weight: bold !important;
    }
    div[data-testid="stMetric"] {
        background-color: #fcfcfc; border-left: 6px solid #4CA1AF; border-radius: 10px; padding: 15px !important;
    }
    .stButton>button {
        background: linear-gradient(90deg, #2C3E50 0%, #4CA1AF 100%) !important;
        color: white !important; font-weight: bold !important; border-radius: 10px !important;
    }
    .login-box {
        margin: auto; padding: 30px; border-radius: 10px;
        background-color: #f8f9fa; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        width: 320px; text-align: center; margin-top: 10vh;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SEGURIDAD ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    _, col_cent, _ = st.columns([1, 1, 1])
    with col_cent:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.subheader("Bagó Logística")
        u = st.text_input("Usuario", placeholder="Usuario", label_visibility="collapsed")
        p = st.text_input("Clave", type="password", placeholder="Contraseña", label_visibility="collapsed")
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
                # 1. Normalización de Carga
                df_c.columns = df_c.columns.str.strip().str.upper()
                df_c['CODIGO'] = df_c['CODIGO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                df_c['DESCRIPCIÓN ZONA'] = df_c['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                
                # 2. Normalización Maestro GP
                col_id_gp = [c for c in m_gp.columns if 'CODIGO' in c][0]
                m_gp_clean = m_gp.copy()
                m_gp_clean[col_id_gp] = m_gp_clean[col_id_gp].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                m_gp_clean = m_gp_clean.drop_duplicates(subset=[col_id_gp])
                
                # 3. NORMALIZACIÓN INTELIGENTE DE MAESTRO COSTOS (Solución al KeyError)
                m_costos_clean = m_costos.copy()
                m_costos_clean.columns = m_costos_clean.columns.str.strip().str.upper()
                
                # Mapeo de nombres posibles para evitar el error
                rename_dict = {}
                for col in m_costos_clean.columns:
                    if "PREP" in col: rename_dict[col] = "PRECIO_PREP"
                    if "TRANS" in col: rename_dict[col] = "PRECIO_TRANS"
                    if "ZONA" in col: rename_dict[col] = "DESCRIPCIÓN ZONA"
                
                m_costos_clean = m_costos_clean.rename(columns=rename_dict)
                m_costos_clean['DESCRIPCIÓN ZONA'] = m_costos_clean['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                m_costos_clean = m_costos_clean.drop_duplicates(subset=['DESCRIPCIÓN ZONA'])
                
                # 4. CRUCE (MERGE) - Ahora las columnas se llaman PRECIO_PREP y PRECIO_TRANS sí o sí
                res = pd.merge(df_c, m_gp_clean[[col_id_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_id_gp, how='left')
                res = pd.merge(res, m_costos_clean[['DESCRIPCIÓN ZONA', 'PRECIO_PREP', 'PRECIO_TRANS']], on='DESCRIPCIÓN ZONA', how='left')
                
                # 5. CÁLCULOS
                for col in ['BULTOS', 'PRECIO_PREP', 'PRECIO_TRANS']:
                    res[col] = pd.to_numeric(res[col], errors='coerce').fillna(0)
                
                res['TOTAL PREPARACION'] = res['PRECIO_PREP'] * res['BULTOS']
                res['TOTAL TRANSPORTE'] = res['PRECIO_TRANS'] * res['BULTOS']
                res['VALOR_LOGISTICA'] = res['TOTAL PREPARACION'] + res['TOTAL TRANSPORTE']
                res['IVA 15%'] = res['VALOR_LOGISTICA'] * 0.15
                res['TOTAL CON IVA'] = res['VALOR_LOGISTICA'] + res['IVA 15%']

                # 6. REPORTE
                st.subheader(f"📋 Resumen: {mes_sel}")
                tipo_f = st.radio("Ver:", ["Todos", "Solo MM", "Solo MP"], horizontal=True)
                
                summary = res.groupby(['GP', 'TIPO'])['VALOR_LOGISTICA'].sum().unstack(fill_value=0).reset_index()
                for c in ['MM', 'MP']: 
                    if c not in summary.columns: summary[c] = 0.0
                
                if tipo_f == "Solo MM": summary = summary[['GP', 'MM']]
                elif tipo_f == "Solo MP": summary = summary[['GP', 'MP']]
                
                summary['SUBTOTAL'] = summary.iloc[:, 1:].sum(axis=1)
                summary['IVA 15%'] = summary['SUBTOTAL'] * 0.15
                summary['TOTAL GENERAL'] = summary['SUBTOTAL'] + summary['IVA 15%']

                tot = {'GP': '--- TOTALES ---'}
                for col in summary.columns[1:]: tot[col] = summary[col].sum()
                summary_f = pd.concat([summary, pd.DataFrame([tot])], ignore_index=True)

                st.table(summary_f.style.format(precision=2).set_properties(**{'background-color': '#2C3E50', 'color': 'white', 'font-weight': 'bold'}, subset=pd.IndexSlice[summary_f.index[-1], :]))
                
                st.session_state['res_actual'] = res
                st.session_state['mes_actual'] = mes_sel
                if st.button("💾 Guardar en Historial"):
                    res['MES_REPORTE'] = mes_sel
                    res['FECHA_REGISTRO'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    pd.concat([pd.read_csv(HISTORICO_FILE) if os.path.exists(HISTORICO_FILE) else pd.DataFrame(), res], ignore_index=True).to_csv(HISTORICO_FILE, index=False)
                    st.success("Guardado.")

# --- PESTAÑA 2: DETALLE ---
with tabs[1]:
    if 'res_actual' in st.session_state:
        df_d = st.session_state['res_actual']
        st.subheader(f"📑 Auditoría: {st.session_state['mes_actual']}")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Bultos", f"{df_d['BULTOS'].sum():,.0f}")
        k2.metric("Neto", f"$ {df_d['VALOR_LOGISTICA'].sum():,.2f}")
        k3.metric("IVA 15%", f"$ {df_d['IVA 15%'].sum():,.2f}")
        k4.metric("Total", f"$ {df_d['TOTAL CON IVA'].sum():,.2f}")
        st.dataframe(df_d, use_container_width=True, height=400)
    else: st.info("Procese un archivo primero.")

# --- PESTAÑAS 3 Y 4 ---
with tabs[2]:
    st.header("⚙️ Configuración")
    ca, cb = st.columns(2)
    with ca:
        ug = st.file_uploader("Maestro GP", type=['xlsx', 'xls', 'csv'], key="ug")
        if ug:
            d = leer_archivo(ug); d.columns = d.columns.str.strip().str.upper()
            guardar_maestro(d, PATH_GP); st.success("GP Guardado.")
    with cb:
        uc = st.file_uploader("Maestro Costos", type=['xlsx', 'xls', 'csv'], key="uc")
        if uc:
            d = leer_archivo(uc); d.columns = d.columns.str.strip().str.upper()
            guardar_maestro(d, PATH_COSTOS); st.success("Costos Guardado.")

with tabs[3]:
    if os.path.exists(HISTORICO_FILE):
        h = pd.read_csv(HISTORICO_FILE)
        m_del = st.selectbox("Borrar mes:", sorted(h['MES_REPORTE'].unique()))
        if st.button("Eliminar"):
            h[h['MES_REPORTE'] != m_del].to_csv(HISTORICO_FILE, index=False); st.rerun()
        st.dataframe(h, use_container_width=True)
