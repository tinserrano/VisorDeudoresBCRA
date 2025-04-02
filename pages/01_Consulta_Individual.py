import streamlit as st
import re
import time
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import pandas as pd

# Importar utilidades comunes
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import (
    obtener_deudas, obtener_deudas_historicas, obtener_cheques_rechazados,
    procesar_deudas, procesar_deudas_historicas, procesar_cheques_rechazados,
    SITUACION_COLORS, SITUACION_MAP
)

st.title("Consulta Individual de Deudores BCRA")
st.markdown("""
Esta página permite realizar consultas detalladas para un CUIT/CUIL/CDI específico, 
visualizando información sobre deudas actuales, históricas y cheques rechazados.
""")

# Consulta individual
with st.form(key='consulta_form'):
    cuit_input = st.text_input("Ingrese CUIT/CUIL/CDI (sin guiones)", "")
    consultar_submit = st.form_submit_button("Consultar")

if cuit_input and not re.match(r'^\d{11}$', cuit_input):
    st.error("El CUIT/CUIL/CDI debe contener exactamente 11 dígitos numéricos, sin guiones.")
    cuit_input = ""

if consultar_submit and cuit_input:
    with st.spinner("Consultando información..."):
        st.subheader(f"Resultados para CUIT/CUIL/CDI: {cuit_input}")
        datos_deudas = obtener_deudas(cuit_input)
        if datos_deudas:
            df_deudas = procesar_deudas(datos_deudas)
            
            if df_deudas is not None:
                st.subheader("Deudas Actuales")
                
                tiene_situacion_irregular = any(df_deudas['Situación'] != 1)
                if tiene_situacion_irregular:
                    st.warning("⚠️ ATENCIÓN: El deudor presenta situaciones crediticias diferentes a 'Normal (1)'")
                
                tab1, tab2, tab3 = st.tabs(["Datos", "Gráfico por Situación", "Gráfico por Entidad"])
                
                with tab1:
                    st.dataframe(df_deudas)
                
                with tab2:
                    df_situacion = df_deudas.groupby('Situación').agg({'Monto': 'sum'}).reset_index()
                    df_situacion['Descripción'] = df_situacion['Situación'].map(SITUACION_MAP)
                    df_situacion['Color'] = df_situacion['Situación'].map(SITUACION_COLORS)
                    
                    # Ordenar por situación para que aparezcan en orden
                    df_situacion = df_situacion.sort_values('Situación')
                    
                    # Crear gráfico con colores personalizados
                    fig = go.Figure()
                    
                    for idx, row in df_situacion.iterrows():
                        fig.add_trace(go.Bar(
                            x=[row['Descripción']],
                            y=[row['Monto']],
                            name=f"Situación {int(row['Situación'])}",
                            marker_color=SITUACION_COLORS[int(row['Situación'])]
                        ))
                    
                    fig.update_layout(
                        title="Deuda por Situación Crediticia",
                        xaxis_title="Situación",
                        yaxis_title="Monto Total (miles de $)",
                        xaxis_tickangle=-45,
                        height=500,
                        barmode='group'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    
                with tab3:
                    df_entidad = df_deudas.groupby(['Entidad', 'Situación']).agg({'Monto': 'sum'}).reset_index()
                    
                    # Crear gráfico con colores personalizados
                    fig = go.Figure()
                    
                    for situacion in sorted(df_entidad['Situación'].unique()):
                        df_filtrado = df_entidad[df_entidad['Situación'] == situacion]
                        
                        fig.add_trace(go.Bar(
                            x=df_filtrado['Entidad'],
                            y=df_filtrado['Monto'],
                            name=f"Situación {int(situacion)}: {SITUACION_MAP[int(situacion)]}",
                            marker_color=SITUACION_COLORS[int(situacion)]
                        ))
                    
                    fig.update_layout(
                        title="Deuda por Entidad y Situación Crediticia",
                        xaxis_title="Entidad Financiera",
                        yaxis_title="Monto Total (miles de $)",
                        xaxis_tickangle=-45,
                        height=500,
                        barmode='stack',
                        legend_title="Situación Crediticia"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                st.subheader("Filtros para Deudas Actuales")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    situacion_filter = st.multiselect(
                        "Filtrar por Situación",
                        options=sorted(df_deudas['Situación'].unique()),
                        default=[]
                    )
                
                with col2:
                    entidad_filter = st.multiselect(
                        "Filtrar por Entidad",
                        options=sorted(df_deudas['Entidad'].unique()),
                        default=[]
                    )
                
                with col3:
                    refinanciaciones_filter = st.checkbox("Solo con Refinanciaciones")
                    situacion_irregular_filter = st.checkbox("Solo situaciones irregulares (≠1)")
                
                df_filtered = df_deudas.copy()
                
                if situacion_filter:
                    df_filtered = df_filtered[df_filtered['Situación'].isin(situacion_filter)]
                
                if entidad_filter:
                    df_filtered = df_filtered[df_filtered['Entidad'].isin(entidad_filter)]
                
                if refinanciaciones_filter:
                    df_filtered = df_filtered[df_filtered['Refinanciaciones'] == True]
                
                if situacion_irregular_filter:
                    df_filtered = df_filtered[df_filtered['Situación'] != 1]
                
                st.subheader("Resultados Filtrados")
                st.dataframe(df_filtered)
                
                csv = df_filtered.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Descargar resultados como CSV",
                    csv,
                    f"deudores_bcra_{cuit_input}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv",
                    key='download-csv'
                )
                
                st.subheader("Métricas")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Cantidad de Entidades", 
                        len(df_deudas['Entidad'].unique())
                    )
                
                with col2:
                    st.metric(
                        "Deuda Total", 
                        f"${df_deudas['Monto'].sum():,.2f}"
                    )
                
                with col3:
                    sit_1_count = len(df_deudas[df_deudas['Situación'] == 1])
                    total_count = len(df_deudas)
                    sit_1_percent = (sit_1_count / total_count * 100) if total_count > 0 else 0
                    st.metric(
                        "Situación 1 (Normal)", 
                        f"{sit_1_count} ({sit_1_percent:.1f}%)"
                    )
                
                with col4:
                    situacion_irregular_count = len(df_deudas[df_deudas['Situación'] != 1])
                    situacion_irregular_percent = (situacion_irregular_count / total_count * 100) if total_count > 0 else 0
                    st.metric(
                        "Situaciones Irregulares", 
                        f"{situacion_irregular_count} ({situacion_irregular_percent:.1f}%)",
                        delta=None if situacion_irregular_count == 0 else f"{situacion_irregular_count}",
                        delta_color="inverse"
                    )
            else:
                st.info("No se encontraron deudas actuales.")
        
        datos_historicos = obtener_deudas_historicas(cuit_input)
        if datos_historicos:
            df_historico = procesar_deudas_historicas(datos_historicos)
            
            if df_historico is not None:
                st.subheader("Deudas Históricas")
                
                hist_tab1, hist_tab2 = st.tabs(["Datos", "Gráfico de Evolución"])
                
                with hist_tab1:
                    st.dataframe(df_historico)
                
                with hist_tab2:
                    df_historico['FechaPeriodo'] = pd.to_datetime(df_historico['Período'], format='%Y%m')
                    df_historico = df_historico.sort_values('FechaPeriodo')
                    
                    df_evolucion = df_historico.groupby(['FechaPeriodo', 'Situación']).agg({'Monto': 'sum'}).reset_index()
                    
                    df_evolucion['SituaciónTexto'] = df_evolucion['Situación'].apply(
                        lambda x: f"{int(x)}: {SITUACION_MAP.get(int(x), 'Desconocida')}"
                    )
                    
                    fig = px.line(
                        df_evolucion, 
                        x='FechaPeriodo', 
                        y='Monto',
                        color='SituaciónTexto',
                        markers=True,
                        title="Evolución de Deudas por Situación Crediticia",
                        labels={
                            'FechaPeriodo': 'Período',
                            'Monto': 'Monto Total (miles de $)',
                            'SituaciónTexto': 'Situación'
                        },
                        height=500
                    )
                    
                    fig.update_layout(
                        xaxis_title="Período",
                        yaxis_title="Monto Total (miles de $)",
                        legend_title="Situación Crediticia",
                        hovermode="x unified"
                    )
                    
                    fig.update_traces(
                        hovertemplate='%{y:,.2f} miles de $<extra></extra>'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.subheader("Evolución por Entidad")
                    
                    entidades = sorted(df_historico['Entidad'].unique())
                    entidades_seleccionadas = st.multiselect(
                        "Seleccionar Entidades para Visualizar",
                        options=entidades,
                        default=entidades[:min(5, len(entidades))]
                    )
                    
                    if entidades_seleccionadas:
                        df_evolucion_entidad = df_historico[df_historico['Entidad'].isin(entidades_seleccionadas)]
                        df_evolucion_entidad = df_evolucion_entidad.groupby(['FechaPeriodo', 'Entidad']).agg({'Monto': 'sum'}).reset_index()
                        
                        fig_entidad = px.line(
                            df_evolucion_entidad, 
                            x='FechaPeriodo', 
                            y='Monto',
                            color='Entidad',
                            markers=True,
                            title="Evolución de Deudas por Entidad",
                            labels={
                                'FechaPeriodo': 'Período',
                                'Monto': 'Monto Total (miles de $)',
                                'Entidad': 'Entidad Financiera'
                            },
                            height=500
                        )
                        
                        fig_entidad.update_layout(
                            xaxis_title="Período",
                            yaxis_title="Monto Total (miles de $)",
                            legend_title="Entidad Financiera",
                            hovermode="x unified"
                        )
                        
                        fig_entidad.update_traces(
                            hovertemplate='%{y:,.2f} miles de $<extra></extra>'
                        )
                        
                        st.plotly_chart(fig_entidad, use_container_width=True)
            else:
                st.info("No se encontraron deudas históricas.")
        
        datos_cheques = obtener_cheques_rechazados(cuit_input)
        if datos_cheques:
            df_cheques = procesar_cheques_rechazados(datos_cheques)
            
            if df_cheques is not None:
                st.subheader("Cheques Rechazados")
                
                cheq_tab1, cheq_tab2 = st.tabs(["Datos", "Gráficos"])
                
                with cheq_tab1:
                    st.dataframe(df_cheques)
                
                with cheq_tab2:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        df_causales = df_cheques.groupby('Causal').size().reset_index(name='Cantidad')
                        
                        fig_causal = px.pie(
                            df_causales, 
                            values='Cantidad', 
                            names='Causal',
                            title="Distribución de Cheques por Causal",
                            hole=0.4
                        )
                        st.plotly_chart(fig_causal, use_container_width=True)
                    
                    with col2:
                        df_montos = df_cheques.groupby('Causal').agg({'Monto': 'sum'}).reset_index()
                        
                        fig_monto = px.bar(
                            df_montos, 
                            x='Causal', 
                            y='Monto',
                            title="Montos Totales por Causal",
                            labels={'Monto': 'Monto Total ($)', 'Causal': 'Causal de Rechazo'}
                        )
                        st.plotly_chart(fig_monto, use_container_width=True)
                    
                    if 'Fecha Rechazo' in df_cheques.columns and df_cheques['Fecha Rechazo'].notna().any():
                        df_cheques['Fecha Rechazo'] = pd.to_datetime(df_cheques['Fecha Rechazo'])
                        df_evolucion_cheques = df_cheques.groupby(df_cheques['Fecha Rechazo'].dt.to_period('M')).size().reset_index()
                        df_evolucion_cheques.columns = ['Mes', 'Cantidad']
                        df_evolucion_cheques['Mes'] = df_evolucion_cheques['Mes'].dt.to_timestamp()
                        
                        fig_evolucion = px.line(
                            df_evolucion_cheques, 
                            x='Mes', 
                            y='Cantidad',
                            markers=True,
                            title="Evolución Mensual de Cheques Rechazados",
                            labels={'Mes': 'Mes', 'Cantidad': 'Cantidad de Cheques Rechazados'}
                        )
                        st.plotly_chart(fig_evolucion, use_container_width=True)
                    
                    if 'Estado Multa' in df_cheques.columns and df_cheques['Estado Multa'].notna().any():
                        df_multas = df_cheques.groupby('Estado Multa').size().reset_index(name='Cantidad')
                        
                        fig_multas = px.pie(
                            df_multas, 
                            values='Cantidad', 
                            names='Estado Multa',
                            title="Estado de Multas por Cheques Rechazados",
                            hole=0.4
                        )
                        st.plotly_chart(fig_multas, use_container_width=True)
            else:
                st.info("No se encontraron cheques rechazados.")

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """

custom_footer = """
            <style>
            .footer {
                position: fixed;
                left: 0;
                bottom: 0;
                width: 100%;
                text-align: center;
                padding: 10px;
                color: #7a7a7a;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .footer a {
                display: flex;
                align-items: center;
                color: #0A66C2;
                text-decoration: none;
                margin-left: 8px;  /* Añadido espacio a la izquierda del enlace */
            }
            .linkedin-logo {
                height: 16px;
                margin-right: 5px;
            }
            </style>
            <div class="footer">
                Desarrollado por
                <a href="https://www.linkedin.com/in/martinepenas/" target="_blank">
                    <svg class="linkedin-logo" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#0A66C2">
                        <path d="M20.5 2h-17A1.5 1.5 0 002 3.5v17A1.5 1.5 0 003.5 22h17a1.5 1.5 0 001.5-1.5v-17A1.5 1.5 0 0020.5 2zM8 19H5v-9h3zM6.5 8.25A1.75 1.75 0 118.3 6.5a1.78 1.78 0 01-1.8 1.75zM19 19h-3v-4.74c0-1.42-.6-1.93-1.38-1.93A1.74 1.74 0 0013 14.19a.66.66 0 000 .14V19h-3v-9h2.9v1.3a3.11 3.11 0 012.7-1.4c1.55 0 3.36.86 3.36 3.66z"></path>
                    </svg>
                </a>
            </div>
            """

# Aplicar los estilos
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
st.markdown(custom_footer, unsafe_allow_html=True)