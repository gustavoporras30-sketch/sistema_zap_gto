from flask import Flask, jsonify, render_template
import pandas as pd
from sqlalchemy import create_engine

app = Flask(__name__)

# 1. CONEXIÓN A POSTGRESQL
usuario = 'postgres'
contrasena = '1593*' # <-- Pon tu contraseña de nuevo
host = 'localhost:5432'
base_datos = 'PRUEBA'

CADENA_CONEXION = f'postgresql://{usuario}:{contrasena}@{host}/{base_datos}'
motor = create_engine(CADENA_CONEXION)

@app.route('/')
def inicio():
    return render_template('index.html')

# ENDPOINT 1: Catálogo geográfico
@app.route('/api/geografia')
def obtener_geografia():
    try:
        query = """
            SELECT DISTINCT cve_ent, nom_ent, cve_mun, nom_mun, cve_loc, nom_loc, ageb 
            FROM agebs_totales 
            ORDER BY cve_ent, cve_mun, cve_loc, ageb;
        """
        df = pd.read_sql(query, motor)
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ENDPOINT 2: KPIs Fotografía Actual (Censo)
@app.route('/api/kpis/<int:entidad>/<int:municipio>/<string:ageb>')
def obtener_kpis(entidad, municipio, ageb):
    try:
        query = f"""
            SELECT r.pobtot, r.vph_nodren, i.gm_2020, i.im_2020, r.vivtot
            FROM resageburb r
            LEFT JOIN imm i ON r.entidad = i.cve_ent AND r.mun = i.cve_mun
            WHERE r.entidad = {entidad} AND r.mun = {municipio} AND r.ageb = '{ageb}'
            LIMIT 1;
        """
        df_kpis = pd.read_sql(query, motor)
        if not df_kpis.empty:
            return jsonify(df_kpis.to_dict(orient='records')[0])
        else:
            return jsonify({"error": "No hay datos para esta AGEB"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ENDPOINT 3 (¡NUEVO!): Evolución Histórica IRSL
@app.route('/api/historico/<nivel>/<int:entidad>/<int:territorio>')
def obtener_historico(nivel, entidad, territorio):
    try:
        if nivel == 'estado':
            query = f"SELECT periodo, pobtot, p15ym_an, vph_nodren, vph_s_agua, irs_long, grs_long FROM irsl_estados WHERE cve_ent = {entidad} ORDER BY periodo ASC;"
        elif nivel == 'municipio':
            query = f"SELECT periodo, pobtot, p15ym_an, vph_nodren, vph_s_agua, irs_long, grs_long FROM irsl_municipios WHERE cve_mun = {territorio} AND cve_ent = {entidad} ORDER BY periodo ASC;"
        
        df = pd.read_sql(query, motor)
        
        # Pandas limpia la columna pobtot (quitando comas si vienen en el CSV)
        if 'pobtot' in df.columns:
            df['pobtot'] = df['pobtot'].astype(str).str.replace(',', '').astype(float)
            
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Iniciando motor analítico en http://localhost:5000 ...")
    app.run(debug=True, port=5000)