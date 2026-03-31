import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Liquidación Logística GP", layout="wide")

st.title("📊 Reporte de Liquidación Logística (IVA 15%)")
st.markdown("Resumen detallado por **Gerente (GP)** y subtotalizado por **Tipo (MM/MP)**")

archivo_subido = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if archivo_subido:
    try:
        # 1. CARGA DE DATOS
        xls = pd.ExcelFile(archivo_subido)
        df_carga = pd.read_excel(xls, 'Carga')
        df_gp = pd.read_excel(xls, 'Maestro_GP')
        df_costos = pd.read_excel(xls, 'Maestro_Costos')

        # Limpiar nombres de columnas
        for df in [df_carga, df_gp, df_costos]:
            df.columns = df.columns.str.strip().str.upper()

        # Limpieza de códigos para evitar el ".0"
        def clean_code(s): return pd.to_numeric(s, errors='coerce').fillna(0).astype(int).astype(str)
        df_carga['CODIGO'] = clean_code(df_carga['CODIGO'])
        col_cod_gp = [c for c in df_gp.columns if 'CODIGO' in c][0]
        df_gp[col_cod_gp] = clean_code(df_gp[col_cod_gp])

        # 2. CRUCES DE INFORMACIÓN
        df_gp = df_gp.drop_duplicates(subset=[col_cod_gp])
        df_costos = df_costos.drop_duplicates(subset=['DESCRIPCIÓN ZONA'])

        # Unir Carga con Maestro_GP para obtener GP y TIPO
        resultado = pd.merge(df_carga, df_gp[[col_cod_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_cod_gp, how='left')
        
        # Unir con Maestro_Costos (Soporta PRECIO_PREP o PREPARACION)
        df_costos = df_costos.rename(columns={'PRECIO_PREP': 'PREPARACION', 'PRECIO_TRANS': 'TRANSPORTE'})
        df_carga['DESCRIPCIÓN ZONA'] = df_carga['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
        df_costos['DESCRIPCIÓN ZONA'] = df_costos['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
        
        resultado = pd.merge(resultado, df_costos[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')

        # 3. CÁLCULOS BASE
        resultado['BULTOS'] = pd.to_numeric(resultado['BULTOS'], errors='coerce').fillna(0)
        resultado['PREPARACION'] = pd.to_numeric(resultado['PREPARACION'], errors='coerce').fillna(0)
        resultado['TRANSPORTE'] = pd.to_numeric(resultado['TRANSPORTE'], errors='coerce').fillna(0)

        resultado['TOTAL PREPARACION'] = resultado['PREPARACION'] * resultado['BULTOS']
        resultado['TOTAL TRANSPORTE'] = resultado['TRANSPORTE'] * resultado['BULTOS']
        resultado['SUBTOTAL'] = resultado['TOTAL PREPARACION'] + resultado['TOTAL TRANSPORTE']

        # --- 4. CUADRO RESUMEN SOLICITADO ---
        # Agrupamos por GP y luego por TIPO
        resumen = resultado.groupby(['GP', 'TIPO']).agg({
            'TOTAL PREPARACION': 'sum',
            'TOTAL TRANSPORTE': 'sum',
            'SUBTOTAL': 'sum'
        }).reset_index()

        # Cálculo de IVA y Total Final
        resumen['IVA 15%'] = resumen['SUBTOTAL'] * 0.15
        resumen['TOTAL CON IVA'] = resumen['SUBTOTAL'] + resumen['IVA 15%']

        # Ordenar para que se vea agrupado por GP
        resumen = resumen.sort_values(by=['GP', 'TIPO'])

        st.subheader("📋 Cuadro Consolidado por GP y Tipo")
        
        # Formatear la tabla para mostrar en Streamlit
        st.table(resumen.style.format({
            'TOTAL PREPARACION': '$ {:,.2f}',
            'TOTAL TRANSPORTE': '$ {:,.2f}',
            'SUBTOTAL': '$ {:,.2f}',
            'IVA 15%': '$ {:,.2f}',
            'TOTAL CON IVA': '$ {:,.2f}'
        }))

        # Totales Generales (Resumen visual rápido)
        c1, c2, c3 = st.columns(3)
        c1.metric("Subtotal General", f"$ {resumen['SUBTOTAL'].sum():,.2f}")
        c2.metric("Total IVA (15%)", f"$ {resumen['IVA 15%'].sum():,.2f}")
        c3.metric("TOTAL A FACTURAR", f"$ {resumen['TOTAL CON IVA'].sum():,.2f}")

        # 5. DESCARGA
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            resumen.to_excel(writer, index=False, sheet_name='Resumen_Liquidacion')
            resultado.to_excel(writer, index=False, sheet_name='Detalle_Items')
        
        st.download_button("📥 Descargar Reporte Final", output.getvalue(), "Liquidacion_Logistica.xlsx")

    except Exception as e:
        st.error(f"Error en el proceso: {e}")
