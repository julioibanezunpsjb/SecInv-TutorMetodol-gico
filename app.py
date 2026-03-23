# -*- coding: utf-8 -*-
"""
Mentor Epistemológico v6 - Streamlit
Sistema de tutor metodológico para investigación en Ciencias Económicas
Mejorado con acompañamiento pedagógico para investigadores novatos
"""

import streamlit as st
from database import Database
from gemini_api import GeminiAPI
from export import export_to_word
import time
from datetime import datetime
from typing import Optional, Dict, List, Any

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE PÁGINA
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Mentor Epistemológico",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES Y CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

# Áreas de investigación (ordenadas alfabéticamente)
AREAS_INVESTIGACION = [
    "Administración",
    "Comercio Internacional",
    "Contabilidad",
    "Criptomonedas/Fintech",
    "Derecho",
    "Economía",
    "Economía Ambiental/Sustentabilidad",
    "Finanzas",
    "Geografía",
    "Historia",
    "Marketing",
    "Recursos Humanos",
    "Turismo",
    "Otra Ciencia Social (especificar)"
]

# Pasos del proceso de investigación
PASOS_INVESTIGACION = {
    0: {"nombre": "💡 Inicio", "descripcion": "Tormenta de ideas"},
    1: {"nombre": "📝 Título", "descripcion": "Título provisional"},
    2: {"nombre": "❓ Problema", "descripcion": "Delimitación del objeto de estudio"},
    3: {"nombre": "🎯 Objetivos", "descripcion": "General y específicos"},
    4: {"nombre": "❗ Hipótesis", "descripcion": "Respuestas tentativas"},
    5: {"nombre": "📚 Marco Teórico", "descripcion": "Fundamentos conceptuales"},
    6: {"nombre": "📐 Metodología", "descripcion": "Diseño y métodos"},
    7: {"nombre": "📊 Finalizar", "descripcion": "Revisión y exportación"}
}

# Glosario metodológico
GLOSARIO_METODOLOGICO = {
    "Problema de Investigación": {
        "definicion": "Interrogante claro y preciso que guía toda la investigación. Debe ser factible de responder mediante métodos científicos.",
        "ejemplo_correcto": "¿Cómo influye la inflación en las decisiones de consumo de las familias de clase media en Buenos Aires durante 2023-2024?",
        "ejemplo_incorrecto": "¿Por qué la economía está mal?"
    },
    "Hipótesis": {
        "definicion": "Respuesta tentativa al problema de investigación, expresada en forma de proposición verificable empíricamente.",
        "ejemplo_correcto": "Las familias de clase media reducen su consumo de bienes no esenciales en un 15% cuando la inflación supera el 50% anual.",
        "ejemplo_incorrecto": "La inflación afecta a todos."
    },
    "Objetivo General": {
        "definicion": "Meta principal de la investigación que establece qué se pretende lograr. Se formula con un verbo en infinitivo.",
        "ejemplo_correcto": "Analizar el impacto de la inflación en los patrones de consumo de las familias de clase media porteñas.",
        "ejemplo_incorrecto": "Estudiar la economía"
    },
    "Objetivos Específicos": {
        "definicion": "Metas parciales que desglosan el objetivo general. Cada uno debe ser medible y alcanzable.",
        "ejemplo_correcto": "1) Identificar los bienes de consumo con mayor sensibilidad a la inflación. 2) Comparar patrones de consumo antes y después de picos inflacionarios.",
        "ejemplo_incorrecto": "Ver qué pasa con los precios"
    },
    "Marco Teórico": {
        "definicion": "Conjunto de teorías, conceptos y antecedentes que sustentan la investigación.",
        "ejemplo_correcto": "Revisión de teorías sobre comportamiento del consumidor (Keynes, Friedman), estudios previos sobre inflación en Argentina.",
        "ejemplo_incorrecto": "La inflación es cuando suben los precios"
    },
    "Metodología": {
        "definicion": "Conjunto de métodos, técnicas y procedimientos para recabar y analizar la información.",
        "ejemplo_correcto": "Estudio cuantitativo, diseño no experimental transversal. Población: familias de CABA. Muestra: 200 hogares.",
        "ejemplo_incorrecto": "Voy a preguntar a la gente"
    }
}

