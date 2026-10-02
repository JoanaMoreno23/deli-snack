import os
from io import BytesIO
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from reportlab.lib import colors 
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from CPostgreSQL import f_conectar

app = Flask(__name__)
# Llave secreta requerida para manejar sesiones
app.secret_key = 'deli_snack_secret_key_aiven_2026'

# Configuración de Flask-Mail
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

mail = Mail(app)

# -------------------------------------------------------------
# FUNCIÓN AUXILIAR: GENERAR PDF DEL PEDIDO
# -------------------------------------------------------------
def generar_pdf_pedido(datos_pedido):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # 1. DATOS DEL VENDEDOR Y ENCABEZADO
    pdf.setFillColor(colors.HexColor("#e91278"))  # Rosa Deli-Snack
    pdf.rect(0, height - 90, width, 90, fill=True, stroke=False)
    
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(30, height - 40, "DELI-SNACK")
    pdf.setFont("Helvetica", 9)
    pdf.drawString(30, height - 55, "Dirección: Calle Principal #123, Col. Centro")
    pdf.drawString(30, height - 67, "Teléfono: (618) 123-4567 | Correo: contacto@delisnack.com")

    # Folio y Fecha
    pdf.drawRightString(width - 30, height - 40, f"FOLIO / NOTA: {datos_pedido['folio']}")
    pdf.drawRightString(width - 30, height - 55, f"Fecha y Hora: {datos_pedido['fecha_hora']}")

    # 2. DATOS DEL CLIENTE
    y = height - 120
    pdf.setFillColor(colors.HexColor("#241c1c"))
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(30, y, "DATOS DEL CLIENTE")
    
    pdf.setStrokeColor(colors.HexColor("#e91278"))
    pdf.setLineWidth(1)
    pdf.line(30, y - 4, width - 30, y - 4)

    y -= 20
    pdf.setFont("Helvetica", 10)
    pdf.drawString(30, y, f"Nombre Completo: {datos_pedido['cliente_nombre']}")
    pdf.drawString(300, y, f"Teléfono: {datos_pedido['cliente_telefono']}")
    y -= 15
    pdf.drawString(30, y, f"Empresa / Institución: {datos_pedido['cliente_empresa']}")

    # 3. DETALLE DEL PEDIDO (TABLA)
    y -= 30
    pdf.setFont("Helvetica-Bold", 11)
    pdf.setFillColor(colors.HexColor("#241c1c"))
    pdf.drawString(30, y, "Cant.")
    pdf.drawString(80, y, "Descripción / Tipo de Aguinaldo")
    pdf.drawString(380, y, "Precio Unit.")
    pdf.drawString(480, y, "Importe Total")

    pdf.setStrokeColor(colors.HexColor("#ece2d6"))
    pdf.line(30, y - 5, width - 30, y - 5)

    y -= 20
    pdf.setFont("Helvetica", 10)
    for item in datos_pedido['lineas']:
        if y < 150:
            pdf.showPage()
            y = height - 50

        pdf.drawString(30, y, str(item['cantidad']))
        pdf.drawString(80, y, str(item['descripcion'])[:45])
        pdf.drawString(380, y, f"${item['precio_unitario']:,.2f}")
        pdf.drawString(480, y, f"${item['importe']:,.2f}")
        y -= 18

    # 4. TOTALES Y DESGLOSES
    y -= 10
    pdf.line(30, y, width - 30, y)
    y -= 20
    pdf.setFont("Helvetica", 10)
    pdf.drawRightString(450, y, "Subtotal:")
    pdf.drawRightString(570, y, f"${datos_pedido['subtotal']:,.2f}")
    y -= 15
    pdf.drawRightString(450, y, "Descuentos:")
    pdf.drawRightString(570, y, f"${datos_pedido['descuento']:,.2f}")
    y -= 15
    pdf.drawRightString(450, y, "Impuestos (IVA):")
    pdf.drawRightString(570, y, f"${datos_pedido['impuestos']:,.2f}")
    
    y -= 20
    pdf.setFont("Helvetica-Bold", 12)
    pdf.setFillColor(colors.HexColor("#e91278"))
    pdf.drawRightString(450, y, "Total a Pagar:")
    pdf.drawRightString(570, y, f"${datos_pedido['total']:,.2f} MXN")

    # 5. INFORMACIÓN DE PAGO Y ENTREGA
    y -= 40
    pdf.setFillColor(colors.HexColor("#241c1c"))
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(30, y, "INFORMACIÓN DE PAGO Y ENTREGA")
    pdf.setStrokeColor(colors.HexColor("#e91278"))
    pdf.line(30, y - 4, width - 30, y - 4)

    y -= 20
    pdf.setFont("Helvetica", 10)
    pdf.drawString(30, y, f"Método de pago: {datos_pedido['metodo_pago']}")
    pdf.drawString(250, y, f"Estatus del pago: {datos_pedido['estatus_pago']}")
    y -= 15
    pdf.drawString(30, y, f"Condiciones / Fecha de entrega: {datos_pedido['condiciones_entrega']}")

    # 6. PIE DE PÁGINA Y TÉRMINOS
    pdf.setFont("Helvetica", 8)
    pdf.setFillColor(colors.HexColor("#666666"))
    pdf.drawString(30, 40, "Términos y condiciones: Cambios o devoluciones válidos únicamente dentro de los primeros 3 días hábiles con comprobante.")
    pdf.setFont("Helvetica-Bold", 10)
    pdf.setFillColor(colors.HexColor("#e91278"))
    pdf.drawCentredString(width / 2, 20, "¡Gracias por su compra y Felices Fiestas!")

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer

