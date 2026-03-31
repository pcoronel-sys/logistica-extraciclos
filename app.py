import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Motor Logístico Extra", layout="wide")

st.title("🚀 Procesador de Logística (Versión Anti-Duplicados)")

archivo_subido = st.file_uploader("Selecciona el archivo Excel", type=['xlsx'])

if archivo_subido:
    try:
        # 1. LEER PESTAÑAS
        xls = pd.ExcelFile(archivo_subido)
        df_carga = pd.read_excel(xls, 'Carga')
        df_gp = pd.read_excel(xls, 'Maestro_GP')
        df_costos = pd.read_excel(xls, 'Maestro_Costos')

        # 2. LIMPIEZA DE COLUMNAS
        df_carga.columns = df_carga.columns.str.strip().str.upper()
        df_gp.columns = df_gp.columns.str.strip().str.upper()
        df_costos.columns = df_costos.columns.str.strip().str.upper()

        # 3. ELIMINAR DUPLICADOS EN LOS MAESTROS (¡Esto evita que se multipliquen las filas!)
        # Nos quedamos solo con la primera vez que aparezca cada producto o zona
        df_gp = df_gp.drop_duplicates(subset=['DENOMINACIÓN MATERIAL'], keep='first')
        df_costos = df_costos.drop_duplicates(subset=['DESCRIPCIÓN ZONA'], keep='first')

        # Estandarizar datos
        df_carga['DENOMINACIÓN MATERIAL'] = df_carga['DENOMINACIÓN MATERIAL'].astype(str).str.strip().str.upper()
        df_gp['DENOMINACIÓN MATERIAL'] = df_gp['DENOMINACIÓN MATERIAL'].astype(str).str.strip().str.upper()
        df_carga['DESCRIPCIÓN ZONA'] = df_carga['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
        df_costos['DESCRIPCIÓN ZONA'] = df_costos['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()

        # 4. CRUCE (Merge)
        # Ahora el cruce es 1 a 1, por lo que no se duplicarán filas
        resultado = pd.merge(df_carga, df_gp[['DENOMINACIÓN MATERIAL', 'GP']], on='DENOMINACIÓN MATERIAL', how='left')
        resultado['QUIEN PAGA'] = resultado['GP']

        resultado = pd.merge(resultado, df_costos[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')

        # 5. CÁLCULOS
        resultado['BULTOS'] = pd.to_numeric(resultado['BULTOS'], errors='coerce').fillna(0)
        resultado['PREPARACION'] = pd.to_numeric(resultado['PREPARACION'], errors='coerce').fillna(0)
        resultado['TRANSPORTE'] = pd.to_numeric(resultado['TRANSPORTE'], errors='coerce').fillna(0)

        resultado['TOTAL PREPARACION'] = resultado['PREPARACION'] * resultado['BULTOS']
        resultado['TOTAL TRANSPORTE'] = resultado['TRANSPORTE'] * resultado['BULTOS']
        resultado['TOTAL A PAGAR'] = resultado['TOTAL PREPARACION'] + resultado['TOTAL TRANSPORTE']

        st.success(f"✅ Procesado. Filas originales: {len(df_carga)} | Filas finales: {len(resultado)}")
        st.dataframe(resultado)

        # 6. BOTÓN DE DESCARGA
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            resultado.to_excel(writer, index=False, sheet_name='Resultado')
        
        st.download_button("📥 Descargar Excel", output.getvalue(), "Reporte_Sin_Duplicados.xlsx")

    except Exception as e:
        st.error(f"Error detectado: {e}")
