import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Motor Logístico Final", layout="wide")

st.title("🚀 Procesador Logístico con Totales y Limpieza Numérica")

archivo_subido = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if archivo_subido:
    try:
        # 1. CARGA Y LIMPIEZA INICIAL
        xls = pd.ExcelFile(archivo_subido)
        df_carga = pd.read_excel(xls, 'Carga')
        df_gp = pd.read_excel(xls, 'Maestro_GP')
        df_costos = pd.read_excel(xls, 'Maestro_Costos')

        # Estandarizar columnas (Mayúsculas y sin espacios)
        for df in [df_carga, df_gp, df_costos]:
            df.columns = df.columns.str.strip().str.upper()

        # Evitar duplicados en maestros
        df_gp = df_gp.drop_duplicates(subset=['DENOMINACIÓN MATERIAL'], keep='first')
        df_costos = df_costos.drop_duplicates(subset=['DESCRIPCIÓN ZONA'], keep='first')

        # 2. CRUCES (MERGE)
        resultado = pd.merge(df_carga, df_gp[['DENOMINACIÓN MATERIAL', 'GP']], on='DENOMINACIÓN MATERIAL', how='left')
        resultado['QUIEN PAGA'] = resultado['GP']
        resultado = pd.merge(resultado, df_costos[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')

        # 3. PROCESAMIENTO NUMÉRICO (Limpieza de comas/puntos)
        cols_numericas = ['BULTOS', 'PREPARACION', 'TRANSPORTE']
        for col in cols_numericas:
            # Convertimos a número puro, eliminando cualquier caracter extraño
            resultado[col] = pd.to_numeric(resultado[col], errors='coerce').fillna(0)

        # CÁLCULOS
        resultado['TOTAL PREPARACION'] = resultado['PREPARACION'] * resultado['BULTOS']
        resultado['TOTAL TRANSPORTE'] = resultado['TRANSPORTE'] * resultado['BULTOS']
        resultado['TOTAL A PAGAR'] = resultado['TOTAL PREPARACION'] + resultado['TOTAL TRANSPORTE']

        # 4. CREAR FILA DE TOTALES AL FINAL
        # Creamos una fila vacía con la palabra "TOTALES"
        fila_totales = pd.Series(dtype='object')
        fila_totales['DENOMINACIÓN MATERIAL'] = '--- TOTALES GENERALES ---'
        fila_totales['TOTAL PREPARACION'] = resultado['TOTAL PREPARACION'].sum()
        fila_totales['TOTAL TRANSPORTE'] = resultado['TOTAL TRANSPORTE'].sum()
        fila_totales['TOTAL A PAGAR'] = resultado['TOTAL A PAGAR'].sum()
        
        # Unir la fila de totales al dataframe
        df_final = pd.concat([resultado, pd.DataFrame([fila_totales])], ignore_index=True)

        st.success("✅ Reporte generado con totales al final")
        st.dataframe(df_final)

        # 5. GENERAR EXCEL CON FORMATO NUMÉRICO
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Reporte_Final')
        
        st.download_button(
            label="📥 Descargar Reporte Final con Totales",
            data=output.getvalue(),
            file_name="Reporte_Logistica_Completo.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Error en el proceso: {e}")
