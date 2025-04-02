import streamlit as st
import re
import time
import pandas as pd
from datetime import datetime
import plotly.express as px
# Imports de ReportLab
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, 
    Table, 
    TableStyle, 
    Paragraph, 
    Spacer
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Importar utilidades comunes
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import (
    obtener_deudas, obtener_deudas_historicas, obtener_cheques_rechazados,
    procesar_deudas, procesar_deudas_historicas, procesar_cheques_rechazados,
    procesar_lista_cuits, SITUACION_COLORS, SITUACION_MAP
)


def crear_pie_pagina(fuente_regular, linkedin_url):
    """
    Crea un pie de página con información de contacto e hipervínculo
    """
    estilos = getSampleStyleSheet()
    
    estilo_pie = ParagraphStyle(
        'PiePagina',
        parent=estilos['Normal'],
        fontName=fuente_regular,
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.gray
    )
    
    # Usar una etiqueta <link> para crear un hipervínculo
    pie_texto = (
        f"Desarrollado por TU_NOMBRE | "
        f"<link href='{linkedin_url}'>Conecta conmigo en LinkedIn</link>"
    )
    
    return Paragraph(pie_texto, estilo_pie)

def registrar_fuentes_personalizadas():
    """
    Registra fuentes personalizadas para usar en el PDF
    """
    try:
        # Lista de posibles ubicaciones de archivos de fuente Tahoma
        rutas_tahoma = [
            'tahoma.ttf',  # Ruta local
            'tahomabd.ttf',  # Ruta local para negrita
            '/usr/share/fonts/truetype/tahoma/tahoma.ttf',  # Ruta Linux
            '/Library/Fonts/tahoma.ttf',  # Ruta macOS
            'C:\\Windows\\Fonts\\tahoma.ttf',  # Ruta Windows
            'C:\\Windows\\Fonts\\tahomabd.ttf'  # Ruta Windows negrita
        ]
        
        # Fuentes predeterminadas
        fuente_regular = 'Helvetica'
        fuente_bold = 'Helvetica-Bold'
        
        # Intentar cargar Tahoma
        for ruta in rutas_tahoma:
            try:
                pdfmetrics.registerFont(TTFont('Tahoma', ruta))
                fuente_regular = 'Tahoma'
                break
            except:
                pass
        
        for ruta in rutas_tahoma:
            try:
                pdfmetrics.registerFont(TTFont('TahomaBold', ruta))
                fuente_bold = 'TahomaBold'
                break
            except:
                pass
        
        return fuente_regular, fuente_bold
    
    except Exception as e:
        st.error(f"Error al registrar fuentes: {e}")
        return 'Helvetica', 'Helvetica-Bold'



def obtener_color_fila(fila):
    """
    Determina el color de fondo para una fila basado en su estado
    
    Colores suaves:
    - Verde claro: Sin irregularidades
    - Rojo claro: Con irregularidades o cheques rechazados
    """
    # Verificar situaciones que indican irregularidad
    situacion_irregular = (
        fila['Tiene Situación Irregular'] == 'Sí' or 
        fila['Tuvo Situación Irregular'] == 'Sí' or 
        fila['Tiene Cheques Rechazados'] == 'Sí'
    )
    
    # Usar colores de ReportLab
    if situacion_irregular:
        return colors.HexColor('#FFB6C1')  # Light Pink suave
    else:
        return colors.HexColor('#90EE90')  # Light Green suave
    


