import streamlit as st
import pandas as pd
from io import BytesIO
import os
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Logística Bagó - Base de Datos Pro", layout="wide", page_icon="🧪")

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
        # Asegurar que todos los datos se traten igual al concatenar
        nuevo_historico = pd.concat([historico_existente, df_detalle], ignore_index=True)
    else:
        nuevo_historico = df_detalle
    
    nuevo_historico.to_csv(HISTORICO_FILE, index=False)
    st.success(f"✅ ¡Base de datos de {mes} almacenada correctamente!")

# --- NAVEGACIÓN ---
st.title("📊 Control y Almacenamiento Logístico")
menu = st.tabs(["🚀 Procesar Carga", "🗄️ Base de Datos Histórica"])

with menu[0]:
    col_mes, col_file = st.columns([1, 3])
    with col_mes:
        mes_sel = st.selectbox("Mes Correspondiente", 
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

            # --- LIMPIEZA Y NORMALIZACIÓN CRÍTICA ---
            for df in [df_carga, df_gp, df_costos]:
                df.columns = df.columns.str.strip().str.upper()

            def clean_str(s): return s.astype(str).str.strip().str.upper()

            # Normalizar códigos (Importante para evitar fallos de cruce)
            df_carga['CODIGO'] = clean_str(df_carga['CODIGO']).str.replace(r'\.0$', '', regex=True)
            col_id = [c for c in df_gp.columns if 'CODIGO' in c][0]
            df_gp[col_id] = clean_str(df_gp[col_id]).str.replace(r'\.0$', '', regex=True)
            
            # Eliminar duplicados en los maestros (Esto evita que los valores se multipliquen por error)
            df_gp = df_gp.drop_duplicates(subset=[col_id])
            
            df_carga['DESCRIPCIÓN ZONA'] = clean_str(df_carga['DESCRIPCIÓN ZONA'])
            df_costos['DESCRIPCIÓN ZONA'] = clean_str(df_costos['DESCRIPCIÓN ZONA'])
            df_costos = df_costos.drop_duplicates(subset=['DESCRIPCIÓN ZONA'])

            # --- PROCESAMIENTO MATEMÁTICO ---
            # 1. Cruzar con GP
            res = pd.merge(df_carga, df_gp[[col_id, 'GP', 'TIPO']], left_on='CODIGO', right_on=col_id, how='left')
            
            # 2. Cruzar con Costos
            df_costos = df_costos.rename(columns={'PRECIO_PREP': 'PREPARACION', 'PRECIO_TRANS': 'TRANSPORTE'})
            res = pd.merge(res, df_costos[['DESCRIPCIÓN ZONA', 'PREPARACION', 'TRANSPORTE']], on='DESCRIPCIÓN ZONA', how='left')
            
            # 3. Cálculo Fila por Fila (Garantiza precisión)
            res['BULTOS'] = pd.to_numeric(res['BULTOS'], errors='coerce').fillna(0)
            res['PREPARACION'] = pd.to_numeric(res['PREPARACION'], errors='coerce').fillna(0)
            res['TRANSPORTE'] = pd.to_numeric(res['TRANSPORTE'], errors='coerce').fillna(0)
            
            # TOTAL LÍNEA = (PREP + TRANS) * BULTOS
            res['LOG_TOT'] = (res['PREPARACION'] + res['TRANSPORTE']) * res['BULTOS']

            # --- RESUMEN VISUAL ---
            st.subheader(f"📊 Resumen de Liquidación - {mes_sel}")
            summary = res.groupby(['GP', 'TIPO'])['LOG_TOT'].sum().unstack(fill_value=0).reset_index()
            
            # Asegurar columnas MM y MP
            for c in ['MM', 'MP']: 
                if c not in summary.columns: summary[c] = 0.0
            
            summary['SUBTOTAL'] = summary['MM'] + summary['MP']
            summary['IVA 15%'] = summary['SUBTOTAL'] * 0.15
            summary['TOTAL'] = summary['SUBTOTAL'] + summary['IVA 15%']

            st.dataframe(summary.style.format(precision=2), use_container_width=True)

            # --- BOTÓN DE ALMACENAMIENTO (GUARDA TODA LA BASE) ---
            st.markdown("---")
            if st.button(f"💾 GUARDAR BASE DE DATOS COMPLETA DE {mes_sel.upper()}"):
                guardar_base_completa(res, mes_sel)

        except Exception as e:
            st.error(f"Error técnico: {e}")

with menu[1]:
    st.subheader("🗄️ Historial de Bases Almacenadas")
    if os.path.exists(HISTORICO_FILE):
        base_h = pd.read_csv(HISTORICO_FILE)
        
        meses_h = ["TODOS"] + sorted(base_h['MES_REPORTE'].unique().tolist())
        mes_f = st.selectbox("Filtrar Historial por Mes", meses_h)
        
        df_ver = base_h if mes_f == "TODOS" else base_h[base_h['MES_REPORTE'] == mes_f]
        
        st.info(f"Registros encontrados: {len(df_ver)}")
        st.dataframe(df_ver, use_container_width=True)
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            csv = df_ver.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar Base (CSV)", csv, "base_bago_completa.csv", "text/csv")
        with col_d2:
            if st.button("🗑️ Borrar Historial"):
                os.remove(HISTORICO_FILE)
                st.rerun()
    else:
        st.info("Aún no hay datos en la base histórica.")
