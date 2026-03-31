import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Motor Logístico Final", layout="wide")

st.title("🚀 Procesador Logístico: Limpieza de Códigos y Totales")

archivo_subido = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if archivo_subido:
    try:
        # 1. CARGAR DATOS
        xls = pd.ExcelFile(archivo_subido)
        df_carga = pd.read_excel(xls, 'Carga')
        df_gp = pd.read_excel(xls, 'Maestro_GP')
        df_costos = pd.read_excel(xls, 'Maestro_Costos')

        # Estandarizar nombres de columnas (Mayúsculas y sin espacios)
        for df in [df_carga, df_gp, df_costos]:
            df.columns = df.columns.str.strip().str.upper()

        # --- LIMPIEZA DE CÓDIGO (Quitar decimales .0) ---
        def formatear_codigo(serie):
            # Convierte a número, quita decimales y lo deja como texto limpio
            return pd.to_numeric(serie, errors='coerce').fillna(0).astype(int).astype(str)

        if 'CODIGO' in df_carga.columns:
            df_carga['CODIGO'] = formatear_codigo(df_carga['CODIGO'])
        
        # Identificar columna de código en el Maestro GP (puede variar el nombre)
        col_cod_gp = [c for c in df_gp.columns if 'CODIGO' in c][0]
        df_gp[col_cod_gp] = formatear_codigo(df_gp[col_cod_gp])

        # 2. EVITAR DUPLICADOS Y CRUCES
        df_gp = df_gp.drop_duplicates(subset=[col_cod_gp], keep='first')
        df_costos = df_costos.drop_duplicates(subset=['DESCRIPCIÓN ZONA'], keep='first')

        # Cruce para GP y Quien Paga
        resultado = pd.merge(df_carga, df_gp[[col_cod_gp, 'GP']], left_on='CODIGO', right_on=col_cod_gp, how='left')
        resultado['QUIEN PAGA'] = resultado['GP']
        
        # Cruce para PREPARACION y TRANSPORTE unitarios
        df_carga['DESCRIPCIÓN ZONA'] = df_carga['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
        df_costos['DESCRIPCIÓN ZONA'] = df_costos['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
        resultado = pd.merge(resultado, df_costos[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')

        # 3. CÁLCULOS MATEMÁTICOS
        resultado['BULTOS'] = pd.to_numeric(resultado['BULTOS'], errors='coerce').fillna(0)
        resultado['PREPARACION'] = pd.to_numeric(resultado['PREPARACION'], errors='coerce').fillna(0)
        resultado['TRANSPORTE'] = pd.to_numeric(resultado['TRANSPORTE'], errors='coerce').fillna(0)

        resultado['TOTAL PREPARACION'] = resultado['PREPARACION'] * resultado['BULTOS']
        resultado['TOTAL TRANSPORTE'] = resultado['TRANSPORTE'] * resultado['BULTOS']
        resultado['TOTAL A PAGAR'] = resultado['TOTAL PREPARACION'] + resultado['TOTAL TRANSPORTE']

        # 4. GENERAR REPORTE CON TOTALES AL FINAL
        resumen_totales = pd.DataFrame([{
            'CODIGO': 'TOTALES',
            'DENOMINACIÓN MATERIAL': 'SUMATORIA DEL REPORTE',
            'TOTAL PREPARACION': resultado['TOTAL PREPARACION'].sum(),
            'TOTAL TRANSPORTE': resultado['TOTAL TRANSPORTE'].sum(),
            'TOTAL A PAGAR': resultado['TOTAL A PAGAR'].sum()
        }])

        df_final = pd.concat([resultado, resumen_totales], ignore_index=True)

        # 5. MOSTRAR Y DESCARGAR
        st.success("✅ ¡Cálculos realizados! Códigos corregidos y totales generados.")
        st.dataframe(df_final)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Reporte_Final')
        
        st.download_button(
            label="📥 Descargar Reporte con Totales",
            data=output.getvalue(),
            file_name="Reporte_Logistica_Extra.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Error en la ejecución: {e}")
