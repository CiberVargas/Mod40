from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import os
import io
import csv
import pandas as pd
from datetime import datetime
from models import db, Person

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['UPLOAD_FOLDER'] = 'uploads'

db.init_app(app)

def parse_date(value):
    """Parse a value into a date object. Accepts dd/mm/YYYY, ISO, pandas Timestamp."""
    if pd.isna(value):
        return None
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.date()
    s = str(value).strip()
    if not s:
        return None
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            pass
    try:
        # fallback: let pandas try (dayfirst=True)
        return pd.to_datetime(s, dayfirst=True).date()
    except Exception:
        return None

@app.before_first_request
def setup():
    # Según lo acordado: recrear la base de datos al iniciar (borrar app.db)
    if os.path.exists('app.db'):
        os.remove('app.db')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('data', exist_ok=True)
    db.create_all()

    # Generar ejemplo si no existe
    example_path = os.path.join('data', 'example.xlsx')
    if not os.path.exists(example_path):
        df = pd.DataFrame([{
            'Nombre': 'Juan Perez',
            'NSS': '12345678901',
            'CURP': 'JUAP880101HDFRRL06',
            'FechaNacimiento': '08/10/1964',
            'FechaUltimaCotizacion': '28/02/2025',
            'FechaPrimeraCotizacion': '22/03/1994',
            'SemanasCotizadas': 1291,
            'EdadRetiro': 61,
            'EdadActual': 61,
            'Conyuge': 'Si',
            'HijosMenores': 0,
            'PadresDependientes': 0,
            'UMA_Valor': 113.14,
            'SalarioMinimoDF': 278.80,
            'SueldoDiarioTopado25UMAs': 2828.50,
            'FechaActual': '15/11/2025',
            'AyudaSoledad': 'No',
            'Comentarios': ''
        }])
        df.to_excel(example_path, index=False)

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
        flash(f'Error al leer el Excel: {e}', 'error')
        return redirect(url_for('index'))

    imported = 0
    for _, row in df.iterrows():
        nss = str(row.get('NSS', '')).strip()
        if not nss:
            continue
        # manejo de duplicados: skip si ya existe NSS
        if Person.query.filter_by(nss=nss).first():
            continue

        p = Person(
            nombre=str(row.get('Nombre', '')).strip(),
            nss=nss,
            curp=str(row.get('CURP', '')).strip(),
            fecha_nacimiento=parse_date(row.get('FechaNacimiento') or row.get('FechaNacimiento')),
            fecha_ultima_cotizacion=parse_date(row.get('FechaUltimaCotizacion')),
            fecha_primera_cotizacion=parse_date(row.get('FechaPrimeraCotizacion')),
            semanas_cotizadas=int(row.get('SemanasCotizadas')) if not pd.isna(row.get('SemanasCotizadas')) else None,
            edad_retiro=int(row.get('EdadRetiro')) if not pd.isna(row.get('EdadRetiro')) else None,
            edad_actual=int(row.get('EdadActual')) if not pd.isna(row.get('EdadActual')) else None,
            conyuge=True if str(row.get('Conyuge', '')).strip().lower() in ('si','sí','s','true','1') else False,
            hijos_menores=int(row.get('HijosMenores')) if not pd.isna(row.get('HijosMenores')) else 0,
            padres_dependientes=int(row.get('PadresDependientes')) if not pd.isna(row.get('PadresDependientes')) else 0,
            uma_valor=float(row.get('UMA_Valor')) if not pd.isna(row.get('UMA_Valor')) else None,
            salario_minimo_df=float(row.get('SalarioMinimoDF')) if not pd.isna(row.get('SalarioMinimoDF')) else None,
            sueldo_diario_topado_25_umas=float(row.get('SueldoDiarioTopado25UMAs')) if not pd.isna(row.get('SueldoDiarioTopado25UMAs')) else None,
            fecha_actual=parse_date(row.get('FechaActual')),
            ayuda_soledad=True if str(row.get('AyudaSoledad', '')).strip().lower() in ('si','sí','s','true','1') else False,
            comentarios=str(row.get('Comentarios', ''))
        )
        db.session.add(p)
        imported += 1

    db.session.commit()
    flash(f'Importadas {imported} filas desde la hoja "{sheet}"', 'success')
    return redirect(url_for('list_persons'))

