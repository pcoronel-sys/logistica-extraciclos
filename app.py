import streamlit as st
import pandas as pd
from io import BytesIO

# Configuración de página ancha para mejor visualización de las columnas
st.set_page_config(page_title="Liquidación Logística Final", layout="wide")

st.title("📊 Reporte de Liquidación Logística (IVA 15%)")
st.markdown("Consolidado por **GP** con desglose horizontal de **MM** y **MP**, e IVA calculado sobre el Subtotal Neto.")

archivo_subido = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if archivo_subido:
    try:
        # 1. CARGA DE DATOS
        xls = pd.ExcelFile(archivo_subido)
        
        # Verificación de pestañas
        pestañas_requeridas = ['Carga', 'Maestro_GP', 'Maestro_Costos']
        if not all(p in xls.sheet_names for p in pestañas_requeridas):
            st.error(f"El archivo debe contener las pestañas: {', '.join(pestañas_requeridas)}")
            st.stop()

        df_carga = pd.read_excel(xls, 'Carga')
        df_gp = pd.read_excel(xls, 'Maestro_GP')
        df_costos = pd.read_excel(xls, 'Maestro_Costos')

        # Limpieza de nombres de columnas
        for df in [df_carga, df_gp, df_costos]:
            df.columns = df.columns.str.strip().str.upper()

        # Limpieza de códigos (Quitar .0 y espacios)
        def clean_c(s): return pd.to_numeric(s, errors='coerce').fillna(0).astype(int).astype(str)
        
        df_carga['CODIGO'] = clean_c(df_carga['CODIGO'])
        # Buscar columna que contenga la palabra CODIGO en el maestro
        col_ref_gp = [c for c in df_gp.columns if 'CODIGO' in c][0]
        df_gp[col_ref_gp] = clean_c(df_gp[col_ref_gp])

        # 2. CRUCES Y PROCESAMIENTO
        df_gp = df_gp.drop_duplicates(subset=[col_ref_gp])
        df_costos = df_costos.drop_duplicates(subset=['DESCRIPCIÓN ZONA'])
        
        # Estandarizar nombres de costos
        df_costos = df_costos.rename(columns={'PRECIO_PREP': 'PREPARACION', 'PRECIO_TRANS': 'TRANSPORTE'})

        # Unir datos
        res = pd.merge(df_carga, df_gp[[col_ref_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_ref_gp, how='left')
        
        df_carga['DESCRIPCIÓN ZONA
