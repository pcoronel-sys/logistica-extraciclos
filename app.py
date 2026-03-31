import streamlit as st
import pandas as pd
from io import BytesIO

# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO
st.set_page_config(page_title="Logística Extra-Ciclos", layout="wide", page_icon="🚚")

# CSS personalizado para mejorar la estética
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    div[data-testid="stTable"] {
        background-color: white;
        border-radius: 10px;
        overflow: hidden;
    }
    </style>
    """, unsafe_index=True)

st.title("🚚 Sistema de Liquidación Logística")
st.info("Sube el archivo Excel para generar el resumen de Gerentes y Tipos.")

archivo_subido = st.file_uploader("📂 Arrastra tu Excel aquí", type=['xlsx'])

if archivo_subido:
    try:
        # --- PROCESAMIENTO (Mantenemos tu lógica ganadora) ---
        xls = pd.ExcelFile(archivo_subido)
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
        df_carga['DESCRIPCIÓN ZONA'] = clean_txt(df_carga['DESCRIPCIÓN ZONA'])
        df_costos['DESCRIPCIÓN ZONA'] = clean_txt(df_costos['DESCRIPCIÓN ZONA'])

        df_gp = df_gp.drop_duplicates(subset=[col_ref_gp])
        df_costos = df_costos.drop_duplicates(subset=['DESCRIPCIÓN ZONA'])
        df_costos = df_costos.rename(columns={'PRECIO_PREP': 'PREPARACION', 'PRECIO_TRANS': 'TRANSPORTE'})

        res = pd.merge(df_carga, df_gp[[col_ref_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_ref_gp, how='left')
        res = pd.merge(res, df_costos[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')

        res['BULTOS'] = clean_num(res['BULTOS'])
        res['PREPARACION'] = clean_num(res['PREPARACION'])
        res['TRANSPORTE'] = clean_num(res['TRANSPORTE'])
        res['LOG_TOT'] = (res['PREPARACION'] + res['TRANSPORTE']) * res['BULTOS']

        # --- CÁLCULOS DEL CUADRO ---
        grouped = res.groupby(['GP', 'TIPO'])['LOG_TOT'].sum().reset_index()
        pivot = grouped.pivot(index='GP', columns='TIPO', values='LOG_TOT').fillna(0).reset_index()

        df_final = pd.DataFrame()
        df_final['GERENTE (GP)'] = pivot['GP']
        df_final['LOGISTICA MM'] = pivot['MM'] if 'MM' in pivot.columns else 0.0
        df_final['LOGISTICA MP'] = pivot['MP'] if 'MP' in pivot.columns else 0.0
        df_final['SUBTOTAL'] = df_final['LOGISTICA MM'] + df_final['LOGISTICA MP']
        df_final['IVA 15%'] = df_final['SUBTOTAL'] * 0.15
        df_final['TOTAL'] = df_final['SUBTOTAL'] + df_final['IVA 15%']

        # --- PARTE VISUAL: MÉTRICAS ---
        st.subheader("📌 Resumen General")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Logística MM", f"$ {df_final['LOGISTICA MM'].sum():,.2f}")
        m2.metric("Logística MP", f"$ {df_final['LOGISTICA MP'].sum():,.2f}")
        m3.metric("IVA Total (15%)", f"$ {df_final['IVA 15%'].sum():,.2f}")
        m4.metric("GRAN TOTAL", f"$ {df_final['TOTAL'].sum():,.2f}", delta="A Facturar", delta_color="normal")

        # --- TABLA DE LIQUIDACIÓN ---
        st.markdown("---")
        st.subheader("📋 Cuadro de Liquidación por GP")
        
        # Totales para la tabla
        tot_row = {'GERENTE (GP)': 'TOTALES GENERALES'}
        for col in df_final.columns[1:]: tot_row[col] = df_final[col].sum()
        df_disp = pd.concat([df_final, pd.DataFrame([tot_row])], ignore_index=True)

        st.table(df_disp.style.format({c: "$ {:,.2f}" for c in df_disp.columns if c != 'GERENTE (GP)'}) \
                 .set_properties(subset=pd.IndexSlice[df_disp.index[-1], :], **{'font-weight': 'bold', 'background-color': '#f0f2f6'}))

        # --- AUDITORÍA Y DESCARGA ---
        col_down1, col_down2 = st.columns(2)
        with col_down1:
            with st.expander("🔍 Auditoría: Ver detalle ítem por ítem"):
                st.dataframe(res)
        
        with col_down2:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_disp.to_excel(writer, index=False, sheet_name='Liquidacion')
                res.to_excel(writer, index=False, sheet_name='Detalle')
            
            st.download_button(
                label="📥 Descargar Reporte en Excel",
                data=output.getvalue(),
                file_name="Liquidacion_Logistica.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    except Exception as e:
        st.error(f"Error: {e}")
