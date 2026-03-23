# -*- coding: utf-8 -*-
"""
Mentor Epistemológico - Integración con Gemini API
Sistema con fallback de modelo y soporte para múltiples API keys
"""

import google.generativeai as genai
from typing import List, Optional, Dict, Any
import time


class GeminiAPI:
    """
    Cliente para interactuar con la API de Gemini.
    Incluye sistema de fallback de modelo y rotación de API keys.
    """
    
    # Configuración de modelos con orden de preferencia
    MODELOS_DISPONIBLES = [
        "gemini-2.0-flash",      # Primera opción
        "gemini-2.5-flash",      # Fallback
        "gemini-1.5-flash",      # Fallback alternativo
    ]
    
    def __init__(self, api_key: str, api_keys_adicionales: List[str] = None):
        """
        Inicializa el cliente de Gemini API.
        
        Args:
            api_key: API key principal
            api_keys_adicionales: Lista de API keys adicionales para rotación
        """
        self.api_keys = [api_key]
        if api_keys_adicionales:
            self.api_keys.extend(api_keys_adicionales)
        
        self.api_key_actual = api_key
        self.modelo_actual = self.MODELOS_DISPONIBLES[0]
        self.modelo_index = 0
        
        # Configurar con la primera API key
        self._configurar_api(api_key)
    
    def _configurar_api(self, api_key: str):
        """Configura la API de Gemini con la key especificada"""
        try:
            genai.configure(api_key=api_key)
            self.api_key_actual = api_key
        except Exception as e:
            raise Exception(f"Error al configurar API: {str(e)}")
    
    def _rotar_api_key(self) -> bool:
        """
        Rota a la siguiente API key disponible.
        
        Returns:
            True si se rotó exitosamente, False si no hay más keys
        """
        indice_actual = self.api_keys.index(self.api_key_actual)
        nuevo_indice = indice_actual + 1
        
        if nuevo_indice < len(self.api_keys):
            self._configurar_api(self.api_keys[nuevo_indice])
            return True
        return False
    
    def _cambiar_modelo(self) -> bool:
        """
        Cambia al siguiente modelo disponible (fallback).
        
        Returns:
            True si cambió de modelo, False si no hay más modelos
        """
        self.modelo_index += 1
        if self.modelo_index < len(self.MODELOS_DISPONIBLES):
            self.modelo_actual = self.MODELOS_DISPONIBLES[self.modelo_index]
            return True
        return False
    
    def _resetear_modelo(self):
        """Resetea al primer modelo disponible"""
        self.modelo_index = 0
        self.modelo_actual = self.MODELOS_DISPONIBLES[0]
    
    def _llamar_modelo(self, prompt: str, max_reintentos: int = 3) -> Optional[str]:
        """
        Realiza una llamada al modelo con sistema de reintentos y fallback.
        
        Args:
            prompt: Prompt a enviar al modelo
            max_reintentos: Número máximo de reintentos
            
        Returns:
            Respuesta del modelo o None si falla
        """
        errores = []
        
        for intento in range(max_reintentos):
            # Intentar con el modelo actual
            try:
                modelo = genai.GenerativeModel(self.modelo_actual)
                response = modelo.generate_content(prompt)
                
                if response and response.text:
                    return response.text
                    
            except Exception as e:
                error_msg = str(e).lower()
                errores.append(f"{self.modelo_actual}: {str(e)}")
                
                # Si es error de modelo no disponible o quota, intentar fallback
                if any(err in error_msg for err in ["not found", "not_available", "quota", "rate limit", "429", "503"]):
                    if self._cambiar_modelo():
                        continue  # Intentar con el siguiente modelo
                
                # Si es error de API key, rotar
                if any(err in error_msg for err in ["api_key", "unauthorized", "401", "403"]):
                    if self._rotar_api_key():
                        self._resetear_modelo()
                        continue
                
                # Si es error de rate limit, esperar y reintentar
                if "rate" in error_msg or "quota" in error_msg:
                    time.sleep(2 ** intento)  # Backoff exponencial
                    continue
        
        # Si llegamos aquí, todos los intentos fallaron
        self._resetear_modelo()  # Resetear para la próxima llamada
        return None
    
    def generar_ideas_investigacion(self, area: str, intereses: str, contexto: str = "") -> List[str]:
        """
        Genera ideas de investigación basadas en el área e intereses del usuario.
        """
        prompt = f"""
Eres un tutor metodológico experto en Ciencias Económicas. Tu tarea es ayudar a un investigador 
novato a encontrar un tema de investigación adecuado.

INFORMACIÓN DEL INVESTIGADOR:
- Área de interés: {area}
- Intereses descritos: {intereses}
- Contexto: {contexto if contexto else "No proporcionado"}

INSTRUCCIONES:
1. Genera exactamente 5 ideas de temas de investigación específicas y viables
2. Cada idea debe ser:
   - Relevante para el área de {area}
   - Factible de investigar con recursos académicos estándar
   - Específica (no demasiado amplia ni demasiado estrecha)
   - Original pero fundamentada en literatura existente
3. Las ideas deben conectarse con los intereses del investigador

FORMATO DE RESPUESTA:
IDEA 1: [Título del tema]
Justificación: [1-2 oraciones explicando la relevancia]

IDEA 2: [Título del tema]
Justificación: [1-2 oraciones]

(continuar hasta IDEA 5)

No agregues texto adicional antes o después de las ideas.
"""
        
        respuesta = self._llamar_modelo(prompt)
        
        if respuesta:
            # Parsear las ideas de la respuesta
            ideas = []
            lineas = respuesta.split("\n")
            idea_actual = ""
            
            for linea in lineas:
                linea = linea.strip()
                if linea.startswith("IDEA"):
                    if idea_actual:
                        ideas.append(idea_actual.strip())
                    idea_actual = linea.split(":", 1)[1].strip() if ":" in linea else linea
                elif idea_actual and linea:
                    idea_actual += " " + linea
            
            if idea_actual:
                ideas.append(idea_actual.strip())
            
            return ideas if ideas else [respuesta]
        
        return []
    
    def sugerir_titulo(self, idea: str, area: str, titulo_actual: str = "") -> List[str]:
        """
        Sugiere títulos para el proyecto de investigación.
        """
        prompt = f"""
Eres un tutor metodológico experto. Ayuda a formular un título académico apropiado.

CONTEXTO:
- Área: {area}
- Idea de investigación: {idea}
- Título actual: {titulo_actual if titulo_actual else "No definido"}

INSTRUCCIONES:
1. Genera 3 opciones de título bien formulados
2. Cada título debe incluir: variable principal, población, contexto
3. Los títulos deben ser académicos pero claros
4. Evita títulos excesivamente largos (máximo 20 palabras)

FORMATO:
TÍTULO 1: [título completo]
TÍTULO 2: [título completo]
TÍTULO 3: [título completo]

Solo responde con los títulos, sin explicaciones adicionales.
"""
        
        respuesta = self._llamar_modelo(prompt)
        
        if respuesta:
            titulos = []
            for linea in respuesta.split("\n"):
                linea = linea.strip()
                if linea.startswith("TÍTULO") and ":" in linea:
                    titulo = linea.split(":", 1)[1].strip()
                    if titulo:
                        titulos.append(titulo)
            return titulos if titulos else [respuesta]
        
        return []
    
    def ayudar_problema(self, titulo: str, problema_actual: str = "") -> str:
        """
        Proporciona orientación para formular el problema de investigación.
        """
        prompt = f"""
Eres un tutor metodológico experto en Ciencias Económicas. Orienta al investigador 
para formular un problema de investigación bien estructurado.

CONTEXTO:
- Título del proyecto: {titulo}
- Problema actual: {problema_actual if problema_actual else "No definido"}

INSTRUCCIONES:
1. Si hay un problema actual, evalúalo y sugiere mejoras
2. Si no hay problema, guía la formulación paso a paso
3. El problema debe formularse como pregunta clara
4. Debe incluir delimitación espacial y temporal

Responde en máximo 150 palabras, de forma directa y práctica.
"""
        
        return self._llamar_modelo(prompt) or "No se pudo generar orientación en este momento."
    
    def generar_ejemplos_problema(self, area: str) -> List[str]:
        """
        Genera ejemplos de problemas bien formulados para el área.
        """
        prompt = f"""
Eres un tutor metodológico. Genera 3 ejemplos de problemas de investigación 
bien formulados para el área de {area}.

REQUISITOS:
1. Cada problema debe formularse como pregunta
2. Debe incluir: variable, población, contexto
3. Debe ser específico y factible

FORMATO:
EJEMPLO 1: [problema formulado como pregunta]
EJEMPLO 2: [problema formulado como pregunta]
EJEMPLO 3: [problema formulado como pregunta]

Solo responde con los ejemplos.
"""
        
        respuesta = self._llamar_modelo(prompt)
        
        if respuesta:
            ejemplos = []
            for linea in respuesta.split("\n"):
                linea = linea.strip()
                if linea.startswith("EJEMPLO") and ":" in linea:
                    ejemplo = linea.split(":", 1)[1].strip()
                    if ejemplo:
                        ejemplos.append(ejemplo)
            return ejemplos if ejemplos else [respuesta]
        
        return []
    
    def sugerir_objetivo_general(self, problema: str, objetivo_actual: str = "") -> str:
        """
        Sugiere un objetivo general basado en el problema.
        """
        prompt = f"""
Eres un tutor metodológico. Sugiere un objetivo general apropiado.

CONTEXTO:
- Problema de investigación: {problema}
- Objetivo actual: {objetivo_actual if objetivo_actual else "No definido"}

INSTRUCCIONES:
1. El objetivo debe responder directamente al problema
2. Usar verbo en infinitivo (Analizar, Determinar, Evaluar, Identificar, Comparar)
3. Incluir: qué se va a hacer, sobre qué/quiénes, para qué

Responde SOLO con el objetivo general sugerido, sin explicaciones.
"""
        
        return self._llamar_modelo(prompt) or "No se pudo generar sugerencia."
    
    def sugerir_objetivos_especificos(self, objetivo_general: str, objetivos_actuales: str = "") -> List[str]:
        """
        Sugiere objetivos específicos.
        """
        prompt = f"""
Eres un tutor metodológico. Genera objetivos específicos apropiados.

CONTEXTO:
- Objetivo general: {objetivo_general}
- Objetivos específicos actuales: {objetivos_actuales if objetivos_actuales else "No definidos"}

INSTRUCCIONES:
1. Generar entre 3 y 5 objetivos específicos
2. Cada objetivo debe ser una parte del objetivo general
3. Deben ser: Específicos, Medibles, Alcanzables, Relevantes

FORMATO:
OE1: [objetivo específico 1]
OE2: [objetivo específico 2]
OE3: [objetivo específico 3]

Solo responde con los objetivos.
"""
        
        respuesta = self._llamar_modelo(prompt)
        
        if respuesta:
            objetivos = []
            for linea in respuesta.split("\n"):
                linea = linea.strip()
                if linea.startswith("OE") and ":" in linea:
                    obj = linea.split(":", 1)[1].strip()
                    if obj:
                        objetivos.append(obj)
            return objetivos if objetivos else [respuesta]
        
        return []
    
    def ayudar_hipotesis(self, problema: str, objetivo_general: str, hipotesis_actual: str = "") -> str:
        """
        Proporciona orientación para formular la hipótesis.
        """
        prompt = f"""
Eres un tutor metodológico. Orienta sobre la formulación de hipótesis.

CONTEXTO:
- Problema: {problema}
- Objetivo general: {objetivo_general}
- Hipótesis actual: {hipotesis_actual if hipotesis_actual else "No definida"}

INSTRUCCIONES:
1. La hipótesis debe ser una respuesta tentativa al problema
2. Debe relacionar variables de forma verificable
3. Si el estudio es exploratorio/descriptivo, puede no requerir hipótesis

Responde en máximo 150 palabras.
"""
        
        return self._llamar_modelo(prompt) or "No se pudo generar orientación."
    
    def sugerir_marco_teorico(self, problema: str, area: str, hipotesis: str = "") -> str:
        """
        Sugiere estructura y contenido para el marco teórico.
        """
        prompt = f"""
Eres un tutor metodológico experto en {area}. Sugiere el marco teórico apropiado.

CONTEXTO:
- Problema: {problema}
- Área: {area}
- Hipótesis: {hipotesis if hipotesis else "No definida"}

INSTRUCCIONES:
1. Sugiere 3-5 teorías o modelos relevantes
2. Indica tipos de antecedentes que debería buscar
3. Sugiere conceptos clave a definir

Responde de forma estructurada en máximo 200 palabras.
"""
        
        return self._llamar_modelo(prompt) or "No se pudo generar sugerencias."
    
    def sugerir_metodologia(self, objetivo_general: str, problema: str, tipo_estudio: str = "") -> str:
        """
        Sugiere el diseño metodológico apropiado.
        """
        prompt = f"""
Eres un tutor metodológico. Sugiere el diseño metodológico apropiado.

CONTEXTO:
- Objetivo general: {objetivo_general}
- Problema: {problema}
- Tipo de estudio indicado: {tipo_estudio if tipo_estudio else "No especificado"}

INSTRUCCIONES:
1. Valida si el tipo de estudio es coherente con los objetivos
2. Sugiere el diseño más apropiado
3. Indica técnicas de recolección de datos adecuadas

Responde de forma estructurada en máximo 200 palabras.
"""
        
        return self._llamar_modelo(prompt) or "No se pudo generar sugerencias."
