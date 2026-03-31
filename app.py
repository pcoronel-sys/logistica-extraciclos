import streamlit as st
import pandas as pd
from io import BytesIO

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Logística Bagó Pro", layout="wide", page_icon="🧪")

# --- ESTILO MINIMALISTA BLANCO Y MAGENTA ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    div[data-testid="stMetric"] {
        background: #fdfdfd;
        border-radius: 10px;
        border: 1px solid #eeeeee;
        border-top: 4px solid #E10078;
        padding: 15px !important;
    }
    .stButton>button {
        background-color: #E10078;
        color: white;
        border-radius: 8px;
        font-weight: 600;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

st.image("https://www.bago.com.ec/wp-content/uploads/2021/05/logo-bago.png", width=150)
st.title("📊 Control de Liquidación Logística")

archivo = st.file_uploader("📂 Cargar archivo Excel", type=['xlsx'])

if archivo:
    try:
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
        
        res = pd.merge(df_carga, df_gp[[col_ref_gp, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_ref_gp, how='left')
        
        df_costos = df_costos.rename(columns={'PRECIO_PREP': 'PREPARACION', 'PRECIO_TRANS': 'TRANSPORTE'})
        res['DESCRIPCIÓN ZONA'] = clean_txt(res['DESCRIPCIÓN ZONA'])
        df_costos['DESCRIPCIÓN ZONA'] = clean_txt(df_costos['DESCRIPCIÓN ZONA'])
        res = pd.merge(res, df_costos[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')

        res['BULTOS'] = clean_num(res['BULTOS'])
        res['LOG_TOT'] = (clean_num(res['PREPARACION']) + clean_num(res['TRANSPORTE'])) * res['BULTOS']

        # --- FILTROS ---
        st.sidebar.header("⚙️ Filtros")
        lista_gp = ["TODOS"] + sorted(res['GP'].dropna().unique().tolist())
        gp_sel = st.sidebar.selectbox("Seleccionar Gerente (GP)", lista_gp)

        res_filtered = res if gp_sel == "TODOS" else res[res['GP'] == gp_sel]

        # --- CÁLCULOS ---
        sum_tipo = res_filtered.groupby('TIPO')['LOG_TOT'].sum()
        mm_val = sum_tipo.get('MM', 0)
        mp_val = sum_tipo.get('MP', 0)
        subtotal = mm_val + mp_val
        iva = subtotal * 0.15
        total = subtotal + iva

        # --- VISUALIZACIÓN ---
        st.markdown('---')
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("LOGÍSTICA MM", f"$ {mm_val:,.2f}")
        c2.metric("LOGÍSTICA MP", f"$ {mp_val:,.2f}")
        c3.metric("IVA (15%)", f"$ {iva:,.2f}")
        c4.metric("TOTAL GP", f"$ {total:,.2f}")

        col_inf, col_tab = st.columns([1, 2])
        with col_inf:
            st.markdown("### 📊 Distribución de Gasto")
            porcentaje_mm = (mm_val / subtotal) if subtotal > 0 else 0
            st.write(f"MM: {porcentaje_mm:.1%}")
            st.progress(porcentaje_mm)
            st.write(f"MP: {1-porcentaje_mm:.1%}")
            st.progress(1-porcentaje_mm)

        with col_tab:
            st.markdown(f"### 📋 Liquidación: {gp_sel}")
            resumen_gp = res_filtered.groupby(['GP', 'TIPO'])['LOG_TOT'].sum().unstack(fill_value=0).reset_index()
            resumen_gp['SUBTOTAL'] = resumen_gp.get('MM', 0) + resumen_gp.get('MP', 0)
            resumen_gp['IVA 15%'] = resumen_gp['SUBTOTAL'] * 0.15
            resumen_gp['TOTAL'] = resumen_gp['SUBTOTAL'] + resumen_gp['IVA 15%']
            st.dataframe(resumen_gp.style.format(precision=2), use_container_width=True)

        # --- DESCARGA ---
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            resumen_gp.to_excel(writer, index=False, sheet_name='Liquidacion')
            res.to_excel(writer, index=False, sheet_name='Detalle')
        st.download_button("📥 DESCARGAR EXCEL", data=output.getvalue(), file_name="Liquidacion_Bago.xlsx", use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
