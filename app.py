import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Liquidación Logística Final", layout="wide")

st.title("📊 Reporte de Liquidación Logística (IVA 15%)")

archivo_subido = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if archivo_subido:
    try:
        xls = pd.ExcelFile(archivo_subido)
        df_carga = pd.read_excel(xls, 'Carga')
        df_gp = pd.read_excel(xls, 'Maestro_GP')
        df_costos = pd.read_excel(xls, 'Maestro_Costos')

        # 1. LIMPIEZA DE COLUMNAS
        for df in [df_carga, df_gp, df_costos]:
            df.columns = df.columns.str.strip().str.upper()

        # 2. LIMPIEZA DE DATOS CLAVE (Quitar espacios y normalizar)
        def clean_text(s): return s.astype(str).str.strip().str.upper()
        def clean_num(s): return pd.to_numeric(s, errors='coerce').fillna(0)

        # Normalizar Códigos
        df_carga['CODIGO'] = clean_text(df_carga['CODIGO']).str.replace('.0', '', regex=False)
        col_ref_gp = [c for c in df_gp.columns if 'CODIGO' in c][0]
        df_gp[col_ref_gp] = clean_text(df_gp[col_ref_gp]).str.replace('.0', '', regex=False)

        # Normalizar Zonas (Esto es lo que causa los ceros)
        df_carga['DESCRIPCIÓN ZONA'] = clean_text(df_carga['DESCRIPCIÓN ZONA'])
        df_costos['DESCRIPCIÓN ZONA'] = clean_text(df_costos['DESCRIPCIÓN ZONA'])

        # 3. CRUCES
        df_gp = df_gp.drop_duplicates(subset=[col_ref_gp])
        df_costos = df_costos.drop_duplicates(subset=['DESCRIPCIÓN ZONA'])
        
        # Unir Carga con GP
        res = pd.merge(df_carga, df_gp[[col_ref_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_ref_gp, how='left')
        
        # Unir con Costos (Asegurar nombres de columnas PREPARACION y TRANSPORTE)
        df_costos = df_costos.rename(columns={'PRECIO_PREP': 'PREPARACION', 'PRECIO_TRANS': 'TRANSPORTE'})
        res = pd.merge(res, df_costos[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')

        # 4. CÁLCULOS
        res['BULTOS'] = clean_num(res['BULTOS'])
        res['PREPARACION'] = clean_num(res['PREPARACION'])
        res['TRANSPORTE'] = clean_num(res['TRANSPORTE'])

        res['LOGISTICA_TOTAL'] = (res['PREPARACION'] + res['TRANSPORTE']) * res['BULTOS']

        # 5. CONSTRUCCIÓN DEL CUADRO FINAL
        grouped = res.groupby(['GP', 'TIPO'])['LOGISTICA_TOTAL'].sum().reset_index()
        pivot = grouped.pivot(index='GP', columns='TIPO', values='LOGISTICA_TOTAL').fillna(0).reset_index()

        df_final = pd.DataFrame()
        df_final['GERENTE (GP)'] = pivot['GP']
        df_final['LOGISTICA MM'] = pivot['MM'] if 'MM' in pivot.columns else 0.0
        df_final['LOGISTICA MP'] = pivot['MP'] if 'MP' in pivot.columns else 0.0
        df_final['SUBTOTAL NETO'] = df_final['LOGISTICA MM'] + df_final['LOGISTICA MP']
        df_final['IVA 15%'] = df_final['SUBTOTAL NETO'] * 0.15
        df_final['TOTAL A FACTURAR'] = df_final['SUBTOTAL NETO'] + df_final['IVA 15%']

        # Fila de Totales
        totales_dict = {'GERENTE (GP)': '--- TOTALES GENERALES ---'}
        for col in df_final.columns[1:]: totales_dict[col] = df_final[col].sum()
        df_reporte = pd.concat([df_final, pd.DataFrame([totales_dict])], ignore_index=True)

        st.subheader("📋 Cuadro Consolidado de Liquidación")
        st.table(df_reporte.style.format({c: "$ {:,.2f}" for c in df_reporte.columns if c != 'GERENTE (GP)'}))

        with st.expander("🔍 Ver Auditoría de Cruces (Revisa si hay Preparación/Transporte en 0 aquí)"):
            st.dataframe(res)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_reporte.to_excel(writer, index=False, sheet_name='Resumen')
            res.to_excel(writer, index=False, sheet_name='Detalle_Revision')
        
        st.download_button("📥 Descargar Reporte Final", output.getvalue(), "Liquidacion_Logistica.xlsx")

    except Exception as e:
        st.error(f"Error: {e}")
