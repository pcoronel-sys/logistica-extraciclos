import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Gestión Bagó", layout="wide", page_icon="🧪")

# --- USUARIO Y CONTRASEÑA ---
USUARIO_PRO = "admin"
CLAVE_PRO = "bago2024"

# --- ESTILO CORPORATIVO ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
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
    .stButton>button {
        background: linear-gradient(90deg, #2C3E50 0%, #4CA1AF 100%);
        color: white; border-radius: 10px; border: none;
        font-weight: bold; height: 3em; width: 100%;
    }
    /* Estilo Login Centrado */
    .login-container { display: flex; justify-content: center; align-items: center; width: 100%; margin-top: 15vh; }
    .login-box { padding: 40px; border-radius: 15px; background-color: #f8f9fa; box-shadow: 0 4px 15px rgba(0,0,0,0.1); width: 100%; max-width: 400px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE SESIÓN ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-container"><div class="login-box">', unsafe_allow_html=True)
        st.title("Bagó Logística")
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("Ingresar"):
            if u == USUARIO_PRO and p == CLAVE_PRO:
                st.session_state['autenticado'] = True
                st.rerun()
            else: st.error("Incorrecto")
        st.markdown('</div></div>', unsafe_allow_html=True)
    st.stop()

# --- BARRA LATERAL LIMPIA ---
st.sidebar.success(f"Usuario: {USUARIO_PRO}")
if st.sidebar.button("Cerrar Sesión"):
    st.session_state['autenticado'] = False
    st.rerun()

# --- RUTAS DE ARCHIVOS ---
PATH_GP = "master_gp.csv"
PATH_COSTOS = "master_costos.csv"
HISTORICO_FILE = "base_historica_bago.csv"

def cargar_maestro(path): return pd.read_csv(path) if os.path.exists(path) else None
def leer_archivo(archivo):
    try:
        if archivo.name.lower().endswith(('.xlsx', '.xls')): return pd.read_excel(archivo)
        return pd.read_csv(archivo, encoding='latin-1')
    except: return None

# --- NAVEGACIÓN ---
st.title("📊 Control de Liquidación Logística")
tabs = st.tabs(["🚀 Liquidación Mensual", "🔍 Detalle de Carga Actual", "⚙️ Configurar Maestros", "🗄️ Historial"])

m_gp = cargar_maestro(PATH_GP)
m_costos = cargar_maestro(PATH_COSTOS)

# --- PESTAÑA 1: LIQUIDACIÓN ---
with tabs[0]:
    if m_gp is None or m_costos is None: st.warning("Configure maestros primero.")
    else:
        c1, c2 = st.columns([1, 2])
        with c1: mes_sel = st.selectbox("Mes", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
        with c2: archivo = st.file_uploader("Subir Excel", type=['xlsx', 'xls', 'csv'])

        if archivo:
            df = leer_archivo(archivo)
            if df is not None:
                df.columns = df.columns.str.strip().str.upper()
                df['CODIGO'] = df['CODIGO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                col_id_gp = [c for c in m_gp.columns if 'CODIGO' in c][0]
                m_gp[col_id_gp] = m_gp[col_id_gp].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                
                res = pd.merge(df, m_gp[[col_id_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_id_gp, how='left')
                m_c = m_costos.rename(columns={'PRECIO_PREP': 'PREPARACION', 'PRECIO_TRANS': 'TRANSPORTE'})
                res = pd.merge(res, m_c[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')
                
                for c in ['BULTOS', 'PREPARACION', 'TRANSPORTE']: res[c] = pd.to_numeric(res[c], errors='coerce').fillna(0)
                res['TOTAL PREPARACION'] = res['PREPARACION'] * res['BULTOS']
                res['TOTAL TRANSPORTE'] = res['TRANSPORTE'] * res['BULTOS']
                res['VALOR_LOGISTICA'] = res['TOTAL PREPARACION'] + res['TOTAL TRANSPORTE']
                res['IVA 15%'] = res['VALOR_LOGISTICA'] * 0.15
                res['TOTAL CON IVA'] = res['VALOR_LOGISTICA'] + res['IVA 15%']

                st.subheader(f"Reporte: {mes_sel}")
                summary = res.groupby(['GP', 'TIPO'])['VALOR_LOGISTICA'].sum().unstack(fill_value=0).reset_index()
                for c in ['MM', 'MP']: 
                    if c not in summary.columns: summary[c] = 0.0
                summary['SUBTOTAL'] = summary['MM'] + summary['MP']
                summary['IVA 15%'] = summary['SUBTOTAL'] * 0.15
                summary['TOTAL'] = summary['SUBTOTAL'] + summary['IVA 15%']

                st.table(summary.style.format(precision=2))
                st.session_state['res_actual'] = res
                st.session_state['mes_actual'] = mes_sel
                if st.button(f"💾 Guardar Periodo {mes_sel}"):
                    res['MES_REPORTE'] = mes_sel
                    res['FECHA_REGISTRO'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    pd.concat([pd.read_csv(HISTORICO_FILE) if os.path.exists(HISTORICO_FILE) else pd.DataFrame(), res], ignore_index=True).to_csv(HISTORICO_FILE, index=False)
                    st.success("Guardado.")

# --- PESTAÑA 2: DETALLE ---
with tabs[1]:
    if 'res_actual' in st.session_state:
        df_v = st.session_state['res_actual']
        st.subheader(f"Auditoría - {st.session_state['mes_actual']}")
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Bultos", f"{df_v['BULTOS'].sum():,.0f}")
        k2.metric("Prep.", f"$ {df_v['TOTAL PREPARACION'].sum():,.2f}")
        k3.metric("Trans.", f"$ {df_v['TOTAL TRANSPORTE'].sum():,.2f}")
        k4.metric("Neto", f"$ {df_v['VALOR_LOGISTICA'].sum():,.2f}")
        k5.metric("Total IVA", f"$ {df_v['TOTAL CON IVA'].sum():,.2f}")
        st.dataframe(df_v, use_container_width=True)
    else: st.info("Sin datos.")

# --- PESTAÑA 3: CONFIG ---
with tabs[2]:
    st.header("Configuración de Maestros")
    # Lógica de carga de maestros omitida por brevedad (igual a la anterior)

# --- PESTAÑA 4: HISTORIAL Y ELIMINACIÓN ---
with tabs[3]:
    st.header("🗄️ Historial de Reportes")
    if os.path.exists(HISTORICO_FILE):
        h_df = pd.read_csv(HISTORICO_FILE)
        
        # --- SECCIÓN ELIMINAR ---
        with st.expander("🗑️ Zona de Peligro: Eliminar Datos"):
            meses_disp = sorted(h_df['MES_REPORTE'].unique())
            mes_a_borrar = st.selectbox("Seleccione el mes que desea ELIMINAR:", meses_disp)
            if st.button(f"Confirmar Eliminación de {mes_a_borrar}"):
                nuevo_h = h_df[h_df['MES_REPORTE'] != mes_a_borrar]
                nuevo_h.to_csv(HISTORICO_FILE, index=False)
                st.error(f"Se han eliminado todos los registros de {mes_a_borrar}.")
                st.rerun()

        st.markdown("---")
        st.subheader("Registros Almacenados")
        st.dataframe(h_df, use_container_width=True)
    else:
        st.info("No hay datos históricos grabados.")
