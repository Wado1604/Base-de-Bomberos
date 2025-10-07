from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- Conexión MySQL ---
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Bomberos12",  # 👈 tu contraseña de MySQL
        database="bomberos"
    )

# --- RUTA DE LOGIN ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE correo=%s AND password=%s", (email, password))
        usuario = cursor.fetchone()
        conn.close()

        if usuario:
            session['loggedin'] = True
            session['id'] = usuario['id']
            session['email'] = usuario['correo']
            session['rol'] = usuario['rol']

            if usuario['rol'] == 'admin':
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('usuario'))
        else:
            flash('Correo o contraseña incorrectos.', 'error')

    return render_template('login.html')

# --- ZONA ADMIN ---
@app.route('/admin')
def admin():
    if 'loggedin' in session and session['rol'] == 'admin':
        return render_template("admin.html", email=session['email'])
    return redirect(url_for('login'))

# --- ZONA USUARIO ---
@app.route('/usuario')
def usuario():
    if 'loggedin' in session and session['rol'] == 'usuario':
        return render_template("usuario.html", email=session['email'])
    return redirect(url_for('login'))

# --- Mostrar y agregar usuarios ---
@app.route("/usuarios", methods=["GET", "POST"])
def usuarios():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":
        nombre = request.form["nombre"]
        correo = request.form["correo"]
        password = request.form["password"]  # ⚠️ pendiente encriptar
        rol = request.form["rol"]

        sql = "INSERT INTO usuarios (nombre_completo, correo, password, rol) VALUES (%s, %s, %s, %s)"
        values = (nombre, correo, password, rol)
        cursor.execute(sql, values)
        db.commit()

    cursor.execute("SELECT * FROM usuarios")
    usuarios = cursor.fetchall()

    cursor.close()
    db.close()
    return render_template("usuarios.html", usuarios=usuarios)

# --- Eliminar usuario ---
@app.route("/eliminar_usuario/<int:id>", methods=["POST"])
def eliminar_usuario(id):
    db = get_db_connection()
    cursor = db.cursor()

    sql = "DELETE FROM usuarios WHERE id = %s"
    cursor.execute(sql, (id,))
    db.commit()

    cursor.close()
    db.close()
    return redirect("/usuarios")

# --- LOGOUT ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

    # ================================
# RUTAS PARA LOS MÓDULOS DEL ADMIN
# ================================

@app.route('/inventario')
def inventario():
    if 'email' in session and session['rol'] == 'admin':
        return render_template('inventario.html', email=session['email'])
    return redirect(url_for('login'))

@app.route('/telefonema')
def telefonema():
    if 'email' in session:
        return render_template('telefonema.html', email=session['email'])
    return redirect(url_for('login'))

@app.route('/servicios')
def servicios():
    if 'email' in session:
        return render_template('servicios.html', email=session['email'])
    return redirect(url_for('login'))

@app.route('/combustible')
def combustible():
    if 'email' in session and session['rol'] == 'admin':
        return render_template('combustible.html', email=session['email'])
    return redirect(url_for('login'))

@app.route('/gestion_usuarios')
def gestion_usuarios():
    if 'email' in session and session['rol'] == 'admin':
        return render_template('gestion_usuarios.html', email=session['email'])
    return redirect(url_for('login'))

@app.route('/bomberos')
def bomberos():
    return render_template('registro_bomberos.html')

@app.route('/insertar_bombero', methods=['POST'])
def insertar_bombero():
    try:
        datos = request.get_json()

        sNombre = datos.get('sNombre')
        sClave = datos.get('sClave')
        sRango = datos.get('sRango')
        tCapacitaciones = datos.get('tCapacitaciones')
        sUsuario = datos.get('sUsuario')
        bActivo = datos.get('bActivo', True)
        sDireccion = datos.get('sDireccion')
        sSangre = datos.get('sSangre')

        # ✅ Conexión usando mysql.connector
        conn = get_db_connection()
        cursor = conn.cursor()

        # Llamada al procedimiento almacenado
        cursor.callproc('sp_InsertarBombero', (
            sNombre,
            sClave,
            sRango,
            tCapacitaciones,
            sUsuario,
            bActivo,
            sDireccion,
            sSangre
        ))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'mensaje': '✅ Bombero insertado correctamente'})

    except Exception as e:
        print(f"Error al insertar bombero: {e}")
        return jsonify({'mensaje': f'❌ Error al insertar: {str(e)}'})



if __name__ == '__main__':
    app.run(debug=True)
