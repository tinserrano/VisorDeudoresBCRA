import streamlit as st
import requests
import pandas as pd
import numpy as np
import json
from datetime import datetime
import time
import re
import urllib3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Suprimir advertencias SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Definir colores para las situaciones crediticias
SITUACION_COLORS = {
    1: "#4CAF50",  # Verde (mejor situación)
    2: "#8BC34A",  # Verde claro
    3: "#FFC107",  # Amarillo
    4: "#FF9800",  # Naranja
    5: "#F44336",  # Rojo
    6: "#B71C1C"   # Rojo oscuro (peor situación)
}

# Mapeo de situaciones crediticias a texto descriptivo
SITUACION_MAP = {
    1: "Normal",
    2: "Con seguimiento especial/Riesgo bajo",
    3: "Con problemas/Riesgo medio",
    4: "Alto riesgo de insolvencia/Riesgo alto",
    5: "Irrecuperable",
    6: "Irrecuperable por disposición técnica"
}

def consultar_api(url, cuit, tipo_consulta="general"):
    """
    Consulta la API del BCRA con manejo de errores.
    El parámetro tipo_consulta permite personalizar el comportamiento para diferentes tipos de consultas.
    """
    try:
        # Desactivar la verificación SSL para evitar problemas de certificados
        response = requests.get(url, verify=False)
        
        # Suprimir las advertencias de seguridad relacionadas con la verificación SSL
        requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            # Comportamiento personalizado según el tipo de consulta
            if tipo_consulta != "cheques" or tipo_consulta == "silencioso":
                st.warning(f"No se encontró información para el CUIT/CUIL/CDI: {cuit}")
            return None
        elif response.status_code == 400:
            error_msg = "Parámetro erróneo. Asegúrese de ingresar un CUIT/CUIL/CDI válido de 11 dígitos."
            try:
                error_data = response.json()
                if "errorMessages" in error_data and error_data["errorMessages"]:
                    error_msg = error_data["errorMessages"][0]
            except:
                pass
            
            # Mostrar errores solo para consultas que no sean silenciosas
            if tipo_consulta != "silencioso":
                st.error(error_msg)
            return None
        else:
            # Mostrar errores solo para consultas que no sean silenciosas
            if tipo_consulta != "silencioso":
                st.error(f"Error al consultar la API: {response.status_code}")
            return None
    except Exception as e:
        # Mostrar errores solo para consultas que no sean silenciosas
        if tipo_consulta != "silencioso":
            st.error(f"Error en la consulta: {str(e)}")
        return None

def obtener_deudas(cuit):
    url = f"https://api.bcra.gob.ar/centraldedeudores/v1.0/Deudas/{cuit}"
    return consultar_api(url, cuit, "deudas")

def obtener_deudas_historicas(cuit):
    url = f"https://api.bcra.gob.ar/centraldedeudores/v1.0/Deudas/Historicas/{cuit}"
    return consultar_api(url, cuit, "historicas")

def obtener_cheques_rechazados(cuit):
    url = f"https://api.bcra.gob.ar/centraldedeudores/v1.0/Deudas/ChequesRechazados/{cuit}"
    return consultar_api(url, cuit, "cheques")

def procesar_deudas(datos):
    if not datos or 'results' not in datos:
        return None
    
    filas = []
    
    for periodo in datos['results']['periodos']:
        for entidad in periodo['entidades']:
            fila = {
                'CUIT': datos['results']['identificacion'],
                'Denominación': datos['results']['denominacion'],
                'Período': periodo['periodo'],
                'Entidad': entidad['entidad'],
                'Situación': entidad['situacion'],
                'Fecha Situación 1': entidad.get('fechaSit1', ''),
                'Monto': entidad['monto'],
                'Días Atraso Pago': entidad.get('diasAtrasoPago', 0),
                'Refinanciaciones': entidad.get('refinanciaciones', False),
                'Recategorización Obligatoria': entidad.get('recategorizacionOblig', False),
                'Situación Jurídica': entidad.get('situacionJuridica', False),
                'Irrecup. por Disposición Técnica': entidad.get('irrecDisposicionTecnica', False),
                'En Revisión': entidad.get('enRevision', False),
                'Proceso Judicial': entidad.get('procesoJud', False)
            }
            filas.append(fila)
    
    if filas:
        return pd.DataFrame(filas)
    else:
        return None

