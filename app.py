import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Reporte Logístico con IVA", layout="wide")

st.title("📊 Resumen Consolidado de Logística (IVA 15%)")

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

        # 2. CRUCES
        df_gp = df_gp.drop_duplicates(subset=[col_cod_gp])
        df_costos = df_costos.drop_duplicates(subset=['DESCRIPCIÓN ZONA'])

        resultado = pd.merge(df_carga, df_gp[[col_cod_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_cod_gp, how='left')
        
        df_carga['DESCRIPCIÓN ZONA'] = df_carga['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
        df_costos['DESCRIPCIÓN ZONA'] = df_costos['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
        resultado = pd.merge(resultado, df_costos[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')

        # 3. CÁLCULOS
        for c in ['BULTOS', 'PREPARACION', 'TRANSPORTE']:
            resultado[c] = pd.to_numeric(resultado[c], errors='coerce').fillna(0)

        resultado['TOTAL PREPARACION'] = resultado['PREPARACION'] * resultado['BULTOS']
        resultado['TOTAL TRANSPORTE'] = resultado['TRANSPORTE'] * resultado['BULTOS']
        resultado['SUBTOTAL'] = resultado['TOTAL PREPARACION'] + resultado['TOTAL TRANSPORTE']

        # --- SECCIÓN DE RESUMEN ÚNICO (Como la imagen) ---
        st.subheader("📝 Cuadro Resumen Consolidado")
        
        # Agrupar por GP y TIPO
        resumen = resultado.groupby(['GP', 'TIPO']).agg({
            'TOTAL PREPARACION': 'sum',
            'TOTAL TRANSPORTE': 'sum',
            'SUBTOTAL': 'sum'
        }).reset_index()

        # Calcular IVA 15% y Total con IVA
        resumen['IVA 15%'] = resumen['SUBTOTAL'] * 0.15
        resumen['TOTAL CON IVA'] = resumen['SUBTOTAL'] + resumen['IVA 15%']

        # Añadir fila de TOTALES GENERALES al final del cuadro
        totales_gen = pd.DataFrame([{
            'GP': 'TOTALES GENERALES',
            'TIPO': '---',
            'TOTAL PREPARACION': resumen['TOTAL PREPARACION'].sum(),
            'TOTAL TRANSPORTE': resumen['TOTAL TRANSPORTE'].sum(),
            'SUBTOTAL': resumen['SUBTOTAL'].sum(),
            'IVA 15%': resumen['IVA 15%'].sum(),
            'TOTAL CON IVA': resumen['TOTAL CON IVA'].sum()
        }])
        
        resumen_final = pd.concat([resumen, totales_gen], ignore_index=True)

        # Mostrar tabla con formato de moneda
        st.table(resumen_final.style.format({
            'TOTAL PREPARACION': '$ {:,.2f}',
            'TOTAL TRANSPORTE': '$ {:,.2f}',
            'SUBTOTAL': '$ {:,.2f}',
            'IVA 15%': '$ {:,.2f}',
            'TOTAL CON IVA': '$ {:,.2f}'
        }))

        # --- DETALLE COMPLETO ABAJO ---
        with st.expander("Ver detalle completo por ítem"):
            st.dataframe(resultado)

        # 4. DESCARGA EXCEL
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            resumen_final.to_excel(writer, index=False, sheet_name='Resumen_Consolidado')
            resultado.to_excel(writer, index=False, sheet_name='Detalle_Completo')
        
        st.download_button("📥 Descargar Reporte Final (IVA 15%)", output.getvalue(), "Reporte_Logistico_IVA.xlsx")

    except Exception as e:
        st.error(f"Error: {e}")
