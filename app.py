import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Motor Logístico Extra", layout="wide")

st.title("🚀 Procesador de Logística y Asignación de GP")
st.markdown("Sube tu archivo Excel con las pestañas: **Carga**, **Maestro_GP** y **Maestro_Costos**.")

archivo_subido = st.file_uploader("Selecciona el archivo Excel", type=['xlsx'])

if archivo_subido:
    try:
        # 1. LEER PESTAÑAS
        xls = pd.ExcelFile(archivo_subido)
        df_carga = pd.read_excel(xls, 'Carga')
        df_gp = pd.read_excel(xls, 'Maestro_GP')
        df_costos = pd.read_excel(xls, 'Maestro_Costos')

        # 2. LIMPIEZA EXTREMA DE COLUMNAS
        # Esto quita espacios vacíos y pone todo en MAYÚSCULAS para evitar errores
        df_carga.columns = df_carga.columns.str.strip().str.upper()
        df_gp.columns = df_gp.columns.str.strip().str.upper()
        df_costos.columns = df_costos.columns.str.strip().str.upper()

        # Estandarizar los datos internos (mayúsculas y sin espacios)
        df_carga['DENOMINACIÓN MATERIAL'] = df_carga['DENOMINACIÓN MATERIAL'].astype(str).str.strip().str.upper()
        df_gp['DENOMINACIÓN MATERIAL'] = df_gp['DENOMINACIÓN MATERIAL'].astype(str).str.strip().str.upper()
        
        df_carga['DESCRIPCIÓN ZONA'] = df_carga['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
        df_costos['DESCRIPCIÓN ZONA'] = df_costos['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()

        # 3. CRUCE PARA GP
        # Buscamos por la denominación para traer al GP
        resultado = pd.merge(df_carga, df_gp[['DENOMINACIÓN MATERIAL', 'GP']], on='DENOMINACIÓN MATERIAL', how='left')
        resultado['QUIEN PAGA'] = resultado['GP']

        # 4. CRUCE PARA COSTOS
        # Aquí traemos PREPARACION y TRANSPORTE unitarios
        resultado = pd.merge(resultado, df_costos[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')

        # 5. CÁLCULOS
        resultado['BULTOS'] = pd.to_numeric(resultado['BULTOS'], errors='coerce').fillna(0)
        resultado['PREPARACION'] = pd.to_numeric(resultado['PREPARACION'], errors='coerce').fillna(0)
        resultado['TRANSPORTE'] = pd.to_numeric(resultado['TRANSPORTE'], errors='coerce').fillna(0)

        resultado['TOTAL PREPARACION'] = resultado['PREPARACION'] * resultado['BULTOS']
        resultado['TOTAL TRANSPORTE'] = resultado['TRANSPORTE'] * resultado['BULTOS']
        resultado['TOTAL A PAGAR'] = resultado['TOTAL PREPARACION'] + resultado['TOTAL TRANSPORTE']

        st.success("✅ ¡Motor ejecutado con éxito!")
        st.dataframe(resultado.head(20))

        # 6. BOTÓN DE DESCARGA
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            resultado.to_excel(writer, index=False, sheet_name='Resultado')
        
        st.download_button(
            label="📥 Descargar Excel Finalizado",
            data=output.getvalue(),
            file_name="Logistica_Procesada.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Error detectado: {e}")
        st.warning("Asegúrate de que las columnas en 'Maestro_Costos' se llamen exactamente: DESCRIPCIÓN ZONA, PREPARACION, TRANSPORTE")