def generar_informe_pdf(df_resultados):
    """
    Genera un informe PDF a partir de los resultados de la consulta de CUITs
    
    Parámetros:
    df_resultados (pd.DataFrame): DataFrame con los resultados de la consulta
    """
    # Definir columnas de resumen al inicio
    columnas_resumen = [
        'CUIT', 
        'Denominación', 
        'Situación Actual', 
        'Tiene Situación Irregular', 
        'Tuvo Situación Irregular', 
        'Tiene Cheques Rechazados'
    ]

    # Registrar fuentes personalizadas
    fuente_regular, fuente_bold = registrar_fuentes_personalizadas()
    
    # Nombre de archivo con fecha y hora actual
    fecha_actual = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"VisorDeudoresBCRA_Informe_{fecha_actual}.pdf"
    
    # Definir tamaño de página y márgenes
    pagesize = landscape(letter)
    left_margin = 15 * mm  # Reducir márgenes
    right_margin = 15 * mm
    top_margin = 15 * mm
    bottom_margin = 15 * mm
    
    # Crear el documento PDF con márgenes personalizados
    doc = SimpleDocTemplate(
        nombre_archivo, 
        pagesize=pagesize,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin
    )
    
    # Estilos de texto
    estilos = getSampleStyleSheet()
    
    # Crear estilos personalizados
    estilo_titulo = ParagraphStyle(
        'TituloPersonalizado',
        parent=estilos['Title'],
        fontName=fuente_bold,
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=6
    )
    
    estilo_normal = ParagraphStyle(
        'NormalPersonalizado',
        parent=estilos['Normal'],
        fontName=fuente_regular,
        fontSize=10,
        alignment=TA_LEFT,
        leading=12
    )
    
    estilo_celda = ParagraphStyle(
        'CeldaPersonalizada',
        parent=estilos['Normal'],
        fontName=fuente_regular,
        fontSize=8,
        alignment=TA_LEFT,
        leading=10,
        textColor='black',
        spaceBefore=2,
        spaceAfter=2
    )
    
    # Elementos del PDF
    elementos = []
    
    # Título del informe - Cambiado para incluir VisorDeudoresBCRA
    elementos.append(Paragraph("VisorDeudoresBCRA - Informe de Deudores", estilo_titulo))
    elementos.append(Paragraph(f"Fecha de Emisión: {datetime.now().strftime('%d/%m/%Y %H:%M')}", estilo_normal))
    elementos.append(Spacer(1, 6))
    
    # Calcular ancho de columnas
    ancho_pagina = pagesize[0] - left_margin - right_margin
    anchos_columnas = [
        0.12 * ancho_pagina,  # CUIT
        0.25 * ancho_pagina,  # Denominación
        0.18 * ancho_pagina,  # Situación Actual
        0.15 * ancho_pagina,  # Situación Irregular Actual
        0.15 * ancho_pagina,  # Situación Histórica
        0.15 * ancho_pagina   # Cheques Rechazados
    ]
    
    # Convertir datos de texto a párrafos
    datos_tabla = [columnas_resumen]  # Encabezados
    for index, fila in df_resultados[columnas_resumen].iterrows():
        fila_parrafos = []
        for valor in fila:
            parrafo = Paragraph(str(valor), estilo_celda)
            fila_parrafos.append(parrafo)
        datos_tabla.append(fila_parrafos)
    
    # Crear tabla con anchos de columna personalizados
    tabla = Table(datos_tabla, colWidths=anchos_columnas, repeatRows=1)
    
    # Estilo de la tabla
    estilo_tabla = TableStyle([
        # Estilo para el encabezado
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,0), fuente_bold),
        ('FONTSIZE', (0,0), (-1,0), 10),
        
        # Bordes
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BOX', (0,0), (-1,-1), 1, colors.black),
    ])
    
    # Agregar color de fondo condicional para cada fila
    for i in range(1, len(datos_tabla)):
        # Obtener color para la fila actual
        color_fila = obtener_color_fila(df_resultados.iloc[i-1])
        
        # Aplicar color de fondo a toda la fila
        estilo_tabla.add('BACKGROUND', (0,i), (-1,i), color_fila)
    
    tabla.setStyle(estilo_tabla)
    
    elementos.append(tabla)
    elementos.append(Spacer(1, 6))
    
    # Sección de CUITs con Cheques Rechazados
    cuits_con_cheques = df_resultados[df_resultados['Tiene Cheques Rechazados'] == 'Sí']
    if not cuits_con_cheques.empty:
        elementos.append(Paragraph("Clientes con Cheques Rechazados:", estilo_normal))
        cheques_texto = "\n".join([
            f"CUIT: {row['CUIT']} - {row['Denominación']}" 
            for _, row in cuits_con_cheques.iterrows()
        ])
        elementos.append(Paragraph(cheques_texto, estilo_normal))
        elementos.append(Spacer(1, 6))
    
    # Sección de CUITs con Situación Irregular
    cuits_con_situacion_irregular = df_resultados[df_resultados['Tiene Situación Irregular'] == 'Sí']
    if not cuits_con_situacion_irregular.empty:
        elementos.append(Paragraph("Clientes con Situación Irregular:", estilo_normal))
        irregular_texto = "\n".join([
            f"CUIT: {row['CUIT']} - {row['Denominación']}" 
            for _, row in cuits_con_situacion_irregular.iterrows()
        ])
        elementos.append(Paragraph(irregular_texto, estilo_normal))
    
    # Agregar pie de página con hipervínculo a LinkedIn
    linkedin_url = "https://www.linkedin.com/in/martinepenas/"
    pie_pagina = crear_pie_pagina(fuente_regular, linkedin_url)
    elementos.append(Spacer(1, 10))
    elementos.append(pie_pagina)
    
    # Construir el PDF
    doc.build(elementos)
    
    return nombre_archivo


