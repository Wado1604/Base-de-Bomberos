from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
import os
from datetime import date, datetime

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


def ensure_usuarios_table():
    # Disabled: table creation is managed manually in your DB. This function is a no-op now.
    return


def ensure_roles_and_admin_user():
    """
    Ensure a minimal `roles` table exists with at least an Admin and Usuario role,
    and ensure a test admin user with username 'user1' exists in `usuarios`.
    Passwords are stored in plain text here to match existing simple login flows; consider
    replacing with hashed passwords later.
    """
    # Disabled: role/user seeding should be done manually in the DB. No-op.
    return


# --- RUTA DE LOGIN ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Try to authenticate using the new `usuarios` table first
        usuario = None
        try:
            cursor.execute("SELECT * FROM usuarios WHERE semail=%s AND spassword_hash=%s", (email, password))
            usuario = cursor.fetchone()
        except Exception as e:
            # If the table doesn't exist or query fails, we'll try legacy table below
            usuario = None

        # If not found in new table, try the legacy `usuarios1` table
        if not usuario:
            try:
                cursor.execute("SELECT * FROM usuarios1 WHERE correo=%s AND password=%s", (email, password))
                usuario = cursor.fetchone()
            except Exception:
                usuario = None
        # If found, and it's from usuarios table, update last login
        if usuario and 'iusuariopk' in usuario:
            try:
                cursor.execute("UPDATE usuarios SET dultimo_login = NOW() WHERE iusuariopk = %s", (usuario['iusuariopk'],))
                conn.commit()
            except Exception as e:
                print(f"Warning: could not update last login: {e}")
        conn.close()

        # Map session fields depending on which table provided the user
        if usuario:
            # usuario from new `usuarios` table
            if 'iusuariopk' in usuario:
                # resolve role name
                try:
                    conn2 = get_db_connection()
                    cur2 = conn2.cursor()
                    cur2.execute("SELECT snombre FROM roles WHERE irolpk = %s", (usuario.get('irolpk', None),))
                    row = cur2.fetchone()
                    role_name = row[0] if row else None
                except Exception:
                    role_name = None
                finally:
                    try:
                        cur2.close()
                        conn2.close()
                    except Exception:
                        pass

                session['loggedin'] = True
                session['id'] = usuario.get('iusuariopk')
                session['email'] = usuario.get('semail') or usuario.get('susername')
                # normalize role name to lowercase so 'Admin' and 'admin' behave the same
                session['rol'] = (role_name or ('admin' if usuario.get('irolpk') == 1 else 'usuario')).lower()
                if session['rol'] == 'admin':
                    return redirect(url_for('admin'))
                else:
                    return redirect(url_for('usuario'))

        # Fallback: if usuario came from legacy table (usuarios1), keep previous behavior
        # legacy schema: id, correo, rol
        if usuario and 'id' in usuario:
            session['loggedin'] = True
            session['id'] = usuario['id']
            session['email'] = usuario.get('correo')
            session['rol'] = (usuario.get('rol') or '').lower()
            if session['rol'] == 'admin':
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('usuario'))

        if usuario:
            session['loggedin'] = True
            session['id'] = usuario['id']
            session['email'] = usuario['correo']
            session['rol'] = (usuario.get('rol') or '').lower()

            if session['rol'] == 'admin':
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
@app.route("/usuarios1", methods=["GET", "POST"])
def usuarios1():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":
        nombre = request.form["nombre"]
        correo = request.form["correo"]
        password = request.form["password"]  # ⚠️ pendiente encriptar
        rol = request.form["rol"]

        sql = "INSERT INTO usuarios1 (nombre_completo, correo, password, rol) VALUES (%s, %s, %s, %s)"
        values = (nombre, correo, password, rol)
        cursor.execute(sql, values)
        db.commit()

    cursor.execute("SELECT * FROM usuarios1")
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