@app.route('/persons')
def list_persons():
    persons = Person.query.order_by(Person.id.desc()).all()
    return render_template('list.html', persons=persons)

@app.route('/edit/<int:id>', methods=['GET','POST'])
def edit(id):
    p = Person.query.get_or_404(id)
    if request.method == 'POST':
        p.nombre = request.form.get('nombre')
        p.nss = request.form.get('nss')
        p.curp = request.form.get('curp')
        p.fecha_nacimiento = parse_date(request.form.get('fecha_nacimiento'))
        p.fecha_ultima_cotizacion = parse_date(request.form.get('fecha_ultima_cotizacion'))
        p.fecha_primera_cotizacion = parse_date(request.form.get('fecha_primera_cotizacion'))
        p.semanas_cotizadas = int(request.form.get('semanas_cotizadas')) if request.form.get('semanas_cotizadas') else None
        p.edad_retiro = int(request.form.get('edad_retiro')) if request.form.get('edad_retiro') else None
        p.edad_actual = int(request.form.get('edad_actual')) if request.form.get('edad_actual') else None
        p.conyuge = True if request.form.get('conyuge') in ('on','si','Si') else False
        p.hijos_menores = int(request.form.get('hijos_menores') or 0)
        p.padres_dependientes = int(request.form.get('padres_dependientes') or 0)
        p.uma_valor = float(request.form.get('uma_valor')) if request.form.get('uma_valor') else None
        p.salario_minimo_df = float(request.form.get('salario_minimo_df')) if request.form.get('salario_minimo_df') else None
        p.sueldo_diario_topado_25_umas = float(request.form.get('sueldo_diario_topado_25_umas')) if request.form.get('sueldo_diario_topado_25_umas') else None
        p.fecha_actual = parse_date(request.form.get('fecha_actual'))
        p.ayuda_soledad = True if request.form.get('ayuda_soledad') in ('on','si','Si') else False
        p.comentarios = request.form.get('comentarios')
        db.session.commit()
        flash('Registro actualizado', 'success')
        return redirect(url_for('list_persons'))
    return render_template('edit.html', p=p)

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    p = Person.query.get_or_404(id)
    db.session.delete(p)
    db.session.commit()
    flash('Registro eliminado', 'success')
    return redirect(url_for('list_persons'))

@app.route('/export')
def export_csv():
    persons = Person.query.order_by(Person.id).all()
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(['Nombre','NSS','CURP','FechaNacimiento','FechaUltimaCotizacion','FechaPrimeraCotizacion','SemanasCotizadas','EdadRetiro','EdadActual','Conyuge','HijosMenores','PadresDependientes','UMA_Valor','SalarioMinimoDF','SueldoDiarioTopado25UMAs','FechaActual','AyudaSoledad','Comentarios'])
    for p in persons:
        writer.writerow([
            p.nombre, p.nss, p.curp,
            p.fecha_nacimiento.strftime('%d/%m/%Y') if p.fecha_nacimiento else '',
            p.fecha_ultima_cotizacion.strftime('%d/%m/%Y') if p.fecha_ultima_cotizacion else '',
            p.fecha_primera_cotizacion.strftime('%d/%m/%Y') if p.fecha_primera_cotizacion else '',
            p.semanas_cotizadas or '', p.edad_retiro or '', p.edad_actual or '',
            'Si' if p.conyuge else 'No', p.hijos_menores or 0, p.padres_dependientes or 0,
            p.uma_valor or '', p.salario_minimo_df or '', p.sueldo_diario_topado_25_umas or '',
            p.fecha_actual.strftime('%d/%m/%Y') if p.fecha_actual else '', 'Si' if p.ayuda_soledad else 'No', p.comentarios or ''
        ])
    si.seek(0)
    return send_file(io.BytesIO(si.getvalue().encode('utf-8')), mimetype='text/csv', as_attachment=True, download_name='persons.csv')

if __name__ == '__main__':
    app.run(debug=True)