def procesar_deudas_historicas(datos):
    if not datos or 'results' not in datos:
        return None
    
    filas = []
    
    for periodo in datos['results']['periodos']:
        for entidad in periodo['entidades']:
            fila = {
                'CUIT': datos['results']['identificacion'],
                'Denominación': datos['results']['denominacion'],
                'Período': periodo['periodo'],
                'Entidad': entidad['entidad'],
                'Situación': entidad['situacion'],
                'Monto': entidad['monto'],
                'En Revisión': entidad.get('enRevision', False),
                'Proceso Judicial': entidad.get('procesoJud', False)
            }
            filas.append(fila)
    
    if filas:
        return pd.DataFrame(filas)
    else:
        return None

def procesar_cheques_rechazados(datos):
    if not datos or 'results' not in datos:
        return None
    
    filas = []
    
    if 'causales' in datos['results']:
        for causal in datos['results']['causales']:
            causal_rechazo = causal.get('causal', '')
            
            for entidad in causal.get('entidades', []):
                entidad_numero = entidad.get('entidad', '')
                
                for detalle in entidad.get('detalle', []):
                    fila = {
                        'CUIT': datos['results']['identificacion'],
                        'Denominación': datos['results']['denominacion'],
                        'Causal': causal_rechazo,
                        'Entidad': entidad_numero,
                        'Número Cheque': detalle.get('nroCheque', ''),
                        'Fecha Rechazo': detalle.get('fechaRechazo', ''),
                        'Monto': detalle.get('monto', 0),
                        'Fecha Pago': detalle.get('fechaPago', ''),
                        'Fecha Pago Multa': detalle.get('fechaPagoMulta', ''),
                        'Estado Multa': detalle.get('estadoMulta', ''),
                        'Cuenta Personal': detalle.get('ctaPersonal', False),
                        'Denominación Jurídica': detalle.get('denomJuridica', ''),
                        'En Revisión': detalle.get('enRevision', False),
                        'Proceso Judicial': detalle.get('procesoJud', False)
                    }
                    filas.append(fila)
    
    if filas:
        return pd.DataFrame(filas)
    else:
        return None