# --- GESTIÓN DE USUARIOS (Nueva tabla) ---
@app.route("/gestion_usuarios", methods=["GET", "POST"])
def gestion_usuarios():
    if 'loggedin' not in session or session['rol'] != 'admin':
        return redirect(url_for('login'))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # --- Mostrar roles y bomberos para llenar el formulario ---
    cursor.execute("SELECT irolpk, snombre FROM roles")
    roles = cursor.fetchall()

    # Build firefighter full names using known column names
    cursor.execute("SELECT ibomberoPK, CONCAT(snombre, ' ', sapellido_paterno, ' ', sapellido_materno) AS nombre_completo FROM bomberos")
    bomberos = cursor.fetchall()

    # --- Registrar nuevo usuario ---
    if request.method == "POST":
        irolpk = request.form["rol"]
        ibomberopk = request.form["bombero"]
        susername = request.form["username"]
        semail = request.form["email"]
        spassword = request.form["password"]  # luego puedes aplicar hash
        sestado = "Activo"

        sql = """
        INSERT INTO usuarios (irolpk, ibomberopk, susername, semail, spassword_hash, sestado)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (irolpk, ibomberopk, susername, semail, spassword, sestado)
        cursor.execute(sql, values)
        db.commit()

        flash("Usuario registrado correctamente.", "success")
        return redirect(url_for("gestion_usuarios"))

    # --- Mostrar todos los usuarios registrados ---
    cursor.execute("""
        SELECT u.iusuariopk, u.susername, u.semail, u.sestado, 
               r.snombre AS rol, 
               CONCAT(b.snombre, ' ', b.sapellido) AS bombero
        FROM usuarios u
        LEFT JOIN roles r ON u.irolpk = r.irolpk
        LEFT JOIN bomberos b ON u.ibomberopk = b.ibomberoPK
        ORDER BY u.dcreado_en DESC
    """)
    usuarios = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("gestion_usuarios.html", usuarios=usuarios, roles=roles, bomberos=bomberos)


@app.route('/usuarios')
def usuarios_alias():
    # Backwards-compatible alias that redirects to the gestion screen for admins
    return redirect(url_for('gestion_usuarios'))


@app.route('/bomberos')
def bomberos():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM bomberos")
    rows = cursor.fetchall()
    # Normalize keys so the template and JS receive the expected field names
    def as_str(v):
        if isinstance(v, (date, datetime)):
            return v.isoformat()
        return v

    def get_first(r, *keys):
        for k in keys:
            if k in r and r[k] is not None:
                return as_str(r[k])
        return None

    def normalize(r):
        return {
            'iBomberospk': get_first(r, 'iBomberospk', 'ibomberospk', 'ibomberoPK', 'iBomberoPK', 'id'),
            'sNombre': get_first(r, 'sNombre', 'snombre', 's_nombre', 'nombre'),
            'sApellido_Paterno': get_first(r, 'sApellido_Paterno', 'sapellido_paterno', 'apellido_paterno'),
            'sApellido_Materno': get_first(r, 'sApellido_Materno', 'sapellido_materno', 'apellido_materno'),
            'dFecha_Nacimiento': get_first(r, 'dFecha_Nacimiento', 'dfecha_nacimiento', 'fecha_nacimiento'),
            'sCurp': get_first(r, 'sCurp', 'scurp', 'curp'),
            'sTelefono': get_first(r, 'sTelefono', 'stelefono', 'telefono'),
            'sCorreo': get_first(r, 'sCorreo', 'scorreo', 'correo', 'email'),
            'sDireccion': get_first(r, 'sDireccion', 'sdireccion', 'direccion'),
            'sCargo': get_first(r, 'sCargo', 'scargo', 'cargo'),
            'sTipo_Ingreso': get_first(r, 'sTipo_Ingreso', 'stipo_ingreso', 'tipo_ingreso'),
            'dFecha_Ingreso': get_first(r, 'dFecha_Ingreso', 'dfecha_ingreso', 'fecha_ingreso'),
            'sNum_Credencial': get_first(r, 'sNum_Credencial', 'snum_credencial', 'num_credencial'),
            'sEstado': get_first(r, 'sEstado', 'sestado', 'estado'),
            'sObservaciones': get_first(r, 'sObservaciones', 'sobservaciones', 'observaciones'),
            'bActivo': get_first(r, 'bActivo', 'bactivo', 'activo')
        }

    bomberos = [normalize(r) for r in rows]
    cursor.close()
    db.close()
    return render_template('registro_bomberos.html', bomberos=bomberos)


@app.route('/')
def index():
    # Redirect root to the login page so users must authenticate first
    return redirect(url_for('login'))


@app.route('/api/bomberos')
def api_bomberos():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM bomberos")
    rows = cursor.fetchall()
    cursor.close()
    db.close()

    def as_str(v):
        if isinstance(v, (date, datetime)):
            return v.isoformat()
        return v

    def get_first(r, *keys):
        for k in keys:
            if k in r and r[k] is not None:
                return as_str(r[k])
        return None

    def normalize(r):
        return {
            'iBomberospk': get_first(r, 'iBomberospk', 'ibomberospk', 'ibomberoPK', 'iBomberoPK', 'id'),
            'sNombre': get_first(r, 'sNombre', 'snombre', 's_nombre', 'nombre'),
            'sApellido_Paterno': get_first(r, 'sApellido_Paterno', 'sapellido_paterno', 'apellido_paterno'),
            'sApellido_Materno': get_first(r, 'sApellido_Materno', 'sapellido_materno', 'apellido_materno'),
            'dFecha_Nacimiento': get_first(r, 'dFecha_Nacimiento', 'dfecha_nacimiento', 'fecha_nacimiento'),
            'sCurp': get_first(r, 'sCurp', 'scurp', 'curp'),
            'sTelefono': get_first(r, 'sTelefono', 'stelefono', 'telefono'),
            'sCorreo': get_first(r, 'sCorreo', 'scorreo', 'correo', 'email'),
            'sDireccion': get_first(r, 'sDireccion', 'sdireccion', 'direccion'),
            'sCargo': get_first(r, 'sCargo', 'scargo', 'cargo'),
            'sTipo_Ingreso': get_first(r, 'sTipo_Ingreso', 'stipo_ingreso', 'tipo_ingreso'),
            'dFecha_Ingreso': get_first(r, 'dFecha_Ingreso', 'dfecha_ingreso', 'fecha_ingreso'),
            'sNum_Credencial': get_first(r, 'sNum_Credencial', 'snum_credencial', 'num_credencial'),
            'sEstado': get_first(r, 'sEstado', 'sestado', 'estado'),
            'sObservaciones': get_first(r, 'sObservaciones', 'sobservaciones', 'observaciones'),
            'bActivo': get_first(r, 'bActivo', 'bactivo', 'activo')
        }

    return jsonify([normalize(r) for r in rows])



@app.route('/insertar_bombero', methods=['POST'])
def insertar_bombero():
    # legacy/JSON endpoint kept for possible AJAX callers
    try:
        if request.is_json:
            datos = request.get_json()
            sNombre = datos.get('sNombre')
            sApellido_Paterno = datos.get('sApellido_Paterno')
            sApellido_Materno = datos.get('sApellido_Materno')
            # map other fields if provided in JSON (optional)
            sDireccion = datos.get('sDireccion')
            bActivo = datos.get('bActivo', 1)

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO bomberos (sNombre, sApellido_Paterno, sApellido_Materno, sDireccion, bActivo)
                VALUES (%s, %s, %s, %s, %s)
            """, (sNombre, sApellido_Paterno, sApellido_Materno, sDireccion, bActivo))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'mensaje': '✅ Bombero insertado correctamente'})
        else:
            # If called via normal form POST, redirect to guardar_bombero handler
            return guardar_bombero()
    except Exception as e:
        print(f"Error al insertar bombero: {e}")
        return jsonify({'mensaje': f'❌ Error al insertar: {str(e)}'})

