import streamlit as st
import pandas as pd
import os
import io
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE RUTAS Y ARCHIVOS ---
PATH_GP = "master_gp.csv"
PATH_COSTOS = "master_costos.csv"
HISTORICO_FILE = "base_historica_bago.csv"

PATH_GP_REPRO = "master_gp_repro.csv"
PATH_COSTOS_REPRO = "master_costos_repro.csv"
HISTORICO_REPRO_FILE = "base_historica_repro.csv"

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Laboratorios Bagó - Conciliación Extra Ciclos", layout="wide", page_icon="🧪")

# --- DISEÑO ESTÉTICO UI/UX PRO (ESTILOS BAGO) ---
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

# --- FUNCIONES DE SOPORTE ---
def cargar_maestro(path): return pd.read_csv(path) if os.path.exists(path) else None

def leer_archivo(archivo):
    try:
        if archivo.name.lower().endswith(('.xlsx', '.xls')): return pd.read_excel(archivo)
        return pd.read_csv(archivo, encoding='latin-1')
    except: return None

def format_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos')
    return output.getvalue()

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
            st.session_state['pagina_actual'] = "sistema_reprograma" 
            st.rerun()

# ---------------------------------------------------------
# PANTALLA 2: SISTEMA PRINCIPAL (EXTRA CICLOS)
# ---------------------------------------------------------
elif st.session_state['pagina_actual'] == "sistema":
    if st.sidebar.button("⬅️ Volver al Menú Principal"):
        st.session_state['pagina_actual'] = "inicio"
        st.rerun()

    m_gp = cargar_maestro(PATH_GP)
    m_costos = cargar_maestro(PATH_COSTOS)

    tabs = st.tabs(["🚀 Liquidación Mensual", "🔍 Detalle Actual", "⚙️ Configurar Maestros", "🗄️ Historial"])

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
                    df_c.columns = df_c.columns.str.strip().str.upper()
                    df_c['CODIGO'] = df_c['CODIGO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    df_c['DESCRIPCIÓN ZONA'] = df_c['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                    df_c['BULTOS'] = pd.to_numeric(df_c['BULTOS'], errors='coerce').fillna(0)
                    
                    col_id_gp = [c for c in m_gp.columns if 'CODIGO' in c.upper()][0]
                    m_gp_clean = m_gp.copy()
                    m_gp_clean[col_id_gp] = m_gp_clean[col_id_gp].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    m_gp_clean = m_gp_clean.drop_duplicates(subset=[col_id_gp])
                    
                    m_costos_clean = m_costos.copy()
                    m_costos_clean.columns = m_costos_clean.columns.str.strip().str.upper()
                    renames = {c: "P_PREP" for c in m_costos_clean.columns if "PREP" in c}
                    renames.update({c: "P_TRANS" for c in m_costos_clean.columns if "TRANS" in c})
                    renames.update({c: "DESCRIPCIÓN ZONA" for c in m_costos_clean.columns if "ZONA" in c})
                    m_costos_clean = m_costos_clean.rename(columns=renames)
                    m_costos_clean['DESCRIPCIÓN ZONA'] = m_costos_clean['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                    m_costos_clean['P_PREP'] = pd.to_numeric(m_costos_clean['P_PREP'], errors='coerce').fillna(0)
                    m_costos_clean['P_TRANS'] = pd.to_numeric(m_costos_clean['P_TRANS'], errors='coerce').fillna(0)
                    m_costos_clean = m_costos_clean.drop_duplicates(subset=['DESCRIPCIÓN ZONA'])
                    
                    res = pd.merge(df_c, m_gp_clean[[col_id_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_id_gp, how='left')
                    res = pd.merge(res, m_costos_clean[['DESCRIPCIÓN ZONA', 'P_PREP', 'P_TRANS']], on='DESCRIPCIÓN ZONA', how='left')

                    if res['GP'].isna().any() or res['P_PREP'].isna().any():
                        st.error("🛑 BLOQUEO: Hay códigos o zonas sin registro.")
                        st.write("Códigos Faltantes:", res[res['GP'].isna()]['CODIGO'].unique())
                        st.write("Zonas Faltantes:", res[res['P_PREP'].isna()]['DESCRIPCIÓN ZONA'].unique())
                    else:
                        res['TOTAL_PREPARACION'] = res['P_PREP'] * res['BULTOS']
                        res['TOTAL_TRANSPORTE'] = res['P_TRANS'] * res['BULTOS']
                        res['SUBTOTAL_NETO'] = res['TOTAL_PREPARACION'] + res['TOTAL_TRANSPORTE']
                        res['IVA_15'] = res['SUBTOTAL_NETO'] * 0.15
                        res['TOTAL_FINAL'] = res['SUBTOTAL_NETO'] + res['IVA_15']

                        st.subheader(f"📋 Resumen: {mes_sel}")
                        summary = res.pivot_table(index='GP', columns='TIPO', values='SUBTOTAL_NETO', aggfunc='sum').fillna(0)
                        for col in ['MM', 'MP']:
                            if col not in summary.columns: summary[col] = 0.0
                        
                        summary['SUBTOTAL'] = summary['MM'] + summary['MP']
                        summary['IVA 15%'] = summary['SUBTOTAL'] * 0.15
                        summary['TOTAL GENERAL'] = summary['SUBTOTAL'] + summary['IVA 15%']
                        
                        summary_f = pd.concat([summary.reset_index(), pd.DataFrame([{'GP': '--- TOTALES ---', **summary.sum()}])], ignore_index=True)
                        st.table(summary_f.style.format(subset=summary_f.columns[1:], formatter="{:,.2f}"))
                        st.download_button("📥 Descargar Resumen", format_excel(summary_f), f"Resumen_{mes_sel}.xlsx")

                        if st.button("💾 Guardar en Historial (Anti-Duplicados)"):
                            res['MES_PROCESO'] = mes_sel
                            if os.path.exists(HISTORICO_FILE):
                                df_h_old = pd.read_csv(HISTORICO_FILE)
                                df_h_old = df_h_old[df_h_old['MES_PROCESO'] != mes_sel]
                                pd.concat([df_h_old, res]).to_csv(HISTORICO_FILE, index=False)
                            else:
                                res.to_csv(HISTORICO_FILE, index=False)
                            st.success("Guardado correctamente.")

                        st.session_state['res_actual'] = res
                        st.session_state['mes_actual'] = mes_sel

    with tabs[1]: # DETALLE ACTUAL
        if 'res_actual' in st.session_state:
            df_full = st.session_state['res_actual']
            st.markdown("### 🔍 Filtros")
            f1, f2, f3 = st.columns(3)
            with f1: sel_gp = st.multiselect("GP", options=sorted(df_full['GP'].unique()))
            with f2: sel_tipo = st.multiselect("Tipo", options=sorted(df_full['TIPO'].unique()))
            with f3: sel_zona = st.multiselect("Zona", options=sorted(df_full['DESCRIPCIÓN ZONA'].unique()))

            df_v = df_full.copy()
            if sel_gp: df_v = df_v[df_v['GP'].isin(sel_gp)]
            if sel_tipo: df_v = df_v[df_v['TIPO'].isin(sel_tipo)]
            if sel_zona: df_v = df_v[df_v['DESCRIPCIÓN ZONA'].isin(sel_zona)]

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Bultos", f"{df_v['BULTOS'].sum():,.0f}")
            k2.metric("Prep.", f"$ {df_v['TOTAL_PREPARACION'].sum():,.2f}")
            k3.metric("Trans.", f"$ {df_v['TOTAL_TRANSPORTE'].sum():,.2f}")
            k4.metric("Total Final", f"$ {df_v['TOTAL_FINAL'].sum():,.2f}")
            
            st.divider()
            st.download_button("📥 Descargar Detalle Filtrado", format_excel(df_v), f"Detalle_{st.session_state['mes_actual']}.xlsx")
            st.dataframe(df_v, use_container_width=True)

    with tabs[2]: # CONFIGURACIÓN
        st.header("⚙️ Maestros")
        ca, cb = st.columns(2)
        with ca:
            ug = st.file_uploader("Cargar GP", type=['csv','xlsx'])
            if ug:
                d = leer_archivo(ug)
                if d is not None: d.to_csv(PATH_GP, index=False); st.success("GP OK")
        with cb:
            uc = st.file_uploader("Cargar Costos", type=['csv','xlsx'])
            if uc:
                d = leer_archivo(uc)
                if d is not None: d.to_csv(PATH_COSTOS, index=False); st.success("Costos OK")

    with tabs[3]: # HISTORIAL
        st.header("🗄️ Historial")
        if os.path.exists(HISTORICO_FILE):
            df_h = pd.read_csv(HISTORICO_FILE)
            for col in ['TOTAL_FINAL', 'BULTOS', 'TOTAL_PREPARACION', 'TOTAL_TRANSPORTE']:
                if col in df_h.columns:
                    df_h[col] = pd.to_numeric(df_h[col], errors='coerce').fillna(0)
            
            opciones_mes = sorted([str(x) for x in df_h['MES_PROCESO'].dropna().unique()])
            if opciones_mes:
                m_h = st.selectbox("Ver Mes:", opciones_mes)
                df_mostrar = df_h[df_h['MES_PROCESO'] == m_h]
                h1, h2, h3 = st.columns(3)
                h1.metric("Bultos Históricos", f"{df_mostrar['BULTOS'].sum():,.0f}")
                h2.metric("Total Facturado", f"$ {df_mostrar['TOTAL_FINAL'].sum():,.2f}")
                h3.metric("Registros", len(df_mostrar))
                st.dataframe(df_mostrar, use_container_width=True)
                
                if st.button(f"🗑️ Eliminar historial de {m_h}", key="del_hist"):
                    df_h = df_h[df_h['MES_PROCESO'] != m_h]
                    df_h.to_csv(HISTORICO_FILE, index=False)
                    st.rerun()
            else:
                st.info("No hay meses válidos en el historial.")
        else:
            st.info("Archivo historial no encontrado.")
# ---------------------------------------------------------
# PANTALLA 3: SISTEMA REPROGRAMA (ESPEJO VV CON DESGLOSE)
# ---------------------------------------------------------
elif st.session_state['pagina_actual'] == "sistema_reprograma":
    if st.sidebar.button("⬅️ Volver al Menú Principal"):
        st.session_state['pagina_actual'] = "inicio"
        st.rerun()

    m_gp_r = cargar_maestro(PATH_GP_REPRO)
    m_costos_r = cargar_maestro(PATH_COSTOS_REPRO)

    tabs = st.tabs(["🚀 Liquidación VV", "🔍 Detalle VV", "⚙️ Configurar Reprograma", "🗄️ Historial VV"])

    with tabs[0]: # TAB 0: LIQUIDACIÓN VV
        if m_gp_r is None or m_costos_r is None: 
            st.warning("⚠️ Cargue los maestros específicos para Reprograma en la pestaña Configurar.")
        else:
            c1, c2 = st.columns([1, 2])
            with c1: mes_sel = st.selectbox("Mes Reprograma", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], key="mes_repro_sel")
            with c2: archivo = st.file_uploader("Subir Carga Reprograma", type=['xlsx', 'xls', 'csv'], key="file_repro_up")

            if archivo:
                df_c = leer_archivo(archivo)
                if df_c is not None:
                    df_c.columns = df_c.columns.str.strip().str.upper()
                    df_c['CODIGO'] = df_c['CODIGO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    df_c['DESCRIPCIÓN ZONA'] = df_c['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                    df_c['BULTOS'] = pd.to_numeric(df_c['BULTOS'], errors='coerce').fillna(0)
                    
                    col_id_gp = [c for c in m_gp_r.columns if 'CODIGO' in c.upper()][0]
                    m_gp_clean = m_gp_r.copy()
                    m_gp_clean[col_id_gp] = m_gp_clean[col_id_gp].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    m_gp_clean = m_gp_clean.drop_duplicates(subset=[col_id_gp])
                    
                    m_costos_clean = m_costos_r.copy()
                    m_costos_clean.columns = m_costos_clean.columns.str.strip().str.upper()
                    renames = {c: "P_PREP" for c in m_costos_clean.columns if "PREP" in c}
                    renames.update({c: "P_TRANS" for c in m_costos_clean.columns if "TRANS" in c})
                    renames.update({c: "DESCRIPCIÓN ZONA" for c in m_costos_clean.columns if "ZONA" in c})
                    m_costos_clean = m_costos_clean.rename(columns=renames)
                    m_costos_clean['DESCRIPCIÓN ZONA'] = m_costos_clean['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                    m_costos_clean['P_PREP'] = pd.to_numeric(m_costos_clean['P_PREP'], errors='coerce').fillna(0)
                    m_costos_clean['P_TRANS'] = pd.to_numeric(m_costos_clean['P_TRANS'], errors='coerce').fillna(0)
                    m_costos_clean = m_costos_clean.drop_duplicates(subset=['DESCRIPCIÓN ZONA'])
                    
                    res = pd.merge(df_c, m_gp_clean[[col_id_gp, 'GP']], left_on='CODIGO', right_on=col_id_gp, how='left')
                    res = pd.merge(res, m_costos_clean[['DESCRIPCIÓN ZONA', 'P_PREP', 'P_TRANS']], on='DESCRIPCIÓN ZONA', how='left')

                    if res['GP'].isna().any() or res['P_PREP'].isna().any():
                        st.error("🛑 BLOQUEO REPROGRAMA: Datos faltantes.")
                        st.write("Códigos Faltantes:", res[res['GP'].isna()]['CODIGO'].unique())
                        st.write("Zonas Faltantes:", res[res['P_PREP'].isna()]['DESCRIPCIÓN ZONA'].unique())
                    else:
                        # Cálculos desglosados
                        res['TOTAL_PREPARACION'] = res['P_PREP'] * res['BULTOS']
                        res['TOTAL_TRANSPORTE'] = res['P_TRANS'] * res['BULTOS']
                        res['SUBTOTAL_NETO'] = res['TOTAL_PREPARACION'] + res['TOTAL_TRANSPORTE']
                        res['IVA_15'] = res['SUBTOTAL_NETO'] * 0.15
                        res['TOTAL_FINAL'] = res['SUBTOTAL_NETO'] + res['IVA_15']

                        st.subheader(f"📋 Resumen Desglosado VV: {mes_sel}")
                        
                        # Resumen por GP con desglose de rubros
                        summary = res.groupby('GP').agg({
                            'TOTAL_PREPARACION': 'sum',
                            'TOTAL_TRANSPORTE': 'sum',
                            'SUBTOTAL_NETO': 'sum'
                        }).reset_index()
                        
                        summary['IVA 15%'] = summary['SUBTOTAL_NETO'] * 0.15
                        summary['TOTAL GENERAL'] = summary['SUBTOTAL_NETO'] + summary['IVA 15%']
                        
                        summary_f = pd.concat([summary, pd.DataFrame([{
                            'GP': '--- TOTALES ---', 
                            'TOTAL_PREPARACION': summary['TOTAL_PREPARACION'].sum(),
                            'TOTAL_TRANSPORTE': summary['TOTAL_TRANSPORTE'].sum(),
                            'SUBTOTAL_NETO': summary['SUBTOTAL_NETO'].sum(), 
                            'IVA 15%': summary['IVA 15%'].sum(), 
                            'TOTAL GENERAL': summary['TOTAL GENERAL'].sum()
                        }])], ignore_index=True)
                        
                        st.table(summary_f.style.format(subset=summary_f.columns[1:], formatter="{:,.2f}"))
                        st.download_button("📥 Descargar Resumen VV", format_excel(summary_f), f"Resumen_VV_{mes_sel}.xlsx")

                        if st.button("💾 Guardar Reprograma en Historial"):
                            res['MES_PROCESO'] = mes_sel
                            if os.path.exists(HISTORICO_REPRO_FILE):
                                df_h_old = pd.read_csv(HISTORICO_REPRO_FILE)
                                df_h_old = df_h_old[df_h_old['MES_PROCESO'] != mes_sel]
                                pd.concat([df_h_old, res]).to_csv(HISTORICO_REPRO_FILE, index=False)
                            else:
                                res.to_csv(HISTORICO_REPRO_FILE, index=False)
                            st.success("Guardado correctamente.")

                        st.session_state['res_repro'] = res
                        st.session_state['mes_repro_actual'] = mes_sel

    with tabs[1]: # TAB 1: DETALLE VV (KPIs DESGLOSADOS)
        if 'res_repro' in st.session_state:
            df_full_r = st.session_state['res_repro']
            
            st.markdown("### 🔍 Análisis Detallado VV")
            f1, f2 = st.columns(2)
            with f1: sel_gp_r = st.multiselect("Filtrar por GP", options=sorted(df_full_r['GP'].unique()), key="f_gp_r")
            with f2: sel_zona_r = st.multiselect("Filtrar por Zona", options=sorted(df_full_r['DESCRIPCIÓN ZONA'].unique()), key="f_zona_r")

            df_v_r = df_full_r.copy()
            if sel_gp_r: df_v_r = df_v_r[df_v_r['GP'].isin(sel_gp_r)]
            if sel_zona_r: df_v_r = df_v_r[df_v_r['DESCRIPCIÓN ZONA'].isin(sel_zona_r)]

            # KPIs DESGLOSADOS (Mismo estilo que Extra Ciclos)
            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric("Bultos", f"{df_v_r['BULTOS'].sum():,.0f}")
            k2.metric("Preparación", f"$ {df_v_r['TOTAL_PREPARACION'].sum():,.2f}")
            k3.metric("Transporte", f"$ {df_v_r['TOTAL_TRANSPORTE'].sum():,.2f}")
            k4.metric("IVA 15%", f"$ {df_v_r['IVA_15'].sum():,.2f}")
            k5.metric("Total Final", f"$ {df_v_r['TOTAL_FINAL'].sum():,.2f}")
            
            st.divider()
            st.download_button("📥 Descargar Detalle Filtrado VV", format_excel(df_v_r), f"Detalle_VV_{st.session_state['mes_repro_actual']}.xlsx")
            st.dataframe(df_v_r, use_container_width=True)

    with tabs[2]: # TAB 2: CONFIGURACIÓN
        st.header("⚙️ Gestión de Maestros Reprograma")
        ca, cb = st.columns(2)
        with ca:
            ug = st.file_uploader("Actualizar Maestro GP (Repro)", type=['csv','xlsx'], key="up_gp_r_tab")
            if ug:
                d = leer_archivo(ug)
                if d is not None: d.to_csv(PATH_GP_REPRO, index=False); st.success("GP Reprograma OK")
        with cb:
            uc = st.file_uploader("Actualizar Maestro Costos (Repro)", type=['csv','xlsx'], key="up_co_r_tab")
            if uc:
                d = leer_archivo(uc)
                if d is not None: d.to_csv(PATH_COSTOS_REPRO, index=False); st.success("Costos Reprograma OK")

    with tabs[3]: # TAB 3: HISTORIAL
        st.header("🗄️ Consulta Histórica VV")
        if os.path.exists(HISTORICO_REPRO_FILE):
            df_h = pd.read_csv(HISTORICO_REPRO_FILE)
            for c in ['TOTAL_PREPARACION', 'TOTAL_TRANSPORTE', 'TOTAL_FINAL', 'BULTOS']:
                if c in df_h.columns: df_h[c] = pd.to_numeric(df_h[c], errors='coerce').fillna(0)
            
            meses = sorted(df_h['MES_PROCESO'].dropna().unique())
            if meses:
                m_h = st.selectbox("Seleccionar Mes:", meses, key="hist_repro_sel")
                df_mostrar = df_h[df_h['MES_PROCESO'] == m_h]
                
                h1, h2, h3, h4 = st.columns(4)
                h1.metric("Bultos", f"{df_mostrar['BULTOS'].sum():,.0f}")
                h2.metric("Prep. Hist.", f"$ {df_mostrar['TOTAL_PREPARACION'].sum():,.2f}")
                h3.metric("Trans. Hist.", f"$ {df_mostrar['TOTAL_TRANSPORTE'].sum():,.2f}")
                h4.metric("Total Facturado", f"$ {df_mostrar['TOTAL_FINAL'].sum():,.2f}")
                
                st.dataframe(df_mostrar, use_container_width=True)
                
                st.markdown('<div class="small-btn">', unsafe_allow_html=True)
                if st.button(f"🗑️ Eliminar historial {m_h}", key="del_repro_hist"):
                    df_h = df_h[df_h['MES_PROCESO'] != m_h]
                    df_h.to_csv(HISTORICO_REPRO_FILE, index=False)
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
# --- BOTÓN DE REGRESO (SOLO VISIBLE FUERA DE INICIO) ---
if st.session_state['pagina_actual'] != "inicio":
    st.markdown("""
        <style>
        .btn-derecha button {
            height: 5px !important;
            width: 5px !important;
            font-size: 0.9rem !important;
            border-radius: 25px !important;
        }
        </style>
        """, unsafe_allow_html=True)

    # Ajuste de columnas para pegarlo a la derecha
    cols = st.columns([50, 1.5]) 
    with cols[1]:
        st.markdown('<div class="btn-derecha">', unsafe_allow_html=True)
        if st.button("🏠", key="btn_inicio_dinamico"):
            st.session_state['pagina_actual'] = "inicio"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