def crear_pie_pagina(fuente_regular, linkedin_url):
    """
    Crea un pie de página con información de contacto e hipervínculo
    """
    estilos = getSampleStyleSheet()
    
    estilo_pie = ParagraphStyle(
        'PiePagina',
        parent=estilos['Normal'],
        fontName=fuente_regular,
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.gray
    )
    
    # Usar una etiqueta <link> para crear un hipervínculo
    pie_texto = (
        f"Información extraida de BCRA | "
        f"<link href='{linkedin_url}'>Conecta con el que te simplifico la tarea en LinkedIn</link>"
    )
    
    return Paragraph(pie_texto, estilo_pie)
    


# Función para mostrar resultados con manejo de estado

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
                return 'background-color: rgba(255, 99, 71, 0.2);'  # Rojo claro
            elif val == 'No':
                return 'background-color: rgba(144, 238, 144, 0.2);'  # Verde claro
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


    
        if st.button("Generar Informe PDF"):
            try:
                ruta_pdf = generar_informe_pdf(df_resultados)
                with open(ruta_pdf, "rb") as pdf_file:
                    st.download_button(
                        label="Descargar Informe PDF",
                        data=pdf_file.read(),
                        file_name=ruta_pdf,
                        mime="application/pdf"
                    )
                st.success(f"Informe PDF generado: {ruta_pdf}")
            except Exception as e:
                st.error(f"Error al generar el informe PDF: {str(e)}")

        
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

st.title("Consulta Múltiple de Deudores BCRA")
st.markdown("""
Esta página permite consultar información de múltiples CUITs/CUILs/CDIs a la vez y 
generar un informe resumido con información relevante sobre cada uno.

Puede ingresar los CUITs/CUILs/CDIs de dos formas:
1. Cargando un archivo CSV o Excel con una columna llamada 'CUIT'.
2. Ingresando una lista de CUITs/CUILs/CDIs separados por comas.
""")

# Inicializar variables de estado si no existen
if 'df_resultados_cache' not in st.session_state:
    st.session_state.df_resultados_cache = None

if 'cuits_texto_cache' not in st.session_state:
    st.session_state.cuits_texto_cache = ""

if 'consulta_realizada' not in st.session_state:
    st.session_state.consulta_realizada = False

# Opciones de consulta múltiple
opcion_multiple = st.radio("Seleccione método de entrada", ["Archivo CSV/Excel", "Lista de CUIT/CUIL/CDI"])

if opcion_multiple == "Archivo CSV/Excel":
    uploaded_file = st.file_uploader("Cargar archivo CSV o Excel", type=["csv", "xlsx"])
    consultar_archivo = st.button("Consultar Archivo")
    
    if consultar_archivo and uploaded_file is not None:
        st.subheader("Procesando archivo de múltiples CUIT/CUIL/CDI")
        
        try:
            # Detectar tipo de archivo
            if uploaded_file.name.endswith('.csv'):
                df_cuits = pd.read_csv(uploaded_file)
            else:  # Excel
                df_cuits = pd.read_excel(uploaded_file)
            
            # Verificar que el archivo tenga la columna de CUIT
            if 'CUIT' not in df_cuits.columns:
                st.error("El archivo debe contener una columna llamada 'CUIT'")
            else:
                # Preparar lista de CUITs para procesar
                cuits_texto = ','.join(df_cuits['CUIT'].astype(str).tolist())
                
                # Solo procesar si ha cambiado la lista de CUITs o no hay resultados en caché
                if cuits_texto != st.session_state.cuits_texto_cache or st.session_state.df_resultados_cache is None:
                    # Procesar la lista de CUITs
                    df_resultados = procesar_lista_cuits(cuits_texto)
                    
                    # Guardar en caché
                    st.session_state.df_resultados_cache = df_resultados
                    st.session_state.cuits_texto_cache = cuits_texto
                    st.session_state.consulta_realizada = True
                
                # Usar resultados de caché
                if st.session_state.df_resultados_cache is not None and not st.session_state.df_resultados_cache.empty:
                    # Mostrar resultados en formato visual
                    mostrar_resultados_multiple_cuits(st.session_state.df_resultados_cache)
                    
                    # Permitir consulta detallada de un CUIT específico
                    st.markdown("---")
                    st.subheader("Consulta Detallada de un CUIT específico")
                    
                    cuits_disponibles = st.session_state.df_resultados_cache['CUIT'].tolist()
                    cuit_seleccionado = st.selectbox(
                        "Seleccione un CUIT para ver detalles completos",
                        options=cuits_disponibles,
                        format_func=lambda x: f"{x} - {st.session_state.df_resultados_cache[st.session_state.df_resultados_cache['CUIT']==x]['Denominación'].values[0]}"
                    )
                    
                    if st.button("Ver Detalles Completos", key="btn_detalles_archivo"):
                        if cuit_seleccionado:
                            st.markdown(f"### Detalles completos para {cuit_seleccionado}")
                            st.markdown(f"**Denominación:** {st.session_state.df_resultados_cache[st.session_state.df_resultados_cache['CUIT']==cuit_seleccionado]['Denominación'].values[0]}")
                            
                            # Mostrar información detallada
                            with st.spinner(f"Consultando información detallada para {cuit_seleccionado}..."):
                                # Obtener y mostrar deudas actuales
                                datos_deudas = obtener_deudas(cuit_seleccionado)
                                if datos_deudas:
                                    df_deudas = procesar_deudas(datos_deudas)
                                    if df_deudas is not None:
                                        st.subheader("Deudas Actuales")
                                        st.dataframe(df_deudas)
                                
                                # Obtener y mostrar deudas históricas
                                datos_historicos = obtener_deudas_historicas(cuit_seleccionado)
                                if datos_historicos:
                                    df_historico = procesar_deudas_historicas(datos_historicos)
                                    if df_historico is not None:
                                        st.subheader("Deudas Históricas")
                                        st.dataframe(df_historico)
                                
                                # Obtener y mostrar cheques rechazados
                                datos_cheques = obtener_cheques_rechazados(cuit_seleccionado)
                                if datos_cheques:
                                    df_cheques = procesar_cheques_rechazados(datos_cheques)
                                    if df_cheques is not None:
                                        st.subheader("Cheques Rechazados")
                                        st.dataframe(df_cheques)
        
        except Exception as e:
            st.error(f"Error al procesar el archivo: {str(e)}")