@app.route("/bomberos_registrados")
def bomberos_registrados():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM bomberos")
    bomberos = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template("bomberos_registrados.html", bomberos=bomberos)


@app.route("/actualizar_bombero/<int:id>", methods=["POST"])
def actualizar_bombero(id):
    db = get_db_connection()
    cursor = db.cursor()

    # Use the form field names from the template
    cursor.execute("""
        UPDATE bomberos
        SET sNombre=%s,
            sApellido_Paterno=%s,
            sApellido_Materno=%s,
            dFecha_Nacimiento=%s,
            sCurp=%s,
            sTelefono=%s,
            sCorreo=%s,
            sDireccion=%s,
            sCargo=%s,
            sTipo_Ingreso=%s,
            dFecha_Ingreso=%s,
            sNum_Credencial=%s,
            sEstado=%s,
            sObservaciones=%s,
            bActivo=%s
    WHERE ibomberoPK=%s
    """, (
        request.form.get("sNombre"),
        request.form.get("sApellido_Paterno"),
        request.form.get("sApellido_Materno"),
        request.form.get("dFecha_Nacimiento"),
        request.form.get("sCurp"),
        request.form.get("sTelefono"),
        request.form.get("sCorreo"),
        request.form.get("sDireccion"),
    request.form.get("sCargo"),
    (request.form.get("sTipo_Ingreso") or '').strip()[:50],
        request.form.get("dFecha_Ingreso"),
        request.form.get("sNum_Credencial"),
    (request.form.get("sEstado") or '').strip()[:50],
        request.form.get("sObservaciones"),
        int(request.form.get("bActivo", 1)),
        id
    ))

    db.commit()
    cursor.close()
    db.close()
    flash("Datos del bombero actualizados correctamente.", "success")
    return redirect(url_for("bomberos"))


