from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

# --- CONFIGURACIÓN DE LA BASE DE DATOS (NEON) ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://neondb_owner:npg_hF4PjcEJq5RO@ep-jolly-waterfall-amgwvrji-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS DE DATOS ---

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False) 
    rol = db.Column(db.String(20), default='cliente')

class Comercio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    rif = db.Column(db.String(20), unique=True)
    direccion = db.Column(db.String(255))
    categoria = db.Column(db.String(50))
    productos = db.relationship('Producto', backref='comercio', lazy=True)

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text)
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    imagen_url = db.Column(db.String(500)) 
    codigo_barras = db.Column(db.String(50), unique=True)
    comercio_id = db.Column(db.Integer, db.ForeignKey('comercio.id'), nullable=False)

with app.app_context():
    db.create_all()
    print("¡Tablas (Usuario, Comercio, Producto) sincronizadas en PostgreSQL!")

# --- RUTAS DE USUARIO ---

@app.route('/')
def index():
    return jsonify({"mensaje": "Servidor de Jaydi Express funcionando 24/7"})

@app.route('/registrar', methods=['POST'])
def registrar():
    try:
        datos = request.json
        usuario_existe = Usuario.query.filter_by(email=datos['email']).first()
        if usuario_existe:
            return jsonify({"mensaje": "Ese correo ya está registrado"}), 400

        password_encriptada = generate_password_hash(datos['password'])
        nuevo_usuario = Usuario(
            nombre=datos['nombre'],
            email=datos['email'],
            password=password_encriptada,
            rol=datos.get('rol', 'cliente')
        )
        db.session.add(nuevo_usuario)
        db.session.commit()
        return jsonify({"mensaje": "Usuario creado con éxito"}), 201
    except Exception as e:
        return jsonify({"mensaje": str(e)}), 400

@app.route('/login', methods=['POST'])
def login():
    try:
        datos = request.json
        usuario = Usuario.query.filter_by(email=datos.get('email')).first()
        if usuario and check_password_hash(usuario.password, datos.get('password')):
            return jsonify({
                "mensaje": "Bienvenido",
                "usuario": {"nombre": usuario.nombre, "email": usuario.email, "rol": usuario.rol}
            }), 200
        else:
            return jsonify({"mensaje": "Correo o contraseña incorrectos"}), 401
    except Exception as e:
        return jsonify({"mensaje": "Error interno del servidor"}), 500

# --- RUTAS DE PRODUCTOS (NUEVAS) ---

@app.route('/productos', methods=['GET'])
def obtener_productos():
    try:
        # Consultamos todos los productos en la nube
        productos = Producto.query.all()
        resultado = []
        for p in productos:
            resultado.append({
                "id": p.id,
                "nombre": p.nombre,
                "descripcion": p.descripcion,
                "precio": p.precio,
                "stock": p.stock,
                "imagen": p.imagen_url,
                "comercio": p.comercio.nombre # Obtenemos el nombre del comercio vinculado
            })
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"mensaje": str(e)}), 500

@app.route('/seed', methods=['GET'])
def seed_data():
    try:
        # Verificamos si ya existe para no duplicar datos de prueba
        if Comercio.query.filter_by(rif="J-12345678-0").first():
            return jsonify({"mensaje": "Los datos de prueba ya existen"}), 200

        nuevo_comercio = Comercio(
            nombre="Farmatodo",
            rif="J-12345678-0",
            direccion="Av. Principal, Los Teques",
            categoria="Farmacia"
        )
        db.session.add(nuevo_comercio)
        db.session.flush()

        p1 = Producto(
            nombre="Acetaminofén 500mg",
            descripcion="Caja de 10 tabletas para el malestar general.",
            precio=2.50,
            stock=50,
            imagen_url="https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?q=80&w=200",
            codigo_barras="7591234567890",
            comercio_id=nuevo_comercio.id
        )

        p2 = Producto(
            nombre="Agua Mineral 1L",
            descripcion="Agua mineral natural purificada.",
            precio=1.00,
            stock=100,
            imagen_url="https://images.unsplash.com/photo-1548839140-29a749e1cf4d?q=80&w=200",
            codigo_barras="7590987654321",
            comercio_id=nuevo_comercio.id
        )

        db.session.add_all([p1, p2])
        db.session.commit()
        return jsonify({"mensaje": "¡Datos de prueba creados con éxito!"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"mensaje": f"Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)