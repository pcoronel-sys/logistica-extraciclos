import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Liquidación Final Logística", layout="wide")

st.title("📑 Reporte de Liquidación Logística (IVA 15%)")
st.markdown("Estructura consolidada por **GP** y **Categoría (MM/MP)**")

archivo_subido = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if archivo_subido:
    try:
        # 1. CARGA Y LIMPIEZA
        xls = pd.ExcelFile(archivo_subido)
        df_carga = pd.read_excel(xls, 'Carga')
        df_gp = pd.read_excel(xls, 'Maestro_GP')
        df_costos = pd.read_excel(xls, 'Maestro_Costos')

        for df in [df_carga, df_gp, df_costos]:
            df.columns = df.columns.str.strip().str.upper()

        # Limpieza de códigos
        def clean_c(s): return pd.to_numeric(s, errors='coerce').fillna(0).astype(int).astype(str)
        df_carga['CODIGO'] = clean_c(df_carga['CODIGO'])
        col_c_gp = [c for c in df_gp.columns if 'CODIGO' in c][0]
        df_gp[col_c_gp] = clean_c(df_gp[col_cod_gp]) if 'col_cod_gp' in locals() else clean_c(df_gp[col_c_gp])

        # 2. CRUCES
        df_gp = df_gp.drop_duplicates(subset=[col_c_gp])
        df_costos = df_costos.drop_duplicates(subset=['DESCRIPCIÓN ZONA'])
        df_costos = df_costos.rename(columns={'PRECIO_PREP': 'PREPARACION', 'PRECIO_TRANS': 'TRANSPORTE'})

        res = pd.merge(df_carga, df_gp[[col_c_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_c_gp, how='left')
        res = pd.merge(res, df_costos[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')

        # 3. CÁLCULOS
        for c in ['BULTOS', 'PREPARACION', 'TRANSPORTE']:
            res[c] = pd.to_numeric(res[c], errors='coerce').fillna(0)

        res['TOT_PREP'] = res['PREPARACION'] * res['BULTOS']
        res['TOT_TRANS'] = res['TRANSPORTE'] * res['BULTOS']
        res['SUBTOTAL'] = res['TOT_PREP'] + res['TOT_TRANS']

        # --- 4. CONSTRUCCIÓN DEL CUADRO FINAL (Como la imagen) ---
        # Agrupamos por GP y TIPO
        cuadro = res.groupby(['GP', 'TIPO']).agg({
            'TOT_PREP': 'sum',
            'TOT_TRANS': 'sum',
            'SUBTOTAL': 'sum'
        }).reset_index()

        # Renombrar columnas para el reporte
        cuadro.columns = ['GERENTE (GP)', 'TIPO', 'PREPARACIÓN', 'TRANSPORTE', 'SUBTOTAL']
        
        # Calcular IVA y TOTAL
        cuadro['IVA 15%'] = cuadro['SUBTOTAL'] * 0.15
        cuadro['TOTAL CON IVA'] = cuadro['SUBTOTAL'] + cuadro['IVA 15%']

        # Mostrar en pantalla
        st.subheader("💰 Resumen de Liquidación")
        st.table(cuadro.style.format({
            'PREPARACIÓN': '$ {:,.2f}',
            'TRANSPORTE': '$ {:,.2f}',
            'SUBTOTAL': '$ {:,.2f}',
            'IVA 15%': '$ {:,.2f}',
            'TOTAL CON IVA': '$ {:,.2f}'
        }))

        # Mostrar Gran Total General
        gran_total = cuadro['TOTAL CON IVA'].sum()
        st.metric("VALOR TOTAL A FACTURAR (CON IVA)", f"$ {gran_total:,.2f}")

        # 5. EXCEL
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            cuadro.to_excel(writer, index=False, sheet_name='Liquidacion')
            res.to_excel(writer, index=False, sheet_name='Detalle_Items')
        
        st.download_button("📥 Descargar Reporte Final", output.getvalue(), "Liquidacion_Final.xlsx")

    except Exception as e:
        st.error(f"Error: {e}")
