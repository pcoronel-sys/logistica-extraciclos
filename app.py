import streamlit as st
import pandas as pd
from io import BytesIO

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Logística Bagó Extra-Ciclos", layout="wide", page_icon="📦")

# CSS para Estilo Bagó (Azul y Blanco)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-top: 4px solid #004a99;
    }
    .bienvenida {
        text-align: center;
        padding: 40px;
        background-color: #004a99;
        color: white;
        border-radius: 15px;
        margin-bottom: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- PANTALLA DE INICIO (ESTADO SIN ARCHIVO) ---
if 'archivo_subido' not in st.session_state:
    st.markdown("""
        <div class="bienvenida">
            <h1>🚀 Sistema de Liquidación Logística</h1>
            <p>Bienvenido al procesador de extra-ciclos. Optimiza tus reportes de MM y MP en segundos.</p>
        </div>
        """, unsafe_allow_html=True)
    
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.subheader("1. Carga")
        st.write("Sube el archivo Excel con las pestañas: *Carga*, *Maestro_GP* y *Maestro_Costos*.")
    with col_info2:
        st.subheader("2. Procesa")
        st.write("El sistema limpia códigos, cruza zonas y calcula el IVA del 15% automáticamente.")
    with col_info3:
        st.subheader("3. Descarga")
        st.write("Obtén tu reporte consolidado horizontal listo para contabilidad.")

st.markdown("---")
archivo = st.file_uploader("📂 Selecciona el archivo Excel de Extra-Ciclos", type=['xlsx'])

if archivo:
    st.session_state['archivo_subido'] = True
    try:
        # --- PROCESAMIENTO ---
        xls = pd.ExcelFile(archivo)
        df_carga = pd.read_excel(xls, 'Carga')
        df_gp = pd.read_excel(xls, 'Maestro_GP')
        df_costos = pd.read_excel(xls, 'Maestro_Costos')

        for df in [df_carga, df_gp, df_costos]:
            df.columns = df.columns.str.strip().str.upper()

        def clean_txt(s): return s.astype(str).str.strip().str.upper()
        def clean_num(s): return pd.to_numeric(s, errors='coerce').fillna(0)

        df_carga['CODIGO'] = clean_txt(df_carga['CODIGO']).str.replace('.0', '', regex=False)
        col_ref_gp = [c for c in df_gp.columns if 'CODIGO' in c][0]
        df_gp[col_ref_gp] = clean_txt(df_gp[col_ref_gp]).str.replace('.0', '', regex=False)
        df_carga['DESCRIPCIÓN ZONA'] = clean_txt(df_carga['DESCRIPCIÓN ZONA'])
        df_costos['DESCRIPCIÓN ZONA'] = clean_txt(df_costos['DESCRIPCIÓN ZONA'])

        df_gp = df_gp.drop_duplicates(subset=[col_ref_gp])
        df_costos = df_costos.drop_duplicates(subset=['DESCRIPCIÓN ZONA'])
        df_costos = df_costos.rename(columns={'PRECIO_PREP': 'PREPARACION', 'PRECIO_TRANS': 'TRANSPORTE'})

        res = pd.merge(df_carga, df_gp[[col_ref_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_ref_gp, how='left')
        res = pd.merge(res, df_costos[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')

        res['BULTOS'] = clean_num(res['BULTOS'])
        res['PREPARACION'] = clean_num(res['PREPARACION'])
        res['TRANSPORTE'] = clean_num(res['TRANSPORTE'])
        res['LOG_TOT'] = (res['PREPARACION'] + res['TRANSPORTE']) * res['BULTOS']

        # --- CONSOLIDACIÓN ---
        grouped = res.groupby(['GP', 'TIPO'])['LOG_TOT'].sum().reset_index()
        pivot = grouped.pivot(index='GP', columns='TIPO', values='LOG_TOT').fillna(0).reset_index()

        df_final = pd.DataFrame()
        df_final['GERENTE (GP)'] = pivot['GP']
        df_final['LOGISTICA MM'] = pivot['MM'] if 'MM' in pivot.columns else 0.0
        df_final['LOGISTICA MP'] = pivot['MP'] if 'MP' in pivot.columns else 0.0
        df_final['SUBTOTAL'] = df_final['LOGISTICA MM'] + df_final['LOGISTICA MP']
        df_final['IVA 15%'] = df_final['SUBTOTAL'] * 0.15
        df_final['TOTAL'] = df_final['SUBTOTAL'] + df_final['IVA 15%']

        # --- PANEL DE RESULTADOS ---
        st.success("✅ Archivo procesado con éxito")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Logística MM", f"$ {df_final['LOGISTICA MM'].sum():,.2f}")
        m2.metric("Logística MP", f"$ {df_final['LOGISTICA MP'].sum():,.2f}")
        m3.metric("IVA 15%", f"$ {df_final['IVA 15%'].sum():,.2f}")
        m4.metric("TOTAL GENERAL", f"$ {df_final['TOTAL'].sum():,.2f}")

        # Uso de Pestañas para organizar la visualización
        tab1, tab2 = st.tabs(["📋 Cuadro de Liquidación", "🔍 Auditoría de Detalles"])

        with tab1:
            tot_row = {'GERENTE (GP)': 'TOTALES GENERALES'}
            for col in df_final.columns[1:]: tot_row[col] = df_final[col].sum()
            df_disp = pd.concat([df_final, pd.DataFrame([tot_row])], ignore_index=True)
            st.dataframe(df_disp.style.format({c: "$ {:,.2f}" for c in df_disp.columns if c != 'GERENTE (GP)'}), use_container_width=True)
            
            # Botón de descarga prominente
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_disp.to_excel(writer, index=False, sheet_name='Liquidacion')
                res.to_excel(writer, index=False, sheet_name='Detalle_Original')
            
            st.download_button(label="📥 Descargar Reporte Final Excel", data=output.getvalue(), 
                               file_name="Liquidacion_Bagó.xlsx", use_container_width=True)

        with tab2:
            st.write("Aquí puedes revisar cada línea del archivo original cruzada con los costos:")
            st.dataframe(res)

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
