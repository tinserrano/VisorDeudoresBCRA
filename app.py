import streamlit as st
import urllib3

# Suprimir advertencias SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuración de la página
st.set_page_config(
    page_title="VisorDeudoresBCRA 🔭",
    page_icon="💰",
    layout="wide"
)


# Crear un nuevo footer personalizado con texto en gris
# Ocultar completamente el footer predeterminado de Streamlit
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """

# Crear un nuevo footer personalizado con el logo de LinkedIn
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


st.title("VisorDeudoresBCRA 🔭")
st.markdown("""
Esta aplicación permite consultar información de deudores registrados en el Banco Central de la República Argentina (BCRA)
y filtrar según diferentes criterios como situación crediticia, cheques rechazados, entre otros.

### Funcionalidades disponibles:
- **Consulta Individual**: Consulta detallada de un CUIT/CUIL/CDI específico.
- **Consulta Múltiple**: Análisis de múltiples CUIT/CUIL/CDI ingresados como lista.

Seleccione una opción del menú de la izquierda para comenzar.
""")

# Agregar información adicional
st.markdown("""
### Situaciones Crediticias en el BCRA

- **Situación 1 - Normal**: Cumplimiento de las obligaciones sin atrasos significativos.
- **Situación 2 - Con seguimiento especial / Riesgo bajo**: Atrasos menores o pequeñas dificultades.
- **Situación 3 - Con problemas / Riesgo medio**: Atrasos de hasta 180 días.
- **Situación 4 - Con alto riesgo de insolvencia / Riesgo alto**: Atrasos entre 180 y 365 días.
- **Situación 5 - Irrecuperable**: Atrasos superiores a un año o quiebra declarada.
- **Situación 6 - Irrecuperable por disposición técnica**: Deudores en situación 5 en otras entidades.

### Fuente de Datos
La información proviene directamente de la API del BCRA.
""")

