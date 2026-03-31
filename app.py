import streamlit as st
# Esta línea ayuda a evitar errores de gráficos que no usaremos
st.set_option('deprecation.showPyplotGlobalUse', False)

import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Logística Automatizada", layout="wide")

st.title("🚚 Sistema de Cálculo Logístico")
st.info("Pestañas requeridas: Carga, Maestro_GP, Maestro_Costos")

archivo = st.file_uploader("Sube tu Excel", type=['xlsx'])

if archivo:
    try:
        df_carga = pd.read_excel(archivo, sheet_name='Carga')
        df_gp = pd.read_excel(archivo, sheet_name='Maestro_GP')
        df_costos = pd.read_excel(archivo, sheet_name='Maestro_Costos')

        # Limpiar datos
        for df in [df_carga, df_gp, df_costos]:
            df.columns = df.columns.str.strip()

        # Cruces
        res = pd.merge(df_carga, df_gp, on='Denominación Material', how='left')
        res = pd.merge(res, df_costos, on='Descripción Zona', how='left')

        # Cálculos
        res['Bultos'] = pd.to_numeric(res['Bultos'], errors='coerce').fillna(0)
        res['Precio_Prep'] = pd.to_numeric(res['Precio_Prep'], errors='coerce').fillna(0)
        res['Precio_Trans'] = pd.to_numeric(res['Precio_Trans'], errors='coerce').fillna(0)

        res['TOTAL PREPARACION'] = res['Precio_Prep'] * res['Bultos']
        res['TOTAL TRANSPORTE'] = res['Precio_Trans'] * res['Bultos']
        res['TOTAL A PAGAR'] = res['TOTAL PREPARACION'] + res['TOTAL TRANSPORTE']

        st.success("✅ Procesado")
        st.dataframe(res.head(10))

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            res.to_excel(writer, index=False)
        
        st.download_button("📥 Descargar Resultado", output.getvalue(), "resultado.xlsx")

    except Exception as e:
        st.error(f"Error: {e}")
