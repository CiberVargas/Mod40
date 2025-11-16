# Modalidad 40 - Importar Excel a SQLite (Flask)

Descripción
-----------
Aplicación mínima en Flask para:
- Subir un archivo Excel (.xlsx) con encabezados en español.
- Mapear columnas al modelo Person y guardar en SQLite.
- Listar, editar, borrar registros desde una UI simple.
- Exportar registros a CSV.
- Ejemplo de Excel en data/example.xlsx (fechas formato dd/mm/aaaa).

Campos esperados en el Excel (encabezados):
- Nombre, NSS, CURP, FechaNacimiento, FechaUltimaCotizacion, FechaPrimeraCotizacion,
  SemanasCotizadas, EdadRetiro, EdadActual, Conyuge, HijosMenores, PadresDependientes,
  UMA_Valor, SalarioMinimoDF, SueldoDiarioTopado25UMAs, FechaActual, AyudaSoledad, Comentarios

Formato de fechas: dd/mm/aaaa preferido; la app tratará de parsear también ISO (YYYY-MM-DD).

Instalación (local)
-------------------
1. Clona el repo y cambia a la rama `feature/excel-db` (cuando esté creada).
2. Crea y activa un entorno virtual (recomendado).
3. Instala dependencias:
   pip install -r requirements.txt
4. Ejecuta:
   export FLASK_APP=app.py
   flask run
   o
   python app.py

Notas importantes
-----------------
- Por ahora la aplicación recrea la base (app.db) al iniciarse (opción elegida). Esto sobrescribe datos previos.
- Manejo de duplicados por NSS: "skip" (las filas con NSS ya existente no se importan).
- Si quieres cambiar el comportamiento (por ejemplo actualizar registros existentes), lo puedo modificar.
- Si quieres que no se borre la base existente, dime y lo cambio para mantenerla y generar migraciones si lo deseas.

Siguientes pasos
----------------
- Implementar cálculo automático de la pensión (resultado_pension) con la fórmula que me indiques o aplicando la Ley 1973 (requiere buscar reglas oficiales).
- Añadir validaciones y tests.