def procesar_lista_cuits(cuits_texto):
    """
    Procesa una lista de CUITs separados por comas y genera un informe resumido
    """
    # Limpiar y extraer CUITs de la cadena de texto
    cuits_lista = [cuit.strip() for cuit in cuits_texto.split(',') if cuit.strip()]
    
    # Validar formato de cada CUIT
    cuits_validos = []
    for cuit in cuits_lista:
        if re.match(r'^\d{11}$', cuit):
            cuits_validos.append(cuit)
        else:
            st.warning(f"CUIT/CUIL/CDI inválido ignorado: {cuit}")
    
    if not cuits_validos:
        st.error("No se encontraron CUITs/CUILs/CDIs válidos para procesar")
        return
    
    # Mostrar información de procesamiento
    st.subheader(f"Procesando {len(cuits_validos)} CUITs/CUILs/CDIs")
    
    # Crear DataFrame para resultados resumidos
    resultados = []
    
    # Procesar cada CUIT
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, cuit in enumerate(cuits_validos):
        # Actualizar progreso
        progress = int((i + 1) / len(cuits_validos) * 100)
        progress_bar.progress(progress)
        status_text.text(f"Procesando CUIT {cuit} ({i+1}/{len(cuits_validos)})")
        
        # Preparar fila de resultados para este CUIT
        resultado_cuit = {
            'CUIT': cuit,
            'Denominación': '',
            'Situación Actual': 'Sin datos',
            'Tiene Situación Irregular': 'No',
            'Tuvo Situación Irregular': 'No',
            'Tiene Cheques Rechazados': 'No',
            'Deuda Total (miles $)': 0,
            'Cantidad Entidades': 0,
            'Detalle Situaciones': '',
            'Cantidad Cheques Rechazados': 0
        }
        
        # Obtener deudas actuales
        datos_deudas = obtener_deudas(cuit)
        periodo_actual = None
        
        if datos_deudas and 'results' in datos_deudas:
            df_deudas = procesar_deudas(datos_deudas)
            
            if df_deudas is not None and not df_deudas.empty:
                # Capturar el período actual para comparación posterior
                if 'Período' in df_deudas.columns and not df_deudas.empty:
                    periodo_actual = df_deudas['Período'].iloc[0]
                
                # Actualizar denominación
                resultado_cuit['Denominación'] = datos_deudas['results']['denominacion']
                
                # Calcular resumen - situación irregular significa > 1, no simplemente ≠ 1
                tiene_situacion_irregular = any(df_deudas['Situación'] > 1)
                resultado_cuit['Tiene Situación Irregular'] = 'Sí' if tiene_situacion_irregular else 'No'
                
                # Calcular la situación más alta (peor)
                max_situacion = df_deudas['Situación'].max()
                resultado_cuit['Situación Actual'] = f"{int(max_situacion)}: {SITUACION_MAP.get(int(max_situacion), 'Desconocida')}"
                
                # Calcular deuda total
                resultado_cuit['Deuda Total (miles $)'] = df_deudas['Monto'].sum()
                
                # Contar entidades
                resultado_cuit['Cantidad Entidades'] = len(df_deudas['Entidad'].unique())
                
                # Crear detalle de situaciones
                situaciones = df_deudas.groupby('Situación').size().reset_index(name='Cantidad')
                detalles = []
                for _, row in situaciones.iterrows():
                    detalles.append(f"Sit.{int(row['Situación'])}: {row['Cantidad']}")
                resultado_cuit['Detalle Situaciones'] = ", ".join(detalles)
        
        # Obtener deudas históricas
        datos_historicos = obtener_deudas_historicas(cuit)
        if datos_historicos and 'results' in datos_historicos:
            df_historico = procesar_deudas_historicas(datos_historicos)
            
            if df_historico is not None and not df_historico.empty:
                # Verificar si tuvo situación irregular en el pasado (excluyendo el período actual)
                df_solo_historico = df_historico.copy()
                
                # Si hay período actual, filtrar para excluirlo del análisis histórico
                if periodo_actual:
                    df_solo_historico = df_historico[df_historico['Período'] != periodo_actual]
                
                # Solo analizar los períodos anteriores y verificar situaciones > 1 (no solo ≠ 1)
                if not df_solo_historico.empty:
                    # Verificar si hubo situaciones irregulares (> 1) en períodos pasados
                    tuvo_situacion_irregular = any(df_solo_historico['Situación'] > 1)
                    resultado_cuit['Tuvo Situación Irregular'] = 'Sí' if tuvo_situacion_irregular else 'No'
        
        # Obtener cheques rechazados
        datos_cheques = obtener_cheques_rechazados(cuit)
        if datos_cheques and 'results' in datos_cheques:
            df_cheques = procesar_cheques_rechazados(datos_cheques)
            
            if df_cheques is not None and not df_cheques.empty:
                resultado_cuit['Tiene Cheques Rechazados'] = 'Sí'
                resultado_cuit['Cantidad Cheques Rechazados'] = len(df_cheques)
        
        # Agregar resultado a la lista
        resultados.append(resultado_cuit)
        
        # Pequeña pausa para no sobrecargar la API
        time.sleep(0.5)
    
    # Crear DataFrame con todos los resultados
    df_resultados = pd.DataFrame(resultados)
    
    return df_resultados

