import streamlit as st
import pandas as pd
from io import BytesIO

# Configuración visual
st.set_page_config(page_title="Motor Logístico Extra", layout="wide")

st.title("🚀 Procesador de Logística y Asignación de GP")
st.markdown("Sube tu archivo Excel con las pestañas: **Carga**, **Maestro_GP** y **Maestro_Costos**.")

archivo_subido = st.file_uploader("Selecciona el archivo Excel", type=['xlsx'])

if archivo_subido:
    try:
        # 1. LEER PESTAÑAS
        df_carga = pd.read_excel(archivo_subido, sheet_name='Carga')
        df_gp = pd.read_excel(archivo_subido, sheet_name='Maestro_GP')
        df_costos = pd.read_excel(archivo_subido, sheet_name='Maestro_Costos')

        # 2. LIMPIEZA DE DATOS (Nombres de columnas y espacios)
        for df in [df_carga, df_gp, df_costos]:
            df.columns = df.columns.str.strip()
        
        # Estandarizar claves para que el cruce sea perfecto
        df_carga['Denominación Material'] = df_carga['Denominación Material'].astype(str).str.strip()
        df_gp['Denominación Material'] = df_gp['Denominación Material'].astype(str).str.strip()
        
        df_carga['Descripción Zona'] = df_carga['Descripción Zona'].astype(str).str.strip()
        df_costos['Descripción Zona'] = df_costos['Descripción Zona'].astype(str).str.strip()

        # 3. CRUCE PARA ASIGNAR GERENTE (GP)
        # Buscamos por 'Denominación Material' para traer la columna 'GP'
        resultado = pd.merge(df_carga, df_gp[['Denominación Material', 'GP']], on='Denominación Material', how='left')
        
        # Llenar la columna 'QUIEN PAGA' con el valor de 'GP'
        resultado['QUIEN PAGA'] = resultado['GP']

        # 4. CRUCE PARA ASIGNAR COSTOS POR ZONA
        # Buscamos por 'Descripción Zona' para traer 'PREPARACION' y 'TRANSPORTE' unitarios
        resultado = pd.merge(resultado, df_costos, on='Descripción Zona', how='left')

        # 5. CÁLCULOS MATEMÁTICOS (Valor Unitario x Bultos)
        # Aseguramos que 'Bultos' y los precios sean números
        resultado['Bultos'] = pd.to_numeric(resultado['Bultos'], errors='coerce').fillna(0)
        resultado['PREPARACION'] = pd.to_numeric(resultado['PREPARACION'], errors='coerce').fillna(0)
        resultado['TRANSPORTE'] = pd.to_numeric(resultado['TRANSPORTE'], errors='coerce').fillna(0)

        # Calculamos los totales
        resultado['TOTAL PREPARACION'] = resultado['PREPARACION'] * resultado['Bultos']
        resultado['TOTAL TRANSPORTE'] = resultado['TRANSPORTE'] * resultado['Bultos']
        resultado['TOTAL A PAGAR'] = resultado['TOTAL PREPARACION'] + resultado['TOTAL TRANSPORTE']

        # 6. MOSTRAR RESULTADOS
        st.success("✅ ¡Cálculos completados con éxito!")
        
        # Reordenar un poco para que se vea como en tu imagen original
        columnas_finales = [
            'Denominación Material', 'GP', 'QUIEN PAGA', 'PREPARACION', 
            'TOTAL PREPARACION', 'TRANSPORTE', 'TOTAL TRANSPORTE', 
            'TOTAL A PAGAR', 'Descripción Zona', 'Bultos'
        ]
        
        # Mostrar solo las columnas que existan en el resultado final
        st.dataframe(resultado[[c for c in columnas_finales if c in resultado.columns]])

        # 7. BOTÓN DE DESCARGA
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            resultado.to_excel(writer, index=False, sheet_name='Resultado_Final')
        
        st.download_button(
            label="📥 Descargar Excel Procesado",
            data=output.getvalue(),
            file_name="Reporte_Logistica_Final.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Ocurrió un error al procesar: {e}")
        st.info("Revisa que los nombres de las pestañas sean: Carga, Maestro_GP y Maestro_Costos")
