import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Automatización Logística", layout="wide")

st.title("🚚 Sistema de Cálculo Logístico x Bultos")
st.info("Asegúrate de que tu Excel tenga las pestañas: Carga, Maestro_GP y Maestro_Costos")

archivo = st.file_uploader("Sube tu archivo Excel aquí", type=['xlsx'])

if archivo:
    try:
        # Cargar datos
        df_carga = pd.read_excel(archivo, sheet_name='Carga')
        df_gp = pd.read_excel(archivo, sheet_name='Maestro_GP')
        df_costos = pd.read_excel(archivo, sheet_name='Maestro_Costos')

        # Limpiar espacios en blanco en los nombres de las columnas por si acaso
        for df in [df_carga, df_gp, df_costos]:
            df.columns = df.columns.str.strip()

        # 1. Cruzar con Gerentes (GP)
        resultado = pd.merge(df_carga, df_gp, on='Denominación Material', how='left')
        resultado['QUIEN PAGA'] = resultado['GP']

        # 2. Cruzar con Costos por Zona
        resultado = pd.merge(resultado, df_costos, on='Descripción Zona', how='left')

        # 3. Cálculos Automáticos
        resultado['Bultos'] = pd.to_numeric(resultado['Bultos'], errors='coerce').fillna(0)
        resultado['Precio_Prep'] = pd.to_numeric(resultado['Precio_Prep'], errors='coerce').fillna(0)
        resultado['Precio_Trans'] = pd.to_numeric(resultado['Precio_Trans'], errors='coerce').fillna(0)

        # Multiplicación solicitada
        resultado['TOTAL PREPARACION'] = resultado['Precio_Prep'] * resultado['Bultos']
        resultado['TOTAL TRANSPORTE'] = resultado['Precio_Trans'] * resultado['Bultos']
        resultado['TOTAL A PAGAR'] = resultado['TOTAL PREPARACION'] + resultado['TOTAL TRANSPORTE']

        # Mostrar resultados en pantalla
        st.success("¡Procesado! Aquí tienes una vista previa:")
        st.dataframe(resultado.head(20))

        # Crear el archivo de descarga
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            resultado.to_excel(writer, index=False, sheet_name='Reporte_Calculado')
        
        st.download_button(
            label="📥 Descargar Excel con Totales",
            data=output.getvalue(),
            file_name="Resultado_Logistica.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Revisa el archivo. Error detectado: {e}")
