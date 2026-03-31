import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Liquidación Logística Horizontal", layout="wide")

st.title("📊 Reporte de Liquidación (Formato de Columnas)")
st.markdown("Consolidado por **GP** con subdivisiones de **MM** y **MP** en columnas.")

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

        # Limpieza de códigos (Quitar .0)
        def clean_c(s): return pd.to_numeric(s, errors='coerce').fillna(0).astype(int).astype(str)
        df_carga['CODIGO'] = clean_c(df_carga['CODIGO'])
        col_c_gp = [c for c in df_gp.columns if 'CODIGO' in c][0]
        df_gp[col_c_gp] = clean_c(df_gp[col_c_gp])

        # 2. PROCESAMIENTO
        df_gp = df_gp.drop_duplicates(subset=[col_c_gp])
        df_costos = df_costos.drop_duplicates(subset=['DESCRIPCIÓN ZONA'])
        df_costos = df_costos.rename(columns={'PRECIO_PREP': 'PREPARACION', 'PRECIO_TRANS': 'TRANSPORTE'})

        res = pd.merge(df_carga, df_gp[[col_c_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_c_gp, how='left')
        res = pd.merge(res, df_costos[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')

        # Cálculos base
        for c in ['BULTOS', 'PREPARACION', 'TRANSPORTE']:
            res[c] = pd.to_numeric(res[c], errors='coerce').fillna(0)

        res['TOT_PREP'] = res['PREPARACION'] * res['BULTOS']
        res['TOT_TRANS'] = res['TRANSPORTE'] * res['BULTOS']

        # --- 3. TRANSFORMACIÓN A COLUMNAS (PIVOT) ---
        # Agrupamos por GP y TIPO
        grouped = res.groupby(['GP', 'TIPO']).agg({
            'TOT_PREP': 'sum',
            'TOT_TRANS': 'sum'
        }).reset_index()

        # Calculamos Subtotal por cada fila antes de pivotear
        grouped['SUBTOTAL'] = grouped['TOT_PREP'] + grouped['TOT_TRANS']

        # Pivoteamos la tabla para que TIPO (MM/MP) se convierta en columnas
        pivot = grouped.pivot(index='GP', columns='TIPO', values=['TOT_PREP', 'TOT_TRANS', 'SUBTOTAL']).fillna(0)
        
        # Aplanamos los nombres de las columnas (ej: TOT_PREP_MM)
        pivot.columns = [f'{col}_{tipo}' for col, tipo in pivot.columns]
        pivot = pivot.reset_index()

        # 4. CÁLCULO DE IVA Y TOTALES POR CATEGORÍA
        # Para MM
        if 'SUBTOTAL_MM' in pivot.columns:
            pivot['IVA 15% MM'] = pivot['SUBTOTAL_MM'] * 0.15
            pivot['TOTAL MM'] = pivot['SUBTOTAL_MM'] + pivot['IVA 15% MM']
        
        # Para MP
        if 'SUBTOTAL_MP' in pivot.columns:
            pivot['IVA 15% MP'] = pivot['SUBTOTAL_MP'] * 0.15
            pivot['TOTAL MP'] = pivot['SUBTOTAL_MP'] + pivot['IVA 15% MP']

        # 5. GRAN TOTAL (Suma de MM y MP)
        pivot['GRAN TOTAL FACTURAR'] = pivot.get('TOTAL MM', 0) + pivot.get('TOTAL MP', 0)

        # Reordenar columnas para que sea legible
        columnas_orden = ['GP']
        for cat in ['MM', 'MP']:
            for concepto in ['TOT_PREP', 'TOT_TRANS', 'SUBTOTAL', 'IVA 15%', 'TOTAL']:
                col_name = f'{concepto}_{cat}' if concepto != 'IVA 15%' else f'IVA 15% {cat}'
                if col_name in pivot.columns:
                    columnas_orden.append(col_name)
        columnas_orden.append('GRAN TOTAL FACTURAR')
        
        df_final = pivot[columnas_orden]

        # 6. MOSTRAR RESULTADOS
        st.subheader("📋 Cuadro Consolidado (MM vs MP en Columnas)")
        st.dataframe(df_final.style.format(precision=2))

        # 7. EXCEL
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Liquidacion_Horizontal')
            res.to_excel(writer, index=False, sheet_name='Detalle_Líneas')
        
        st.download_button("📥 Descargar Reporte en Columnas", output.getvalue(), "Liquidacion_Horizontal.xlsx")

    except Exception as e:
        st.error(f"Error al procesar: {e}")
