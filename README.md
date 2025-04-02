# VisorDeudoresBCRA

## app StreamlitCloud


## Descripción
VisorDeudoresBCRA es una aplicación web desarrollada con Streamlit que permite consultar información de deudores registrados en el Banco Central de la República Argentina (BCRA). La aplicación facilita el análisis de situaciones crediticias, deudas históricas y cheques rechazados, tanto para consultas individuales como múltiples.

## Características principales
- Consulta Individual: Análisis detallado de un CUIT/CUIL/CDI específico
- Consulta Múltiple: Procesamiento de listas de CUIT/CUIL/CDI para análisis comparativo
- Visualización de datos: Gráficos interactivos para análisis de situación crediticia
- Exportación de informes: Generación de informes en formato PDF

## Situaciones Crediticias en el BCRA
- Situación 1 - Normal: Cumplimiento de las obligaciones sin atrasos significativos
- Situación 2 - Con seguimiento especial / Riesgo bajo: Atrasos menores o pequeñas dificultades
- Situación 3 - Con problemas / Riesgo medio: Atrasos de hasta 180 días
- Situación 4 - Con alto riesgo de insolvencia / Riesgo alto: Atrasos entre 180 y 365 días
- Situación 5 - Irrecuperable: Atrasos superiores a un año o quiebra declarada
- Situación 6 - Irrecuperable por disposición técnica: Deudores en situación 5 en otras entidades


## Instalación

```
pip install -r requirements.txt
streamlit run app.py
```