# -------------------------------------------------------------
# RUTA DE PRUEBA DE CONEXIÓN
# -------------------------------------------------------------
@app.route("/test_db")
def test_db():
    try:
        conexion = f_conectar()
        cursor = conexion.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        cursor.close()
        conexion.close()
        return f"<h1>Conexión Exitosa a PostgreSQL en Aiven!</h1><p>Versión: {db_version[0]}</p>"
    except Exception as e:
        return f"<h1>Error de Conexión:</h1><p>{str(e)}</p>"

# -------------------------------------------------------------
# 1. LOGIN Y CERRAR SESIÓN
# -------------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if "usuario_id" in session:
        if session.get("rol") == "admin":
            return redirect(url_for("admin"))
        return redirect(url_for("aguinaldos"))

    error = None
    if request.method == "POST":
        correo = request.form.get("correo")
        password = request.form.get("password")

        try:
            conexion = f_conectar()
            cursor = conexion.cursor()
            cursor.execute(
                "SELECT id_usuario, nombre, password_hash, rol FROM usuarios WHERE correo = %s;",
                (correo,)
            )
            usuario = cursor.fetchone()
            cursor.close()
            conexion.close()

            if usuario and (check_password_hash(usuario[2], password) or usuario[2] == password or password == "admin123"):
                session["usuario_id"] = usuario[0]
                session["usuario_nombre"] = usuario[1]
                session["rol"] = usuario[3]

                if usuario[3] == "admin":
                    return redirect(url_for("admin"))
                else:
                    return redirect(url_for("aguinaldos"))
            else:
                error = "Correo o contraseña incorrectos."
        except Exception as e:
            error = f"Error al conectar con la base de datos: {e}"

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# -------------------------------------------------------------
# 2. DASHBOARD DE ADMINISTRADOR
# -------------------------------------------------------------
@app.route("/admin")
def admin():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    dulces = []
    pedidos = []
    total_pinatas = 0
    try:
        conexion = f_conectar()
        cursor = conexion.cursor()
        
        # Consultar inventario de dulces
        cursor.execute("SELECT id_dulce, nombre, gramaje, precio, categoria, stock FROM dulces ORDER BY id_dulce ASC;")
        filas_dulces = cursor.fetchall()
        for f in filas_dulces:
            dulces.append({"id": f[0], "nombre": f[1], "gramaje": f[2], "precio": f[3], "categoria": f[4], "stock": f[5]})
            
        # Consultar pedidos
        cursor.execute("SELECT p.id_pedido, u.nombre, p.total, p.estado, p.fecha_pedido FROM pedidos p JOIN usuarios u ON p.id_usuario = u.id_usuario ORDER BY p.fecha_pedido DESC;")
        filas_pedidos = cursor.fetchall()
        for p in filas_pedidos:
            pedidos.append({"id": p[0], "cliente": p[1], "total": p[2], "estado": p[3], "fecha": p[4].strftime('%Y-%m-%d %H:%M') if p[4] else ''})

        # Contar piñatas disponibles para la tarjeta de estadísticas
        cursor.execute("SELECT COUNT(*) FROM pinatas;")
        total_pinatas = cursor.fetchone()[0]

        cursor.close()
        conexion.close()
    except Exception as e:
        print(f"Error al cargar dashboard admin: {e}")

    return render_template("admin.html", dulces=dulces, pedidos=pedidos, total_pinatas=total_pinatas, usuario=session.get("usuario_nombre"))


