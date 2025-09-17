from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'usuario'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    creada_en = db.Column(db.DateTime, default=datetime.utcnow)
    
    tareas = db.relationship('Tarea', backref='usuario', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Tarea(db.Model):
    __tablename__ = 'tarea'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    completada = db.Column(db.Boolean, default=False)
    creada_en = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_limite = db.Column(db.Date, nullable=True)
    categoria = db.Column(db.String(50), default='laboral')
    
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    
    def __repr__(self):
        return f'<Tarea {self.titulo}>'