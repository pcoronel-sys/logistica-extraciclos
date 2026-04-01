import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Laboratorios Bagó - Extra Ciclos", layout="wide", page_icon="🧪")

# --- 🎨 MOTOR DE ESTILOS "GLASS EFECT" PREMIUM 🎨 ---
st.markdown("""
    <style>
    /* Ocultar elementos estándar de Streamlit */
    header, [data-testid="stHeader"], footer { display: none !important; }
    
    /* FONDO DE LA APP CON DEGRADADO SUAVE */
    .stApp {
        background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
    }

    /* --- 🪞 PANTALLA PRINCIPAL: CONTENEDOR EFECTO CRISTAL (GLASSMORPHISM) 🪞 --- */
    .glass-container {
        position: relative;
        margin: auto;
        top: 10vh;
        width: 80%;
        padding: 60px;
        background: rgba(255, 255, 255, 0.45); /* Fondo semi-transparente */
        backdrop-filter: blur(15px); /* DESENFOQUE DE CRISTAL */
        -webkit-backdrop-filter: blur(15px);
        border-radius: 30px;
        border: 1px solid rgba(255, 255, 255, 0.5); /* Borde brillante fino */
        box-shadow: 0 25px 45px rgba(0,0,0,0.05); /* Sombra suave */
        text-align: center;
        z-index: 1;
    }

    /* --- TÍTULOS PREMIUM --- */
    .main-title { 
        background: linear-gradient(90deg, #E91E63 0%, #C2185B 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 60px; font-weight: bold; margin-bottom: 0px; 
    }
    .sub-title { color: #7f8c8d; font-size: 22px; margin-bottom: 60px; font-weight: 300; }
    .almacen-tag { color: #E91E63; font-weight: bold; font-size: 16px; margin-bottom: 15px; letter-spacing: 1px; }
    
    /* --- ⛓️ BOTONES CENTRALES ESTILO RELIEVE/METAL ⛓️ --- */
    /* Botones grandes en el menú principal */
    .stButton>button {
        background: linear-gradient(145deg, #ff216d, #d11c5a) !important;
        color: white !important; font-weight: bold !important; font-size: 17px !important;
        border-radius: 20px !important; border: 1px solid rgba(255,255,255,0.2) !important;
        height: 4em !important; width: 100% !important;
        box-shadow: 5px 5px 15px #c7c9c8, -5px -5px 15px #ffffff !important; /* Relieve neumórfico */
        transition: 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 8px 8px 25px #b8bab9 !important;
        background: linear-gradient(145deg, #ff3d81, #e61f64) !important;
    }
    .stButton>button:active {
        box-shadow: inset 5px 5px 10px #a61647, inset -5px -5px 10px #ff2a83 !important;
    }

    /* --- 📊 ESTILOS PARA EL SISTEMA INTERNO (Mantenidos) --- */
    [data-testid="stTable"] thead tr th {
        background-color: #2C3E50 !important; color: white !important; font-weight: bold !important;
    }
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.6) !important;
        backdrop-filter: blur(5px);
        border-radius: 15px; padding: 20px !important;
        box-shadow: 5px 5px 15px rgba(0,0,0,0.02);
        border: 1px solid rgba(255, 255, 255, 0.4);
    }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE NAVEGACIÓN ---
if 'pagina_actual' not in st.session_state:
    st.session_state['pagina_actual'] = "inicio"

# ---------------------------------------------------------
# PANTALLA DE INICIO (LIMPIA Y CON GLASS EFECT)
# ---------------------------------------------------------
if st.session_state['pagina_actual'] == "inicio":
    
    # Contenedor principal con efecto cristal
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    
    st.markdown("<p style='color:#90a4ae; font-weight:bold; letter-spacing:2px;'>👋 BUENAS TARDES, EQUIPO BAGÓ</p>", unsafe_allow_html=True)
    st.markdown("<h1 class='main-title'>Laboratorios Bagó</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Sistema de Cálculo de Extra Ciclos</p>", unsafe_allow_html=True)

    _, col_btn1, col_btn2, _ = st.columns([0.5, 2, 2, 0.5])
    
    with col_btn1:
        st.markdown("<p class='almacen-tag'>📦 ALMACÉN 1010</p>", unsafe_allow_html=True)
        if st.button("CALCULAR: MATERIAL DE EMPAQUE"):
            st.session_state['pagina_actual'] = "sistema"
            st.rerun()

    with col_btn2:
        st.markdown("<p class='almacen-tag'>🔢 ALMACÉN 1070</p>", unsafe_allow_html=True)
        if st.button("CALCULAR: MATERIAL PROMOCIONAL"):
            st.session_state['pagina_actual'] = "sistema"
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True) # Cerrar contenedor cristal

# ---------------------------------------------------------
# SISTEMA PRINCIPAL (TU CÓDIGO ORIGINAL INTACTO)
# ---------------------------------------------------------
elif st.session_state['pagina_actual'] == "sistema":
    
    # Botón lateral para regresar
    with st.sidebar:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⬅️ REGRESAR AL MENÚ PRINCIPAL"):
            st.session_state['pagina_actual'] = "inicio"
            st.rerun()
        st.markdown("---")

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

    st.title("📊 Auditoría de Cálculo de Extra Ciclos")
    tabs = st.tabs(["🚀 Liquidación", "🔍 Detalle Actual", "⚙️ Configurar Maestros", "🗄️ Historial"])

    m_gp = cargar_maestro(PATH_GP)
    m_costos = cargar_maestro(PATH_COSTOS)

    # --- PESTAÑA 1: LIQUIDACIÓN ---
    with tabs[0]:
        if m_gp is None or m_costos is None: st.warning("⚠️ Cargue los maestros en la pestaña Configurar.")
        else:
            c1, c2 = st.columns([1, 2])
            with c1: mes_sel = st.selectbox("Mes", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
            with c2: archivo = st.file_uploader("Subir Archivo de Movimientos", type=['xlsx', 'xls', 'csv'])

            if archivo:
                df_c = leer_archivo(archivo)
                if df_c is not None:
                    df_c.columns = df_c.columns.str.strip().str.upper()
                    df_c['CODIGO'] = df_c['CODIGO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    df_c['DESCRIPCIÓN ZONA'] = df_c['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                    
                    col_id_gp = [c for c in m_gp.columns if 'CODIGO' in c][0]
                    m_gp_clean = m_gp.copy()
                    m_gp_clean[col_id_gp] = m_gp_clean[col_id_gp].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    m_gp_clean = m_gp_clean.drop_duplicates(subset=[col_id_gp])
                    
                    m_costos_clean = m_costos.copy()
                    m_costos_clean.columns = m_costos_clean.columns.str.strip().str.upper()
                    
                    renames = {}
                    for col in m_costos_clean.columns:
                        if "PREP" in col: renames[col] = "PRECIO_PREP"
                        elif "TRANS" in col: renames[col] = "PRECIO_TRANS"
                        elif "ZONA" in col: renames[col] = "DESCRIPCIÓN ZONA"
                    
                    m_costos_clean = m_costos_clean.rename(columns=renames)
                    m_costos_clean['DESCRIPCIÓN ZONA'] = m_costos_clean['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                    m_costos_clean = m_costos_clean.drop_duplicates(subset=['DESCRIPCIÓN ZONA'])
                    
                    res = pd.merge(df_c, m_gp_clean[[col_id_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_id_gp, how='left')
                    res = pd.merge(res, m_costos_clean[['DESCRIPCIÓN ZONA', 'PRECIO_PREP', 'PRECIO_TRANS']], on='DESCRIPCIÓN ZONA', how='left')
                    
                    for col in ['BULTOS', 'PRECIO_PREP', 'PRECIO_TRANS']:
                        res[col] = pd.to_numeric(res[col], errors='coerce').fillna(0)
                    
                    res['TOTAL PREPARACION'] = res['PRECIO_PREP'] * res['BULTOS']
                    res['TOTAL TRANSPORTE'] = res['PRECIO_TRANS'] * res['BULTOS']
                    res['VALOR_LOGISTICA'] = res['TOTAL PREPARACION'] + res['TOTAL TRANSPORTE']
                    res['IVA 15%'] = res['VALOR_LOGISTICA'] * 0.15
                    res['TOTAL CON IVA'] = res['VALOR_LOGISTICA'] + res['IVA 15%']

                    st.subheader(f"📋 Resumen de Cálculo: {mes_sel}")
                    tipo_f = st.radio("Ver por Tipo:", ["Todos", "Solo MM", "Solo MP"], horizontal=True)
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
            st.subheader(f"📑 Desglose de Auditoría: {st.session_state['mes_actual']}")
            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric("Bultos", f"{df_d['BULTOS'].sum():,.0f}")
            k2.metric("Total Prep.", f"$ {df_d['TOTAL PREPARACION'].sum():,.2f}")
            k3.metric("Total Trans.", f"$ {df_d['TOTAL TRANSPORTE'].sum():,.2f}")
            k4.metric("Valor Neto", f"$ {df_d['VALOR_LOGISTICA'].sum():,.2f}")
            k5.metric("Total c/ IVA", f"$ {df_d['TOTAL CON IVA'].sum():,.2f}")
            st.markdown("---")
            st.dataframe(df_d, use_container_width=True, height=450)
        else: st.info("Procese un archivo primero.")

    # --- PESTAÑAS 3 Y 4 ---
    with tabs[2]:
        st.header("⚙️ Configuración de Maestros")
        ca, cb = st.columns(2)
        with ca:
            ug = st.file_uploader("Actualizar Maestro GP", type=['xlsx', 'xls', 'csv'], key="maestro_gp")
            if ug:
                d = leer_archivo(ug); d.columns = d.columns.str.strip().str.upper()
                guardar_maestro(d, PATH_GP); st.success("GP Guardado.")
        with cb:
            uc = st.file_uploader("Actualizar Maestro Costos", type=['xlsx', 'xls', 'csv'], key="maestro_costos")
            if uc:
                d = leer_archivo(uc); d.columns = d.columns.str.strip().str.upper()
                guardar_maestro(d, PATH_COSTOS); st.success("Costos Guardado.")

    with tabs[3]:
        if os.path.exists(HISTORICO_FILE):
            h = pd.read_csv(HISTORICO_FILE)
            st.subheader("📋 Historial de Cálculos")
            m_del = st.selectbox("Mes a borrar:", sorted(h['MES_REPORTE'].unique()))
            if st.button("❌ Eliminar Periodo"):
                h[h['MES_REPORTE'] != m_del].to_csv(HISTORICO_FILE, index=False); st.rerun()
            st.dataframe(h, use_container_width=True)
