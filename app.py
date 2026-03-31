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

st.title("📊 Control de Liquidación Logística")
st.caption("Laboratorios Bagó del Ecuador S.A. | Gestión de Extra-Ciclos")
st.markdown("---")

archivo = st.file_uploader("📂 Cargar archivo Excel", type=['xlsx'])

if archivo:
    try:
        # --- CARGA ---
        xls = pd.ExcelFile(archivo)
        df_carga = pd.read_excel(xls, 'Carga')
        df_gp = pd.read_excel(xls, 'Maestro_GP')
        df_costos = pd.read_excel(xls, 'Maestro_Costos')

        # --- LIMPIEZA ROBUSTA ---
        def clean_dataframe(df):
            # 1. Columnas a mayúsculas y sin espacios
            df.columns = df.columns.str.strip().str.upper()
            # 2. Convertir todo a string, quitar espacios y pasar a mayúsculas para evitar el error .str
            return df.apply(lambda x: x.astype(str).str.strip().str.upper() if x.name != 'BULTOS' and x.name != 'PREPARACION' and x.name != 'TRANSPORTE' else x)

        df_carga = clean_dataframe(df_carga)
        df_gp = clean_dataframe(df_gp)
        df_costos = clean_dataframe(df_costos)

        # Normalizar Códigos (Quitar el .0 que aparece cuando Excel lee números)
        df_carga['CODIGO'] = df_carga['CODIGO'].str.replace(r'\.0$', '', regex=True)
        col_id_gp = [c for c in df_gp.columns if 'CODIGO' in c][0]
        df_gp[col_id_gp] = df_gp[col_id_gp].str.replace(r'\.0$', '', regex=True)

        # --- PROCESAMIENTO ---
        # Unión con Maestro GP
        res = pd.merge(df_carga, df_gp[[col_id_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_id_gp, how='left')
        
        # Unión con Costos
        df_costos = df_costos.rename(columns={'PRECIO_PREP': 'PREPARACION', 'PRECIO_TRANS': 'TRANSPORTE'})
        res = pd.merge(res, df_costos[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')

        # Convertir valores numéricos finales
        res['BULTOS'] = pd.to_numeric(res['BULTOS'], errors='coerce').fillna(0)
        res['PREPARACION'] = pd.to_numeric(res['PREPARACION'], errors='coerce').fillna(0)
        res['TRANSPORTE'] = pd.to_numeric(res['TRANSPORTE'], errors='coerce').fillna(0)
        res['LOG_TOT'] = (res['PREPARACION'] + res['TRANSPORTE']) * res['BULTOS']

        # --- FILTROS ---
        st.sidebar.header("⚙️ Opciones de Filtro")
        gp_list = ["TODOS"] + sorted(res['GP'].dropna().unique().tolist())
        sel_gp = st.sidebar.selectbox("Filtrar por Gerente", gp_list)
        
        filt = res.copy()
        if sel_gp != "TODOS":
            filt = filt[filt['GP'] == sel_gp]

        # --- MÉTRICAS ---
        mm_val = filt[filt['TIPO'] == 'MM']['LOG_TOT'].sum()
        mp_val = filt[filt['TIPO'] == 'MP']['LOG_TOT'].sum()
        subtotal = mm_val + mp_val
        iva = subtotal * 0.15
        total_gen = subtotal + iva

        st.markdown(f"### 📈 Indicadores: {sel_gp}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("LOGÍSTICA MM", f"$ {mm_val:,.2f}")
        c2.metric("LOGÍSTICA MP", f"$ {mp_val:,.2f}")
        c3.metric("IVA (15%)", f"$ {iva:,.2f}")
        c4.metric("TOTAL A PAGAR", f"$ {total_gen:,.2f}")

        # --- VISUALIZACIÓN ---
        st.markdown("---")
        g1, g2 = st.columns([1, 2])
        with g1:
            if subtotal > 0:
                fig = px.pie(values=[mm_val, mp_val], names=['MM', 'MP'], 
                             color_discrete_sequence=['#E10078', '#004a99'], hole=0.5)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sin datos para graficar")
        with g2:
            summary = filt.groupby(['GP', 'TIPO'])['LOG_TOT'].sum().unstack(fill_value=0).reset_index()
            for col in ['MM', 'MP']:
                if col not in summary.columns: summary[col] = 0.0
            summary['SUBTOTAL'] = summary['MM'] + summary['MP']
            summary['IVA 15%'] = summary['SUBTOTAL'] * 0.15
            summary['TOTAL'] = summary['SUBTOTAL'] + summary['IVA 15%']
            st.dataframe(summary.style.format(precision=2), use_container_width=True)

        # --- DESCARGA ---
        st.tabs(["🔍 Auditoría de Detalles"]) # Mantenemos estructura limpia
        st.dataframe(res)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            summary.to_excel(writer, index=False, sheet_name='Liquidacion')
            res.to_excel(writer, index=False, sheet_name='Detalle_Completo')
        st.download_button("📥 DESCARGAR REPORTE EXCEL", data=output.getvalue(), file_name="Liquidacion_Bago.xlsx", use_container_width=True)

    except Exception as e:
        st.error(f"Error en el procesamiento: {e}")
