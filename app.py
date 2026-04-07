import streamlit as st
import pandas as pd
import os
import io
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Laboratorios Bagó - Conciliación Extra Ciclos", layout="wide", page_icon="🧪")

# --- DISEÑO ESTÉTICO UI/UX PRO (INTACTO) ---
MAGENTA_BAGO = "#C7006A" 
MAGENTA_OSCURO = "#8A004A"

st.markdown(f"""
    <style>
    header, [data-testid="stHeader"] {{ display: none !important; }}
    .main {{ background: radial-gradient(circle at top right, #ffffff, #f0f2f6); }}
    .welcome-text {{ text-align: center; color: #888; font-size: 1.2rem; font-weight: 300; letter-spacing: 2px; text-transform: uppercase; margin-bottom: -10px; }}
    .main-title {{ color: {MAGENTA_BAGO}; font-size: 5rem !important; font-weight: 900 !important; text-align: center; margin-top: 0px; letter-spacing: -4px; filter: drop-shadow(0px 10px 15px rgba(199, 0, 106, 0.2)); line-height: 1; }}
    
    div.stButton > button {{ 
        background: rgba(250, 255, 255, 0.7) !important; 
        backdrop-filter: blur(15px) !important; 
        color: #333 !important; 
        border: 1px solid rgba(200, 200, 200, 0.3) !important; 
        border-radius: 20px !important; 
        height: 150px !important; 
        width: 100% !important; 
        box-shadow: 0 20px 40px rgba(0,0,0,0.05) !important; 
        transition: all 0.6s cubic-bezier(0.165, 0.84, 0.44, 1.0) !important; 
        font-size: 1.4rem !important; 
        font-weight: 800 !important; 
    }}
    div.stButton > button:hover {{ 
        background: linear-gradient(135deg, {MAGENTA_BAGO} 0%, {MAGENTA_OSCURO} 100%) !important; 
        color: white !important; 
        transform: translateY(-15px) scale(1.03) !important; 
    }}
    
    [data-testid="stSidebar"] {{ background-color: white !important; border-right: 1px solid #eee; }}
    [data-testid="stTable"] thead tr th {{ background-color: #2C3E50 !important; color: white !important; font-weight: bold !important; }}
    div[data-testid="stMetric"] {{ background: white !important; border-radius: 20px !important; padding: 20px !important; border-left: 8px solid {MAGENTA_BAGO} !important; box-shadow: 0 10px 20px rgba(0,0,0,0.04) !important; }}
    
    .small-btn button {{
        height: auto !important;
        padding: 5px 15px !important;
        font-size: 0.8rem !important;
        background: #ff4b4b22 !important;
        color: #ff4b4b !important;
        border: 1px solid #ff4b4b !important;
    }}
    </style>
    """, unsafe_allow_html=True)

if 'pagina_actual' not in st.session_state:
    st.session_state['pagina_actual'] = "inicio"

hora_ajustada = (datetime.now() - timedelta(hours=5)).hour
saludo_txt = "☀️ Buenos días" if 5 <= hora_ajustada < 12 else "🌤️ Buenas tardes" if 12 <= hora_ajustada < 19 else "🌙 Buenas noches"

