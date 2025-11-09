from flask import Flask, request, render_template_string, redirect, g
import sqlite3
import os

app_segura = Flask(__name__)
DATABASE_SEGURA = 'db_segura.db'
USUARIO_ADMIN = 'admin'
PASS_ADMIN = 'ypf2025'

# --- Configuración de Base de Datos ---

def get_db_segura():
    # Inicializa la conexión a la base de datos
    db = getattr(g, '_database_segura', None)
    if db is None:
        db = g._database_segura = sqlite3.connect(DATABASE_SEGURA)
        db.row_factory = sqlite3.Row
    return db

@app_segura.teardown_appcontext
def close_connection_segura(exception):
    # Cierra la conexión al finalizar la solicitud
    db = getattr(g, '_database_segura', None)
    if db is not None:
        db.close()

def init_db_segura():
    # Crea la tabla de usuarios y añade un usuario administrador de prueba
    with app_segura.app_context():
        db = get_db_segura()
        cursor = db.cursor()
        cursor.execute("DROP TABLE IF EXISTS usuarios")
        cursor.execute("CREATE TABLE usuarios (username TEXT, password TEXT)")
        # Insertamos el usuario que el atacante quiere suplantar
        cursor.execute("INSERT INTO usuarios (username, password) VALUES (?, ?)", (USUARIO_ADMIN, PASS_ADMIN))
        db.commit()

# --- Plantilla HTML (Reutilizada) ---

HTML_LOGIN_SEGURO = """
<!DOCTYPE html>
<html>
<head>
    <title>Login SEGURO</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 flex items-center justify-center min-h-screen">
    <div class="bg-white p-8 rounded-lg shadow-xl w-96">
        <h1 class="text-3xl font-bold mb-6 text-center text-green-600">Login - SEGURO</h1>
        
        <!-- Muestra el estado del login -->
        {% if mensaje %}
            <div class="mb-4 p-3 rounded-lg text-sm {% if 'ÉXITO' in mensaje %}bg-green-100 text-green-700{% else %}bg-red-100 text-red-700{% endif %}">
                {{ mensaje }}
            </div>
        {% endif %}

        <form method="POST" action="/seguro">
            <div class="mb-4">
                <label for="username" class="block text-gray-700 text-sm font-semibold mb-2">Usuario:</label>
                <input type="text" id="username" name="username" class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500" required>
            </div>
            <div class="mb-6">
                <label for="password" class="block text-gray-700 text-sm font-semibold mb-2">Contraseña:</label>
                <input type="password" id="password" name="password" class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500" required>
            </div>
            <button type="submit" class="w-full bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 transition duration-200 font-bold">
                Iniciar Sesión
            </button>
        </form>
    </div>
    <p class="absolute bottom-4 right-4 text-xs text-gray-500">Credenciales de prueba: {{ admin_user }}/{{ admin_pass }}</p>
</body>
</html>
"""

# --- Lógica de Autenticación SEGURA ---

@app_segura.route("/seguro", methods=["GET", "POST"])
def login_seguro():
    mensaje = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        db = get_db_segura()
        
        # LA SOLUCIÓN: Usar parámetros '?' en la consulta y pasar los datos 
        #    como una tupla separada (consultas parametrizadas).
        query = "SELECT username FROM usuarios WHERE username = ? AND password = ?"
        
        cursor = db.cursor()
        # Ejecución segura: la DB trata 'admin' -- ' como un valor literal, NO como código.
        cursor.execute(query, (username, password)) 
        
        user = cursor.fetchone()
        
        if user:
            mensaje = f"ÉXITO: Autenticación exitosa para el usuario: {user['username']}"
        else:
            mensaje = "FALLO: Credenciales inválidas o no encontrado."

    return render_template_string(HTML_LOGIN_SEGURO, 
                                  mensaje=mensaje, 
                                  admin_user=USUARIO_ADMIN, 
                                  admin_pass=PASS_ADMIN)

if __name__ == "__main__":
    # Si el archivo de la DB no existe, lo inicializamos
    if not os.path.exists(DATABASE_SEGURA):
        init_db_segura()
    app_segura.run(port=5001, debug=True)