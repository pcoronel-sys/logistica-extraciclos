import streamlit as st
import pandas as pd
from io import BytesIO

# Configuración de la página
st.set_page_config(page_title="Automatización Logística", layout="wide")

st.title("🚚 Procesador Logístico: GP y Bultos")
st.markdown("""
### Instrucciones de las pestañas en tu Excel:
1. **Carga**: Datos del día (`Denominación Material`, `Descripción Zona`, `Bultos`).
2. **Maestro_GP**: Relación (`Denominación Material` y `GP`).
3. **Maestro_Costos**: Precios (`Descripción Zona`, `Precio_Prep`, `Precio_Trans`).
""")

archivo = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if archivo:
    try:
        # 1. Cargar las pestañas
        df_carga = pd.read_excel(archivo, sheet_name='Carga')
        df_gp = pd.read_excel(archivo, sheet_name='Maestro_GP')
        df_costos = pd.read_excel(archivo, sheet_name='Maestro_Costos')

        # 2. Limpieza de datos (Quitar espacios vacíos y estandarizar a mayúsculas)
        for df in [df_carga, df_gp, df_costos]:
            df.columns = df.columns.str.strip()
            # Convertir columnas clave a mayúsculas y sin espacios para que el cruce sea perfecto
            if 'Denominación Material' in df.columns:
                df['Denominación Material'] = df['Denominación Material'].astype(str).str.strip().str.upper()
            if 'Descripción Zona' in df.columns:
                df['Descripción Zona'] = df['Descripción Zona'].astype(str).str.strip().str.upper()

        # 3. Cruce para asignar Gerente (GP)
        resultado = pd.merge(df_carga, df_gp, on='Denominación Material', how='left')
        resultado['QUIEN PAGA'] = resultado['GP']

        # 4. Cruce para asignar Precios por Zona
        resultado = pd.merge(resultado, df_costos, on='Descripción Zona', how='left')

        # 5. Cálculos Matemáticos
        # Aseguramos que sean números, si hay texto lo pone como 0
        resultado['Bultos'] = pd.to_numeric(resultado['Bultos'], errors='coerce').fillna(0)
        resultado['Precio_Prep'] = pd.to_numeric(resultado['Precio_Prep'], errors='coerce').fillna(0)
        resultado['Precio_Trans'] = pd.to_numeric(resultado['Precio_Trans'], errors='coerce').fillna(0)

        # Operaciones: Valor Unitario * Bultos
        resultado['TOTAL PREPARACION'] = resultado['Precio_Prep'] * resultado['Bultos']
        resultado['TOTAL TRANSPORTE'] = resultado['Precio_Trans'] * resultado['Bultos']
        resultado['TOTAL A PAGAR'] = resultado['TOTAL PREPARACION'] + resultado['TOTAL TRANSPORTE']

        # 6. Mostrar Vista Previa
        st.success("✅ ¡Cálculos realizados con éxito!")
        st.dataframe(resultado)

        # 7. Preparar descarga
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            resultado.to_excel(writer, index=False, sheet_name='Resultados')
        
        st.download_button(
            label="📥 Descargar Excel Final",
            data=output.getvalue(),
            file_name="Logistica_Procesada.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Hubo un problema al leer el archivo: {e}")
        st.info("Revisa que los nombres de las pestañas sean exactamente: Carga, Maestro_GP y Maestro_Costos")
