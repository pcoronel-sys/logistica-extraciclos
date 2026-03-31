import streamlit as st
import pandas as pd
from io import BytesIO
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Logística Bagó Intelligence", layout="wide", page_icon="🧪")

# --- ESTILO CORPORATIVO BLANCO Y MAGENTA ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    
    /* Tarjetas de Métricas */
    div[data-testid="stMetric"] {
        background: #ffffff;
        border-radius: 12px;
        border: 1px solid #f0f0f0;
        border-top: 5px solid #E10078;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        padding: 20px !important;
    }

    /* Botones dinámicos */
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

# --- CABECERA ---
col_logo, col_tit = st.columns([1, 4])
with col_logo:
    st.image("https://www.bago.com.ec/wp-content/uploads/2021/05/logo-bago.png", width=120)
with col_tit:
    st.title("Control de Liquidación Logística")
    st.caption("Laboratorios Bagó del Ecuador S.A. | Gestión de Extra-Ciclos")

archivo = st.file_uploader("", type=['xlsx'])

if archivo:
    try:
        # --- CARGA Y NORMALIZACIÓN ---
        xls = pd.ExcelFile(archivo)
        df_carga = pd.read_excel(xls, 'Carga')
        df_gp = pd.read_excel(xls, 'Maestro_GP')
        df_costos = pd.read_excel(xls, 'Maestro_Costos')

        # Función de limpieza profunda
        def clean_all(df):
            df.columns = df.columns.str.strip().str.upper()
            return df.apply(lambda x: x.str.strip().str.upper() if x.dtype == "object" else x)

        df_carga = clean_all(df_carga)
        df_gp = clean_all(df_gp)
        df_costos = clean_all(df_costos)

        # Limpieza de códigos (quitar .0 de Excel)
        df_carga['CODIGO'] = df_carga['CODIGO'].astype(str).str.replace('.0', '', regex=False)
        col_id_gp = [c for c in df_gp.columns if 'CODIGO' in c][0]
        df_gp[col_id_gp] = df_gp[col_id_gp].astype(str).str.replace('.0', '', regex=False)

        # --- PROCESAMIENTO DE CRUCES ---
        # Cruce con Gerentes
        res = pd.merge(df_carga, df_gp[[col_id_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_id_gp, how='left')
        
        # Cruce con Costos
        df_costos = df_costos.rename(columns={'PRECIO_PREP': 'PREPARACION', 'PRECIO_TRANS': 'TRANSPORTE'})
        res = pd.merge(res, df_costos[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')

        # Cálculos de Totales
        res['BULTOS'] = pd.to_numeric(res['BULTOS'], errors='coerce').fillna(0)
        res['LOG_TOT'] = (pd.to_numeric(res['PREPARACION'], errors='coerce').fillna(0) + 
                          pd.to_numeric(res['TRANSPORTE'], errors='coerce').fillna(0)) * res['BULTOS']

        # --- PANEL LATERAL (FILTROS) ---
        st.sidebar.image("https://www.bago.com.ec/wp-content/uploads/2021/05/logo-bago.png", width=100)
        st.sidebar.header("Opciones de Visualización")
        
        gp_list = ["TODOS"] + sorted(res['GP'].dropna().unique().tolist())
        sel_gp = st.sidebar.selectbox("Filtrar por Gerente", gp_list)
        
        tipo_list = ["AMBOS", "MM", "MP"]
        sel_tipo = st.sidebar.radio("Tipo de Material", tipo_list)

        # Aplicar Filtros
        filt = res.copy()
        if sel_gp != "TODOS": filt = filt[filt['GP'] == sel_gp]
        if sel_tipo != "AMBOS": filt = filt[filt['TIPO'] == sel_tipo]

        # --- MÉTRICAS PRINCIPALES ---
        mm_val = filt[filt['TIPO'] == 'MM']['LOG_TOT'].sum()
        mp_val = filt[filt['TIPO'] == 'MP']['LOG_TOT'].sum()
        subtotal = mm_val + mp_val
        iva = subtotal * 0.15
        total_gen = subtotal + iva

        st.markdown("### 📊 Indicadores Clave")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("LOGÍSTICA MM", f"$ {mm_val:,.2f}")
        c2.metric("LOGÍSTICA MP", f"$ {mp_val:,.2f}")
        c3.metric("IVA (15%)", f"$ {iva:,.2f}")
        c4.metric("TOTAL A PAGAR", f"$ {total_gen:,.2f}")

        # --- GRÁFICOS E INTELIGENCIA ---
        st.markdown("---")
        g1, g2 = st.columns([1, 2])

        with g1:
            st.markdown("#### Distribución de Gasto")
            if subtotal > 0:
                fig = px.pie(values=[mm_val, mp_val], names=['MM', 'MP'], 
                             color_discrete_sequence=['#E10078', '#004a99'], hole=0.5)
                fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos para graficar")

        with g2:
            st.markdown(f"#### Resumen Consolidado: {sel_gp}")
            # Cuadro resumen dinámico
            summary = filt.groupby(['GP', 'TIPO'])['LOG_TOT'].sum().unstack(fill_value=0).reset_index()
            for col in ['MM', 'MP']: 
                if col not in summary.columns: summary[col] = 0.