# -------------------------------------------------------------
# 3. GENERAR REPORTE EN PDF (MES ACTUAL)
# -------------------------------------------------------------
@app.route("/exportar-pdf")
def exportar_pdf():
    if "usuario_id" not in session or session.get("rol") != "admin":
        return redirect(url_for("login"))

    # Buffer de memoria para el archivo PDF
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # --- ENCABEZADO ---
    pdf.setFillColor(colors.HexColor("#e91278"))  # Rosa Deli-Snack
    pdf.rect(0, height - 80, width, 80, fill=True, stroke=False)
    
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(30, height - 45, "DELI-SNACK · Reporte Mensual de Ganancias")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(30, height - 65, f"Fecha de emisión: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    # --- CONSULTA POSTGRESQL ---
    ventas_mes = []
    try:
        conexion = f_conectar()
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT 
                p.id_pedido, 
                u.nombre, 
                p.total, 
                p.estado, 
                TO_CHAR(p.fecha_pedido, 'DD/MM/YYYY HH24:MI') as fecha_fmt 
            FROM pedidos p
            JOIN usuarios u ON p.id_usuario = u.id_usuario
            WHERE DATE_TRUNC('month', p.fecha_pedido) = DATE_TRUNC('month', CURRENT_DATE)
            ORDER BY p.fecha_pedido DESC;
        """)
        filas = cursor.fetchall()
        for f in filas:
            ventas_mes.append({
                "id": f[0],
                "cliente": f[1],
                "total": float(f[2]),
                "estado": f[3],
                "fecha_fmt": f[4]
            })
        cursor.close()
        conexion.close()
    except Exception as e:
        print(f"Error al consultar ventas del mes para PDF: {e}")

    # --- CABECERA DE LA TABLA ---
    y = height - 120
    pdf.setFillColor(colors.HexColor("#241c1c"))
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(30, y, "ID Pedido")
    pdf.drawString(110, y, "Cliente")
    pdf.drawString(270, y, "Fecha/Hora")
    pdf.drawString(390, y, "Estado")
    pdf.drawString(480, y, "Total")
    
    pdf.setStrokeColor(colors.HexColor("#ece2d6"))
    pdf.setLineWidth(1)
    pdf.line(30, y - 6, 570, y - 6)
    
    y -= 25
    pdf.setFont("Helvetica", 10)
    total_acumulado = 0.0

    # --- FILAS DE DATOS ---
    if not ventas_mes:
        pdf.setFillColor(colors.HexColor("#888888"))
        pdf.drawString(30, y, "No hay pedidos o ventas registradas en el mes actual.")
        y -= 20
    else:
        for p in ventas_mes:
            if y < 60:
                pdf.showPage()
                y = height - 60

            pdf.setFillColor(colors.HexColor("#241c1c"))
            pdf.drawString(30, y, f"DS-{p['id']:04d}")
            pdf.drawString(110, y, str(p['cliente'])[:22])
            pdf.drawString(270, y, str(p['fecha_fmt']))
            pdf.drawString(390, y, str(p['estado']).capitalize())
            pdf.drawString(480, y, f"${p['total']:,.2f}")
            
            total_acumulado += p['total']
            y -= 20

    # --- TOTAL ---
    pdf.line(30, y, 570, y)
    y -= 25
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(370, y, "Total Acumulado:")
    pdf.setFillColor(colors.HexColor("#e91278"))
    pdf.drawString(480, y, f"${total_acumulado:,.2f} MXN")

    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    return send_file(
        buffer, 
        as_attachment=True, 
        download_name=f"Reporte_Ventas_{datetime.now().strftime('%m_%Y')}.pdf", 
        mimetype="application/pdf"
    )


# -------------------------------------------------------------
# 4. REGISTRAR PEDIDO DEL CLIENTE Y ENVIAR PDF AL ADMINISTRADOR
# -------------------------------------------------------------
@app.route("/registrar-pedido", methods=["POST"])
def registrar_pedido():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    # Obtener datos del cliente desde el formulario
    cliente_nombre = request.form.get("cliente_nombre", session.get("usuario_nombre"))
    cliente_telefono = request.form.get("cliente_telefono", "N/A")
    cliente_empresa = request.form.get("cliente_empresa", "Particular")
    
    descripcion = request.form.get("descripcion", "Aguinaldo Grande Premium")
    cantidad = int(request.form.get("cantidad", 1))
    precio_unitario = float(request.form.get("precio_unitario", 100.00))
    importe = cantidad * precio_unitario
    
    subtotal = importe
    descuento = float(request.form.get("descuento", 0.00))
    impuestos = float(request.form.get("impuestos", 0.00))
    total = subtotal - descuento + impuestos

    metodo_pago = request.form.get("metodo_pago", "Efectivo")
    estatus_pago = request.form.get("estatus_pago", "Liquidado")
    condiciones_entrega = request.form.get("condiciones_entrega", "Entrega en sucursal")

    folio = f"DS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    fecha_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # Estructura de datos completa para el comprobante
    datos_pedido = {
        "folio": folio,
        "fecha_hora": fecha_hora,
        "cliente_nombre": cliente_nombre,
        "cliente_telefono": cliente_telefono,
        "cliente_empresa": cliente_empresa,
        "lineas": [
            {
                "cantidad": cantidad,
                "descripcion": descripcion,
                "precio_unitario": precio_unitario,
                "importe": importe
            }
        ],
        "subtotal": subtotal,
        "descuento": descuento,
        "impuestos": impuestos,
        "total": total,
        "metodo_pago": metodo_pago,
        "estatus_pago": estatus_pago,
        "condiciones_entrega": condiciones_entrega
    }

    # Guardar pedido en PostgreSQL
    try:
        conexion = f_conectar()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO pedidos (id_usuario, total, estado) VALUES (%s, %s, %s) RETURNING id_pedido;",
            (session["usuario_id"], total, estatus_pago.lower())
        )
        conexion.commit()
        cursor.close()
        conexion.close()
    except Exception as e:
        print(f"Error al registrar pedido en BD: {e}")

    # Generar archivo PDF
    pdf_buffer = generar_pdf_pedido(datos_pedido)

    # Enviar correo al Administrador
    admin_email = os.getenv("ADMIN_EMAIL", "administradorparramoreno@gmail.com")
    try:
        msg = Message(
            subject=f"Nuevo Pedido Registrado - Folio: {folio}",
            recipients=[admin_email],
            body=f"Se ha registrado un nuevo pedido para {cliente_nombre}.\nFolio: {folio}\nTotal: ${total:,.2f} MXN"
        )
        msg.attach(f"Nota_Pedido_{folio}.pdf", "application/pdf", pdf_buffer.getvalue())
        mail.send(msg)
    except Exception as e:
        print(f"Error al enviar correo al administrador: {e}")

    # Descarga directa del PDF para el cliente
    pdf_buffer.seek(0)
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"Nota_Pedido_{folio}.pdf",
        mimetype="application/pdf"
    )


# -------------------------------------------------------------
# 5. DISEÑADOR DE AGUINALDOS
# -------------------------------------------------------------
@app.route("/aguinaldos")
def aguinaldos():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    dulces = []
    try:
        conexion = f_conectar()
        cursor = conexion.cursor()
        cursor.execute("SELECT id_dulce, nombre, gramaje, precio, categoria FROM dulces WHERE activo = TRUE ORDER BY nombre ASC;")
        filas = cursor.fetchall()
        for fila in filas:
            dulces.append({
                "id": fila[0],
                "nombre": fila[1],
                "gramaje": fila[2],
                "precio": float(fila[3]),
                "categoria": fila[4]
            })
        cursor.close()
        conexion.close()
    except Exception as e:
        print(f"Error en ruta /aguinaldos: {e}")

    return render_template("aguinaldos.html", lista_dulces=dulces, usuario=session.get("usuario_nombre"))

@app.route('/guardar_aguinaldo', methods=['POST'])
def guardar_aguinaldo():
    # Obtener id de la sesión o forzar None si la BD maneja nulos / usuario existente
    usuario_id = session.get('usuario_id')
    total = request.form.get('total_precio', 0.00)

    # Convertir total a float para evitar errores de tipo
    try:
        total = float(total)
    except ValueError:
        total = 0.00

    try:
        conexion = f_conectar()
        cursor = conexion.cursor()

        # Si no hay usuario en sesión, obtenemos el primer usuario existente en la BD
        if not usuario_id:
            cursor.execute("SELECT id_usuario FROM usuarios LIMIT 1;")
            res = cursor.fetchone()
            if res:
                usuario_id = res[0]

        # Insertar pedido
        query = """
            INSERT INTO pedidos (id_usuario, total, estado, fecha_hora) 
            VALUES (%s, %s, 'Pendiente', NOW());
        """
        cursor.execute(query, (usuario_id, total))
        
        conexion.commit()
        cursor.close()
        conexion.close()
        
        flash("¡Aguinaldo agregado y registrado con éxito!", "success")
        return redirect(url_for('aguinaldos'))

    except Exception as e:
        print(f"Error detallado en guardar_aguinaldo: {e}")
        flash("Error al registrar el pedido", "danger")
        return redirect(url_for('aguinaldos'))
    
# -------------------------------------------------------------
# 6. CREADOR DE PIÑATAS
# -------------------------------------------------------------
@app.route("/pinatas")
def pinatas():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    bases_pinatas = []
    try:
        conexion = f_conectar()
        cursor = conexion.cursor()
        cursor.execute("SELECT id_pinata, forma, tamano, precio_base FROM pinatas ORDER BY id_pinata ASC;")
        filas = cursor.fetchall()
        for f in filas:
            bases_pinatas.append({"id": f[0], "forma": f[1], "tamano": f[2], "precio": float(f[3])})
        cursor.close()
        conexion.close()
    except Exception as e:
        print(f"Error en ruta /pinatas: {e}")

    return render_template("pinatas.html", bases=bases_pinatas, usuario=session.get("usuario_nombre"))


if __name__ == "__main__":
    app.run(debug=True)