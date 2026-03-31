import streamlit as st
import pandas as pd
from io import BytesIO
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Logística Bagó Pro", layout="wide", page_icon="🧪")

# --- ESTILO MINIMALISTA BLANCO Y MAGENTA ---
st.markdown("""
    <style>
    /* Fondo Blanco Puro */
    .stApp {
        background-color: #ffffff;
    }
    
    /* Tarjetas Blancas con Sombra Suave */
    .glass-card {
        background: #ffffff;
        border-radius: 15px;
        border: 1px solid #e6e6e6;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }

    /* Métricas */
    div[data-testid="stMetric"] {
        background: #fdfdfd;
        border-radius: 10px;
        border: 1px solid #eeeeee;
        border-top: 4px solid #E10078;
        padding: 15px !important;
    }

    /* Botones Magenta */
    .stButton>button {
        background-color: #E10078;
        color: white;
        border-radius: 8px;
        border: none;
        transition: 0.3s;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #8E004C;
        color: white;
        box-shadow: 0 4px 8px rgba(225, 0, 120, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)

# --- ENCABEZADO ---
st.image("https://www.bago.com.ec/wp-content/uploads/2021/05/logo-bago.png", width=150)
st.title("📊 Control de Liquidación Logística")
st.markdown("Plataforma de gestión de gastos para extra-ciclos.")

archivo = st.file_uploader("📂 Cargar archivo Excel", type=['xlsx'])

if archivo:
    try:
        # --- PROCESAMIENTO ---
        xls = pd.ExcelFile(archivo)
        df_carga = pd.read_excel(xls, 'Carga')
        df_gp = pd.read_excel(xls, 'Maestro_GP')
        df_costos = pd.read_excel(xls, 'Maestro_Costos')

        for df in [df_carga, df_gp, df_costos]:
            df.columns = df.columns.str.strip().str.upper()

        def clean_txt(s): return s.astype(str).str.strip().str.upper()
        def clean_num(s): return pd.to_numeric(s, errors='coerce').fillna(0)

        df_carga['CODIGO'] = clean_txt(df_carga['CODIGO']).str.replace('.0', '', regex=False)
        col_ref_gp = [c for c in df_gp.columns if 'CODIGO' in c][0]
        df_gp[col_ref_gp] = clean_txt(df_gp[col_ref_gp]).str.replace('.0', '', regex=False)
        
        # Cruces
        res = pd.merge(df_carga, df_gp[[col_ref_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_ref_gp, how='left')
        
        # Identificar códigos faltantes en Maestro
        faltantes = res[res['GP'].isna()]['CODIGO'].unique()

        df_costos = df_costos.rename(columns={'PRECIO_PREP': 'PREPARACION', 'PRECIO_TRANS': 'TRANSPORTE'})
        res['DESCRIPCIÓN ZONA'] = clean_txt(res['DESCRIPCIÓN ZONA'])
        df_costos['DESCRIPCIÓN ZONA'] = clean_txt(df_costos['DESCRIPCIÓN ZONA'])
        
        res = pd.merge(res, df_costos[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')

        res['BULTOS'] = clean_num(res['BULTOS'])
        res['LOG_TOT'] = (clean_num(res['PREPARACION']) + clean_num(res['TRANSPORTE'])) * res['BULTOS']

        # --- FILTROS LATERALES ---
        st.sidebar.header("⚙️ Filtros de Reporte")
        lista_gp = ["TODOS"] + sorted(res['GP'].dropna().unique().tolist())
        gp_seleccionado = st.sidebar.selectbox("Seleccionar Gerente (GP)", lista_gp)

        if gp_seleccionado != "TODOS":
            res_filtered = res[res['GP'] == gp_seleccionado]
        else:
            res_filtered = res

        # --- CÁLCULOS ---
        grouped = res_filtered.groupby('TIPO')['LOG_TOT'].sum().reset_index()
        pivot = grouped.set_index('TIPO').T
        
        mm_val = pivot['MM'].values[0] if 'MM' in pivot.columns else 0
        mp_val = pivot['MP'].values[0] if 'MP' in pivot.columns else 0
        subtotal = mm_val + mp_val
        iva = subtotal * 0.15
        total = subtotal + iva

        # --- VISUALIZACIÓN ---
        st.markdown('---')
        if len(faltantes) > 0:
            st.warning(f"⚠️ Se detectaron {len(faltantes)} códigos sin registro en el Maestro GP. Revisa la pestaña de Auditoría.")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("LOGÍSTICA MM", f"$ {mm_val:,.2f}")
        c2.metric("LOGÍSTICA MP", f"$ {mp_val:,.2f}")
        c3.metric("IVA (15%)", f"$ {iva:,.2f}")
        c4.metric("TOTAL GP", f"$ {total:,.2f}")

        col_graf, col_tab = st.columns([1, 2])

        with col_graf:
            st.markdown("### 📈 Mix de Gasto")
            fig = px.pie(values=[mm_val, mp_val], names=['MM', 'MP'], 
                         color_discrete_sequence=['#E10078', '#004a99'], hole=0.4)
            st.plotly_chart(fig, use_container_width=True)

        with col_tab:
            st.markdown(f"### 📋 Liquidación: {gp_seleccionado}")
            # Cuadro detallado del GP actual
            resumen_gp = res_filtered.groupby(['GP', 'TIPO'])['LOG_TOT'].sum().unstack(fill_value=0).reset_index()
            resumen_gp['SUBTOTAL'] = resumen_gp.get('MM', 0) + resumen_gp.get('MP', 0)
            resumen_gp['IVA 15%'] = resumen_gp['SUBTOTAL'] * 0.15
            resumen_gp['TOTAL'] = resumen_gp['SUBTOTAL'] + resumen_gp['IVA 15%']
            
            st.dataframe(resumen_gp.style.format(precision=2), use_container_width=True)

        # --- AUDITORÍA Y DESCARGA ---
        tab_aud, tab_falt = st.tabs(["🔍 Detalle Completo", "❌ Códigos Faltantes"])
        
        with tab_aud:
            st.dataframe(res)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                resumen_gp.to_excel(writer, index=False, sheet_name='Liquidacion')
                res.to_excel(writer, index=False, sheet_name='Detalle')
            st.download_button("📥 DESCARGAR EXCEL", data=output.getvalue(), file_name="Liquidacion_Bago_Pro.xlsx", use_container_width=True)

        with tab_falt:
            if len(faltantes) > 0:
                st.write("Los siguientes códigos están en 'Carga' pero no en 'Maestro_GP':")
                st.write(faltantes)
            else:
                st.success("¡Todo en orden! Todos los códigos existen en el Maestro.")

    except Exception as e:
        st.error(f"Error: {e}")
