import streamlit as st
import pandas as pd
from io import BytesIO
import os
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Logística Bagó - Histórico", layout="wide", page_icon="🧪")

# --- ESTILO CORPORATIVO ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    div[data-testid="stMetric"] {
        background: #ffffff;
        border-radius: 12px;
        border-top: 5px solid #E10078;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    .stButton>button {
        background: linear-gradient(90deg, #E10078 0%, #8E004C 100%);
        color: white; border-radius: 10px; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIÓN PARA EL HISTÓRICO ---
HISTORICO_FILE = "historico_liquidaciones.csv"

def guardar_en_historico(df, mes):
    df['MES_REPORTE'] = mes
    df['FECHA_REGISTRO'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if os.path.exists(HISTORICO_FILE):
        historico_existente = pd.read_csv(HISTORICO_FILE)
        # Evitar duplicar el mismo mes si ya se guardó (opcional)
        nuevo_historico = pd.concat([historico_existente, df], ignore_index=True)
    else:
        nuevo_historico = df
    
    nuevo_historico.to_csv(HISTORICO_FILE, index=False)
    st.success(f"✅ Datos de {mes} guardados en el histórico.")

# --- NAVEGACIÓN ---
st.title("📊 Gestión Logística Bagó")
menu = st.tabs(["🚀 Procesar Mes Actual", "📂 Ventana de Histórico"])

with menu[0]:
    st.subheader("Carga de Datos Mensuales")
    
    col_mes, col_file = st.columns([1, 3])
    with col_mes:
        mes_seleccionado = st.selectbox("Selecciona el Mes", 
            ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
    
    with col_file:
        archivo = st.file_uploader("Subir Excel Extra-Ciclos", type=['xlsx'])

    if archivo:
        try:
            xls = pd.ExcelFile(archivo)
            df_carga = pd.read_excel(xls, 'Carga')
            df_gp = pd.read_excel(xls, 'Maestro_GP')
            df_costos = pd.read_excel(xls, 'Maestro_Costos')

            # --- LIMPIEZA ---
            def clean_df(df):
                df.columns = df.columns.str.strip().str.upper()
                return df.apply(lambda x: x.astype(str).str.strip().str.upper() if x.name not in ['BULTOS', 'PREPARACION', 'TRANSPORTE'] else x)

            df_carga = clean_df(df_carga)
            df_gp = clean_df(df_gp)
            df_costos = clean_df(df_costos)

            # Cruces y Cálculos
            df_carga['CODIGO'] = df_carga['CODIGO'].str.replace(r'\.0$', '', regex=True)
            col_id = [c for c in df_gp.columns if 'CODIGO' in c][0]
            df_gp[col_id] = df_gp[col_id].str.replace(r'\.0$', '', regex=True)
            
            res = pd.merge(df_carga, df_gp[[col_id, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_id, how='left')
            df_costos = df_costos.rename(columns={'PRECIO_PREP': 'PREPARACION', 'PRECIO_TRANS': 'TRANSPORTE'})
            res = pd.merge(res, df_costos[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')
            
            res['BULTOS'] = pd.to_numeric(res['BULTOS'], errors='coerce').fillna(0)
            res['LOG_TOT'] = (pd.to_numeric(res['PREPARACION'], errors='coerce').fillna(0) + 
                              pd.to_numeric(res['TRANSPORTE'], errors='coerce').fillna(0)) * res['BULTOS']

            # Resumen para el cuadro
            summary = res.groupby(['GP', 'TIPO'])['LOG_TOT'].sum().unstack(fill_value=0).reset_index()
            for c in ['MM', 'MP']: 
                if c not in summary.columns: summary[c] = 0.0
            summary['SUBTOTAL'] = summary['MM'] + summary['MP']
            summary['IVA 15%'] = summary['SUBTOTAL'] * 0.15
            summary['TOTAL'] = summary['SUBTOTAL'] + summary['IVA 15%']

            st.markdown("### Resultados del Mes")
            st.dataframe(summary.style.format(precision=2), use_container_width=True)

            # --- BOTÓN PARA ALMACENAR ---
            if st.button(f"💾 ALMACENAR DATOS DE {mes_seleccionado.upper()} EN HISTÓRICO"):
                guardar_en_historico(summary, mes_seleccionado)

        except Exception as e:
            st.error(f"Error: {e}")

with menu[1]:
    st.subheader("📚 Almacén Histórico de Liquidaciones")
    
    if os.path.exists(HISTORICO_FILE):
        df_hist = pd.read_csv(HISTORICO_FILE)
        
        # Filtros del histórico
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            meses_disp = ["TODOS"] + df_hist['MES_REPORTE'].unique().tolist()
            f_mes = st.selectbox("Filtrar Historial por Mes", meses_disp)
        
        df_mostrar = df_hist if f_mes == "TODOS" else df_hist[df_hist['MES_REPORTE'] == f_mes]
        
        st.dataframe(df_mostrar, use_container_width=True)
        
        # Botón para descargar TODO el histórico
        csv_nacional = df_mostrar.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Consolidado Histórico (CSV)", csv_nacional, "historico_total_bago.csv", "text/csv")
        
        if st.button("🗑️ Borrar Historial (Cuidado)"):
            if os.path.exists(HISTORICO_FILE):
                os.remove(HISTORICO_FILE)
                st.warning("Historial eliminado.")
                st.rerun()
    else:
        st.info("Aún no hay datos almacenados. Procesa un mes y dale a 'Almacenar'.")
