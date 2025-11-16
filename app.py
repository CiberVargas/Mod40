from flask import Flask, request, redirect, render_template, send_file
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
db = SQLAlchemy(app)

class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    nss = db.Column(db.String(50), unique=True, nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

@app.before_first_request
def create_tables():
    if os.path.exists('app.db'):
        os.remove('app.db')
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/import', methods=['POST'])
def import_data():
    file = request.files['file']
    df = pd.read_excel(file)
    for index, row in df.iterrows():
        nss = row['nss']
        if not Person.query.filter_by(nss=nss).first():
            person = Person(
                name=row['name'],
                nss=nss,
                birth_date=pd.to_datetime(row['birth_date'], format='%d/%m/%Y'),
                is_active=row['is_active']
            )
            db.session.add(person)
    db.session.commit()
    return redirect('/')

@app.route('/export')
def export_data():
    people = Person.query.all()
    df = pd.DataFrame([{'name': p.name, 'nss': p.nss, 'birth_date': p.birth_date, 'is_active': p.is_active} for p in people])
    df.to_excel('data/example.xlsx', index=False)
    return send_file('data/example.xlsx', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