# Tooltips contextuales por campo
TOOLTIPS = {
    "titulo": {
        "titulo": "📝 Título Provisional",
        "explicacion": "El título debe incluir: variable principal, población y contexto. Ejemplo: 'Factores que influyen en la decisión de compra de consumidores millennials en tiendas online'",
        "consejo": "Evita títulos muy largos o demasiado generales. Un buen título anticipa el problema de investigación."
    },
    "problema": {
        "titulo": "❓ Formulación del Problema",
        "explicacion": "El problema se formula como pregunta. Debe incluir: población, variable(s), tiempo/espacio. Debe ser respondible con los recursos disponibles.",
        "consejo": "Un buen problema no es ni muy amplio (imposible de responder) ni muy específico (sin relevancia)."
    },
    "objetivo_general": {
        "titulo": "🎯 Objetivo General",
        "explicacion": "Verbo en infinitivo + qué + para qué. Verbos comunes: Analizar, Determinar, Evaluar, Identificar, Comparar. Evita: Estudiar, Conocer (muy vagos).",
        "consejo": "El objetivo general debe responder directamente al problema de investigación."
    },
    "objetivos_especificos": {
        "titulo": "📋 Objetivos Específicos",
        "explicacion": "Desglosan el objetivo general en metas parciales. Usualmente 3-5 objetivos. Cada uno debe ser: Específico, Medible, Alcanzable, Relevante.",
        "consejo": "Los objetivos específicos juntos deben permitir alcanzar el objetivo general."
    },
    "hipotesis": {
        "titulo": "❗ Hipótesis",
        "explicacion": "Respuesta anticipada al problema. Debe ser: Clara, Precisa, Verificable. Relaciona variables.",
        "consejo": "No toda investigación requiere hipótesis. Los estudios exploratorios pueden prescindir de ellas."
    },
    "marco_teorico": {
        "titulo": "📚 Marco Teórico",
        "explicacion": "Incluye: 1) Antecedentes (estudios previos), 2) Bases teóricas (teorías que sustentan), 3) Definición de términos básicos.",
        "consejo": "No es un resumen de libros, sino una construcción argumentativa que fundamenta tu investigación."
    },
    "metodologia": {
        "titulo": "📐 Diseño Metodológico",
        "explicacion": "Define: Tipo de estudio, Diseño, Población y muestra, Técnicas e instrumentos.",
        "consejo": "La metodología debe ser coherente con los objetivos."
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE UTILIDAD
# ═══════════════════════════════════════════════════════════════════════════════

def obtener_api_key() -> str:
    """Obtiene la API key desde secrets"""
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
        if "gemini" in st.secrets and "api_keys" in st.secrets["gemini"]:
            keys = st.secrets["gemini"]["api_keys"]
            if isinstance(keys, list) and len(keys) > 0:
                return keys[0]
    except Exception:
        pass
    return st.secrets.get("GEMINI_API_KEY", "")


def inicializar_sesion():
    """Inicializa variables de sesión necesarias"""
    if "usuario" not in st.session_state:
        st.session_state.usuario = None
    if "proyecto_actual" not in st.session_state:
        st.session_state.proyecto_actual = None
    if "paso_actual" not in st.session_state:
        st.session_state.paso_actual = 1
    if "modo_guiado" not in st.session_state:
        st.session_state.modo_guiado = True
    if "datos_proyecto" not in st.session_state:
        st.session_state.datos_proyecto = {}
    if "brainstorming_realizado" not in st.session_state:
        st.session_state.brainstorming_realizado = False
    if "ideas_sugeridas" not in st.session_state:
        st.session_state.ideas_sugeridas = []


def mostrar_progreso():
    """Muestra barra de progreso visual"""
    pasos_completados = sum(1 for k, v in st.session_state.datos_proyecto.items() 
                           if v and k not in ["brainstorming", "area", "comentarios", "intereses_iniciales", "contexto", "ideas_generadas", "idea_seleccionada", "nombre_proyecto"])
    total_pasos = 6
    porcentaje = min(100, max(0, int((pasos_completados / total_pasos) * 100)))
    
    # Crear columnas para el indicador visual
    cols = st.columns(7)
    pasos_visuales = [
        ("💡", "Inicio"),
        ("📝", "Título"),
        ("❓", "Problema"),
        ("🎯", "Objetivos"),
        ("❗", "Hipótesis"),
        ("📚", "Marco Teórico"),
        ("📊", "Final")
    ]
    
    for i, (icono, nombre) in enumerate(pasos_visuales):
        with cols[i]:
            if i == 0:
                estado = "✅" if st.session_state.brainstorming_realizado else icono
            else:
                campo = ["titulo", "problema", "objetivo_general", "hipotesis", "marco_teorico", "metodologia"][i-1]
                if i == 4:  # Hipótesis
                    estado = "✅" if st.session_state.datos_proyecto.get("hipotesis") or st.session_state.datos_proyecto.get("sin_hipotesis") else icono
                else:
                    estado = "✅" if st.session_state.datos_proyecto.get(campo) else icono
            
            st.markdown(f"<div style='text-align: center; font-size: 20px;'>{estado}</div>", unsafe_allow_html=True)
            st.caption(nombre)
    
    st.progress(porcentaje)
    st.caption(f"Progreso: {porcentaje}% completado")


def mostrar_tooltip_contextual(campo: str):
    """Muestra tooltip metodológico expandible"""
    if campo in TOOLTIPS:
        tooltip = TOOLTIPS[campo]
        with st.expander(f"📖 {tooltip['titulo']} - Guía metodológica"):
            st.markdown(f"**¿Qué es?**")
            st.info(tooltip['explicacion'])
            st.markdown(f"**💡 Consejo:** {tooltip['consejo']}")


def mostrar_ejemplos(campo: str):
    """Muestra ejemplos correctos e incorrectos"""
    terminos_relacionados = {
        "titulo": ["Problema de Investigación"],
        "problema": ["Problema de Investigación"],
        "objetivo_general": ["Objetivo General"],
        "objetivos_especificos": ["Objetivos Específicos"],
        "hipotesis": ["Hipótesis"],
        "marco_teorico": ["Marco Teórico"],
        "metodologia": ["Metodología"]
    }
    
    for termino in terminos_relacionados.get(campo, []):
        if termino in GLOSARIO_METODOLOGICO:
            info = GLOSARIO_METODOLOGICO[termino]
            with st.expander(f"📝 Ejemplos: {termino}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**✅ Ejemplo Correcto:**")
                    st.success(info["ejemplo_correcto"])
                with col2:
                    st.markdown("**❌ Ejemplo Incorrecto:**")
                    st.error(info["ejemplo_incorrecto"])
                st.markdown(f"**Definición:** {info['definicion']}")


def validar_campo(campo: str, valor: str) -> tuple:
    """Valida un campo y retorna (es_valido, mensaje)"""
    if not valor or len(valor.strip()) < 10:
        return False, "⚠️ El campo está vacío o es muy corto"
    
    validaciones = {
        "problema": lambda v: ("?" in v, "✅ Pregunta formulada" if "?" in v else "⚠️ Debe formularse como pregunta"),
        "objetivo_general": lambda v: (any(v.lower().startswith(verbo) for verbo in 
            ["analizar", "determinar", "evaluar", "identificar", "comparar", "establecer", "proponer", "diseñar"]),
            "✅ Verbo apropiado" if any(v.lower().startswith(verbo) for verbo in 
            ["analizar", "determinar", "evaluar", "identificar", "comparar", "establecer", "proponer", "diseñar"]) 
            else "⚠️ Se recomienda iniciar con verbo en infinitivo"),
        "titulo": lambda v: (20 < len(v) < 150, "✅ Longitud adecuada" if 20 < len(v) < 150 else "⚠️ Título muy corto o muy largo"),
    }
    
    if campo in validaciones:
        return validaciones[campo](valor)
    
    return True, "✅ Campo completado"


def mostrar_glosario_sidebar():
    """Muestra glosario metodológico en sidebar"""
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 📖 Glosario Metodológico")
        
        termino = st.selectbox(
            "Selecciona un término:",
            options=list(GLOSARIO_METODOLOGICO.keys()),
            key="glosario_select"
        )
        
        if termino:
            info = GLOSARIO_METODOLOGICO[termino]
            st.markdown(f"**Definición:**")
            st.info(info["definicion"])


def guardar_proyecto_automatico(db: Database):
    """Guarda automáticamente el proyecto actual"""
    if st.session_state.usuario and st.session_state.proyecto_actual:
        try:
            db.actualizar_proyecto(
                st.session_state.usuario["id"],
                st.session_state.proyecto_actual,
                st.session_state.datos_proyecto
            )
        except Exception as e:
            st.warning(f"Auto-guardado pendiente: {str(e)}")

# ═══════════════════════════════════════════════════════════════════════════════
# INTERFACES DE USUARIO
# ═══════════════════════════════════════════════════════════════════════════════

def interfaz_login(db: Database):
    """Interfaz de inicio de sesión / registro"""
    st.title("🎓 Mentor Epistemológico")
    st.markdown("### Sistema de Tutor Metodológico para Investigación en Ciencias Económicas y Ciencias Sociales")
    
    tab_login, tab_registro = st.tabs(["🔐 Iniciar Sesión", "📝 Registrarse"])
    
    with tab_login:
        st.markdown("#### Iniciar Sesión")
        email = st.text_input("📧 Email", key="login_email")
        password = st.text_input("🔑 Contraseña", type="password", key="login_password")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Ingresar", use_container_width=True):
                if email and password:
                    usuario = db.verificar_usuario(email, password)
                    if usuario:
                        st.session_state.usuario = usuario
                        st.rerun()
                    else:
                        st.error("❌ Credenciales incorrectas")
                else:
                    st.warning("⚠️ Completa todos los campos")
    
    with tab_registro:
        st.markdown("#### Crear Cuenta Nueva")
        nombre = st.text_input("👤 Nombre completo", key="reg_nombre")
        email = st.text_input("📧 Email institucional", key="reg_email")
        institucion = st.text_input("🏛️ Institución", key="reg_institucion")
        password = st.text_input("🔑 Contraseña (mínimo 6 caracteres)", type="password", key="reg_password")
        password_confirm = st.text_input("🔑 Confirmar contraseña", type="password", key="reg_password_confirm")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Crear Cuenta", use_container_width=True):
                if not all([nombre, email, password]):
                    st.error("❌ Completa todos los campos obligatorios")
                elif len(password) < 6:
                    st.error("❌ La contraseña debe tener al menos 6 caracteres")
                elif password != password_confirm:
                    st.error("❌ Las contraseñas no coinciden")
                else:
                    if db.crear_usuario(nombre, email, password, institucion):
                        st.success("✅ Cuenta creada. Ahora puedes iniciar sesión.")
                    else:
                        st.error("❌ El email ya está registrado")


def interfaz_seleccion_proyecto(db: Database):
    """Interfaz para seleccionar o crear proyecto"""
    st.title("📁 Mis Proyectos de Investigación")
    
    proyectos = db.obtener_proyectos(st.session_state.usuario["id"])
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Proyectos existentes")
        if proyectos:
            for proyecto in proyectos:
                with st.container():
                    proyecto_data = proyecto[3] if proyecto[3] else {}
                    titulo = proyecto_data.get("titulo", "Sin título")
                    fecha = proyecto[2].strftime("%d/%m/%Y") if proyecto[2] else "N/A"
                    
                    col_a, col_b = st.columns([4, 1])
                    with col_a:
                        st.markdown(f"**📄 {titulo}**")
                        st.caption(f"Última modificación: {fecha}")
                    with col_b:
                        if st.button("Abrir", key=f"abrir_{proyecto[0]}"):
                            st.session_state.proyecto_actual = proyecto[0]
                            st.session_state.datos_proyecto = proyecto_data
                            st.session_state.brainstorming_realizado = proyecto_data.get("area") is not None
                            st.session_state.paso_actual = 1
                            st.rerun()
                    st.divider()
        else:
            st.info("📭 No tienes proyectos aún. Crea uno nuevo para comenzar.")
    
    with col2:
        st.markdown("### Crear nuevo proyecto")
        nuevo_nombre = st.text_input("Nombre del proyecto", key="nuevo_proyecto_nombre")
        if st.button("🆕 Crear Proyecto", use_container_width=True):
            if nuevo_nombre:
                proyecto_id = db.crear_proyecto(st.session_state.usuario["id"], nuevo_nombre)
                if proyecto_id:
                    st.session_state.proyecto_actual = proyecto_id
                    st.session_state.datos_proyecto = {"nombre_proyecto": nuevo_nombre}
                    st.session_state.brainstorming_realizado = False
                    st.session_state.paso_actual = 0
                    st.rerun()
            else:
                st.warning("⚠️ Ingresa un nombre para el proyecto")


def interfaz_brainstorming(api: GeminiAPI, db: Database):
    """Interfaz de tormenta de ideas inicial con orientación por área"""
    st.title("🎯 Tormenta de Ideas Inicial")
    st.markdown("### Exploración del tema de investigación")
    
    st.info("""
    👋 **Bienvenido/a a la etapa inicial de tu investigación!**
    
    En esta etapa, exploraremos juntos posibles temas de investigación basándonos 
    en tu área de interés. El sistema te sugerirá ideas y te ayudará a delimitar 
    tu tema de investigación.
    """)
    
    # Selección de área
    st.markdown("#### 1️⃣ Selecciona tu área de interés:")
    
    area_seleccionada = st.selectbox(
        "Área de investigación:",
        options=AREAS_INVESTIGACION,
        key="area_investigacion",
        help="Selecciona el área general donde se enmarca tu investigación"
    )
    
    # Campo para especificar si es "Otra"
    area_especifica = ""
    if area_seleccionada == "Otra (especificar)":
        area_especifica = st.text_input(
            "Especifica el área:",
            key="area_especifica",
            placeholder="Ej: Economía de la Salud, Econometría Aplicada..."
        )
    
    # Intereses específicos
    st.markdown("#### 2️⃣ Cuéntanos sobre tus intereses:")
    
    intereses = st.text_area(
        "Describe brevemente tus intereses de investigación:",
        height=100,
        key="intereses_usuario",
        placeholder="Ejemplo: Me interesa investigar sobre el impacto del comercio electrónico en las pequeñas tiendas locales...",
        help="Incluye: contexto, observaciones, inquietudes personales o profesionales"
    )
    
    # Contexto opcional
    contexto = st.text_area(
        "Contexto adicional (opcional):",
        height=60,
        key="contexto_usuario",
        placeholder="Ej: Soy docente universitario, trabajo en el sector bancario..."
    )
    
    # Botón para generar ideas
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("💡 Generar Ideas de Investigación", use_container_width=True, type="primary"):
            if intereses:
                area_final = area_especifica if area_seleccionada == "Otra (especificar)" else area_seleccionada
                
                with st.spinner("🤔 Analizando tus intereses y generando sugerencias..."):
                    ideas = api.generar_ideas_investigacion(
                        area=area_final,
                        intereses=intereses,
                        contexto=contexto
                    )
                
                if ideas:
                    st.session_state.ideas_sugeridas = ideas
                    st.session_state.datos_proyecto["area"] = area_final
                    st.session_state.datos_proyecto["intereses_iniciales"] = intereses
                    st.session_state.datos_proyecto["contexto"] = contexto
                    st.session_state.datos_proyecto["ideas_generadas"] = ideas
                    st.success("✅ Ideas generadas exitosamente!")
                else:
                    st.error("❌ No se pudieron generar ideas. Verifica la conexión con el asistente.")
            else:
                st.warning("⚠️ Por favor, describe tus intereses de investigación.")
    
    # Mostrar ideas generadas
    if st.session_state.ideas_sugeridas:
        st.markdown("---")
        st.markdown("#### 💡 Ideas de Investigación Sugeridas")
        st.markdown("*Selecciona una idea o combínalas para desarrollar tu tema:*")
        
        for i, idea in enumerate(st.session_state.ideas_sugeridas, 1):
            with st.container():
                st.markdown(f"**Opción {i}:** {idea}")
                
                col_a, col_b = st.columns([3, 1])
                with col_b:
                    if st.button(f"📌 Seleccionar", key=f"seleccionar_idea_{i}"):
                        st.session_state.datos_proyecto["idea_seleccionada"] = idea
                        st.session_state.brainstorming_realizado = True
                        guardar_proyecto_automatico(db)
                        st.session_state.paso_actual = 1
                        st.rerun()
                st.divider()
        
        # Opción para tema personalizado
        st.markdown("#### 📝 O define tu propio tema:")
        tema_personalizado = st.text_input(
            "Escribe tu tema de investigación:",
            key="tema_personalizado"
        )
        if st.button("✅ Usar este tema"):
            if tema_personalizado:
                st.session_state.datos_proyecto["idea_seleccionada"] = tema_personalizado
                st.session_state.brainstorming_realizado = True
                guardar_proyecto_automatico(db)
                st.session_state.paso_actual = 1
                st.rerun()


def interfaz_paso_titulo(api: GeminiAPI, db: Database):
    """Interfaz para el paso de título provisional"""
    st.header("📝 Paso 1: Título Provisional")
    
    mostrar_tooltip_contextual("titulo")
    mostrar_ejemplos("titulo")
    
    if st.session_state.datos_proyecto.get("idea_seleccionada"):
        st.info(f"💡 **Idea seleccionada:** {st.session_state.datos_proyecto['idea_seleccionada']}")
    
    titulo_actual = st.session_state.datos_proyecto.get("titulo", "")
    
    titulo = st.text_area(
        "Escribe tu título provisional:",
        value=titulo_actual,
        height=80,
        key="input_titulo",
        help="El título debe incluir: variable principal, población y contexto"
    )
    
    if titulo:
        es_valido, mensaje = validar_campo("titulo", titulo)
        if es_valido:
            st.success(mensaje)
        else:
            st.warning(mensaje)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🤖 Sugerir título con IA"):
            if st.session_state.datos_proyecto.get("idea_seleccionada") or titulo:
                with st.spinner("Generando sugerencias..."):
                    sugerencias = api.sugerir_titulo(
                        st.session_state.datos_proyecto.get("idea_seleccionada", ""),
                        st.session_state.datos_proyecto.get("area", ""),
                        titulo
                    )
                if sugerencias:
                    st.markdown("**Sugerencias:**")
                    for sug in sugerencias:
                        st.markdown(f"• {sug}")
            else:
                st.warning("Primero escribe un borrador de título")
    
    with col2:
        if st.button("✅ Guardar y continuar"):
            if titulo and len(titulo) > 10:
                st.session_state.datos_proyecto["titulo"] = titulo
                guardar_proyecto_automatico(db)
                st.session_state.paso_actual = 2
                st.rerun()
            else:
                st.error("El título es muy corto")


def interfaz_paso_problema(api: GeminiAPI, db: Database):
    """Interfaz para el paso de problema de investigación"""
    st.header("❓ Paso 2: Problema de Investigación")
    
    mostrar_tooltip_contextual("problema")
    mostrar_ejemplos("problema")
    
    if st.session_state.datos_proyecto.get("titulo"):
        st.info(f"📄 **Título actual:** {st.session_state.datos_proyecto['titulo']}")
    
    problema_actual = st.session_state.datos_proyecto.get("problema", "")
    
    problema = st.text_area(
        "Formula tu problema de investigación como pregunta:",
        value=problema_actual,
        height=100,
        key="input_problema",
        help="El problema debe ser una pregunta clara y delimitada"
    )
    
    if problema:
        es_valido, mensaje = validar_campo("problema", problema)
        if es_valido:
            st.success(mensaje)
        else:
            st.warning(mensaje)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("🤖 Ayuda para formular"):
            with st.spinner("Generando orientación..."):
                ayuda = api.ayudar_problema(
                    st.session_state.datos_proyecto.get("titulo", ""),
                    problema
                )
            if ayuda:
                st.markdown("**Orientación:**")
                st.info(ayuda)
    
    with col2:
        if st.button("🤖 Ejemplos similares"):
            with st.spinner("Buscando ejemplos..."):
                ejemplos = api.generar_ejemplos_problema(
                    st.session_state.datos_proyecto.get("area", "ciencias económicas")
                )
            if ejemplos:
                st.markdown("**Ejemplos de problemas bien formulados:**")
                for ej in ejemplos:
                    st.markdown(f"• {ej}")
    
    with col3:
        if st.button("✅ Guardar y continuar"):
            if problema and len(problema) > 15:
                st.session_state.datos_proyecto["problema"] = problema
                guardar_proyecto_automatico(db)
                st.session_state.paso_actual = 3
                st.rerun()
            else:
                st.error("El problema está incompleto")


def interfaz_paso_objetivos(api: GeminiAPI, db: Database):
    """Interfaz para el paso de objetivos"""
    st.header("🎯 Paso 3: Objetivos de Investigación")
    
    tab_og, tab_oe = st.tabs(["🎯 Objetivo General", "📋 Objetivos Específicos"])
    
    with tab_og:
        mostrar_tooltip_contextual("objetivo_general")
        mostrar_ejemplos("objetivo_general")
        
        if st.session_state.datos_proyecto.get("problema"):
            st.info(f"❓ **Problema:** {st.session_state.datos_proyecto['problema']}")
        
        og_actual = st.session_state.datos_proyecto.get("objetivo_general", "")
        objetivo_general = st.text_area(
            "Escribe el objetivo general:",
            value=og_actual,
            height=80,
            key="input_obj_general"
        )
        
        if objetivo_general:
            es_valido, mensaje = validar_campo("objetivo_general", objetivo_general)
            if es_valido:
                st.success(mensaje)
            else:
                st.warning(mensaje)
        
        if st.button("🤖 Sugerir objetivo general"):
            with st.spinner("Generando..."):
                sugerencia = api.sugerir_objetivo_general(
                    st.session_state.datos_proyecto.get("problema", ""),
                    objetivo_general
                )
            if sugerencia:
                st.info(f"**Sugerencia:** {sugerencia}")
    
    with tab_oe:
        mostrar_tooltip_contextual("objetivos_especificos")
        mostrar_ejemplos("objetivos_especificos")
        
        oe_actual = st.session_state.datos_proyecto.get("objetivos_especificos", "")
        objetivos_especificos = st.text_area(
            "Escribe los objetivos específicos (uno por línea):",
            value=oe_actual,
            height=120,
            key="input_obj_especificos",
            help="Generalmente se formulan entre 3 y 5 objetivos específicos"
        )
        
        if st.button("🤖 Sugerir objetivos específicos"):
            with st.spinner("Generando..."):
                sugerencias = api.sugerir_objetivos_especificos(
                    st.session_state.datos_proyecto.get("objetivo_general", ""),
                    objetivos_especificos
                )
            if sugerencias:
                st.markdown("**Sugerencias:**")
                for sug in sugerencias:
                    st.markdown(f"• {sug}")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("⬅️ Volver al problema"):
            st.session_state.paso_actual = 2
            st.rerun()
    with col3:
        if st.button("✅ Guardar y continuar"):
            if objetivo_general:
                st.session_state.datos_proyecto["objetivo_general"] = objetivo_general
                st.session_state.datos_proyecto["objetivos_especificos"] = objetivos_especificos
                guardar_proyecto_automatico(db)
                st.session_state.paso_actual = 4
                st.rerun()
            else:
                st.error("El objetivo general es obligatorio")


def interfaz_paso_hipotesis(api: GeminiAPI, db: Database):
    """Interfaz para el paso de hipótesis"""
    st.header("❗ Paso 4: Hipótesis de Investigación")
    
    mostrar_tooltip_contextual("hipotesis")
    mostrar_ejemplos("hipotesis")
    
    if st.session_state.datos_proyecto.get("problema"):
        st.info(f"❓ **Problema:** {st.session_state.datos_proyecto['problema']}")
    
    sin_hipotesis = st.checkbox(
        "Mi investigación no requiere hipótesis (estudio exploratorio/descriptivo)",
        value=st.session_state.datos_proyecto.get("sin_hipotesis", False),
        key="check_sin_hipotesis"
    )
    
    if sin_hipotesis:
        st.session_state.datos_proyecto["sin_hipotesis"] = True
        st.info("""
        📋 **Investigación sin hipótesis:** Los estudios exploratorios y descriptivos 
        no requieren hipótesis formal. En su lugar, se formulan preguntas de investigación.
        """)
        
        justificacion = st.text_area(
            "Justifica brevemente por qué tu estudio no requiere hipótesis:",
            value=st.session_state.datos_proyecto.get("justificacion_sin_hip", ""),
            key="input_justificacion_sin_hip"
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("⬅️ Volver a objetivos"):
                st.session_state.paso_actual = 3
                st.rerun()
        with col2:
            if st.button("✅ Guardar y continuar"):
                st.session_state.datos_proyecto["justificacion_sin_hip"] = justificacion
                guardar_proyecto_automatico(db)
                st.session_state.paso_actual = 5
                st.rerun()
    else:
        st.session_state.datos_proyecto["sin_hipotesis"] = False
        
        hip_actual = st.session_state.datos_proyecto.get("hipotesis", "")
        hipotesis = st.text_area(
            "Formula tu hipótesis de investigación:",
            value=hip_actual,
            height=100,
            key="input_hipotesis"
        )
        
        st.markdown("#### Variables de la hipótesis:")
        
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            var_indep = st.text_input(
                "Variable independiente:",
                value=st.session_state.datos_proyecto.get("variable_independiente", ""),
                key="input_var_indep"
            )
        with col_v2:
            var_dep = st.text_input(
                "Variable dependiente:",
                value=st.session_state.datos_proyecto.get("variable_dependiente", ""),
                key="input_var_dep"
            )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🤖 Ayuda para formular hipótesis"):
                with st.spinner("Generando orientación..."):
                    ayuda = api.ayudar_hipotesis(
                        st.session_state.datos_proyecto.get("problema", ""),
                        st.session_state.datos_proyecto.get("objetivo_general", ""),
                        hipotesis
                    )
                if ayuda:
                    st.info(ayuda)
        
        with col2:
            if st.button("✅ Guardar y continuar"):
                if hipotesis:
                    st.session_state.datos_proyecto["hipotesis"] = hipotesis
                    st.session_state.datos_proyecto["variable_independiente"] = var_indep
                    st.session_state.datos_proyecto["variable_dependiente"] = var_dep
                    guardar_proyecto_automatico(db)
                    st.session_state.paso_actual = 5
                    st.rerun()
                else:
                    st.error("Debes formular una hipótesis o indicar que tu estudio no la requiere")
    
    if not sin_hipotesis:
        if st.button("⬅️ Volver a objetivos"):
            st.session_state.paso_actual = 3
            st.rerun()


def interfaz_paso_marco_teorico(api: GeminiAPI, db: Database):
    """Interfaz para el paso de marco teórico"""
    st.header("📚 Paso 5: Marco Teórico")
    
    mostrar_tooltip_contextual("marco_teorico")
    mostrar_ejemplos("marco_teorico")
    
    st.markdown("""
    El marco teórico comprende tres componentes principales:
    1. **Antecedentes**: Estudios previos relacionados
    2. **Bases teóricas**: Teorías y modelos que sustentan la investigación
    3. **Definición de términos**: Conceptos clave operacionalizados
    """)
    
    st.subheader("1. Antecedentes de la Investigación")
    antecedentes = st.text_area(
        "Describe los estudios previos relevantes:",
        value=st.session_state.datos_proyecto.get("antecedentes", ""),
        height=120,
        key="input_antecedentes",
        help="Incluye: autor, año, hallazgos principales y su relación con tu estudio"
    )
    
    st.subheader("2. Bases Teóricas")
    bases_teoricas = st.text_area(
        "Describe las teorías y modelos que sustentan tu investigación:",
        value=st.session_state.datos_proyecto.get("bases_teoricas", ""),
        height=120,
        key="input_bases_teoricas",
        help="Ej: Teoría keynesiana, Modelo de expectativas racionales..."
    )
    
    st.subheader("3. Definición de Términos Básicos")
    definiciones = st.text_area(
        "Define los conceptos clave de tu investigación:",
        value=st.session_state.datos_proyecto.get("definiciones", ""),
        height=120,
        key="input_definiciones",
        help="Incluye definiciones operacionales de tus variables principales"
    )
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🤖 Sugerir marco teórico"):
            with st.spinner("Generando sugerencias..."):
                sugerencias = api.sugerir_marco_teorico(
                    st.session_state.datos_proyecto.get("problema", ""),
                    st.session_state.datos_proyecto.get("area", ""),
                    st.session_state.datos_proyecto.get("hipotesis", "")
                )
            if sugerencias:
                st.info(sugerencias)
    
    with col2:
        if st.button("✅ Guardar y continuar"):
            st.session_state.datos_proyecto["antecedentes"] = antecedentes
            st.session_state.datos_proyecto["bases_teoricas"] = bases_teoricas
            st.session_state.datos_proyecto["definiciones"] = definiciones
            st.session_state.datos_proyecto["marco_teorico"] = f"{antecedentes}\n\n{bases_teoricas}\n\n{definiciones}"
            guardar_proyecto_automatico(db)
            st.session_state.paso_actual = 6
            st.rerun()
    
    if st.button("⬅️ Volver a hipótesis"):
        st.session_state.paso_actual = 4
        st.rerun()


def interfaz_paso_metodologia(api: GeminiAPI, db: Database):
    """Interfaz para el paso de metodología"""
    st.header("📐 Paso 6: Diseño Metodológico")
    
    mostrar_tooltip_contextual("metodologia")
    mostrar_ejemplos("metodologia")
    
    st.subheader("1. Tipo de Estudio")
    tipo_estudio = st.selectbox(
        "Selecciona el tipo de estudio:",
        options=["", "Exploratorio", "Descriptivo", "Correlacional", "Explicativo", "Experimental"],
        index=["", "Exploratorio", "Descriptivo", "Correlacional", "Explicativo", "Experimental"].index(
            st.session_state.datos_proyecto.get("tipo_estudio", "")
        ),
        key="select_tipo_estudio"
    )
    
    st.subheader("2. Diseño de Investigación")
    diseño = st.selectbox(
        "Selecciona el diseño:",
        options=["", "No experimental - Transversal", "No experimental - Longitudinal", 
                 "Experimental - Pre-experimental", "Experimental - Cuasi-experimental", 
                 "Experimental - Experimental puro"],
        index=["", "No experimental - Transversal", "No experimental - Longitudinal", 
               "Experimental - Pre-experimental", "Experimental - Cuasi-experimental", 
               "Experimental - Experimental puro"].index(
            st.session_state.datos_proyecto.get("diseño", "")
        ),
        key="select_diseño"
    )
    
    st.subheader("3. Población y Muestra")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        poblacion = st.text_area(
            "Describe la población:",
            value=st.session_state.datos_proyecto.get("poblacion", ""),
            height=80,
            key="input_poblacion"
        )
    with col_p2:
        muestra = st.text_area(
            "Describe la muestra:",
            value=st.session_state.datos_proyecto.get("muestra", ""),
            height=80,
            key="input_muestra"
        )
    
    st.subheader("4. Técnicas e Instrumentos")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        tecnicas = st.multiselect(
            "Selecciona las técnicas:",
            options=["Encuesta", "Entrevista", "Observación", "Análisis documental", 
                    "Focus group", "Análisis de datos secundarios", "Experimento"],
            default=st.session_state.datos_proyecto.get("tecnicas", []),
            key="multiselect_tecnicas"
        )
    with col_t2:
        instrumentos = st.text_area(
            "Describe los instrumentos:",
            value=st.session_state.datos_proyecto.get("instrumentos", ""),
            height=80,
            key="input_instrumentos"
        )
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🤖 Sugerir metodología"):
            with st.spinner("Generando sugerencias..."):
                sugerencias = api.sugerir_metodologia(
                    st.session_state.datos_proyecto.get("objetivo_general", ""),
                    st.session_state.datos_proyecto.get("problema", ""),
                    tipo_estudio
                )
            if sugerencias:
                st.info(sugerencias)
    
    with col2:
        if st.button("✅ Guardar y finalizar"):
            st.session_state.datos_proyecto["tipo_estudio"] = tipo_estudio
            st.session_state.datos_proyecto["diseño"] = diseño
            st.session_state.datos_proyecto["poblacion"] = poblacion
            st.session_state.datos_proyecto["muestra"] = muestra
            st.session_state.datos_proyecto["tecnicas"] = tecnicas
            st.session_state.datos_proyecto["instrumentos"] = instrumentos
            st.session_state.datos_proyecto["metodologia"] = f"Tipo: {tipo_estudio}, Diseño: {diseño}"
            guardar_proyecto_automatico(db)
            st.session_state.paso_actual = 7
            st.rerun()
    
    if st.button("⬅️ Volver a marco teórico"):
        st.session_state.paso_actual = 5
        st.rerun()


def interfaz_finalizacion(db: Database):
    """Interfaz de finalización y exportación"""
    st.header("📊 Finalización del Proyecto")
    
    st.markdown("### Resumen de tu proyecto de investigación")
    
    datos = st.session_state.datos_proyecto
    
    with st.expander("📄 Ver resumen completo", expanded=True):
        st.markdown(f"""
        **Área:** {datos.get('area', 'No especificada')}
        
        **Título:** {datos.get('titulo', 'No definido')}
        
        **Problema:** {datos.get('problema', 'No definido')}
        
        **Objetivo General:** {datos.get('objetivo_general', 'No definido')}
        
        **Hipótesis:** {datos.get('hipotesis', 'No definida') if not datos.get('sin_hipotesis') else 'Sin hipótesis (estudio exploratorio/descriptivo)'}
        
        **Marco Teórico:** {'Definido' if datos.get('marco_teorico') else 'Pendiente'}
        
        **Metodología:** {'Definida' if datos.get('metodologia') else 'Pendiente'}
        """)
    
    campos_completados = sum(1 for k in ['titulo', 'problema', 'objetivo_general', 'hipotesis', 'marco_teorico', 'metodologia'] 
                            if datos.get(k) or (k == 'hipotesis' and datos.get('sin_hipotesis')))
    porcentaje = int((campos_completados / 6) * 100)
    
    st.progress(porcentaje)
    st.markdown(f"**Progreso: {porcentaje}%**")
    
    if porcentaje < 100:
        st.warning("⚠️ Tu proyecto está incompleto. Puedes continuar editando o exportar lo que tienes.")
    
    st.markdown("### 📥 Exportar Proyecto")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Exportar a Word", use_container_width=True, type="primary"):
            with st.spinner("Generando documento..."):
                archivo = export_to_word(datos)
                if archivo:
                    st.success("✅ Documento generado exitosamente")
                    with open(archivo, "rb") as f:
                        st.download_button(
                            label="⬇️ Descargar Documento Word",
                            data=f,
                            file_name=f"proyecto_investigacion_{datetime.now().strftime('%Y%m%d')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
    
    with col2:
        if st.button("⬅️ Volver a metodología"):
            st.session_state.paso_actual = 6
            st.rerun()


def interfaz_principal(api: GeminiAPI, db: Database):
    """Interfaz principal del usuario autenticado"""
    
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.usuario['nombre']}")
        st.caption(f"📧 {st.session_state.usuario['email']}")
        
        st.markdown("---")
        
        st.markdown("### 📍 Navegación")
        
        mostrar_progreso()
        
        st.markdown("---")
        
        paso_seleccionado = st.selectbox(
            "Ir al paso:",
            options=list(PASOS_INVESTIGACION.keys()),
            format_func=lambda x: PASOS_INVESTIGACION[x]["nombre"],
            index=st.session_state.paso_actual,
            key="navegacion_pasos"
        )
        
        if paso_seleccionado != st.session_state.paso_actual:
            st.session_state.paso_actual = paso_seleccionado
            st.rerun()
        
        st.markdown("---")
        
        if st.button("📁 Cambiar Proyecto"):
            st.session_state.proyecto_actual = None
            st.session_state.datos_proyecto = {}
            st.session_state.paso_actual = 0
            st.rerun()
        
        if st.button("🚪 Cerrar Sesión"):
            st.session_state.usuario = None
            st.session_state.proyecto_actual = None
            st.session_state.datos_proyecto = {}
            st.rerun()
        
        mostrar_glosario_sidebar()
    
    paso = st.session_state.paso_actual
    
    if paso == 0:
        interfaz_brainstorming(api, db)
    elif paso == 1:
        interfaz_paso_titulo(api, db)
    elif paso == 2:
        interfaz_paso_problema(api, db)
    elif paso == 3:
        interfaz_paso_objetivos(api, db)
    elif paso == 4:
        interfaz_paso_hipotesis(api, db)
    elif paso == 5:
        interfaz_paso_marco_teorico(api, db)
    elif paso == 6:
        interfaz_paso_metodologia(api, db)
    elif paso == 7:
        interfaz_finalizacion(db)


# ═══════════════════════════════════════════════════════════════════════════════
# APLICACIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Función principal de la aplicación"""
    
    inicializar_sesion()
    
    api_key = obtener_api_key()
    
    if not api_key:
        st.error("❌ Error de configuración: API Key no encontrada. Configure GEMINI_API_KEY en los secrets de Streamlit Cloud.")
        st.info("""
        **Instrucciones para configurar la API Key:**
        1. Ve a tu app en Streamlit Cloud
        2. Click en "Settings" → "Secrets"
        3. Agrega: `GEMINI_API_KEY = "tu-api-key-aqui"`
        4. Guarda y reinicia la app
        """)
        return
    
    try:
        db = Database()
        api = GeminiAPI(api_key)
    except Exception as e:
        st.error(f"❌ Error al inicializar servicios: {str(e)}")
        return
    
    if not st.session_state.usuario:
        interfaz_login(db)
    elif not st.session_state.proyecto_actual:
        interfaz_seleccion_proyecto(db)
    else:
        interfaz_principal(api, db)


if __name__ == "__main__":
    main()
