import streamlit as st
import pandas as pd
from io import BytesIO
import os
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Logística Bagó - Base de Datos", layout="wide", page_icon="🧪")

# --- ESTILO CORPORATIVO ---
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
    }
    </style>
    """, unsafe_allow_html=True)

HISTORICO_FILE = "base_historica_completa.csv"

# --- FUNCIÓN PARA ALMACENAR BASE COMPLETA ---
def guardar_base_completa(df_detalle, mes):
    df_detalle['MES_REPORTE'] = mes
    df_detalle['FECHA_REGISTRO'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if os.path.exists(HISTORICO_FILE):
        historico_existente = pd.read_csv(HISTORICO_FILE)
        # Convertimos columnas a string para evitar errores de tipo al concatenar
        nuevo_historico = pd.concat([historico_existente, df_detalle], ignore_index=True)
    else:
        nuevo_historico = df_detalle
    
    nuevo_historico.to_csv(HISTORICO_FILE, index=False)
    st.success(f"✅ ¡Base completa de {mes} almacenada con éxito!")

# --- NAVEGACIÓN ---
st.title("📊 Gestión y Almacenamiento Logístico")
menu = st.tabs(["🚀 Procesar y Cargar", "🗄️ Base de Datos Histórica"])

with menu[0]:
    col_mes, col_file = st.columns([1, 3])
    with col_mes:
        mes_sel = st.selectbox("Mes de Carga", 
            ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
    with col_file:
        archivo = st.file_uploader("Subir archivo Excel", type=['xlsx'])

    if archivo:
        try:
            xls = pd.ExcelFile(archivo)
            df_carga = pd.read_excel(xls, 'Carga')
            df_gp = pd.read_excel(xls, 'Maestro_GP')
            df_costos = pd.read_excel(xls, 'Maestro_Costos')

            # --- LIMPIEZA ---
            for df in [df_carga, df_gp, df_costos]:
                df.columns = df.columns.str.strip().str.upper()

            def clean_str(s): return s.astype(str).str.strip().str.upper()

            # Normalizar códigos y zonas para el cruce
            df_carga['CODIGO'] = clean_str(df_carga['CODIGO']).str.replace(r'\.0$', '', regex=True)
            col_id = [c for c in df_gp.columns if 'CODIGO' in c][0]
            df_gp[col_id] = clean_str(df_gp[col_id]).str.replace(r'\.0$', '', regex=True)
            
            df_carga['DESCRIPCIÓN ZONA'] = clean_str(df_carga['DESCRIPCIÓN ZONA'])
            df_costos['DESCRIPCIÓN ZONA'] = clean_str(df_costos['DESCRIPCIÓN ZONA'])

            # --- PROCESAMIENTO (CRUCES LIMPIOS) ---
            # 1. Unir con Maestro_GP
            res = pd.merge(df_carga, df_gp[[col_id, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_id, how='left')
            
            # 2. Unir con Maestro_Costos
            df_costos = df_costos.rename(columns={'PRECIO_PREP': 'PREPARACION', 'PRECIO_TRANS': 'TRANSPORTE'})
            res = pd.merge(res, df_costos[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')
            
            # 3. CÁLCULO FILA POR FILA (Aquí se corrige la multiplicación)
            res['BULTOS'] = pd.to_numeric(res['BULTOS'], errors='coerce').fillna(0)
            res['PREPARACION'] = pd.to_numeric(res['PREPARACION'], errors='coerce').fillna(0)
            res['TRANSPORTE'] = pd.to_numeric(res['TRANSPORTE'], errors='coerce').fillna(0)
            
            res['LOG_TOT'] = (res['PREPARACION'] + res['TRANSPORTE']) * res['BULTOS']

            # --- VISTA PREVIA ---
            st.subheader(f"Vista Previa de Liquidación - {mes_sel}")
            summary = res.groupby(['GP', 'TIPO'])['LOG_TOT'].sum().unstack(fill_value=0).reset_index()
            for c in ['MM', 'MP']: 
                if c not in summary.columns: summary[c] = 0.0
            
            summary['SUBTOTAL'] = summary['MM'] + summary['MP']
            summary['IVA 15%'] = summary['SUBTOTAL'] * 0.15
            summary['TOTAL'] = summary['SUBTOTAL'] + summary['IVA 15%']

            st.dataframe(summary.style.format(precision=2), use_container_width=True)

            # --- BOTÓN PARA GUARDAR TODA LA BASE ---
            if st.button(f"💾 GUARDAR BASE DETALLADA DE {mes_sel.upper()}"):
                guardar_base_completa(res, mes_sel)

        except Exception as e:
            st.error(f"Error en proceso: {e}")

with menu[1]:
    st.subheader("🗄️ Histórico Completo de Movimientos")
    if os.path.exists(HISTORICO_FILE):
        base_h = pd.read_csv(HISTORICO_FILE)
        
        # Filtros para navegar la base
        meses_h = ["TODOS"] + base_h['MES_REPORTE'].unique().tolist()
        mes_f = st.selectbox("Filtrar por Mes", meses_h)
        
        df_ver = base_h if mes_f == "TODOS" else base_h[base_h['MES_REPORTE'] == mes_f]
        
        st.write(f"Mostrando {len(df_ver)} registros:")
        st.dataframe(df_ver, use_container_width=True)
        
        # Descarga de la base completa
        csv = df_ver.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Base de Datos (CSV)", csv, "base_bago_historica.csv", "text/csv")
    else:
        st.info("La base de datos está vacía. Procesa un archivo y guárdalo.")
