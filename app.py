from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os
from models import db, Person
from io import StringIO
import io
import csv

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['UPLOAD_FOLDER'] = 'uploads'

# initialize DB
db.init_app(app)

with app.app_context():
    db.create_all()
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('data', exist_ok=True)
    # generate example Excel if it does not exist
    example_path = os.path.join('data', 'example.xlsx')
    if not os.path.exists(example_path):
        df_example = pd.DataFrame([
            {
                'Nombre': 'Juan Perez',
                'NSS': '12345678901',
                'CURP': 'JUAP880101HDFRRL06',
                'FechaNacimiento': '1980-01-01',
                'FechaAlta': '2000-01-01',
                'AniosCotizados': 25,
                'SBC': 500.0,
                'Promedio': 450.0,
                'TipoPension': 'Retiro',
                'Comentarios': ''
            }
        ])
        df_example.to_excel(example_path, index=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    f = request.files.get('file')
    if not f:
        flash('No se subió ningún archivo.', 'error')
        return redirect(url_for('index'))
    filename = os.path.join(app.config['UPLOAD_FOLDER'], f.filename)
    f.save(filename)
    try:
        xls = pd.ExcelFile(filename)
        sheet = request.form.get('sheet') or xls.sheet_names[0]
        df = pd.read_excel(xls, sheet_name=sheet)
    except Exception as e:
        flash(f'Error al leer Excel: {e}', 'error')
        return redirect(url_for('index'))

    count = 0
    for _, row in df.iterrows():
        p = Person(
            nombre=str(row.get('Nombre', ''))[:200],
            nss=str(row.get('NSS', ''))[:50],
            curp=str(row.get('CURP', ''))[:50],
            fecha_nacimiento=str(row.get('FechaNacimiento', ''))[:50],
            fecha_alta=str(row.get('FechaAlta', ''))[:50],
            fecha_baja=str(row.get('FechaBaja', ''))[:50],
            anos_cotizados=row.get('AniosCotizados') if 'AniosCotizados' in df.columns else None,
            sbc=row.get('SBC') if 'SBC' in df.columns else None,
            promedio=row.get('Promedio') if 'Promedio' in df.columns else None,
            tipo_pension=str(row.get('TipoPension', ''))[:50],
            comentarios=str(row.get('Comentarios', ''))[:500]
        )
        db.session.add(p)
        count += 1
    db.session.commit()
    flash(f'Importadas {count} filas desde hoja "{sheet}".', 'success')
    return redirect(url_for('list_persons'))

@app.route('/persons')
def list_persons():
    persons = Person.query.order_by(Person.id.desc()).all()
    return render_template('list.html', persons=persons)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    p = Person.query.get_or_404(id)
    if request.method == 'POST':
        p.nombre = request.form.get('nombre')
        p.nss = request.form.get('nss')
        p.curp = request.form.get('curp')
        p.fecha_nacimiento = request.form.get('fecha_nacimiento')
        p.fecha_alta = request.form.get('fecha_alta')
        p.fecha_baja = request.form.get('fecha_baja')
        p.anos_cotizados = request.form.get('anos_cotizados') or None
        p.sbc = request.form.get('sbc') or None
        p.promedio = request.form.get('promedio') or None
        p.tipo_pension = request.form.get('tipo_pension')
        p.comentarios = request.form.get('comentarios')
        db.session.commit()
        flash('Registro actualizado.', 'success')
        return redirect(url_for('list_persons'))
    return render_template('edit.html', p=p)

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    p = Person.query.get_or_404(id)
    db.session.delete(p)
    db.session.commit()
    flash('Registro eliminado.', 'success')
    return redirect(url_for('list_persons'))

@app.route('/export')
def export_csv():
    persons = Person.query.order_by(Person.id).all()
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['id','Nombre','NSS','CURP','FechaNacimiento','FechaAlta','FechaBaja','AniosCotizados','SBC','Promedio','TipoPension','Comentarios'])
    for p in persons:
        writer.writerow([p.id, p.nombre, p.nss, p.curp, p.fecha_nacimiento, p.fecha_alta, p.fecha_baja, p.anos_cotizados, p.sbc, p.promedio, p.tipo_pension, p.comentarios])
    si.seek(0)
    return send_file(io.BytesIO(si.getvalue().encode('utf-8')),
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name='persons.csv')

if __name__ == '__main__':
    app.run(debug=True)