@app.route('/actualizar_bombero', methods=['POST'])
def actualizar_bombero_form():
    # Update handler that reads the id from a hidden form field named 'id'
    id_raw = request.form.get('id')
    try:
        id_val = int(id_raw)
    except (TypeError, ValueError):
        flash('ID de bombero inválido para actualizar.', 'error')
        return redirect(url_for('bomberos'))

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE bomberos
        SET sNombre=%s,
            sApellido_Paterno=%s,
            sApellido_Materno=%s,
            dFecha_Nacimiento=%s,
            sCurp=%s,
            sTelefono=%s,
            sCorreo=%s,
            sDireccion=%s,
            sCargo=%s,
            sTipo_Ingreso=%s,
            dFecha_Ingreso=%s,
            sNum_Credencial=%s,
            sEstado=%s,
            sObservaciones=%s,
            bActivo=%s
    WHERE ibomberoPK=%s
    """, (
        request.form.get("sNombre"),
        request.form.get("sApellido_Paterno"),
        request.form.get("sApellido_Materno"),
        request.form.get("dFecha_Nacimiento"),
        request.form.get("sCurp"),
        request.form.get("sTelefono"),
        request.form.get("sCorreo"),
        request.form.get("sDireccion"),
        request.form.get("sCargo"),
        (request.form.get("sTipo_Ingreso") or '').strip()[:50],
        request.form.get("dFecha_Ingreso"),
        request.form.get("sNum_Credencial"),
        (request.form.get("sEstado") or '').strip()[:50],
        request.form.get("sObservaciones"),
        int(request.form.get("bActivo", 1)),
        id_val
    ))

    db.commit()
    cursor.close()
    db.close()
    flash("Datos del bombero actualizados correctamente.", "success")
    return redirect(url_for('bomberos'))


@app.route('/guardar_bombero', methods=['POST'])
def guardar_bombero():
    # Handler for form POST when creating a new bombero from the template
    try:
        # Debug: log incoming form data so we can see what the server receives
        print("[guardar_bombero] form data:", dict(request.form))
        db = get_db_connection()
        cursor = db.cursor()

        # Parse bActivo safely (select returns '1' or '0')
        b_activo_raw = request.form.get('bActivo')
        try:
            b_activo_val = int(b_activo_raw) if (b_activo_raw is not None and b_activo_raw != '') else 1
        except ValueError:
            b_activo_val = 1

        cursor.execute("""
            INSERT INTO bomberos (
                sNombre, sApellido_Paterno, sApellido_Materno, dFecha_Nacimiento,
                sCurp, sTelefono, sCorreo, sDireccion, sCargo, sTipo_Ingreso,
                dFecha_Ingreso, sNum_Credencial, sEstado, sObservaciones, bActivo
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            request.form.get('sNombre'),
            request.form.get('sApellido_Paterno'),
            request.form.get('sApellido_Materno'),
            request.form.get('dFecha_Nacimiento'),
            request.form.get('sCurp'),
            request.form.get('sTelefono'),
            request.form.get('sCorreo'),
            request.form.get('sDireccion'),
            request.form.get('sCargo'),
            (request.form.get('sTipo_Ingreso') or '').strip()[:50],
            request.form.get('dFecha_Ingreso'),
            request.form.get('sNum_Credencial'),
            (request.form.get('sEstado') or '').strip()[:50],
            request.form.get('sObservaciones'),
            b_activo_val
        ))

        db.commit()
        cursor.close()
        db.close()
        flash('Bombero guardado correctamente.', 'success')
        return redirect(url_for('bomberos'))
    except Exception as e:
        print(f"Error al guardar bombero: {e}")
        flash(f'Error al guardar bombero: {e}', 'error')
        return redirect(url_for('bomberos'))

    # Base de datos simulada en memoria (lista de diccionarios)
bomberos = [
    {"id": 1, "nombre": "Juan Pérez", "edad": 30, "rango": "Cabo", "estacion": "Estación 1"},
    {"id": 2, "nombre": "Luis Gómez", "edad": 28, "rango": "Teniente", "estacion": "Estación 2"},
    {"id": 3, "nombre": "Carlos Ramírez", "edad": 32, "rango": "Sargento", "estacion": "Estación 3"}
]

if __name__ == '__main__':
    app.run(debug=True)