def mostrar_resultados_multiple_cuits(df_resultados):
    """
    Muestra los resultados del análisis de múltiples CUITs de forma visual
    """
    if df_resultados is None or df_resultados.empty:
        st.warning("No se obtuvieron resultados para analizar")
        return
    
    # Crear pestañas para diferentes vistas
    tab1, tab2 = st.tabs(["Resumen", "Análisis Detallado"])
    
    with tab1:
        # Aplicar formato condicional
        st.subheader("Informe Resumido de CUITs/CUILs/CDIs")
        
        # Convertir columnas de estado a valores booleanos para filtrado
        df_filtro = df_resultados.copy()
        df_filtro['Tiene Situación Irregular Bool'] = df_filtro['Tiene Situación Irregular'] == 'Sí'
        df_filtro['Tuvo Situación Irregular Bool'] = df_filtro['Tuvo Situación Irregular'] == 'Sí'
        df_filtro['Tiene Cheques Rechazados Bool'] = df_filtro['Tiene Cheques Rechazados'] == 'Sí'
        
        # Opciones de filtro - usar session_state para mantener los valores entre rerenders
        if 'mostrar_con_irregularidades' not in st.session_state:
            st.session_state.mostrar_con_irregularidades = False
        if 'mostrar_con_historico_irregular' not in st.session_state:
            st.session_state.mostrar_con_historico_irregular = False
        if 'mostrar_con_cheques' not in st.session_state:
            st.session_state.mostrar_con_cheques = False
        
        st.markdown("### Filtros")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            mostrar_con_irregularidades = st.checkbox(
                "Solo con situación irregular actual", 
                value=st.session_state.mostrar_con_irregularidades,
                key="cb_situacion_irregular",
                on_change=lambda: setattr(st.session_state, 'mostrar_con_irregularidades', st.session_state.cb_situacion_irregular)
            )
        
        with col2:
            mostrar_con_historico_irregular = st.checkbox(
                "Solo con historial irregular", 
                value=st.session_state.mostrar_con_historico_irregular,
                key="cb_historico_irregular",
                on_change=lambda: setattr(st.session_state, 'mostrar_con_historico_irregular', st.session_state.cb_historico_irregular)
            )
        
        with col3:
            mostrar_con_cheques = st.checkbox(
                "Solo con cheques rechazados", 
                value=st.session_state.mostrar_con_cheques,
                key="cb_cheques",
                on_change=lambda: setattr(st.session_state, 'mostrar_con_cheques', st.session_state.cb_cheques)
            )
        
        # Aplicar filtros
        df_mostrar = df_filtro.copy()
        
        if mostrar_con_irregularidades:
            df_mostrar = df_mostrar[df_mostrar['Tiene Situación Irregular Bool']]
        
        if mostrar_con_historico_irregular:
            df_mostrar = df_mostrar[df_mostrar['Tuvo Situación Irregular Bool']]
        
        if mostrar_con_cheques:
            df_mostrar = df_mostrar[df_mostrar['Tiene Cheques Rechazados Bool']]
        
        # Eliminar columnas auxiliares de filtro
        df_mostrar = df_mostrar.drop(columns=[
            'Tiene Situación Irregular Bool', 
            'Tuvo Situación Irregular Bool', 
            'Tiene Cheques Rechazados Bool'
        ])
        
        # Aplicar colores condicionales a la tabla
        def highlight_si_no(val):
            if val == 'Sí':
                return 'background-color: rgba(255, 0, 0, 0.2);'  # Rojo claro
            elif val == 'No':
                return 'background-color: rgba(0, 255, 0, 0.2);'  # Verde claro
            return ''
            
        # Mostrar tabla con formateo condicional
        st.dataframe(
            df_mostrar.style.applymap(
                highlight_si_no, 
                subset=['Tiene Situación Irregular', 'Tuvo Situación Irregular', 'Tiene Cheques Rechazados']
            )
        )
        
        # Botón para descargar resultados
        csv = df_mostrar.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Descargar informe como CSV",
            csv,
            f"informe_cuits_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv",
            key='download-csv-informe'
        )
        
        # Mostrar métricas resumen
        st.subheader("Resumen General")
        total_cuits = len(df_resultados)
        
        # Calcular métricas generales
        cuits_con_irregularidades = sum(df_resultados['Tiene Situación Irregular'] == 'Sí')
        cuits_con_historico = sum(df_resultados['Tuvo Situación Irregular'] == 'Sí')
        cuits_con_cheques = sum(df_resultados['Tiene Cheques Rechazados'] == 'Sí')
        
        # Mostrar métricas en columnas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total de CUITs analizados", 
                total_cuits
            )
        
        with col2:
            pct_irreg = (cuits_con_irregularidades / total_cuits * 100) if total_cuits > 0 else 0
            st.metric(
                "Con situación irregular actual", 
                f"{cuits_con_irregularidades} ({pct_irreg:.1f}%)"
            )
        
        with col3:
            pct_hist = (cuits_con_historico / total_cuits * 100) if total_cuits > 0 else 0
            st.metric(
                "Con historial irregular", 
                f"{cuits_con_historico} ({pct_hist:.1f}%)"
            )
        
        with col4:
            pct_cheques = (cuits_con_cheques / total_cuits * 100) if total_cuits > 0 else 0
            st.metric(
                "Con cheques rechazados", 
                f"{cuits_con_cheques} ({pct_cheques:.1f}%)"
            )
    
    with tab2:
        st.subheader("Análisis de CUITs/CUILs/CDIs por Categorías")
        
        # Gráfico de distribución por situación
        st.markdown("### Distribución por Situación Crediticia")
        
        # Extraer la categoría de situación (solo el número)
        df_resultados['Categoría Situación'] = df_resultados['Situación Actual'].apply(
            lambda x: int(x.split(':')[0]) if x != 'Sin datos' else 0
        )
        
        # Contar CUITs por categoría
        categoria_counts = df_resultados['Categoría Situación'].value_counts().reset_index()
        categoria_counts.columns = ['Situación', 'Cantidad']
        
        # Crear diccionario para mapear cada situación con su descripción
        situacion_map_completo = {
            0: "Sin datos",
            1: "Normal",
            2: "Con seguimiento especial/Riesgo bajo",
            3: "Con problemas/Riesgo medio",
            4: "Alto riesgo de insolvencia/Riesgo alto",
            5: "Irrecuperable",
            6: "Irrecuperable por disposición técnica"
        }
        
        # Agregar descripción
        categoria_counts['Descripción'] = categoria_counts['Situación'].map(situacion_map_completo)
        
        # Crear gráfico
        fig = px.pie(
            categoria_counts,
            values='Cantidad',
            names='Descripción',
            title="Distribución de CUITs por Situación Crediticia",
            color='Situación',
            color_discrete_map={
                0: "#CCCCCC",  # Gris para sin datos
                1: "#4CAF50",  # Verde
                2: "#8BC34A",  # Verde claro
                3: "#FFC107",  # Amarillo
                4: "#FF9800",  # Naranja
                5: "#F44336",  # Rojo
                6: "#B71C1C"   # Rojo oscuro
            }
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Gráfico de situaciones irregulares por período
        st.markdown("### Análisis de Situaciones Irregulares")
        
        # Crear categorías de análisis
        categorias = [
            "Sin irregularidades",
            "Con irregularidades solo actuales",
            "Con irregularidades solo históricas",
            "Con irregularidades actuales e históricas"
        ]
        
        # Calcular conteos
        sin_irreg = sum((df_resultados['Tiene Situación Irregular'] == 'No') & 
                         (df_resultados['Tuvo Situación Irregular'] == 'No'))
        
        solo_actual = sum((df_resultados['Tiene Situación Irregular'] == 'Sí') & 
                           (df_resultados['Tuvo Situación Irregular'] == 'No'))
        
        solo_historica = sum((df_resultados['Tiene Situación Irregular'] == 'No') & 
                              (df_resultados['Tuvo Situación Irregular'] == 'Sí'))
        
        ambas = sum((df_resultados['Tiene Situación Irregular'] == 'Sí') & 
                     (df_resultados['Tuvo Situación Irregular'] == 'Sí'))
        
        # Crear datos para gráfico
        df_analisis = pd.DataFrame({
            'Categoría': categorias,
            'Cantidad': [sin_irreg, solo_actual, solo_historica, ambas]
        })
        
        # Crear gráfico de barras
        fig = px.bar(
            df_analisis,
            x='Categoría',
            y='Cantidad',
            title="Análisis de Situaciones Irregulares",
            color='Categoría',
            color_discrete_map={
                "Sin irregularidades": "#4CAF50",
                "Con irregularidades solo actuales": "#FFC107",
                "Con irregularidades solo históricas": "#FF9800",
                "Con irregularidades actuales e históricas": "#F44336"
            }
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Análisis de cheques rechazados
        st.markdown("### Análisis de Cheques Rechazados")
        
        # Crear categorías de análisis
        df_cheques_analisis = pd.DataFrame({
            'Categoría': ["Sin cheques rechazados", "Con cheques rechazados"],
            'Cantidad': [
                sum(df_resultados['Tiene Cheques Rechazados'] == 'No'),
                sum(df_resultados['Tiene Cheques Rechazados'] == 'Sí')
            ]
        })
        
        # Crear gráfico
        fig = px.pie(
            df_cheques_analisis,
            values='Cantidad',
            names='Categoría',
            title="Distribución de CUITs por Cheques Rechazados",
            color='Categoría',
            color_discrete_map={
                "Sin cheques rechazados": "#4CAF50",
                "Con cheques rechazados": "#F44336"
            }
        )
        st.plotly_chart(fig, use_container_width=True)