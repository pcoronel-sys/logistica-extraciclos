import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Reporte Logístico por Tipo", layout="wide")

st.title("📊 Procesador Logístico: Clasificación MM vs MP")

archivo_subido = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if archivo_subido:
    try:
        # 1. CARGA DE DATOS
        xls = pd.ExcelFile(archivo_subido)
        df_carga = pd.read_excel(xls, 'Carga')
        df_gp = pd.read_excel(xls, 'Maestro_GP')
        df_costos = pd.read_excel(xls, 'Maestro_Costos')

        # Estandarizar columnas
        for df in [df_carga, df_gp, df_costos]:
            df.columns = df.columns.str.strip().str.upper()

        # Limpiar Códigos (Quitar .0)
        def fmt_code(s): return pd.to_numeric(s, errors='coerce').fillna(0).astype(int).astype(str)
        
        df_carga['CODIGO'] = fmt_code(df_carga['CODIGO'])
        col_cod_gp = [c for c in df_gp.columns if 'CODIGO' in c][0]
        df_gp[col_cod_gp] = fmt_code(df_gp[col_cod_gp])

        # 2. PROCESAMIENTO (Cruces incluyendo TIPO)
        df_gp = df_gp.drop_duplicates(subset=[col_cod_gp])
        df_costos = df_costos.drop_duplicates(subset=['DESCRIPCIÓN ZONA'])

        # Cruzamos para traer GP y TIPO (MM/MP)
        resultado = pd.merge(df_carga, df_gp[[col_cod_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_cod_gp, how='left')
        resultado['QUIEN PAGA'] = resultado['GP']
        
        # Cruzamos para traer costos de zona
        df_carga['DESCRIPCIÓN ZONA'] = df_carga['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
        df_costos['DESCRIPCIÓN ZONA'] = df_costos['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
        resultado = pd.merge(resultado, df_costos[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')

        # 3. CÁLCULOS
        for c in ['BULTOS', 'PREPARACION', 'TRANSPORTE']:
            resultado[c] = pd.to_numeric(resultado[c], errors='coerce').fillna(0)

        resultado['TOTAL PREPARACION'] = resultado['PREPARACION'] * resultado['BULTOS']
        resultado['TOTAL TRANSPORTE'] = resultado['TRANSPORTE'] * resultado['BULTOS']
        resultado['TOTAL A PAGAR'] = resultado['TOTAL PREPARACION'] + resultado['TOTAL TRANSPORTE']

        # --- SECCIÓN DE RESUMENES ---
        st.subheader("📌 Resumen Ejecutivo")
        
        # Crear 3 métricas principales
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Preparación", f"$ {resultado['TOTAL PREPARACION'].sum():,.2f}")
        m2.metric("Total Transporte", f"$ {resultado['TOTAL TRANSPORTE'].sum():,.2f}")
        m3.metric("Gran Total", f"$ {resultado['TOTAL A PAGAR'].sum():,.2f}")

        # Crear dos tablas: Una por GP y otra por TIPO
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.markdown("### Por Gerente (GP)")
            res_gp = resultado.groupby('GP')['TOTAL A PAGAR'].sum().reset_index()
            st.table(res_gp.style.format({'TOTAL A PAGAR': '$ {:,.2f}'}))

        with col_b:
            st.markdown("### Por Tipo (MM / MP)")
            # Agrupamos por la nueva columna TIPO
            res_tipo = resultado.groupby('TIPO')['TOTAL A PAGAR'].sum().reset_index()
            st.table(res_tipo.style.format({'TOTAL A PAGAR': '$ {:,.2f}'}))

        # --- DETALLE COMPLETO ---
        st.subheader("📝 Detalle de Transacciones")
        st.dataframe(resultado)

        # 4. EXCEL CON MÚLTIPLES HOJAS
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            resultado.to_excel(writer, index=False, sheet_name='Detalle_Completo')
            res_gp.to_excel(writer, index=False, sheet_name='Resumen_GP')
            res_tipo.to_excel(writer, index=False, sheet_name='Resumen_Tipo')
        
        st.download_button("📥 Descargar Reporte con MM/MP", output.getvalue(), "Reporte_Logistico_Categorizado.xlsx")

    except Exception as e:
        st.error(f"Error: {e}")
