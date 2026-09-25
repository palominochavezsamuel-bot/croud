"""
Backend - Gestor de contraseñas (Baúl)
Actividad CRUD en Python-Flask - SENA

Este módulo expone una API REST con operaciones CRUD (Crear, Leer,
Actualizar, Eliminar) sobre la tabla `baul` de la base de datos
`gestor_contrasena`.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import pymysql
import bcrypt
from flasgger import Swagger

# Inicializamos la aplicación Flask
app = Flask(__name__)

# Habilitamos CORS para permitir que el frontend (otro origen/puerto)
# pueda consumir esta API sin ser bloqueado por el navegador.
CORS(app)

# Inicializamos Swagger, que genera documentación interactiva de la API
# a partir de los docstrings de cada endpoint (disponible en /apidocs).
swagger = Swagger(app)


# ---------------------------------------------------------------------------
# Conexión a la base de datos
# ---------------------------------------------------------------------------
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'gestor_contrasena')


def conectar(vhost, vuser, vpass, vdb):
    """
    Crea y retorna una conexión a la base de datos MySQL.

    Parámetros:
        vhost (str): host del servidor de base de datos.
        vuser (str): usuario de conexión.
        vpass (str): contraseña del usuario.
        vdb (str): nombre de la base de datos a usar.
    """
    conn = pymysql.connect(host=vhost, user=vuser, passwd=vpass, db=vdb, charset='utf8mb4')
    return conn


# ---------------------------------------------------------------------------
# CRUD: Consultar (Read)
# ---------------------------------------------------------------------------

# Ruta para consulta general
@app.route("/", methods=['GET'])
def consulta_general():
    """
    Consulta general del baúl de contraseñas
    ---
    responses:
      200:
        description: Lista de registros
    """
    try:
        # Se abre la conexión con la base de datos
        conn = conectar(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)
        cur = conn.cursor()
        # Se ejecuta la consulta SELECT para traer todos los registros
        cur.execute("SELECT * FROM baul")
        datos = cur.fetchall()
        data = []
        # Se recorre cada fila devuelta y se convierte en un diccionario
        # para poder serializarla fácilmente como JSON
        for row in datos:
            dato = {'id_baul': row[0], 'Plataforma': row[1], 'usuario': row[2], 'clave': row[3]}
            data.append(dato)
        cur.close()
        conn.close()
        return jsonify({'baul': data, 'mensaje': 'Baúl de contraseñas'})
    except Exception as ex:
        # Se captura cualquier error de conexión/consulta y se registra en consola
        print(ex)
        return jsonify({'mensaje': 'Error'})


# Ruta para consulta individual
@app.route("/consulta_individual/<codigo>", methods=['GET'])
def consulta_individual(codigo):
    """
    Consulta individual por ID
    ---
    parameters:
      - name: codigo
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Registro encontrado
    """
    try:
        conn = conectar(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)
        cur = conn.cursor()
        # Se usa una consulta parametrizada (%s) en lugar de f-string
        # para evitar inyección SQL al construir la sentencia.
        cur.execute("SELECT * FROM baul WHERE id_baul = %s", (codigo,))
        datos = cur.fetchone()
        cur.close()
        conn.close()
        if datos:
            dato = {'id_baul': datos[0], 'Plataforma': datos[1], 'usuario': datos[2], 'clave': datos[3]}
            return jsonify({'baul': dato, 'mensaje': 'Registro encontrado'})
        else:
            return jsonify({'mensaje': 'Registro no encontrado'})
    except Exception as ex:
        print(ex)
        return jsonify({'mensaje': 'Error'})


# ---------------------------------------------------------------------------
# CRUD: Registrar (Create)
# ---------------------------------------------------------------------------

# Ruta para registro
@app.route("/registro/", methods=['POST'])
def registro():
    """
    Registrar nueva contraseña
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            plataforma:
              type: string
            usuario:
              type: string
            clave:
              type: string
    responses:
      200:
        description: Registro agregado
    """
    try:
        # Se obtienen los datos enviados en el cuerpo de la petición (JSON)
        data = request.get_json()
        plataforma = data['plataforma']
        usuario = data['usuario']
        # La contraseña NUNCA se guarda en texto plano: se encripta con
        # bcrypt (hash + salt) antes de insertarla en la base de datos.
        clave = bcrypt.hashpw(data['clave'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        conn = conectar(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)
        cur = conn.cursor()
        cur.execute("INSERT INTO baul (plataforma, usuario, clave) VALUES (%s, %s, %s)",
                    (plataforma, usuario, clave))
        # commit() confirma la transacción y persiste los cambios
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensaje': 'Registro agregado'})
    except Exception as ex:
        print(ex)
        return jsonify({'mensaje': 'Error'})


# ---------------------------------------------------------------------------
# CRUD: Eliminar (Delete)
# ---------------------------------------------------------------------------

# Ruta para eliminar registro
@app.route("/eliminar/<codigo>", methods=['DELETE'])
def eliminar(codigo):
    """
    Eliminar registro por ID
    ---
    parameters:
      - name: codigo
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Registro eliminado
    """
    try:
        conn = conectar(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)
        cur = conn.cursor()
        # Se elimina el registro cuyo id coincide con el código recibido
        cur.execute("DELETE FROM baul WHERE id_baul = %s", (codigo,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensaje': 'Eliminado'})
    except Exception as ex:
        print(ex)
        return jsonify({'mensaje': 'Error'})


# ---------------------------------------------------------------------------
# CRUD: Actualizar (Update)
# ---------------------------------------------------------------------------

# Ruta para actualizar registro
@app.route("/actualizar/<codigo>", methods=['PUT'])
def actualizar(codigo):
    """
    Actualizar registro por ID
    ---
    parameters:
      - name: codigo
        in: path
        required: true
        type: integer
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            plataforma:
              type: string
            usuario:
              type: string
            clave:
              type: string
    responses:
      200:
        description: Registro actualizado
    """
    try:
        data = request.get_json()
        plataforma = data['plataforma']
        usuario = data['usuario']
        # Se vuelve a encriptar la clave antes de actualizarla en la BD
        clave = bcrypt.hashpw(data['clave'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        conn = conectar(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)
        cur = conn.cursor()
        cur.execute("UPDATE baul SET plataforma = %s, usuario = %s, clave = %s WHERE id_baul = %s",
                    (plataforma, usuario, clave, codigo))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensaje': 'Registro actualizado'})
    except Exception as ex:
        print(ex)
        return jsonify({'mensaje': 'Error'})


# ---------------------------------------------------------------------------
# Punto de entrada de la aplicación
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    # debug=True habilita el recargado automático y mensajes de error
    # detallados; se debe desactivar en un entorno de producción.
    app.run(debug=True)
