import streamlit as st
import pandas as pd
import os
import io
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Laboratorios Bagó - Conciliación Extra Ciclos", layout="wide", page_icon="🧪")

# --- DISEÑO ESTÉTICO UI/UX PRO ---
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
                df_c = leer_archivo(archivo)
                if df_c is not None:
                    # Limpieza y Normalización
                    df_c.columns = df_c.columns.str.strip().str.upper()
                    df_c['CODIGO'] = df_c['CODIGO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    df_c['DESCRIPCIÓN ZONA'] = df_c['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                    df_c['BULTOS'] = pd.to_numeric(df_c['BULTOS'], errors='coerce').fillna(0)
                    
                    col_id_gp = [c for c in m_gp.columns if 'CODIGO' in c.upper()][0]
                    m_gp_clean = m_gp.copy().drop_duplicates(subset=[col_id_gp])
                    m_gp_clean[col_id_gp] = m_gp_clean[col_id_gp].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    
                    m_costos_clean = m_costos.copy()
                    m_costos_clean.columns = m_costos_clean.columns.str.strip().str.upper()
                    renames = {c: "P_PREP" for c in m_costos_clean.columns if "PREP" in c}
                    renames.update({c: "P_TRANS" for c in m_costos_clean.columns if "TRANS" in c})
                    renames.update({c: "DESCRIPCIÓN ZONA" for c in m_costos_clean.columns if "ZONA" in c})
                    m_costos_clean = m_costos_clean.rename(columns=renames).drop_duplicates(subset=['DESCRIPCIÓN ZONA'])
                    m_costos_clean['DESCRIPCIÓN ZONA'] = m_costos_clean['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                    
                    # Cruce
                    res = pd.merge(df_c, m_gp_clean[[col_id_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_id_gp, how='left')
                    res = pd.merge(res, m_costos_clean[['DESCRIPCIÓN ZONA', 'P_PREP', 'P_TRANS']], on='DESCRIPCIÓN ZONA', how='left')

                    # Validación
                    faltan_gp = res[res['GP'].isna()]['CODIGO'].unique()
                    faltan_costo = res[res['P_PREP'].isna() | res['P_TRANS'].isna()]['DESCRIPCIÓN ZONA'].unique()

                    if len(faltan_gp) > 0 or len(faltan_costo) > 0:
                        st.error("🛑 BLOQUEADO: Datos incompletos.")
                        e1, e2 = st.columns(2)
                        with e1: st.warning(f"Sin GP: {len(faltan_gp)}"); st.write(faltan_gp)
                        with e2: st.warning(f"Sin Tarifa: {len(faltan_costo)}"); st.write(faltan_costo)
                    else:
                        # Cálculos Segregados
                        res['TOTAL_PREPARACION'] = res['P_PREP'] * res['BULTOS']
                        res['TOTAL_TRANSPORTE'] = res['P_TRANS'] * res['BULTOS']
                        res['SUBTOTAL_NETO'] = res['TOTAL_PREPARACION'] + res['TOTAL_TRANSPORTE']
                        res['IVA_15'] = res['SUBTOTAL_NETO'] * 0.15
                        res['TOTAL_FINAL'] = res['SUBTOTAL_NETO'] + res['IVA_15']

                        st.subheader(f"📋 Resumen Consolidado: {mes_sel}")
                        
                        # Tabla Resumen MM / MP
                        summary = res.pivot_table(index='GP', columns='TIPO', values='SUBTOTAL_NETO', aggfunc='sum').fillna(0)
                        for col in ['MM', 'MP']:
                            if col not in summary.columns: summary[col] = 0.0
                        
                        summary['SUBTOTAL'] = summary['MM'] + summary['MP']
                        summary['IVA 15%'] = summary['SUBTOTAL'] * 0.15
                        summary['TOTAL GENERAL'] = summary['SUBTOTAL'] + summary['IVA 15%']

                        summary_reset = summary.reset_index()
                        tot_vals = summary_reset.select_dtypes(include=['number']).sum()
                        fila_total = pd.DataFrame([{'GP': '--- TOTALES ---', **tot_vals}])
                        summary_f = pd.concat([summary_reset, fila_total], ignore_index=True)

                        st.table(summary_f.style.format(subset=summary_f.columns[1:], formatter="{:,.2f}"))
                        
                        if st.button("💾 Guardar en Historial"):
                            res['MES_PROCESO'] = mes_sel
                            res['FECHA_REGISTRO'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                            res.to_csv(HISTORICO_FILE, mode='a', index=False, header=not os.path.exists(HISTORICO_FILE))
                            st.success(f"Datos de {mes_sel} guardados.")

                        st.session_state['res_actual'] = res
                        st.session_state['mes_actual'] = mes_sel

    with tabs[1]: # DETALLE ACTUAL (Métricas Segregadas)
        if 'res_actual' in st.session_state:
            df_d = st.session_state['res_actual']
            
            # --- KPIs SEGREGADOS POR PREPARACIÓN Y TRANSPORTE ---
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Bultos Totales", f"{df_d['BULTOS'].sum():,.0f}")
            m2.metric("Total Preparación", f"$ {df_d['TOTAL_PREPARACION'].sum():,.2f}")
            m3.metric("Total Transporte", f"$ {df_d['TOTAL_TRANSPORTE'].sum():,.2f}")
            m4.metric("Total c/ IVA", f"$ {df_d['TOTAL_FINAL'].sum():,.2f}")
            
            st.divider()
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_d.to_excel(writer, index=False, sheet_name='Detalle_Logistica')
            st.download_button("📥 Descargar Reporte Excel", output.getvalue(), f"Liquidacion_{st.session_state['mes_actual']}.xlsx")
            
            st.dataframe(df_d, use_container_width=True)
        else:
            st.info("Sin datos procesados.")

    with tabs[2]: # CONFIG
        st.header("⚙️ Maestros")
        ca, cb = st.columns(2)
        with ca:
            ug = st.file_uploader("Cargar Maestro GP", type=['xlsx', 'xls', 'csv'])
            if ug:
                d = leer_archivo(ug); d.columns = d.columns.str.strip().str.upper()
                d.to_csv(PATH_GP, index=False); st.success("GP actualizado.")
        with cb:
            uc = st.file_uploader("Cargar Maestro Costos", type=['xlsx', 'xls', 'csv'])
            if uc:
                d = leer_archivo(uc); d.columns = d.columns.str.strip().str.upper()
                d.to_csv(PATH_COSTOS, index=False); st.success("Costos actualizado.")

    with tabs[3]: # HISTORIAL
        st.header("🗄️ Histórico")
        if os.path.exists(HISTORICO_FILE):
            df_hist = pd.read_csv(HISTORICO_FILE)
            sel_m = st.selectbox("Mes:", df_hist['MES_PROCESO'].unique())
            v_hist = df_hist[df_hist['MES_PROCESO'] == sel_m]
            
            out_h = io.BytesIO()
            with pd.ExcelWriter(out_h, engine='openpyxl') as writer:
                v_hist.to_excel(writer, index=False, sheet_name='Historico')
            st.download_button(f"📥 Exportar {sel_m}", out_h.getvalue(), f"Historial_{sel_m}.xlsx")
            st.dataframe(v_hist)
