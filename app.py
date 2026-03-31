import streamlit as st
import pandas as pd
from io import BytesIO
import os
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Logística Bagó - Control Total", layout="wide", page_icon="🧪")

# --- ESTILO CORPORATIVO MAGENTA ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    div[data-testid="stMetric"] {
        background: #fdfdfd;
        border-radius: 12px;
        border-top: 5px solid #E10078;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    .stButton>button {
        background: linear-gradient(90deg, #E10078 0%, #8E004C 100%);
        color: white; border-radius: 10px; font-weight: bold; width: 100%;
        height: 3em;
    }
    /* Estilo para las tablas */
    .stDataFrame { background-color: white; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

HISTORICO_FILE = "base_historica_bago.csv"

# --- FUNCIÓN PARA GUARDAR BASE COMPLETA ---
def guardar_en_base_datos(df_detalle, mes):
    df_detalle['MES_REPORTE'] = mes
    df_detalle['FECHA_REGISTRO'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if os.path.exists(HISTORICO_FILE):
        historico_old = pd.read_csv(HISTORICO_FILE)
        # Limpiar posibles columnas vacías o errores de carga previa
        nuevo_hist = pd.concat([historico_old, df_detalle], ignore_index=True)
    else:
        nuevo_hist = df_detalle
    
    nuevo_hist.to_csv(HISTORICO_FILE, index=False)
    st.success(f"✅ La base detallada de {mes} ha sido almacenada correctamente.")

# --- NAVEGACIÓN ---
st.title("📊 Control de Liquidación y Base Histórica")
pestanas = st.tabs(["🚀 Procesar Nueva Carga", "🗄️ Base de Datos Acumulada"])

with pestanas[0]:
    col_izq, col_der = st.columns([1, 3])
    with col_izq:
        mes_actual = st.selectbox("Mes a Procesar", 
            ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
    with col_der:
        archivo = st.file_uploader("Subir archivo Excel", type=['xlsx'])

    if archivo:
        try:
            # CARGA DE HOJAS
            xls = pd.ExcelFile(archivo)
            df_carga = pd.read_excel(xls, 'Carga')
            df_gp = pd.read_excel(xls, 'Maestro_GP')
            df_costos = pd.read_excel(xls, 'Maestro_Costos')

            # NORMALIZACIÓN (Mayúsculas y sin espacios)
            def normalizar(df):
                df.columns = df.columns.str.strip().str.upper()
                return df.apply(lambda x: x.astype(str).str.strip().str.upper() if x.name not in ['BULTOS', 'PREPARACION', 'TRANSPORTE', 'PRECIO_PREP', 'PRECIO_TRANS'] else x)

            df_carga = normalizar(df_carga)
            df_gp = normalizar(df_gp)
            df_costos = normalizar(df_costos)

            # LIMPIEZA DE CÓDIGOS Y DUPLICADOS EN MAESTROS
            df_carga['CODIGO'] = df_carga['CODIGO'].str.replace(r'\.0$', '', regex=True)
            col_id = [c for c in df_gp.columns if 'CODIGO' in c][0]
            df_gp[col_id] = df_gp[col_id].str.replace(r'\.0$', '', regex=True)
            
            # ELIMINAR DUPLICADOS EN MAESTROS (Evita multiplicar valores por error)
            df_gp = df_gp.drop_duplicates(subset=[col_id])
            df_costos = df_costos.drop_duplicates(subset=['DESCRIPCIÓN ZONA'])

            # CRUCES (JOIN)
            res = pd.merge(df_carga, df_gp[[col_id, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_id, how='left')
            
            # Renombrar costos si vienen con el nombre antiguo
            df_costos = df_costos.rename(columns={'PRECIO_PREP': 'PREPARACION', 'PRECIO_TRANS': 'TRANSPORTE'})
            res = pd.merge(res, df_costos[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')

            # CÁLCULO FILA POR FILA (Precisión Matemática)
            res['BULTOS'] = pd.to_numeric(res['BULTOS'], errors='coerce').fillna(0)
            res['PREPARACION'] = pd.to_numeric(res['PREPARACION'], errors='coerce').fillna(0)
            res['TRANSPORTE'] = pd.to_numeric(res['TRANSPORTE'], errors='coerce').fillna(0)
            
            # (Precio Prep + Precio Trans) * Cantidad Bultos
            res['VALOR_LOGISTICA'] = (res['PREPARACION'] + res['TRANSPORTE']) * res['BULTOS']

            # --- VISTA DE RESULTADOS ---
            st.subheader(f"📋 Resumen de Liquidación: {mes_actual}")
            
            # Agrupar para el resumen visual
            summary = res.groupby(['GP', 'TIPO'])['VALOR_LOGISTICA'].sum().unstack(fill_value=0).reset_index()
            for c in ['MM', 'MP']: 
                if c not in summary.columns: summary[c] = 0.0
            
            summary['SUBTOTAL'] = summary['MM'] + summary['MP']
            summary['IVA 15%'] = summary['SUBTOTAL'] * 0.15
            summary['TOTAL FINAL'] = summary['SUBTOTAL'] + summary['IVA 15%']

            # AÑADIR FILA DE TOTALES AL RESUMEN (Sin dañar la base)
            totales = {'GP': '--- TOTALES GENERALES ---'}
            for col in summary.columns[1:]: totales[col] = summary[col].sum()
            summary_con_totales = pd.concat([summary, pd.DataFrame([totales])], ignore_index=True)

            st.dataframe(summary_con_totales.style.format(precision=2), use_container_width=True)

            # BOTÓN PARA GUARDAR LA BASE COMPLETA
            st.markdown("---")
            if st.button(f"💾 ALMACENAR BASE DETALLADA DE {mes_actual.upper()}"):
                guardar_en_base_datos(res, mes_actual)

        except Exception as e:
            st.error(f"Se detectó un error en el archivo: {e}")

with pestanas[1]:
    st.subheader("🗄️ Historial Acumulado (Base de Datos)")
    if os.path.exists(HISTORICO_FILE):
        base_completa = pd.read_csv(HISTORICO_FILE)
        
        # Filtro de Mes
        meses_h = ["TODOS"] + sorted(base_completa['MES_REPORTE'].unique().tolist())
        filtro_mes = st.selectbox("Ver Mes Específico", meses_h)
        
        df_final_ver = base_completa if filtro_mes == "TODOS" else base_completa[base_completa['MES_REPORTE'] == filtro_mes]
        
        st.write(f"Registros en la base: {len(df_final_ver)}")
        st.dataframe(df_final_ver, use_container_width=True)
        
        # Descarga de la base completa en CSV
        csv_data = df_final_ver.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Base de Datos Completa", csv_data, "base_historica_logistica.csv", "text/csv")
        
        if st.sidebar.button("⚠️ Borrar TODA la Base"):
            os.remove(HISTORICO_FILE)
            st.rerun()
    else:
        st.info("La base de datos está vacía. Procesa un mes y utiliza el botón 'Almacenar'.")