else:  # Opción Lista de CUIT/CUIL/CDI
    cuits_lista = st.text_area("Ingrese CUIT/CUIL/CDI separados por comas", st.session_state.cuits_texto_cache)
    consultar_lista = st.button("Consultar Lista")
    
    if consultar_lista and cuits_lista:
        # Solo procesar si ha cambiado la lista de CUITs o no hay resultados en caché
        if cuits_lista != st.session_state.cuits_texto_cache or st.session_state.df_resultados_cache is None:
            # Procesar la lista de CUITs
            df_resultados = procesar_lista_cuits(cuits_lista)
            
            # Guardar en caché
            st.session_state.df_resultados_cache = df_resultados
            st.session_state.cuits_texto_cache = cuits_lista
            st.session_state.consulta_realizada = True
    
    # Si ya se realizó una consulta previamente, mostrar los resultados
    if st.session_state.consulta_realizada and st.session_state.df_resultados_cache is not None:
        # Mostrar resultados en formato visual
        mostrar_resultados_multiple_cuits(st.session_state.df_resultados_cache)
        
        # Permitir consulta detallada de un CUIT específico
        st.markdown("---")
        st.subheader("Consulta Detallada de un CUIT específico")
        
        cuits_disponibles = st.session_state.df_resultados_cache['CUIT'].tolist()
        cuit_seleccionado = st.selectbox(
            "Seleccione un CUIT para ver detalles completos",
            options=cuits_disponibles,
            format_func=lambda x: f"{x} - {st.session_state.df_resultados_cache[st.session_state.df_resultados_cache['CUIT']==x]['Denominación'].values[0] if st.session_state.df_resultados_cache[st.session_state.df_resultados_cache['CUIT']==x]['Denominación'].values[0] else x}"
        )
        
        if st.button("Ver Detalles Completos", key="btn_detalles_lista"):
            if cuit_seleccionado:
                st.markdown(f"### Detalles completos para {cuit_seleccionado}")
                denominacion = st.session_state.df_resultados_cache[st.session_state.df_resultados_cache['CUIT']==cuit_seleccionado]['Denominación'].values[0]
                if denominacion:
                    st.markdown(f"**Denominación:** {denominacion}")
                
                # Mostrar información detallada
                with st.spinner(f"Consultando información detallada para {cuit_seleccionado}..."):
                    # Obtener y mostrar deudas actuales
                    datos_deudas = obtener_deudas(cuit_seleccionado)
                    if datos_deudas:
                        df_deudas = procesar_deudas(datos_deudas)
                        if df_deudas is not None:
                            st.subheader("Deudas Actuales")
                            st.dataframe(df_deudas)
                    
                    # Obtener y mostrar deudas históricas
                    datos_historicos = obtener_deudas_historicas(cuit_seleccionado)
                    if datos_historicos:
                        df_historico = procesar_deudas_historicas(datos_historicos)
                        if df_historico is not None:
                            st.subheader("Deudas Históricas")
                            st.dataframe(df_historico)
                    
                    # Obtener y mostrar cheques rechazados
                    datos_cheques = obtener_cheques_rechazados(cuit_seleccionado)
                    if datos_cheques:
                        df_cheques = procesar_cheques_rechazados(datos_cheques)
                        if df_cheques is not None:
                            st.subheader("Cheques Rechazados")
                            st.dataframe(df_cheques)

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