# ---------------------------------------------------------
# PANTALLA 1: INICIO
# ---------------------------------------------------------
if st.session_state['pagina_actual'] == "inicio":
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f'<p class="welcome-text">{saludo_txt},</p>', unsafe_allow_html=True)
    st.markdown('<p class="main-title">Laboratorios Bagó</p>', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:#555; font-weight:300; margin-bottom:60px;'>SISTEMA DE CONCILIACION DE EXTRA CICLOS </h3>", unsafe_allow_html=True)
    
    _, col_l, col_r, _ = st.columns([6.5, 1.8, 1.8, 6.5])
    with col_l:
        if st.button("\n\n EXTRA CICLOS"):
            st.session_state['pagina_actual'] = "sistema" 
            st.rerun()
    with col_r:
        if st.button("\n REPROGRAMA"):
            st.toast("Módulo en desarrollo...", icon="⚠️")

# ---------------------------------------------------------
# PANTALLA 2: SISTEMA PRINCIPAL
# ---------------------------------------------------------
elif st.session_state['pagina_actual'] == "sistema":
    if st.sidebar.button("⬅️ Volver al Menú Principal"):
        st.session_state['pagina_actual'] = "inicio"
        st.rerun()

    PATH_GP = "master_gp.csv"
    PATH_COSTOS = "master_costos.csv"
    HISTORICO_FILE = "base_historica_bago.csv"

    def cargar_maestro(path): return pd.read_csv(path) if os.path.exists(path) else None
    def leer_archivo(archivo):
        try:
            if archivo.name.lower().endswith(('.xlsx', '.xls')): return pd.read_excel(archivo)
            return pd.read_csv(archivo, encoding='latin-1')
        except: return None

    st.title("📊 Control de Liquidación Logística")
    tabs = st.tabs(["🚀 Liquidación Mensual", "🔍 Detalle Actual", "⚙️ Configurar Maestros", "🗄️ Historial"])

    m_gp = cargar_maestro(PATH_GP)
    m_costos = cargar_maestro(PATH_COSTOS)

    with tabs[0]: # LIQUIDACIÓN
        if m_gp is None or m_costos is None: 
            st.warning("⚠️ Cargue los maestros en la pestaña Configurar.")
        else:
            c1, c2 = st.columns([1, 2])
            with c1: mes_sel = st.selectbox("Mes", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
            with c2: archivo = st.file_uploader("Subir Carga Mensual", type=['xlsx', 'xls', 'csv'])

            if archivo:
                df_raw = leer_archivo(archivo)
                if df_raw is not None:
                    # 1. CONSOLIDACIÓN DE CARGA (Suma bultos si hay filas repetidas en el Excel)
                    df_raw.columns = df_raw.columns.str.strip().str.upper()
                    df_raw['CODIGO'] = df_raw['CODIGO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.upper()
                    df_raw['DESCRIPCIÓN ZONA'] = df_raw['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                    df_raw['BULTOS'] = pd.to_numeric(df_raw['BULTOS'], errors='coerce').fillna(0)
                    df_c = df_raw.groupby(['CODIGO', 'DESCRIPCIÓN ZONA'], as_index=False)['BULTOS'].sum()
                    
                    # 2. LIMPIEZA DE MAESTROS (Fuerza registros únicos para evitar duplicados)
                    col_id_gp = [c for c in m_gp.columns if 'CODIGO' in c.upper()][0]
                    m_gp_clean = m_gp.copy().drop_duplicates(subset=[col_id_gp])
                    m_gp_clean[col_id_gp] = m_gp_clean[col_id_gp].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.upper()
                    
                    m_costos_clean = m_costos.copy()
                    m_costos_clean.columns = m_costos_clean.columns.str.strip().str.upper()
                    ren = {c: "P_PREP" for c in m_costos_clean.columns if "PREP" in c}
                    ren.update({c: "P_TRANS" for c in m_costos_clean.columns if "TRANS" in c})
                    ren.update({c: "DESCRIPCIÓN ZONA" for c in m_costos_clean.columns if "ZONA" in c})
                    m_costos_clean = m_costos_clean.rename(columns=ren).drop_duplicates(subset=['DESCRIPCIÓN ZONA'])
                    m_costos_clean['DESCRIPCIÓN ZONA'] = m_costos_clean['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                    
                    # 3. MAPEADO (Diccionarios para evitar MERGE que duplica filas)
                    dict_gp = m_gp_clean.set_index(col_id_gp)['GP'].to_dict()
                    dict_tipo = m_gp_clean.set_index(col_id_gp)['TIPO'].to_dict()
                    dict_prep = m_costos_clean.set_index('DESCRIPCIÓN ZONA')['P_PREP'].to_dict()
                    dict_trans = m_costos_clean.set_index('DESCRIPCIÓN ZONA')['P_TRANS'].to_dict()

                    res = df_c.copy()
                    res['GP'] = res['CODIGO'].map(dict_gp)
                    res['TIPO'] = res['CODIGO'].map(dict_tipo)
                    res['P_PREP'] = res['DESCRIPCIÓN ZONA'].map(dict_prep)
                    res['P_TRANS'] = res['DESCRIPCIÓN ZONA'].map(dict_trans)

                    # 4. VALIDACIÓN DE ERRORES
                    sin_gp = res[res['GP'].isna()]['CODIGO'].unique()
                    sin_tar = res[res['P_PREP'].isna()]['DESCRIPCIÓN ZONA'].unique()

                    if len(sin_gp) > 0 or len(sin_tar) > 0:
                        st.error("🛑 BLOQUEO: Hay datos en el Excel que no existen en tus Maestros.")
                        col1, col2 = st.columns(2)
                        with col1:
                            if len(sin_gp) > 0: st.warning(f"❌ Códigos sin GP: {list(sin_gp)}")
                        with col2:
                            if len(sin_tar) > 0: st.warning(f"❌ Zonas sin Tarifa: {list(sin_tar)}")
                    else:
                        # 5. CÁLCULOS
                        res['TOTAL_PREPARACION'] = res['P_PREP'] * res['BULTOS']
                        res['TOTAL_TRANSPORTE'] = res['P_TRANS'] * res['BULTOS']
                        res['SUBTOTAL_NETO'] = res['TOTAL_PREPARACION'] + res['TOTAL_TRANSPORTE']
                        res['IVA_15'] = res['SUBTOTAL_NETO'] * 0.15
                        res['TOTAL_FINAL'] = res['SUBTOTAL_NETO'] + res['IVA_15']

                        st.subheader(f"📋 Resumen Consolidado: {mes_sel}")
                        summary = res.pivot_table(index='GP', columns='TIPO', values='SUBTOTAL_NETO', aggfunc='sum').fillna(0)
                        for col in ['MM', 'MP']:
                            if col not in summary.columns: summary[col] = 0.0
                        
                        summary['SUBTOTAL'] = summary['MM'] + summary['MP']
                        summary['IVA 15%'] = summary['SUBTOTAL'] * 0.15
                        summary['TOTAL GENERAL'] = summary['SUBTOTAL'] + summary['IVA 15%']
                        
                        summary_f = pd.concat([summary.reset_index(), pd.DataFrame([{'GP': '--- TOTALES ---', **summary.sum()}])], ignore_index=True)
                        st.table(summary_f.style.format(subset=summary_f.columns[1:], formatter="{:,.2f}"))
                        
                        if st.button("💾 Guardar en Historial"):
                            res['MES_PROCESO'] = mes_sel
                            existe = os.path.exists(HISTORICO_FILE)
                            res.to_csv(HISTORICO_FILE, mode='a', index=False, header=not existe)
                            st.success(f"¡Datos de {mes_sel} añadidos correctamente!")

                        st.session_state['res_actual'] = res
                        st.session_state['mes_actual'] = mes_sel

    with tabs[1]: # DETALLE ACTUAL (KPIs)
        if 'res_actual' in st.session_state:
            df_full = st.session_state['res_actual']
            st.markdown("### 🔍 Filtros de Búsqueda")
            f1, f2, f3 = st.columns(3)
            with f1: sel_gp = st.multiselect("Filtrar por GP", options=sorted(df_full['GP'].unique()))
            with f2: sel_tipo = st.multiselect("Filtrar por Tipo", options=sorted(df_full['TIPO'].unique()))
            with f3: sel_zona = st.multiselect("Filtrar por Zona", options=sorted(df_full['DESCRIPCIÓN ZONA'].unique()))

            df_v = df_full.copy()
            if sel_gp: df_v = df_v[df_v['GP'].isin(sel_gp)]
            if sel_tipo: df_v = df_v[df_v['TIPO'].isin(sel_tipo)]
            if sel_zona: df_v = df_v[df_v['DESCRIPCIÓN ZONA'].isin(sel_zona)]

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Bultos Filtrados", f"{df_v['BULTOS'].sum():,.0f}")
            k2.metric("Preparación", f"$ {df_v['TOTAL_PREPARACION'].sum():,.2f}")
            k3.metric("Transporte", f"$ {df_v['TOTAL_TRANSPORTE'].sum():,.2f}")
            k4.metric("Total Final", f"$ {df_v['TOTAL_FINAL'].sum():,.2f}")
            
            st.divider()
            st.dataframe(df_v, use_container_width=True)

    with tabs[2]: # CONFIG
        st.header("⚙️ Maestros")
        ca, cb = st.columns(2)
        with ca:
            ug = st.file_uploader("Cargar GP", type=['csv','xlsx'])
            if ug: d = leer_archivo(ug); d.to_csv(PATH_GP, index=False); st.success("GP OK")
        with cb:
            uc = st.file_uploader("Cargar Costos", type=['csv','xlsx'])
            if uc: d = leer_archivo(uc); d.to_csv(PATH_COSTOS, index=False); st.success("Costos OK")

    with tabs[3]: # HISTORIAL
        st.header("🗄️ Historial")
        if os.path.exists(HISTORICO_FILE):
            df_h = pd.read_csv(HISTORICO_FILE)
            meses_disponibles = df_h['MES_PROCESO'].dropna().unique()
            opciones_mes = sorted([str(m) for m in meses_disponibles])
            if opciones_mes:
                m_h = st.selectbox("Ver Mes:", opciones_mes)
                st.dataframe(df_h[df_h['MES_PROCESO'] == m_h], use_container_width=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                col_b, _ = st.columns([1, 4])
                with col_b:
                    st.markdown('<div class="small-btn">', unsafe_allow_html=True)
                    if st.button(f"🗑️ Eliminar historial de {m_h}", key="del_btn"):
                        df_h = df_h[df_h['MES_PROCESO'] != m_h]
                        df_h.to_csv(HISTORICO_FILE, index=False)
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
