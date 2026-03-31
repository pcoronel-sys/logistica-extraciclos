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

        # --- MOTOR DE LIMPIEZA DE CÓDIGO (Quitar decimales) ---
        def limpiar_codigo(serie):
            # Convierte a número, luego a entero (quita el .0) y finalmente a texto
            return pd.to_numeric(serie, errors='coerce').fillna(0).astype(int).astype(str)

        if 'CODIGO' in df_carga.columns:
            df_carga['CODIGO'] = limpiar_codigo(df_carga['CODIGO'])
        
        # En el maestro el código puede llamarse 'CODIGO' o 'CODIGO BAGÓ'
        col_busqueda_gp = 'CODIGO' if 'CODIGO' in df_gp.columns else df_gp.columns[0]
        df_gp[col_busqueda_gp] = limpiar_codigo(df_gp[col_busqueda_gp])

        # 2. EVITAR DUPLICADOS Y CRUCES
        df_gp = df_gp.drop_duplicates(subset=[col_busqueda_gp], keep='first')
        df_costos = df_costos.drop_duplicates(subset=['DESCRIPCIÓN ZONA'], keep='first')

        # Cruce para GP
        resultado = pd.merge(df_carga, df_gp[[col_busqueda_gp, 'GP']], left_on='CODIGO', right_on=col_busqueda_gp, how='left')
        
        # Cruce para Costos (Normalizamos zonas antes)
        df_carga['DESCRIPCIÓN ZONA'] = df_carga['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
        df_costos['DESCRIPCIÓN ZONA'] = df_costos['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
        resultado = pd.merge(resultado, df_costos[['DESCRIPCIÓN ZONA', 'PRECIO_PREP', 'PRECIO_TRANS']], on='DESCRIPCIÓN ZONA', how='left')

        # 3. CÁLCULOS
        resultado['BULTOS'] = pd.to_numeric(resultado['BULTOS'], errors='coerce').fillna(0)
        resultado['PRECIO_PREP'] = pd.to_numeric(resultado['PRECIO_PREP'], errors='coerce').fillna(0)
        resultado['PRECIO_TRANS'] = pd.to_numeric(resultado['PRECIO_TRANS'], errors='coerce').fillna(0)

        resultado['TOTAL PREPARACION'] = resultado['PRECIO_PREP'] * resultado['BULTOS']
        resultado['TOTAL TRANSPORTE'] = resultado['PRECIO_TRANS'] * resultado['BULTOS']
        resultado['TOTAL A PAGAR'] = resultado['TOTAL PREPARACION'] + resultado['TOTAL TRANSPORTE']

        # 4. FILA DE TOTALES Y REPORTE
        # Sumamos los valores
        sum_prep = resultado['TOTAL PREPARACION'].sum()
        sum_trans = resultado['TOTAL TRANSPORTE'].sum()
        sum_total = resultado['TOTAL A PAGAR'].sum()

        # Creamos la fila de totales
        fila_totales = pd.DataFrame([{
            'CODIGO': 'TOTALES',
            'DENOMINACIÓN MATERIAL': '--- RESUMEN FINAL ---',
            'TOTAL PREPARACION': sum_prep,
            'TOTAL TRANSPORTE': sum_trans,
            'TOTAL A PAGAR': sum_total
        }])

        df_final = pd.concat([resultado, fila_totales], ignore_index=True)

        # 5. MOSTRAR Y DESCARGAR
        st.success("✅ Procesado con éxito. Códigos limpiados y totales calculados.")
        st.dataframe(df_final)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Reporte_Logistica')
        
        st.download_button(
            label="📥 Descargar Reporte Final",
            data=output.getvalue(),
            file_name="Reporte_Final_Limpio.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Error: {e}")
