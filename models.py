from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()

class Person(db.Model):
    __tablename__ = 'persons'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    nss = db.Column(db.String(50), unique=True, nullable=False)
    curp = db.Column(db.String(50))

    fecha_nacimiento = db.Column(db.Date)
    fecha_ultima_cotizacion = db.Column(db.Date)
    fecha_primera_cotizacion = db.Column(db.Date)

    semanas_cotizadas = db.Column(db.Integer)
    edad_retiro = db.Column(db.Integer)
    edad_actual = db.Column(db.Integer)

    conyuge = db.Column(db.Boolean, default=False)
    hijos_menores = db.Column(db.Integer, default=0)
    padres_dependientes = db.Column(db.Integer, default=0)

    uma_valor = db.Column(db.Float)
    salario_minimo_df = db.Column(db.Float)
    sueldo_diario_topado_25_umas = db.Column(db.Float)

    fecha_actual = db.Column(db.Date)
    ayuda_soledad = db.Column(db.Boolean, default=False)

    resultado_pension = db.Column(db.Float)  # campo para almacenar cálculo (opcional)
    comentarios = db.Column(db.Text)