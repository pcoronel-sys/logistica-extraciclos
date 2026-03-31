import streamlit as st
import pandas as pd
from io import BytesIO

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Logística Bagó", layout="wide", page_icon="🧪")

# --- ESTILO GLASSMORPHISM Y COLORES MAGENTA ---
st.markdown("""
    <style>
    /* Fondo general */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Efecto Glass para tarjetas */
    .glass-card {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.18);
        padding: 25px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1);
        margin-bottom: 20px;
    }

    /* Estilo para métricas (Glass Magenta) */
    div[data-testid="stMetric"] {
        background: rgba(225, 0, 120, 0.05);
        backdrop-filter: blur(4px);
        border-radius: 15px;
        border-left: 5px solid #E10078; /* Magenta Bagó */
        padding: 15px !important;
    }

    /* Botones dinámicos */
    .stButton>button {
        background: linear-gradient(90deg, #E10078 0%, #8E004C 100%);
        color: white;
        border-radius: 12px;
        border: none;
        padding: 10px 25px;
        transition: all 0.3s ease;
        font-weight: bold;
        width: 100%;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(225, 0, 120, 0.4);
        color: white;
    }

    /* Títulos */
    h1, h2, h3 {
        color: #1a1a1a;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .bago-banner {
        background: linear-gradient(90deg, #004a99 0%, #E10078 100%);
        padding: 40px;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- PANTALLA DE INICIO ---
if 'procesado' not in st.session_state:
    st.markdown("""
        <div class="bago-banner">
            <h1 style="color: white; margin:0;">LABORATORIOS BAGÓ</h1>
            <p style="font-size: 1.2rem; opacity: 0.9;">Sistema Inteligente de Liquidación Logística</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    col_a, col_b = st.columns([1, 2])
    with col_a:
        st.image("https://www.bago.com.ec/wp-content/uploads/2021/05/logo-bago.png", width=200) # Logo genérico si está disponible
    with col_b:
        st.subheader("🚀 ¡Bienvenido!")
        st.write("Sube tu archivo de extra-ciclos para procesar los gastos de MM y MP.")
    st.markdown('</div>', unsafe_allow_html=True)

archivo = st.file_uploader("", type=['xlsx'])

if archivo:
    st.session_state['procesado'] = True
    try:
        # --- LÓGICA DE PROCESAMIENTO ---
        xls = pd.ExcelFile(archivo)
        df_carga = pd.read_excel(xls, 'Carga')
        df_gp = pd.read_excel(xls, 'Maestro_GP')
        df_costos = pd.read_excel(xls, 'Maestro_Costos')

        # Normalización
        for df in [df_carga, df_gp, df_costos]:
            df.columns = df.columns.str.strip().str.upper()

        def clean_txt(s): return s.astype(str).str.strip().str.upper()
        def clean_num(s): return pd.to_numeric(s, errors='coerce').fillna(0)

        df_carga['CODIGO'] = clean_txt(df_carga['CODIGO']).str.replace('.0', '', regex=False)
        col_ref_gp = [c for c in df_gp.columns if 'CODIGO' in c][0]
        df_gp[col_ref_gp] = clean_txt(df_gp[col_ref_gp]).str.replace('.0', '', regex=False)
        df_carga['DESCRIPCIÓN ZONA'] = clean_txt(df_carga['DESCRIPCIÓN ZONA'])
        df_costos['DESCRIPCIÓN ZONA'] = clean_txt(df_costos['DESCRIPCIÓN ZONA'])

        df_gp = df_gp.drop_duplicates(subset=[col_ref_gp])
        df_costos = df_costos.drop_duplicates(subset=['DESCRIPCIÓN ZONA'])
        df_costos = df_costos.rename(columns={'PRECIO_PREP': 'PREPARACION', 'PRECIO_TRANS': 'TRANSPORTE'})

        res = pd.merge(df_carga, df_gp[[col_ref_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_ref_gp, how='left')
        res = pd.merge(res, df_costos[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')

        res['BULTOS'] = clean_num(res['BULTOS'])
        res['LOG_TOT'] = (clean_num(res['PREPARACION']) + clean_num(res['TRANSPORTE'])) * res['BULTOS']

        # --- CÁLCULOS FINALES ---
        grouped = res.groupby(['GP', 'TIPO'])['LOG_TOT'].sum().reset_index()
        pivot = grouped.pivot(index='GP', columns='TIPO', values='LOG_TOT').fillna(0).reset_index()

        df_final = pd.DataFrame({'GERENTE (GP)': pivot['GP']})
        df_final['LOGISTICA MM'] = pivot['MM'] if 'MM' in pivot.columns else 0.0
        df_final['LOGISTICA MP'] = pivot['MP'] if 'MP' in pivot.columns else 0.0
        df_final['SUBTOTAL'] = df_final['LOGISTICA MM'] + df_final['LOGISTICA MP']
        df_final['IVA 15%'] = df_final['SUBTOTAL'] * 0.15
        df_final['TOTAL A FACTURAR'] = df_final['SUBTOTAL'] + df_final['IVA 15%']

        # --- INTERFAZ DE RESULTADOS ---
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("📉 Resumen Ejecutivo")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("LOGÍSTICA MM", f"$ {df_final['LOGISTICA MM'].sum():,.2f}")
        c2.metric("LOGÍSTICA MP", f"$ {df_final['LOGISTICA MP'].sum():,.2f}")
        c3.metric("IVA 15%", f"$ {df_final['IVA 15%'].sum():,.2f}")
        c4.metric("GRAN TOTAL", f"$ {df_final['TOTAL A FACTURAR'].sum():,.2f}")
        st.markdown('</div>', unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["📋 Liquidación GP", "🔍 Detalle Técnico"])

        with tab1:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            tot_row = {'GERENTE (GP)': 'TOTALES GENERALES'}
            for col in df_final.columns[1:]: tot_row[col] = df_final[col].sum()
            df_disp = pd.concat([df_final, pd.DataFrame([tot_row])], ignore_index=True)
            
            st.dataframe(df_disp.style.format({c: "$ {:,.2f}" for c in df_disp.columns if c != 'GERENTE (GP)'}), use_container_width=True)
            
            # Botón de descarga con estilo
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_disp.to_excel(writer, index=False, sheet_name='Resumen')
                res.to_excel(writer, index=False, sheet_name='Detalle')
            
            st.download_button("📥 DESCARGAR REPORTE GERENCIAL", data=output.getvalue(), file_name="Liquidacion_Bago.xlsx", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with tab2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.dataframe(res, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error en el sistema: {e}")
