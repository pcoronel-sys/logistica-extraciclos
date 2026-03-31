import streamlit as st
import pandas as pd
from io import BytesIO

# Configuración de página ancha para mejor visualización de las columnas
st.set_page_config(page_title="Liquidación Logística Final", layout="wide")

st.title("📊 Reporte de Liquidación Logística (IVA 15%)")
st.markdown("Consolidado por **GP** con desglose horizontal de **MM** y **MP**, e IVA calculado sobre el Subtotal Neto.")

archivo_subido = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if archivo_subido:
    try:
        # 1. CARGA DE DATOS
        xls = pd.ExcelFile(archivo_subido)
        
        # Verificación de pestañas
        pestañas_requeridas = ['Carga', 'Maestro_GP', 'Maestro_Costos']
        if not all(p in xls.sheet_names for p in pestañas_requeridas):
            st.error(f"El archivo debe contener las pestañas: {', '.join(pestañas_requeridas)}")
            st.stop()

        df_carga = pd.read_excel(xls, 'Carga')
        df_gp = pd.read_excel(xls, 'Maestro_GP')
        df_costos = pd.read_excel(xls, 'Maestro_Costos')

        # Limpieza de nombres de columnas
        for df in [df_carga, df_gp, df_costos]:
            df.columns = df.columns.str.strip().str.upper()

        # Limpieza de códigos (Quitar .0 y espacios)
        def clean_c(s): return pd.to_numeric(s, errors='coerce').fillna(0).astype(int).astype(str)
        
        df_carga['CODIGO'] = clean_c(df_carga['CODIGO'])
        # Buscar columna que contenga la palabra CODIGO en el maestro
        col_ref_gp = [c for c in df_gp.columns if 'CODIGO' in c][0]
        df_gp[col_ref_gp] = clean_c(df_gp[col_ref_gp])

        # 2. CRUCES Y PROCESAMIENTO
        df_gp = df_gp.drop_duplicates(subset=[col_ref_gp])
        df_costos = df_costos.drop_duplicates(subset=['DESCRIPCIÓN ZONA'])
        
        # Estandarizar nombres de costos
        df_costos = df_costos.rename(columns={'PRECIO_PREP': 'PREPARACION', 'PRECIO_TRANS': 'TRANSPORTE'})

        # Unir datos
        res = pd.merge(df_carga, df_gp[[col_ref_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_ref_gp, how='left')
        
        df_carga['DESCRIPCIÓN ZONA'] = df_carga['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
        df_costos['DESCRIPCIÓN ZONA'] = df_costos['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
        res = pd.merge(res, df_costos[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')

        # 3. CÁLCULOS BASE
        for c in ['BULTOS', 'PREPARACION', 'TRANSPORTE']:
            res[c] = pd.to_numeric(res[c], errors='coerce').fillna(0)

        # Logística Total = (Prep + Trans) * Bultos
        res['LOGISTICA_TOTAL'] = (res['PREPARACION'] + res['TRANSPORTE']) * res['BULTOS']

        # --- 4. TRANSFORMACIÓN A COLUMNAS (PIVOT) ---
        grouped = res.groupby(['GP', 'TIPO'])['LOGISTICA_TOTAL'].sum().reset_index()
        pivot = grouped.pivot(index='GP', columns='TIPO', values='LOGISTICA_TOTAL').fillna(0)
        pivot = pivot.reset_index()

        # 5. CONSTRUCCIÓN DEL CUADRO FINAL
        df_final = pd.DataFrame()
        df_final['GERENTE (GP)'] = pivot['GP']
        
        # Asignar MM y MP si existen
        df_final['LOGISTICA MM'] = pivot['MM'] if 'MM' in pivot.columns else 0.0
        df_final['LOGISTICA MP'] = pivot['MP'] if 'MP' in pivot.columns else 0.0
        
        # Cálculos Finales
        df_final['SUBTOTAL NETO'] = df_final['LOGISTICA MM'] + df_final['LOGISTICA MP']
        df_final['IVA 15%'] = df_final['SUBTOTAL NETO'] * 0.15
        df_final['TOTAL A FACTURAR'] = df_final['SUBTOTAL NETO'] + df_final['IVA 15%']

        # Fila de Totales Generales
        totales_dict = {'GERENTE (GP)': '--- TOTALES GENERALES ---'}
        for col in df_final.columns[1:]:
            totales_dict[col] = df_final[col].sum()
        
        df_reporte = pd.concat([df_final, pd.DataFrame([totales_dict])], ignore_index=True)

        # 6. MOSTRAR RESULTADOS EN PANTALLA
        st.subheader("📋 Cuadro Consolidado de Liquidación")
        st.table(df_reporte.style.format({c: "$ {:,.2f}" for c in df_reporte.columns if c != 'GERENTE (GP)'}))

        # Detalle expandible
        with st.expander("Ver detalle de carga procesada (Ítem por ítem)"):
            st.dataframe(res)

        # 7. EXCEL
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_reporte.to_excel(writer, index=False, sheet_name='Liquidacion_Consolidada')
            res.to_excel(writer, index=False, sheet_name='Detalle_Original')
        
        st.download_button(
            label="📥 Descargar Reporte Final (Excel)",
            data=output.getvalue(),
            file_name="Reporte_Liquidacion_Logistica.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Se produjo un error durante el procesamiento: {e}")
