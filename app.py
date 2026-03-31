import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Liquidación Logística Final", layout="wide")

st.title("📊 Reporte de Liquidación Logística (IVA 15%)")
st.markdown("Consolidado por **GP** con desglose de **MM** y **MP**, e IVA calculado sobre la suma total.")

archivo_subido = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if archivo_subido:
    try:
        # 1. CARGA DE DATOS
        xls = pd.ExcelFile(archivo_subido)
        df_carga = pd.read_excel(xls, 'Carga')
        df_gp = pd.read_excel(xls, 'Maestro_GP')
        df_costos = pd.read_excel(xls, 'Maestro_Costos')

        # Limpieza de nombres de columnas
        for df in [df_carga, df_gp, df_costos]:
            df.columns = df.columns.str.strip().str.upper()

        # Limpieza de códigos (Quitar .0)
        def clean_c(s): return pd.to_numeric(s, errors='coerce').fillna(0).astype(int).astype(str)
        df_carga['CODIGO'] = clean_c(df_carga['CODIGO'])
        col_ref_gp = [c for c in df_gp.columns if 'CODIGO' in c][0]
        df_gp[col_ref_gp] = clean_c(df_gp[col_ref_gp])

        # 2. CRUCES Y PROCESAMIENTO
        df_gp = df_gp.drop_duplicates(subset=[col_ref_gp])
        df_costos = df_costos.drop_duplicates(subset=['DESCRIPCIÓN ZONA'])
        # Soporte para ambos nombres de columna posibles
        df_costos = df_costos.rename(columns={'PRECIO_PREP': 'PREPARACION', 'PRECIO_TRANS': 'TRANSPORTE'})

        res = pd.merge(df_carga, df_gp[[col_ref_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_ref_gp, how='left')
        
        df_carga['DESCRIPCIÓN ZONA'] = df_carga['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
        df_costos['DESCRIPCIÓN ZONA'] = df_costos['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
        res = pd.merge(res, df_costos[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')

        # 3. CÁLCULOS BASE
        for c in ['BULTOS', 'PREPARACION', 'TRANSPORTE']:
            res[c] = pd.to_numeric(res[c], errors='coerce').fillna(0)

        res['LOGISTICA_TOTAL'] = (res['PREPARACION'] + res['TRANSPORTE']) * res['BULTOS']

        # --- 4. TRANSFORMACIÓN A COLUMNAS (PIVOT) ---
        grouped = res.groupby(['GP', 'TIPO'])['LOGISTICA_TOTAL'].sum().reset_index()
        pivot = grouped.pivot(index='GP', columns='TIPO', values='LOGISTICA_TOTAL').fillna(0)
        pivot = pivot.reset_index()

        # 5. CONSTRUCCIÓN DEL CUADRO FINAL (Horizontal)
        df_final = pd.DataFrame()
        df_final['GERENTE (GP)'] = pivot['GP']
        
        # Columnas de Logística puras
        df_final['LOGISTICA MM'] = pivot['MM'] if 'MM' in pivot.columns else 0.0
        df_final['LOGISTICA MP'] = pivot['MP'] if 'MP' in pivot.columns else 0.0
        
        # SUBTOTAL NETO (Suma de las dos logísticas)
        df_final['SUBTOTAL NETO'] = df_final['LOGISTICA MM'] + df_final['LOGISTICA MP']
        
        # IVA 15% SOBRE EL SUBTOTAL
        df_final['IVA 15%'] = df_final['SUBTOTAL NETO'] * 0.15
        
        # TOTAL A FACTURAR POR GP
        df_final['TOTAL A FACTURAR'] = df_final['SUBTOTAL NETO'] + df_final['IVA 15%']

        # Fila de Totales Generales al final del cuadro
        totales_dict = {'GERENTE (GP)': '--- TOTALES GENERALES ---'}
        for col in df_final.columns[1:]:
            totales_dict[col] = df_final[col].sum()
        
        df_reporte = pd.concat([df_final, pd.DataFrame([totales_dict])], ignore_index=True)

        # 6. MOSTRAR RESULTADOS
        st.subheader("📋 Cuadro Consolidado de Liquidación")
        st.table(df_reporte.style.format({c: "$ {:,.2f}" for c in df_reporte.columns if c != 'GERENTE (GP)'}))

        # Mantener el detalle de la carga procesada
        with st.expander("Ver detalle de carga procesada (Ítem por ítem)"):
            st.dataframe(res)

        # 7. GENERAR ARCHIVO EXCEL
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_reporte.to_excel(writer, index=False, sheet_name='Liquidacion_Consolidada')
            res.to_excel(writer, index=False, sheet_name='Detalle_Original')
        
        st.download_button("📥 Descargar Reporte Final (Formato Horizontal)", output.getvalue(), "Liquidacion_Logistica_Final.xlsx")

    except Exception as e:
        st.error(f"Error: {e}")
