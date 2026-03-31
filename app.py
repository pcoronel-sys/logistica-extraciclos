import streamlit as st
import pandas as pd
from io import BytesIO

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Logística Extra-Ciclos", layout="wide", page_icon="🚚")

# CSS para Colores Corporativos y Estilo
st.markdown("""
    <style>
    .main {
        background-color: #f0f2f6;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 5px solid #004a99; /* Azul Corporativo */
    }
    h1 {
        color: #004a99;
    }
    div[data-testid="stExpander"] {
        background-color: white;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🚚 Sistema de Liquidación Logística")
st.markdown("---")

archivo_subido = st.file_uploader("📂 Arrastra tu archivo Excel aquí", type=['xlsx'])

if archivo_subido:
    try:
        # --- PROCESAMIENTO ---
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

        # --- CONSOLIDACIÓN ---
        grouped = res.groupby(['GP', 'TIPO'])['LOG_TOT'].sum().reset_index()
        pivot = grouped.pivot(index='GP', columns='TIPO', values='LOG_TOT').fillna(0).reset_index()

        df_final = pd.DataFrame()
        df_final['GERENTE (GP)'] = pivot['GP']
        df_final['LOGISTICA MM'] = pivot['MM'] if 'MM' in pivot.columns else 0.0
        df_final['LOGISTICA MP'] = pivot['MP'] if 'MP' in pivot.columns else 0.0
        df_final['SUBTOTAL'] = df_final['LOGISTICA MM'] + df_final['LOGISTICA MP']
        df_final['IVA 15%'] = df_final['SUBTOTAL'] * 0.15
        df_final['TOTAL'] = df_final['SUBTOTAL'] + df_final['IVA 15%']

        # --- VISUAL: MÉTRICAS RESALTADAS ---
        st.subheader("📌 Resumen de Gastos Generales")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Logística MM", f"$ {df_final['LOGISTICA MM'].sum():,.2f}")
        m2.metric("Logística MP", f"$ {df_final['LOGISTICA MP'].sum():,.2f}")
        m3.metric("IVA Total (15%)", f"$ {df_final['IVA 15%'].sum():,.2f}")
        m4.metric("GRAN TOTAL", f"$ {df_final['TOTAL'].sum():,.2f}")

        # --- TABLA DE LIQUIDACIÓN ---
        st.markdown("### 📋 Cuadro de Liquidación por Gerente")
        
        tot_row = {'GERENTE (GP)': 'TOTALES GENERALES'}
        for col in df_final.columns[1:]: tot_row[col] = df_final[col].sum()
        df_disp = pd.concat([df_final, pd.DataFrame([tot_row])], ignore_index=True)

        # Estilo para la tabla (Negritas en la última fila)
        st.dataframe(df_disp.style.format({c: "$ {:,.2f}" for c in df_disp.columns if c != 'GERENTE (GP)'}), use_container_width=True)

        # --- ACCIONES Y AUDITORÍA ---
        st.markdown("---")
        c_audit, c_down = st.columns([2, 1])
        
        with c_audit:
            with st.expander("🔍 Auditoría de Datos (Ver detalle por ítem)"):
                st.dataframe(res)
        
        with c_down:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_disp.to_excel(writer, index=False, sheet_name='Liquidacion')
                res.to_excel(writer, index=False, sheet_name='Detalle_Revision')
            
            st.download_button(
                label="📥 Descargar Reporte Final Excel",
                data=output.getvalue(),
                file_name="Liquidacion_Extra_Ciclos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    except Exception as e:
        st.error(f"Se produjo un error: {e}")
