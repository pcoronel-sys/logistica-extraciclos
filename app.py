import streamlit as st
import pandas as pd
from io import BytesIO

# Configuración de la página
st.set_page_config(page_title="Reporte Logístico Consolidado", layout="wide")

st.title("📊 Sistema de Liquidación Logística (IVA 15%)")
st.markdown("Generación de reporte automático por **GP** y **TIPO (MM/MP)**")

archivo_subido = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if archivo_subido:
    try:
        # 1. CARGA DE PESTAÑAS
        xls = pd.ExcelFile(archivo_subido)
        df_carga = pd.read_excel(xls, 'Carga')
        df_gp = pd.read_excel(xls, 'Maestro_GP')
        df_costos = pd.read_excel(xls, 'Maestro_Costos')

        # Limpiar nombres de columnas
        for df in [df_carga, df_gp, df_costos]:
            df.columns = df.columns.str.strip().str.upper()

        # --- MOTOR DE LIMPIEZA DE CÓDIGO (Quitar decimales .0) ---
        def limpiar_cod(s):
            return pd.to_numeric(s, errors='coerce').fillna(0).astype(int).astype(str)
        
        df_carga['CODIGO'] = limpiar_cod(df_carga['CODIGO'])
        # Buscamos la columna de código en el maestro (puede ser 'CODIGO' o 'CODIGO BAGÓ')
        col_ref_gp = [c for c in df_gp.columns if 'CODIGO' in c][0]
        df_gp[col_ref_gp] = limpiar_cod(df_gp[col_ref_gp])

        # 2. PROCESAMIENTO Y CRUCES
        df_gp = df_gp.drop_duplicates(subset=[col_ref_gp])
        df_costos = df_costos.drop_duplicates(subset=['DESCRIPCIÓN ZONA'])

        # Unir Carga con Maestro_GP para tener GP y TIPO (MM/MP)
        resultado = pd.merge(df_carga, df_gp[[col_ref_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_ref_gp, how='left')
        
        # Unir con Maestro_Costos (Renombrando Precio_Prep a PREPARACION si es necesario)
        df_costos = df_costos.rename(columns={'PRECIO_PREP': 'PREPARACION', 'PRECIO_TRANS': 'TRANSPORTE'})
        df_carga['DESCRIPCIÓN ZONA'] = df_carga['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
        df_costos['DESCRIPCIÓN ZONA'] = df_costos['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
        
        resultado = pd.merge(resultado, df_costos[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')

        # 3. CÁLCULOS POR LÍNEA
        resultado['BULTOS'] = pd.to_numeric(resultado['BULTOS'], errors='coerce').fillna(0)
        resultado['PREPARACION'] = pd.to_numeric(resultado['PREPARACION'], errors='coerce').fillna(0)
        resultado['TRANSPORTE'] = pd.to_numeric(resultado['TRANSPORTE'], errors='coerce').fillna(0)

        resultado['TOTAL PREPARACION'] = resultado['PREPARACION'] * resultado['BULTOS']
        resultado['TOTAL TRANSPORTE'] = resultado['TRANSPORTE'] * resultado['BULTOS']
        resultado['SUBTOTAL'] = resultado['TOTAL PREPARACION'] + resultado['TOTAL TRANSPORTE']

        # --- 4. CUADRO RESUMEN CONSOLIDADO (Como en la imagen) ---
        st.subheader("📋 Resumen Consolidado de Gastos")
        
        # Agrupamos por GP y TIPO
        resumen = resultado.groupby(['GP', 'TIPO']).agg({
            'TOTAL PREPARACION': 'sum',
            'TOTAL TRANSPORTE': 'sum',
            'SUBTOTAL': 'sum'
        }).reset_index()

        # Calcular IVA 15% y Total con IVA
        resumen['IVA 15%'] = resumen['SUBTOTAL'] * 0.15
        resumen['TOTAL CON IVA'] = resumen['SUBTOTAL'] + resumen['IVA 15%']

        # Fila de Totales Generales
        totales_data = {
            'GP': '--- TOTALES GENERALES ---',
            'TIPO': '',
            'TOTAL PREPARACION': resumen['TOTAL PREPARACION'].sum(),
            'TOTAL TRANSPORTE': resumen['TOTAL TRANSPORTE'].sum(),
            'SUBTOTAL': resumen['SUBTOTAL'].sum(),
            'IVA 15%': resumen['IVA 15%'].sum(),
            'TOTAL CON IVA': resumen['TOTAL CON IVA'].sum()
        }
        resumen_final = pd.concat([resumen, pd.DataFrame([totales_data])], ignore_index=True)

        # Mostrar tabla estilizada
        st.table(resumen_final.style.format({
            'TOTAL PREPARACION': '$ {:,.2f}',
            'TOTAL TRANSPORTE': '$ {:,.2f}',
            'SUBTOTAL': '$ {:,.2f}',
            'IVA 15%': '$ {:,.2f}',
            'TOTAL CON IVA': '$ {:,.2f}'
        }))

        # 5. DESCARGA DEL REPORTE
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            resumen_final.to_excel(writer, index=False, sheet_name='Cuadro_Resumen')
            resultado.to_excel(writer, index=False, sheet_name='Detalle_por_Item')
        
        st.download_button(
            label="📥 Descargar Reporte Final (Cuadro + Detalle)",
            data=output.getvalue(),
            file_name="Reporte_Logistica_Consolidado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Vista previa del detalle abajo
        with st.expander("Ver detalle por ítem"):
            st.dataframe(resultado)

    except Exception as e:
        st.error(f"Error al procesar: {e}")
