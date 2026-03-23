# -*- coding: utf-8 -*-
"""
Mentor Epistemológico - Base de Datos SQLite
Manejo de usuarios y proyectos con aislamiento por usuario
"""

import sqlite3
import bcrypt
import json
from datetime import datetime
from typing import Optional, Dict, List, Any
import os


class Database:
    """
    Clase para manejar la base de datos SQLite.
    Proporciona aislamiento de datos entre usuarios.
    """
    
    def __init__(self, db_path: str = "mentor_epistemologico.db"):
        """
        Inicializa la conexión a la base de datos.
        
        Args:
            db_path: Ruta al archivo de base de datos
        """
        # Usar directorio del proyecto o directorio temporal
        if db_path == "mentor_epistemologico.db":
            # En Streamlit Cloud, usar directorio persistente si está disponible
            persist_dir = os.environ.get("STREAMLIT_SERVER_PERSIST_DIR", "")
            if persist_dir:
                db_path = os.path.join(persist_dir, db_path)
        
        self.db_path = db_path
        self._inicializar_db()
    
    def _obtener_conexion(self) -> sqlite3.Connection:
        """Obtiene una conexión a la base de datos."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _inicializar_db(self):
        """Crea las tablas si no existen."""
        conn = self._obtener_conexion()
        cursor = conn.cursor()
        
        # Tabla de usuarios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                institucion TEXT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ultimo_acceso TIMESTAMP
            )
        """)
        
        # Tabla de proyectos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proyectos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                nombre TEXT NOT NULL,
                datos_json TEXT,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        conn.close()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # MÉTODOS DE USUARIOS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def crear_usuario(self, nombre: str, email: str, password: str, 
                      institucion: str = None) -> Optional[int]:
        """
        Crea un nuevo usuario.
        
        Args:
            nombre: Nombre completo del usuario
            email: Email del usuario (único)
            password: Contraseña en texto plano
            institucion: Institución del usuario (opcional)
            
        Returns:
            ID del usuario creado o None si falla
        """
        try:
            # Hashear contraseña
            password_hash = bcrypt.hashpw(
                password.encode('utf-8'), 
                bcrypt.gensalt()
            ).decode('utf-8')
            
            conn = self._obtener_conexion()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO usuarios (nombre, email, password_hash, institucion)
                VALUES (?, ?, ?, ?)
            """, (nombre, email, password_hash, institucion))
            
            usuario_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return usuario_id
            
        except sqlite3.IntegrityError:
            # Email ya existe
            return None
        except Exception as e:
            print(f"Error al crear usuario: {str(e)}")
            return None
    
    def verificar_usuario(self, email: str, password: str) -> Optional[Dict]:
        """
        Verifica las credenciales de un usuario.
        
        Args:
            email: Email del usuario
            password: Contraseña en texto plano
            
        Returns:
            Diccionario con datos del usuario o None si las credenciales son inválidas
        """
        try:
            conn = self._obtener_conexion()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, nombre, email, institucion, password_hash
                FROM usuarios
                WHERE email = ?
            """, (email,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                # Verificar contraseña
                if bcrypt.checkpw(
                    password.encode('utf-8'), 
                    row['password_hash'].encode('utf-8')
                ):
                    # Actualizar último acceso
                    self._actualizar_ultimo_acceso(row['id'])
                    
                    return {
                        'id': row['id'],
                        'nombre': row['nombre'],
                        'email': row['email'],
                        'institucion': row['institucion']
                    }
            
            return None
            
        except Exception as e:
            print(f"Error al verificar usuario: {str(e)}")
            return None
    
    def _actualizar_ultimo_acceso(self, usuario_id: int):
        """Actualiza la fecha de último acceso del usuario."""
        try:
            conn = self._obtener_conexion()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE usuarios
                SET ultimo_acceso = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (usuario_id,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error al actualizar último acceso: {str(e)}")
    
    def obtener_usuario_por_id(self, usuario_id: int) -> Optional[Dict]:
        """
        Obtiene un usuario por su ID.
        
        Args:
            usuario_id: ID del usuario
            
        Returns:
            Diccionario con datos del usuario o None
        """
        try:
            conn = self._obtener_conexion()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, nombre, email, institucion, fecha_registro
                FROM usuarios
                WHERE id = ?
            """, (usuario_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            print(f"Error al obtener usuario: {str(e)}")
            return None
    
    # ═══════════════════════════════════════════════════════════════════════════
    # MÉTODOS DE PROYECTOS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def crear_proyecto(self, usuario_id: int, nombre: str) -> Optional[int]:
        """
        Crea un nuevo proyecto para un usuario.
        
        Args:
            usuario_id: ID del usuario propietario
            nombre: Nombre del proyecto
            
        Returns:
            ID del proyecto creado o None si falla
        """
        try:
            conn = self._obtener_conexion()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO proyectos (usuario_id, nombre, datos_json)
                VALUES (?, ?, ?)
            """, (usuario_id, nombre, json.dumps({})))
            
            proyecto_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return proyecto_id
            
        except Exception as e:
            print(f"Error al crear proyecto: {str(e)}")
            return None
    
    def obtener_proyectos(self, usuario_id: int) -> List[tuple]:
        """
        Obtiene todos los proyectos de un usuario.
        
        Args:
            usuario_id: ID del usuario
            
        Returns:
            Lista de tuplas (id, nombre, fecha_actualizacion, datos_json)
        """
        try:
            conn = self._obtener_conexion()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, nombre, fecha_actualizacion, datos_json
                FROM proyectos
                WHERE usuario_id = ?
                ORDER BY fecha_actualizacion DESC
            """, (usuario_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            proyectos = []
            for row in rows:
                datos = json.loads(row['datos_json']) if row['datos_json'] else {}
                proyectos.append((
                    row['id'],
                    row['nombre'],
                    datetime.fromisoformat(row['fecha_actualizacion']) if row['fecha_actualizacion'] else None,
                    datos
                ))
            
            return proyectos
            
        except Exception as e:
            print(f"Error al obtener proyectos: {str(e)}")
            return []
    
    def obtener_proyecto(self, proyecto_id: int, usuario_id: int) -> Optional[Dict]:
        """
        Obtiene un proyecto específico, verificando que pertenezca al usuario.
        
        Args:
            proyecto_id: ID del proyecto
            usuario_id: ID del usuario (para verificación de propiedad)
            
        Returns:
            Diccionario con datos del proyecto o None
        """
        try:
            conn = self._obtener_conexion()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, nombre, datos_json, fecha_creacion, fecha_actualizacion
                FROM proyectos
                WHERE id = ? AND usuario_id = ?
            """, (proyecto_id, usuario_id))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                datos = json.loads(row['datos_json']) if row['datos_json'] else {}
                return {
                    'id': row['id'],
                    'nombre': row['nombre'],
                    'datos': datos,
                    'fecha_creacion': row['fecha_creacion'],
                    'fecha_actualizacion': row['fecha_actualizacion']
                }
            
            return None
            
        except Exception as e:
            print(f"Error al obtener proyecto: {str(e)}")
            return None
    
    def actualizar_proyecto(self, usuario_id: int, proyecto_id: int, 
                           datos: Dict) -> bool:
        """
        Actualiza los datos de un proyecto.
        
        Args:
            usuario_id: ID del usuario (para verificación)
            proyecto_id: ID del proyecto
            datos: Diccionario con los datos a guardar
            
        Returns:
            True si se actualizó correctamente, False si no
        """
        try:
            conn = self._obtener_conexion()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE proyectos
                SET datos_json = ?, fecha_actualizacion = CURRENT_TIMESTAMP
                WHERE id = ? AND usuario_id = ?
            """, (json.dumps(datos), proyecto_id, usuario_id))
            
            affected = cursor.rowcount
            conn.commit()
            conn.close()
            
            return affected > 0
            
        except Exception as e:
            print(f"Error al actualizar proyecto: {str(e)}")
            return False
    
    def eliminar_proyecto(self, usuario_id: int, proyecto_id: int) -> bool:
        """
        Elimina un proyecto.
        
        Args:
            usuario_id: ID del usuario (para verificación)
            proyecto_id: ID del proyecto
            
        Returns:
            True si se eliminó correctamente, False si no
        """
        try:
            conn = self._obtener_conexion()
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM proyectos
                WHERE id = ? AND usuario_id = ?
            """, (proyecto_id, usuario_id))
            
            affected = cursor.rowcount
            conn.commit()
            conn.close()
            
            return affected > 0
            
        except Exception as e:
            print(f"Error al eliminar proyecto: {str(e)}")
            return False
