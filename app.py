# ---------------------------------------------------------
# PANTALLA 3: SISTEMA REPROGRAMA (ESPEJO VV)
# ---------------------------------------------------------
elif st.session_state['pagina_actual'] == "sistema_reprograma":
    if st.sidebar.button("⬅️ Volver al Menú Principal"):
        st.session_state['pagina_actual'] = "inicio"
        st.rerun()

    m_gp_r = cargar_maestro(PATH_GP_REPRO)
    m_costos_r = cargar_maestro(PATH_COSTOS_REPRO)

    tabs = st.tabs(["🚀 Liquidación VV", "🔍 Detalle VV", "⚙️ Configurar Reprograma", "🗄️ Historial VV"])

    with tabs[0]: # LIQUIDACIÓN VV
        if m_gp_r is None or m_costos_r is None: 
            st.warning("⚠️ Cargue los maestros específicos para Reprograma en la pestaña Configurar.")
        else:
            c1, c2 = st.columns([1, 2])
            with c1: mes_sel = st.selectbox("Mes Reprograma", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], key="mes_repro")
            with c2: archivo = st.file_uploader("Subir Carga Reprograma", type=['xlsx', 'xls', 'csv'], key="file_repro")

            if archivo:
                df_c = leer_archivo(archivo)
                if df_c is not None:
                    df_c.columns = df_c.columns.str.strip().str.upper()
                    df_c['CODIGO'] = df_c['CODIGO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    df_c['DESCRIPCIÓN ZONA'] = df_c['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                    df_c['BULTOS'] = pd.to_numeric(df_c['BULTOS'], errors='coerce').fillna(0)
                    
                    # Limpieza Maestros Reprograma
                    col_id_gp = [c for c in m_gp_r.columns if 'CODIGO' in c.upper()][0]
                    m_gp_clean = m_gp_r.copy()
                    m_gp_clean[col_id_gp] = m_gp_clean[col_id_gp].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    m_gp_clean = m_gp_clean.drop_duplicates(subset=[col_id_gp])
                    
                    m_costos_clean = m_costos_r.copy()
                    m_costos_clean.columns = m_costos_clean.columns.str.strip().str.upper()
                    renames = {c: "P_PREP" for c in m_costos_clean.columns if "PREP" in c}
                    renames.update({c: "P_TRANS" for c in m_costos_clean.columns if "TRANS" in c})
                    renames.update({c: "DESCRIPCIÓN ZONA" for c in m_costos_clean.columns if "ZONA" in c})
                    m_costos_clean = m_costos_clean.rename(columns=renames)
                    m_costos_clean['DESCRIPCIÓN ZONA'] = m_costos_clean['DESCRIPCIÓN ZONA'].astype(str).str.strip().str.upper()
                    m_costos_clean = m_costos_clean.drop_duplicates(subset=['DESCRIPCIÓN ZONA'])
                    
                    # Merge y Cálculos
                    res = pd.merge(df_c, m_gp_clean[[col_id_gp, 'GP']], left_on='CODIGO', right_on=col_id_gp, how='left')
                    res = pd.merge(res, m_costos_clean[['DESCRIPCIÓN ZONA', 'P_PREP', 'P_TRANS']], on='DESCRIPCIÓN ZONA', how='left')

                    if res['GP'].isna().any() or res['P_PREP'].isna().any():
                        st.error("🛑 BLOQUEO REPROGRAMA: Datos faltantes.")
                        st.write("Códigos Faltantes:", res[res['GP'].isna()]['CODIGO'].unique())
                        st.write("Zonas Faltantes:", res[res['P_PREP'].isna()]['DESCRIPCIÓN ZONA'].unique())
                    else:
                        res['TOTAL_FINAL'] = (res['P_PREP'] + res['P_TRANS']) * res['BULTOS'] * 1.15
                        res['SUBTOTAL'] = (res['P_PREP'] + res['P_TRANS']) * res['BULTOS']

                        st.subheader(f"📋 Resumen VV: {mes_sel}")
                        # Resumen simplificado solo para VV
                        summary = res.groupby('GP')['SUBTOTAL'].sum().reset_index()
                        summary.columns = ['GP', 'SUBTOTAL VV']
                        summary['IVA 15%'] = summary['SUBTOTAL VV'] * 0.15
                        summary['TOTAL GENERAL'] = summary['SUBTOTAL VV'] + summary['IVA 15%']
                        
                        summary_f = pd.concat([summary, pd.DataFrame([{'GP': '--- TOTALES ---', 'SUBTOTAL VV': summary['SUBTOTAL VV'].sum(), 'IVA 15%': summary['IVA 15%'].sum(), 'TOTAL GENERAL': summary['TOTAL GENERAL'].sum()}])], ignore_index=True)
                        st.table(summary_f.style.format(subset=summary_f.columns[1:], formatter="{:,.2f}"))
                        
                        st.download_button("📥 Descargar Resumen VV", format_excel(summary_f), f"Resumen_VV_{mes_sel}.xlsx")

                        if st.button("💾 Guardar Reprograma"):
                            res['MES_PROCESO'] = mes_sel
                            if os.path.exists(HISTORICO_REPRO_FILE):
                                df_h_old = pd.read_csv(HISTORICO_REPRO_FILE)
                                df_h_old = df_h_old[df_h_old['MES_PROCESO'] != mes_sel]
                                pd.concat([df_h_old, res]).to_csv(HISTORICO_REPRO_FILE, index=False)
                            else:
                                res.to_csv(HISTORICO_REPRO_FILE, index=False)
                            st.success("Guardado en Historial Reprograma.")

                        st.session_state['res_repro'] = res
                        st.session_state['mes_repro_actual'] = mes_sel

    with tabs[1]: # DETALLE VV
        if 'res_repro' in st.session_state:
            df_v = st.session_state['res_repro']
            st.metric("Total VV del Mes", f"$ {df_v['TOTAL_FINAL'].sum():,.2f}")
            st.dataframe(df_v, use_container_width=True)

    with tabs[2]: # CONFIGURAR REPROGRAMA
        st.header("⚙️ Maestros Reprograma")
        ca, cb = st.columns(2)
        with ca:
            ug = st.file_uploader("Cargar GP Reprograma", type=['csv','xlsx'], key="up_gp_r")
            if ug:
                d = leer_archivo(ug)
                if d is not None: d.to_csv(PATH_GP_REPRO, index=False); st.success("GP Reprograma OK")
        with cb:
            uc = st.file_uploader("Cargar Costos Reprograma", type=['csv','xlsx'], key="up_co_r")
            if uc:
                d = leer_archivo(uc)
                if d is not None: d.to_csv(PATH_COSTOS_REPRO, index=False); st.success("Costos Reprograma OK")

    with tabs[3]: # HISTORIAL VV
        if os.path.exists(HISTORICO_REPRO_FILE):
            df_h = pd.read_csv(HISTORICO_REPRO_FILE)
            meses = df_h['MES_PROCESO'].unique()
            m_h = st.selectbox("Seleccionar Mes Histórico VV:", meses)
            st.dataframe(df_h[df_h['MES_PROCESO'] == m_h], use_container_width=True)
