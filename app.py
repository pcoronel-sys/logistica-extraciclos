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

# --- CABECERA (Sin imagen externa) ---
st.title("📊 Control de Liquidación Logística")
st.caption("Laboratorios Bagó del Ecuador S.A. | Gestión de Extra-Ciclos")
st.markdown("---")

archivo = st.file_uploader("📂 Cargar archivo Excel", type=['xlsx'])

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
            # Limpiar solo columnas de texto
            for col in df.select_dtypes(include=['object']).columns:
                df[col] = df[col].astype(str).str.strip().str.upper()
            return df

        df_carga = clean_all(df_carga)
        df_gp = clean_all(df_gp)
        df_costos = clean_all(df_costos)

        # Limpieza de códigos (quitar .0 de Excel)
        df_carga['CODIGO'] = df_carga['CODIGO'].str.replace('.0', '', regex=False)
        col_id_gp = [c for c in df_gp.columns if 'CODIGO' in c][0]
        df_gp[col_id_gp] = df_gp[col_id_gp].str.replace('.0', '', regex=False)

        # --- PROCESAMIENTO DE CRUCES ---
        res = pd.merge(df_carga, df_gp[[col_id_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_id_gp, how='left')
        
        # Identificar códigos faltantes
        faltantes = res[res['GP'].isna()]['CODIGO'].unique()

        df_costos = df_costos.rename(columns={'PRECIO_PREP': 'PREPARACION', 'PRECIO_TRANS': 'TRANSPORTE'})
        res = pd.merge(res, df_costos[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')

        # Cálculos de Totales
        res['BULTOS'] = pd.to_numeric(res['BULTOS'], errors='coerce').fillna(0)
        res['PREPARACION'] = pd.to_numeric(res['PREPARACION'], errors='coerce').fillna(0)
        res['TRANSPORTE'] = pd.to_numeric(res['TRANSPORTE'], errors='coerce').fillna(0)
        res['LOG_TOT'] = (res['PREPARACION'] + res['TRANSPORTE']) * res['BULTOS']

        # --- PANEL LATERAL (FILTROS) ---
        st.sidebar.header("⚙️ Opciones de Filtro")
        gp_list = ["TODOS"] + sorted(res['GP'].dropna().unique().tolist())
        sel_gp = st.sidebar.selectbox("Filtrar por Gerente", gp_list)
        
        # Aplicar Filtros
        filt = res.copy()
        if sel_gp != "TODOS":
            filt = filt[filt['GP'] == sel_gp]

        # --- MÉTRICAS PRINCIPALES ---
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

        # --- GRÁFICOS Y TABLA ---
        st.markdown("---")
        g1, g2 = st.columns([1, 2])

        with g1:
            st.markdown("#### Distribución de Gasto")
            if subtotal > 0:
                fig = px.pie(values=[mm_val, mp_val], names=['MM', 'MP'], 
                             color_discrete_sequence=['#E10078', '#004a99'], hole=0.5)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sin datos para graficar")

        with g2:
            st.markdown("#### Resumen por Categoría")
            summary = filt.groupby(['GP', 'TIPO'])['LOG_TOT'].sum().unstack(fill_value=0).reset_index()
            # Asegurar columnas MM y MP
            for col in ['MM', 'MP']:
                if col not in summary.columns: summary[col] = 0.0
            
            summary['SUBTOTAL'] = summary['MM'] + summary['MP']
            summary['IVA 15%'] = summary['SUBTOTAL'] * 0.15
            summary['TOTAL'] = summary['SUBTOTAL'] + summary['IVA 15%']
            
            st.dataframe(summary.style.format(precision=2), use_container_width=True)

        # --- DESCARGAS Y AUDITORÍA ---
        tab_aud, tab_falt = st.tabs(["🔍 Auditoría de Detalles", "❌ Códigos Faltantes"])
        
        with tab_aud:
            st.dataframe(res)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                summary.to_excel(writer, index=False, sheet_name='Liquidacion')
                res.to_excel(writer, index=False, sheet_name='Detalle_Completo')
            st.download_button("📥 DESCARGAR REPORTE EXCEL", data=output.getvalue(), file_name="Liquidacion_Bago.xlsx", use_container_width=True)

        with tab_falt:
            if len(faltantes) > 0:
                st.error(f"Se encontraron {len(faltantes)} códigos que no están en el Maestro GP:")
                st.write(faltantes)
            else:
                st.success("✅ Todos los códigos están correctamente mapeados en el Maestro.")

    except Exception as e:
        st.error(f"Error en el procesamiento: {e}")
