from flask import Flask, request, render_template_string, redirect, g
import sqlite3
import os

app = Flask(__name__)
DATABASE = 'db_insegura.db'
USUARIO_ADMIN = 'admin'
PASS_ADMIN = 'ypf2025'

# --- Configuración de Base de Datos ---

def get_db():
    # Inicializa la conexión a la base de datos
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row # Permite acceder a las columnas por nombre
    return db

@app.teardown_appcontext
def close_connection(exception):
    # Cierra la conexión al finalizar la solicitud
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    # Crea la tabla de usuarios y añade un usuario administrador de prueba
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DROP TABLE IF EXISTS usuarios")
        cursor.execute("CREATE TABLE usuarios (username TEXT, password TEXT)")
        # Insertamos el usuario que el atacante quiere suplantar
        cursor.execute("INSERT INTO usuarios (username, password) VALUES (?, ?)", (USUARIO_ADMIN, PASS_ADMIN))
        db.commit()

# --- Plantilla HTML ---

HTML_LOGIN = """
<!DOCTYPE html>
<html>
<head>
    <title>Login Inseguro</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 flex items-center justify-center min-h-screen">
    <div class="bg-white p-8 rounded-lg shadow-xl w-96">
        <h1 class="text-3xl font-bold mb-6 text-center text-red-600">Login - VULNERABLE</h1>
        
        <!-- Muestra el estado del login -->
        {% if mensaje %}
            <div class="mb-4 p-3 rounded-lg text-sm {% if 'ÉXITO' in mensaje %}bg-green-100 text-green-700{% else %}bg-red-100 text-red-700{% endif %}">
                {{ mensaje }}
            </div>
        {% endif %}

        <form method="POST" action="/">
            <div class="mb-4">
                <label for="username" class="block text-gray-700 text-sm font-semibold mb-2">Usuario:</label>
                <input type="text" id="username" name="username" class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500" required>
            </div>
            <div class="mb-6">
                <label for="password" class="block text-gray-700 text-sm font-semibold mb-2">Contraseña:</label>
                <input type="password" id="password" name="password" class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500" required>
            </div>
            <button type="submit" class="w-full bg-red-600 text-white py-2 rounded-lg hover:bg-red-700 transition duration-200 font-bold">
                Iniciar Sesión
            </button>
        </form>
    </div>
    <p class="absolute bottom-4 right-4 text-xs text-gray-500">Credenciales de prueba: {{ admin_user }}/{{ admin_pass }}</p>
</body>
</html>
"""

# --- Lógica de Autenticación VULNERABLE ---

@app.route("/", methods=["GET", "POST"])
def login_vulnerable():
    mensaje = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        db = get_db()
        
        # LA VULNERABILIDAD: Concatenación directa de la entrada del usuario en la consulta SQL
        # Si el usuario introduce ' or 1=1 -- en el campo de usuario, esto cambia la lógica SQL
        query = f"SELECT username FROM usuarios WHERE username = '{username}' AND password = '{password}'"
        
        cursor = db.cursor()
        # Ejecución de la consulta peligrosa
        cursor.execute(query) 
        
        user = cursor.fetchone()
        
        if user:
            mensaje = f"ÉXITO: Autenticación exitosa para el usuario: {user['username']}"
        else:
            mensaje = "FALLO: Credenciales inválidas o no encontrado."

    return render_template_string(HTML_LOGIN, 
                                  mensaje=mensaje, 
                                  admin_user=USUARIO_ADMIN, 
                                  admin_pass=PASS_ADMIN)

if __name__ == "__main__":
    # Si el archivo de la DB no existe, lo inicializamos
    if not os.path.exists(DATABASE):
        init_db()
    app.run(port=5000, debug=True)