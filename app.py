import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from models import db, Usuario, Tarea
from sqlalchemy.exc import OperationalError
from sqlalchemy import text
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clave-temporal-desarrollo')

# Configuración para base de datos
if os.environ.get('VERCEL'):
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        if database_url.startswith('postgres://'):
            app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace('postgres://', 'postgresql://')
        else:
            app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/tareas.db'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tareas.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Crear tablas de base de datos
with app.app_context():
    try:
        db.session.execute(text("SELECT 1 FROM usuario LIMIT 1")).fetchall()
        print("Base de datos verificada correctamente")
    except OperationalError:
        print("Creando tablas de base de datos...")
        db.create_all()
        print("Tablas creadas correctamente")

# Rutas de autenticación
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        usuario = Usuario.query.filter_by(username=username).first()
        
        if usuario and usuario.check_password(password):
            session['user_id'] = usuario.id
            session['username'] = usuario.username
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if Usuario.query.filter_by(username=username).first():
            flash('El usuario ya existe', 'error')
            return redirect(url_for('register'))
        
        nuevo_usuario = Usuario(username=username)
        nuevo_usuario.set_password(password)
        
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        flash('Usuario registrado exitosamente. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada exitosamente', 'success')
    return redirect(url_for('login'))

# Rutas de tareas
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    q = request.args.get('q', '')
    orden = request.args.get('orden', 'recientes')
    
    try:
        consulta = Tarea.query.filter_by(usuario_id=session['user_id'])
        
        if q:
            consulta = consulta.filter(
                (Tarea.titulo.ilike(f'%{q}%')) | (Tarea.descripcion.ilike(f'%{q}%'))
            )
        
        if orden == 'recientes':
            consulta = consulta.order_by(Tarea.creada_en.desc())
        elif orden == 'antiguas':
            consulta = consulta.order_by(Tarea.creada_en.asc())
        elif orden == 'titulo':
            consulta = consulta.order_by(Tarea.titulo.asc())
        
        tareas = consulta.all()
        
    except OperationalError as e:
        flash('Error en la base de datos', 'error')
        tareas = []
    
    hoy = datetime.now().date()
    
    return render_template('index.html', 
                         tareas=tareas, 
                         username=session['username'],
                         q=q,
                         orden=orden,
                         hoy=hoy)

@app.route('/crear', methods=['POST'])
def crear():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        titulo = request.form['titulo']
        descripcion = request.form.get('descripcion', '')
        fecha_limite_str = request.form['fecha_limite']
        categoria = request.form['categoria']
        
        fecha_limite = datetime.strptime(fecha_limite_str, '%Y-%m-%d').date()
        
        nueva_tarea = Tarea(
            titulo=titulo,
            descripcion=descripcion,
            fecha_limite=fecha_limite,
            categoria=categoria,
            usuario_id=session['user_id']
        )
        
        db.session.add(nueva_tarea)
        db.session.commit()
        
        flash('Tarea creada exitosamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear la tarea: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/editar/<int:tarea_id>', methods=['GET', 'POST'])
def editar(tarea_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        tarea = Tarea.query.get_or_404(tarea_id)
        
        if tarea.usuario_id != session['user_id']:
            flash('No tienes permisos para editar esta tarea', 'error')
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            tarea.titulo = request.form['titulo']
            tarea.descripcion = request.form.get('descripcion', '')
            
            fecha_limite_str = request.form.get('fecha_limite', '')
            if fecha_limite_str:
                tarea.fecha_limite = datetime.strptime(fecha_limite_str, '%Y-%m-%d').date()
            
            tarea.categoria = request.form.get('categoria', 'laboral')
            
            db.session.commit()
            flash('Tarea actualizada exitosamente', 'success')
            return redirect(url_for('index'))
        
        return render_template('editar.html', tarea=tarea)
    
    except Exception as e:
        flash('Error al editar la tarea', 'error')
        return redirect(url_for('index'))

@app.route('/toggle/<int:tarea_id>', methods=['POST'])
def toggle(tarea_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        tarea = Tarea.query.get_or_404(tarea_id)
        
        if tarea.usuario_id != session['user_id']:
            flash('No tienes permisos para modificar esta tarea', 'error')
            return redirect(url_for('index'))
        
        tarea.completada = not tarea.completada
        db.session.commit()
        
    except Exception as e:
        flash('Error al modificar la tarea', 'error')
    
    return redirect(url_for('index'))

@app.route('/eliminar/<int:tarea_id>', methods=['POST'])
def eliminar(tarea_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        tarea = Tarea.query.get_or_404(tarea_id)
        
        if tarea.usuario_id != session['user_id']:
            flash('No tienes permisos para eliminar esta tarea', 'error')
            return redirect(url_for('index'))
        
        db.session.delete(tarea)
        db.session.commit()
        flash('Tarea eliminada exitosamente', 'success')
        
    except Exception as e:
        flash('Error al eliminar la tarea', 'error')
    
    return redirect(url_for('index'))

# Configuración para Vercel
if __name__ == '__main__':
    app.run(debug=True)
else:
    application = app