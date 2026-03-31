import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Automatización Logística", layout="wide")

st.title("🚚 Calculador Automático de Logística")
st.write("Sube tu Excel y el sistema calculará Totales x Bultos y asignará GP.")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if uploaded_file:
    try:
        # 1. Leer las pestañas
        df_carga = pd.read_excel(uploaded_file, sheet_name='Carga')
        df_gp = pd.read_excel(uploaded_file, sheet_name='Maestro_GP')
        df_costos = pd.read_excel(uploaded_file, sheet_name='Maestro_Costos')

        # 2. Cruce para asignar el GP (Gerente de Producto)
        # Traemos la columna 'GP' basada en el 'Denominación Material'
        df_final = pd.merge(df_carga, df_gp, on='Denominación Material', how='left')
        df_final['QUIEN PAGA'] = df_final['GP'] # Se asume que el GP es quien paga

        # 3. Cruce para asignar Precios Unitarios por Zona
        # Traemos 'Precio_Prep' y 'Precio_Trans' basados en 'Descripción Zona'
        df_final = pd.merge(df_final, df_costos, on='Descripción Zona', how='left')

        # 4. CÁLCULOS MATEMÁTICOS (Multiplicación por Bultos)
        # Rellenamos bultos vacíos con 0 para evitar errores
        df_final['Bultos'] = df_final['Bultos'].fillna(0)
        
        # Totales
        df_final['TOTAL PREPARACION'] = df_final['Precio_Prep'] * df_final['Bultos']
        df_final['TOTAL TRANSPORTE'] = df_final['Precio_Trans'] * df_final['Bultos']
        
        # Gran Total
        df_final['TOTAL A PAGAR'] = df_final['TOTAL PREPARACION'] + df_final['TOTAL TRANSPORTE']

        # 5. Ordenar columnas como en tu imagen (opcional)
        columnas_ordenadas = [
            'Denominación Material', 'GP', 'QUIEN PAGA', 'Precio_Prep', 
            'TOTAL PREPARACION', 'Precio_Trans', 'TOTAL TRANSPORTE', 
            'TOTAL A PAGAR', 'Descripción Zona', 'Bultos'
        ]
        # Solo mostramos las que existan para evitar errores
        cols_presentes = [c for c in columnas_ordenadas if c in df_final.columns]
        
        st.success("✅ Procesado correctamente")
        st.dataframe(df_final[cols_presentes])

        # Botón de descarga
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Resultado')
        
        st.download_button(
            label="📥 Descargar Excel Procesado",
            data=output.getvalue(),
            file_name="Logistica_Calculada.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Error: Asegúrate de que las pestañas y columnas tengan los nombres correctos. Detalle: {e}")
