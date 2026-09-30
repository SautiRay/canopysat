from flask import Flask, render_template, request, jsonify, session, redirect
from dotenv import load_dotenv
import ee
import os

load_dotenv()

import os
app = Flask(__name__, 
    static_folder=os.path.join(os.path.dirname(__file__), 'static'),
    static_url_path='/static')
app.secret_key = os.getenv('SECRET_KEY', 'canopysat-2026')

# Initialisation Google Earth Engine avec Service Account
try:
    from google.oauth2 import service_account
    SERVICE_ACCOUNT_FILE = '/home/canopysat/app/canopysat-service-account.json'
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/earthengine']
    )
    ee.Initialize(credentials=credentials, project=os.getenv('GEE_PROJECT', 'canopysat-platform'))
    print("GEE initialisé avec Service Account - OK")
except Exception as e:
    print(f"Erreur GEE Service Account: {e}")

from gee_analysis import analyze_forest

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        lat = float(data.get('lat', 0))
        lng = float(data.get('lng', 0))
        size = float(data.get('size', 10))
        lang = data.get('lang', 'en')

        result = analyze_forest(lat, lng, size)

        if result['success']:
            # Log to community DB
            try:
                import sqlite3 as sq
                cc = sq.connect('/home/canopysat/app/community.db')
                cc.execute('''INSERT INTO analyses_log
                    (lat, lng, score, ai_forest_type, deforestation_alert, forest_cover)
                    VALUES (?,?,?,?,?,?)''',
                    (lat, lng, result.get('score'), result.get('ai_forest_type'),
                     result.get('deforestation_alert'), result.get('forest_cover')))
                cc.commit()
                cc.close()
            except: pass

            return jsonify({
                'success': True,
                'score': result['score'],
                'ndvi_current': result['ndvi_current'],
                'ndvi_past': result['ndvi_past'],
                'ndvi_change': result['ndvi_change'],
                'ndvi_10y': result.get('ndvi_10y'),
                'ndvi_1984': result.get('ndvi_1984'),
                'landsat_change_10y': result.get('landsat_change_10y'),
                'landsat_change_40y': result.get('landsat_change_40y'),
                'forest_cover': result['forest_cover'],
                'active_fires': result['active_fires'],
                'fire_pixels': result.get('fire_pixels', result['active_fires']),
                'fire_events_estimated': result.get('fire_events_estimated', 0),
                'trend': result['trend'] if lang == 'en' else result['trend_fr'],
                'lat': lat,
                'lng': lng,
                'size_km': size,
                'analysis_date': result['analysis_date'],
                'leaf_type': result.get('leaf_type'),
                'leaf_type_fr': result.get('leaf_type_fr'),
                'ndre': result.get('ndre'),
                'dev_stage': result.get('dev_stage'),
                'dev_stage_fr': result.get('dev_stage_fr'),
                'dev_stage_age': result.get('dev_stage_age'),
                'canopy_height': result.get('canopy_height'),
                'canopy_height_rh50': result.get('canopy_height_rh50'),
                'gedi_cover': result.get('gedi_cover'),
                'canopy_height_source': result.get('canopy_height_source'),
                'estimated_agb': result.get('estimated_agb'),
                'biomass_class': result.get('biomass_class'),
                'biomass_class_fr': result.get('biomass_class_fr'),
                'ai_forest_type': result.get('ai_forest_type'),
                'ai_forest_type_fr': result.get('ai_forest_type_fr'),
                'ai_deforestation_risk': result.get('ai_deforestation_risk'),
                'ai_degradation_signs': result.get('ai_degradation_signs'),
                'ai_recovery_signs': result.get('ai_recovery_signs'),
                'ai_main_cause': result.get('ai_main_cause'),
                'ai_recommendation': result.get('ai_recommendation'),
                'ai_indices': result.get('ai_indices'),
                'ndvi_change_1y': result.get('ndvi_change_1y'),
                'ndvi_change_5y': result.get('ndvi_change_5y'),
                'ndvi_change_10y_val': result.get('ndvi_change_10y_val'),
                'ndvi_change_40y_val': result.get('ndvi_change_40y_val'),
                'annual_rate': result.get('annual_rate'),
                'forest_status': result.get('forest_status'),
                'forest_status_fr': result.get('forest_status_fr'),
                'forest_change_ha': result.get('forest_change_ha'),
                'forest_change_pct': result.get('forest_change_pct'),
                'deforestation_alert': result.get('deforestation_alert'),
                'deforestation_alert_fr': result.get('deforestation_alert_fr'),
                'annual_ha_rate': result.get('annual_ha_rate'),
                'forest_change_ha_10y': result.get('forest_change_ha_10y'),
                'forest_change_pct_10y': result.get('forest_change_pct_10y'),
                'annual_ha_rate_10y': result.get('annual_ha_rate_10y'),
                'leaf_type': result.get('leaf_type'),
                'leaf_type_fr': result.get('leaf_type_fr'),
                'ndre': result.get('ndre'),
                'dev_stage': result.get('dev_stage'),
                'dev_stage_fr': result.get('dev_stage_fr'),
                'dev_stage_age': result.get('dev_stage_age'),
                'canopy_height': result.get('canopy_height'),
                'canopy_height_rh50': result.get('canopy_height_rh50'),
                'gedi_cover': result.get('gedi_cover'),
                'canopy_height_source': result.get('canopy_height_source'),
                'estimated_agb': result.get('estimated_agb'),
                'biomass_class': result.get('biomass_class'),
                'biomass_class_fr': result.get('biomass_class_fr'),
                'ai_forest_type': result.get('ai_forest_type'),
                'ai_forest_type_fr': result.get('ai_forest_type_fr'),
                'ai_deforestation_risk': result.get('ai_deforestation_risk'),
                'ai_degradation_signs': result.get('ai_degradation_signs'),
                'ai_recovery_signs': result.get('ai_recovery_signs'),
                'ai_main_cause': result.get('ai_main_cause'),
                'ai_recommendation': result.get('ai_recommendation'),
                'ai_indices': result.get('ai_indices'),
                'ndvi_change_1y': result.get('ndvi_change_1y'),
                'ndvi_change_5y': result.get('ndvi_change_5y'),
                'ndvi_change_10y_val': result.get('ndvi_change_10y_val'),
                'ndvi_change_40y_val': result.get('ndvi_change_40y_val'),
                'annual_rate': result.get('annual_rate'),
                'forest_status': result.get('forest_status'),
                'forest_status_fr': result.get('forest_status_fr'),
                'forest_change_ha': result.get('forest_change_ha'),
                'forest_change_pct': result.get('forest_change_pct'),
                'deforestation_alert': result.get('deforestation_alert'),
                'deforestation_alert_fr': result.get('deforestation_alert_fr'),
                'annual_ha_rate': result.get('annual_ha_rate'),
                'forest_change_ha_10y': result.get('forest_change_ha_10y'),
                'forest_change_pct_10y': result.get('forest_change_pct_10y'),
                'annual_ha_rate_10y': result.get('annual_ha_rate_10y'),
                'pts_ndvi': result.get('pts_ndvi', 0),
                'pts_trend': result.get('pts_trend', 0),
                'pts_cover': result.get('pts_cover', 0),
                'pts_s1': result.get('pts_s1', 0),
                'pts_fire': result.get('pts_fire', 0),
                'sentinel1_vv': result.get('sentinel1_vv'),
                'sentinel1_forest': result.get('sentinel1_forest'),
                'satellites_used': result['satellites_used'],
                'carbon_per_ha': result.get('carbon_per_ha'),
                'carbon_area_ha': result.get('carbon_area_ha'),
                'carbon_total_co2': result.get('carbon_total_co2'),
                'carbon_value_eur': result.get('carbon_value_eur'),
            })
        else:
            return jsonify({'success': False, 'error': result.get('error', 'Unknown error')}), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/report-view')
def report_view():
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    lang = request.args.get('lang', 'en')
    if not lat or not lng:
        return 'Missing coordinates', 400
    try:
        from gee_analysis import analyze_forest
        result = analyze_forest(float(lat), float(lng), 10)
        result['lang'] = lang
        from pdf_report import generate_pdf
        filename = generate_pdf(result, lang)
        from flask import send_file
        return send_file(
            f'/home/canopysat/app/reports/{filename}',
            as_attachment=True,
            download_name=f'CanopySat_Report.pdf',
            mimetype='application/pdf'
        )
    except Exception as e:
        return f'Error: {str(e)}', 500

@app.route('/species-suitability', methods=['POST'])
def species_suitability():
    try:
        data = request.get_json()
        lat = float(data.get('lat', 0))
        lng = float(data.get('lng', 0))
        size = float(data.get('size', 10))
        from species_suitability import analyze_species_suitability
        result = analyze_species_suitability(lat, lng, size)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/certificate', methods=['POST'])
def certificate():
    try:
        data = request.get_json()
        lang = data.get('lang', 'en')
        from certificate_report import generate_certificate
        filename = generate_certificate(data, lang)
        from flask import send_file
        return send_file(
            f'/home/canopysat/app/reports/{filename}',
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/report', methods=['POST'])
def report():
    try:
        data = request.get_json()
        lang = data.get('lang', 'en')
        # Species suitability only included if user explicitly ran the analysis
        # data['species_suitability'] is set by the frontend if user clicked ANALYZE SPECIES SUITABILITY
        from pdf_report import generate_pdf
        filename = generate_pdf(data, lang)
        from flask import send_file
        return send_file(
            f'/home/canopysat/app/reports/{filename}',
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/about')
def about():
    lang = request.args.get('lang', 'en')
    return render_template('about.html', lang=lang)

@app.route('/api-docs')
def api_docs_page():
    lang = request.args.get('lang', 'en')
    return render_template('api.html', lang=lang)

@app.route('/academy')
def academy():
    lang = request.args.get('lang', 'en')
    return render_template('academy.html', lang=lang)

@app.route('/resources')
def resources():
    lang = request.args.get('lang', 'en')
    return render_template('resources.html', lang=lang)

# Forest case studies data
FOREST_CASES = {
    'amazon-brazil': {
        'slug': 'amazon-brazil',
        'name': 'Amazon Rainforest',
        'country': 'Brazil',
        'lat': -3.4653, 'lng': -62.2159, 'size': 50,
        'score': 80, 'ndvi': 0.82, 'cover': 98.5,
        'height': 9.8, 'fires': 42, 's1': -8.2,
        'trend_3y': '+0.012', 'trend_10y': '+0.089', 'trend_40y': '+0.124',
        'ai_type': 'Dense Tropical Forest',
        'alert': 'STABLE — No significant change',
        'date': '2026-09-16',
        'description': 'The Amazon Rainforest is the world largest tropical rainforest, covering over 5.5 million km² across nine countries. It represents over half of the planet remaining rainforests and comprises the largest and most biodiverse tract of tropical rainforest in the world. CanopySat satellite monitoring shows a Forest Integrity Score of 80/100 with stable vegetation cover and no significant deforestation detected in this analysis zone.',
    },
    'congo-basin': {
        'slug': 'congo-basin',
        'name': 'Congo Basin Forest',
        'country': 'Democratic Republic of Congo',
        'lat': -0.7893, 'lng': 23.6568, 'size': 50,
        'score': 73, 'ndvi': 0.773, 'cover': 100.0,
        'height': 11.6, 'fires': 18, 's1': -9.1,
        'trend_3y': '+0.008', 'trend_10y': '+0.054', 'trend_40y': '+0.098',
        'ai_type': 'Dense Tropical Forest',
        'alert': 'STABLE — No significant change',
        'date': '2026-09-16',
        'description': 'The Congo Basin is home to the world second-largest tropical rainforest, covering approximately 3.7 million km². It is the most important carbon sink in Africa and is critical for regional climate regulation. The forest provides habitat for endangered species including forest elephants, gorillas and okapis. CanopySat satellite monitoring shows 100% forest cover with stable vegetation indices.',
    },
    'black-forest-germany': {
        'slug': 'black-forest-germany',
        'name': 'Black Forest',
        'country': 'Germany',
        'lat': 48.3614, 'lng': 8.1450, 'size': 50,
        'score': 68, 'ndvi': 0.729, 'cover': 95.8,
        'height': 10.5, 'fires': 3, 's1': -11.2,
        'trend_3y': '+0.021', 'trend_10y': '+0.187', 'trend_40y': '+0.231',
        'ai_type': 'Temperate Forest', 'agb': 78.4, 'stage': 'Old-growth forest (>120 years)',
        'alert': 'STABLE — No significant change',
        'date': '2026-09-16',
        'description': 'The Black Forest (Schwarzwald) in southwestern Germany is one of Europe most iconic temperate forests, covering approximately 6,000 km². It is characterized by dense coniferous and mixed forests, with spruce, fir and beech as dominant species. The forest has shown remarkable recovery since the 1980s acid rain period, with CanopySat satellite data confirming a positive 40-year NDVI trend of +0.231.',
    },
    'borneo-indonesia': {
        'slug': 'borneo-indonesia',
        'name': 'Borneo Rainforest',
        'country': 'Indonesia / Malaysia',
        'lat': -0.5000, 'lng': 114.0000, 'size': 50,
        'score': 51, 'ndvi': 0.613, 'cover': 72.9,
        'height': 10.0, 'fires': 991, 's1': -6.993,
        'trend_3y': '-0.018', 'trend_10y': '-0.124', 'trend_40y': '-0.198',
        'ai_type': 'Tropical/Equatorial Forest', 'agb': 45.0, 'stage': 'Mature forest (60-120 years)',
        'alert': 'CRITICAL — Severe deforestation detected',
        'date': '2026-09-16',
        'description': 'The Borneo rainforest is one of the oldest and most biodiverse rainforests on Earth, estimated at 140 million years old. However, it faces severe deforestation pressure from palm oil plantations, logging and fires. CanopySat satellite monitoring detects CRITICAL deforestation alert with 991 fire pixels per year and only 72.9% forest cover remaining — a dramatic decline from historical levels.',
    },
    'siberia-russia': {
        'slug': 'siberia-russia',
        'name': 'Siberian Taiga',
        'country': 'Russia',
        'lat': 60.0000, 'lng': 100.0000, 'size': 50,
        'score': 78, 'ndvi': 0.631, 'cover': 99.1,
        'height': 20.2, 'fires': 551, 's1': -10.22,
        'trend_3y': '+0.005', 'trend_10y': '+0.041', 'trend_40y': '+0.087',
        'ai_type': 'Boreal/Coniferous Forest', 'agb': 183.6, 'stage': 'Mature forest (60-120 years)',
        'alert': 'POSITIVE — Forest recovery detected',
        'date': '2026-09-16',
        'description': 'The Siberian Taiga is the world largest forest biome, covering over 5 million km² of boreal forest. It stores an enormous amount of carbon and plays a critical role in global climate regulation. CanopySat satellite data shows 99.1% forest cover with a positive recovery trend, though 551 fire pixels per year indicate significant wildfire activity — a growing concern under climate change.',
    },
    'kenya-forest': {
        'slug': 'kenya-forest',
        'name': 'Kenya Highlands Forest',
        'country': 'Kenya',
        'lat': -0.0236, 'lng': 37.9062, 'size': 50,
        'score': 47, 'ndvi': 0.458, 'cover': 61.8,
        'height': 6.5, 'fires': 1093, 's1': -9.261,
        'trend_3y': '-0.012', 'trend_10y': '-0.089', 'trend_40y': '-0.134',
        'ai_type': 'Savanna/Woodland', 'agb': 19.0, 'stage': 'Growing forest (20-60 years)',
        'alert': 'CRITICAL — Severe deforestation detected',
        'date': '2026-09-16',
        'description': 'The Kenya Highlands forest ecosystem is under severe pressure from agricultural expansion, charcoal production and population growth. CanopySat satellite monitoring shows CRITICAL deforestation with 1,093 fire pixels per year, 61.8% forest cover and a negative 40-year NDVI trend of -0.134. This ecosystem is critical for water security in East Africa and requires urgent protection.',
    },
    'cameroon-forest': {
        'slug': 'cameroon-forest',
        'name': 'Cameroon Forest',
        'country': 'Cameroon',
        'lat': 3.8480, 'lng': 11.5021, 'size': 50,
        'score': 73, 'ndvi': 0.691, 'cover': 89.0,
        'height': 7.5, 'fires': 1221, 's1': -7.138,
        'trend_3y': '-0.008', 'trend_10y': '+0.031', 'trend_40y': '+0.056',
        'ai_type': 'Dense Tropical Forest', 'agb': 25.3, 'stage': 'Mature forest (60-120 years)',
        'alert': 'STABLE — No significant change',
        'date': '2026-09-16',
        'description': 'Cameroon is home to a significant portion of the Congo Basin forest ecosystem, the second largest tropical rainforest in the world. CanopySat satellite monitoring shows 89% forest cover with stable vegetation. However, 1,221 fire pixels per year indicate significant fire pressure, and continued monitoring is essential to protect this biodiversity hotspot.',
    },
    'turkey-forest': {
        'slug': 'turkey-forest',
        'name': 'Turkey Forest',
        'country': 'Turkey',
        'lat': 37.8716, 'lng': 32.4846, 'size': 50,
        'score': 30, 'ndvi': 0.237, 'cover': 10.6,
        'height': 3.1, 'fires': 1006, 's1': -11.02,
        'trend_3y': '+0.014', 'trend_10y': '+0.089', 'trend_40y': '+0.112',
        'ai_type': 'Savanna/Woodland', 'agb': 4.3, 'stage': 'Young forest (0-20 years)',
        'alert': 'POSITIVE — Forest recovery detected',
        'date': '2026-09-16',
        'description': 'Central Turkey forests face significant pressure from wildfires, overgrazing and historical deforestation. CanopySat satellite monitoring shows only 10.6% forest cover with a Forest Integrity Score of 30/100. However, there is a positive recovery trend with young forest growth detected (+0.112 over 40 years), indicating reforestation efforts are having some impact despite 1,006 fire pixels per year.',
    },
    'rwanda-forest': {
        'slug': 'rwanda-forest',
        'name': 'Rwanda Highland Forest',
        'country': 'Rwanda',
        'lat': -1.9403, 'lng': 29.8739, 'size': 50,
        'score': 52, 'ndvi': 0.455, 'cover': 71.1,
        'height': 4.2, 'fires': 193, 's1': -7.859,
        'trend_3y': '-0.009', 'trend_10y': '-0.054', 'trend_40y': '-0.098',
        'ai_type': 'Tropical/Equatorial Forest', 'agb': 7.9, 'stage': 'Growing forest (20-60 years)',
        'alert': 'CRITICAL — Severe deforestation detected',
        'date': '2026-09-16',
        'description': 'Rwanda highland forests are under severe pressure despite being one of the most densely populated countries in Africa. CanopySat satellite monitoring shows CRITICAL deforestation with 71.1% forest cover and a negative long-term trend. These forests are critical habitat for mountain gorillas and play a key role in water regulation for the Great Lakes region.',
    },
    'france-forest': {
        'slug': 'france-forest',
        'name': 'French Forest',
        'country': 'France',
        'lat': 45.0000, 'lng': 2.3522, 'size': 50,
        'score': 68, 'ndvi': 0.743, 'cover': 99.2,
        'height': 8.6, 'fires': 152, 's1': -10.481,
        'trend_3y': '+0.019', 'trend_10y': '+0.143', 'trend_40y': '+0.187',
        'ai_type': 'Temperate Forest', 'agb': 33.3, 'stage': 'Mature forest (60-120 years)',
        'alert': 'STABLE — No significant change',
        'date': '2026-09-16',
        'description': 'France has significantly increased its forest cover over the past 40 years, with CanopySat satellite data confirming a positive NDVI trend of +0.187 since 1984. French forests cover approximately 31% of the national territory and are primarily composed of oak, beech and pine. The analysis zone shows 99.2% forest cover with stable vegetation health.',
    },
    'mayombe-congo': {
        'slug': 'mayombe-congo', 'name': 'Mayombe Forest', 'country': 'Congo',
        'lat': -4.5, 'lng': 12.5, 'size': 50,
        'score': 73, 'ndvi': 0.712, 'cover': 95.8, 'height': 12.1,
        'fires': 5598, 's1': -7.203, 'trend_3y': '-0.004', 'trend_10y': '+0.389', 'trend_40y': '+0.492',
        'ai_type': 'Dense Tropical Forest', 'agb': 65.9, 'stage': 'Mature forest (60-120 years)',
        'alert': 'CAUTION — Light forest degradation', 'date': '2026-09-18',
        'description': 'The Mayombe Forest in the Republic of Congo is one of the oldest and most biodiverse forests in Africa, spanning approximately 22,000 km². CanopySat satellite monitoring shows 95.8% forest cover with a CAUTION alert — 5,598 fire pixels detected per year indicate significant fire pressure on this critical ecosystem.',
    },
    'gabon-forest': {
        'slug': 'gabon-forest', 'name': 'Gabon Rainforest', 'country': 'Gabon',
        'lat': -0.5, 'lng': 11.5, 'size': 50,
        'score': 73, 'ndvi': 0.756, 'cover': 92.1, 'height': 14.2,
        'fires': 883, 's1': -7.384, 'trend_3y': '-0.006', 'trend_10y': '+0.449', 'trend_40y': '+0.696',
        'ai_type': 'Dense Tropical Forest', 'agb': 90.7, 'stage': 'Old-growth forest (>120 years)',
        'alert': 'WARNING — Significant forest loss', 'date': '2026-09-18',
        'description': 'Gabon is one of the most forested countries in Africa, with over 85% of its territory covered by tropical rainforest. CanopySat satellite monitoring shows a WARNING alert with a negative 3-year NDVI trend, indicating emerging deforestation pressure despite the country strong conservation policies.',
    },
    'madagascar-forest': {
        'slug': 'madagascar-forest', 'name': 'Madagascar Forest', 'country': 'Madagascar',
        'lat': -18.5, 'lng': 47.0, 'size': 50,
        'score': 41, 'ndvi': 0.354, 'cover': 23.3, 'height': 2.9,
        'fires': 4944, 's1': -11.677, 'trend_3y': '+0.018', 'trend_10y': '+0.182', 'trend_40y': '+0.175',
        'ai_type': 'Savanna/Woodland', 'agb': 3.8, 'stage': 'Young forest (0-20 years)',
        'alert': 'POSITIVE — Forest recovery detected', 'date': '2026-09-18',
        'description': 'Madagascar has lost over 90% of its original forest cover due to slash-and-burn agriculture. CanopySat satellite monitoring shows only 23.3% forest cover remaining. However, a POSITIVE recovery trend is detected with young forest growth (+0.018 NDVI over 3 years), suggesting reforestation efforts are beginning to take effect.',
    },
    'ivory-coast-forest': {
        'slug': 'ivory-coast-forest', 'name': 'Ivory Coast Forest', 'country': 'Côte d Ivoire',
        'lat': 6.5, 'lng': -5.5, 'size': 50,
        'score': 73, 'ndvi': 0.677, 'cover': 97.9, 'height': 9.1,
        'fires': 870, 's1': -8.191, 'trend_3y': '+0.066', 'trend_10y': '+0.370', 'trend_40y': '+0.383',
        'ai_type': 'Dense Tropical Forest', 'agb': 37.3, 'stage': 'Mature forest (60-120 years)',
        'alert': 'STABLE — No significant change', 'date': '2026-09-18',
        'description': 'The forests of Côte d Ivoire are part of the Upper Guinean forest ecosystem, one of the world biodiversity hotspots. CanopySat satellite monitoring shows 97.9% forest cover with a positive 3-year trend (+0.066), indicating forest recovery after decades of deforestation driven by cocoa and coffee cultivation.',
    },
    'western-ghats-india': {
        'slug': 'western-ghats-india', 'name': 'Western Ghats Forest', 'country': 'India',
        'lat': 10.5, 'lng': 76.5, 'size': 50,
        'score': 66, 'ndvi': 0.667, 'cover': 96.4, 'height': 10.0,
        'fires': 247, 's1': -7.797, 'trend_3y': '-0.016', 'trend_10y': '+0.353', 'trend_40y': '+0.407',
        'ai_type': 'Tropical/Equatorial Forest', 'agb': 45.0, 'stage': 'Mature forest (60-120 years)',
        'alert': 'STABLE — No significant change', 'date': '2026-09-18',
        'description': 'The Western Ghats is one of the world eight hottest biodiversity hotspots, recognized as a UNESCO World Heritage Site. CanopySat satellite monitoring shows 96.4% forest cover with stable vegetation. The slight negative 3-year trend (-0.016) warrants continued monitoring of this critical ecosystem that provides water to millions of people in India.',
    },
    'atlantic-forest-brazil': {
        'slug': 'atlantic-forest-brazil', 'name': 'Atlantic Forest', 'country': 'Brazil',
        'lat': -20.0, 'lng': -43.0, 'size': 50,
        'score': 68, 'ndvi': 0.594, 'cover': 88.1, 'height': 9.1,
        'fires': 1018, 's1': -8.769, 'trend_3y': '+0.004', 'trend_10y': '+0.299', 'trend_40y': '+0.323',
        'ai_type': 'Tropical/Equatorial Forest', 'agb': 37.3, 'stage': 'Growing forest (20-60 years)',
        'alert': 'POSITIVE — Forest recovery detected', 'date': '2026-09-18',
        'description': 'The Atlantic Forest (Mata Atlântica) is one of the most threatened biomes on Earth, having lost over 85% of its original cover. CanopySat satellite monitoring shows a POSITIVE recovery trend with growing forest regeneration, confirming the impact of Brazil conservation programs in this biodiversity hotspot that shelters over 20,000 plant species.',
    },
    'philippines-forest': {
        'slug': 'philippines-forest', 'name': 'Philippines Forest', 'country': 'Philippines',
        'lat': 7.5, 'lng': 125.0, 'size': 50,
        'score': 73, 'ndvi': 0.703, 'cover': 97.9, 'height': 8.8,
        'fires': 1349, 's1': -7.999, 'trend_3y': '-0.031', 'trend_10y': '+0.334', 'trend_40y': '+0.388',
        'ai_type': 'Dense Tropical Forest', 'agb': 34.8, 'stage': 'Mature forest (60-120 years)',
        'alert': 'STABLE — No significant change', 'date': '2026-09-18',
        'description': 'The Philippines is one of the world 18 mega-biodiversity countries, with tropical forests covering significant portions of its islands. CanopySat satellite monitoring shows 97.9% forest cover but a concerning negative 3-year NDVI trend (-0.031), indicating emerging deforestation pressure that requires urgent monitoring.',
    },
    'malaysian-forest': {
        'slug': 'malaysian-forest', 'name': 'Malaysian Rainforest', 'country': 'Malaysia',
        'lat': 4.5, 'lng': 117.5, 'size': 50,
        'score': 65, 'ndvi': 0.641, 'cover': 85.2, 'height': 9.8,
        'fires': 312, 's1': -8.102, 'trend_3y': '-0.012', 'trend_10y': '+0.187', 'trend_40y': '+0.213',
        'ai_type': 'Dense Tropical Forest', 'agb': 43.2, 'stage': 'Mature forest (60-120 years)',
        'alert': 'CAUTION — Light forest degradation', 'date': '2026-09-18',
        'description': 'Malaysian Borneo contains some of the oldest and most diverse rainforests on Earth. CanopySat satellite monitoring shows significant deforestation pressure from palm oil plantations and logging, with a negative 3-year vegetation trend. These forests are critical habitat for orangutans, pygmy elephants and thousands of endemic species.',
    },
    'colombian-amazon': {
        'slug': 'colombian-amazon', 'name': 'Colombian Amazon', 'country': 'Colombia',
        'lat': 1.0, 'lng': -73.0, 'size': 50,
        'score': 73, 'ndvi': 0.796, 'cover': 99.5, 'height': 9.6,
        'fires': 25, 's1': -7.766, 'trend_3y': '-0.020', 'trend_10y': '+0.421', 'trend_40y': '+0.445',
        'ai_type': 'Dense Tropical Forest', 'agb': 41.5, 'stage': 'Old-growth forest (>120 years)',
        'alert': 'STABLE — No significant change', 'date': '2026-09-18',
        'description': 'The Colombian Amazon covers approximately 480,000 km² and is one of the most biodiverse regions on Earth. CanopySat satellite monitoring shows 99.5% forest cover with very low fire activity (25 pixels/year). Despite the stable alert, the negative 3-year trend (-0.020) warrants continued monitoring of this critical carbon sink.',
    },
    'peruvian-amazon': {
        'slug': 'peruvian-amazon', 'name': 'Peruvian Amazon', 'country': 'Peru',
        'lat': -4.5, 'lng': -74.0, 'size': 50,
        'score': 80, 'ndvi': 0.792, 'cover': 95.0, 'height': 9.6,
        'fires': 9, 's1': -7.87, 'trend_3y': '+0.004', 'trend_10y': '+0.418', 'trend_40y': '+0.453',
        'ai_type': 'Dense Tropical Forest', 'agb': 41.5, 'stage': 'Old-growth forest (>120 years)',
        'alert': 'STABLE — No significant change', 'date': '2026-09-18',
        'description': 'The Peruvian Amazon is home to the highest biodiversity on Earth, covering over 60% of Peru territory. CanopySat satellite monitoring shows a Forest Integrity Score of 80/100 — the highest in our database — with 95% forest cover, only 9 fire pixels per year and a positive long-term vegetation trend.',
    },
    'canadian-boreal': {
        'slug': 'canadian-boreal', 'name': 'Canadian Boreal Forest', 'country': 'Canada',
        'lat': 55.0, 'lng': -95.0, 'size': 50,
        'score': 56, 'ndvi': 0.502, 'cover': 76.4, 'height': 16.1,
        'fires': 25, 's1': -12.774, 'trend_3y': '+0.001', 'trend_10y': '+0.375', 'trend_40y': '+0.327',
        'ai_type': 'Boreal/Coniferous Forest', 'agb': 116.6, 'stage': 'Growing forest (20-60 years)',
        'alert': 'WARNING — Significant forest loss', 'date': '2026-09-18',
        'description': 'The Canadian Boreal Forest is the world largest intact forest ecosystem, covering approximately 3 million km². CanopySat satellite monitoring shows a WARNING alert with 76.4% forest cover and significant biomass (116.6 t/ha). This forest stores enormous amounts of carbon and is increasingly threatened by wildfires intensified by climate change.',
    },
    'pacific-northwest-usa': {
        'slug': 'pacific-northwest-usa', 'name': 'Pacific Northwest Forest', 'country': 'United States',
        'lat': 47.5, 'lng': -122.5, 'size': 50,
        'score': 49, 'ndvi': 0.417, 'cover': 60.2, 'height': 7.5,
        'fires': 274, 's1': -12.396, 'trend_3y': '+0.019', 'trend_10y': '+0.223', 'trend_40y': '+0.231',
        'ai_type': 'Temperate Forest', 'agb': 25.3, 'stage': 'Growing forest (20-60 years)',
        'alert': 'STABLE — No significant change', 'date': '2026-09-18',
        'description': 'The Pacific Northwest temperate rainforest is one of the rarest ecosystems on Earth, characterized by Douglas fir, Sitka spruce and western red cedar. CanopySat satellite monitoring shows 60.2% forest cover with a positive recovery trend, reflecting ongoing reforestation efforts after decades of logging in Washington and Oregon states.',
    },
    'bialowieza-poland': {
        'slug': 'bialowieza-poland', 'name': 'Białowieża Forest', 'country': 'Poland / Belarus',
        'lat': 52.7, 'lng': 23.8, 'size': 50,
        'score': 57, 'ndvi': 0.653, 'cover': 96.1, 'height': 20.9,
        'fires': 98, 's1': -10.579, 'trend_3y': '-0.064', 'trend_10y': '+0.352', 'trend_40y': '+0.382',
        'ai_type': 'Temperate Forest', 'agb': 196.6, 'stage': 'Mature forest (60-120 years)',
        'alert': 'STABLE — No significant change', 'date': '2026-09-18',
        'description': 'Białowieża Forest is one of the last and largest remnants of the primeval forest that once covered much of Europe. A UNESCO World Heritage Site shared between Poland and Belarus, it is home to the European bison. CanopySat satellite monitoring shows 96.1% forest cover with 20.9m canopy height and very high biomass (196.6 t/ha), but a concerning 3-year decline (-0.064).',
    },
    'swedish-boreal': {
        'slug': 'swedish-boreal', 'name': 'Swedish Boreal Forest', 'country': 'Sweden',
        'lat': 64.0, 'lng': 18.0, 'size': 50,
        'score': 39, 'ndvi': 0.453, 'cover': 65.0, 'height': 14.5,
        'fires': 32, 's1': -10.47, 'trend_3y': '-0.203', 'trend_10y': '+0.179', 'trend_40y': '+0.232',
        'ai_type': 'Boreal/Coniferous Forest', 'agb': 94.6, 'stage': 'Growing forest (20-60 years)',
        'alert': 'CRITICAL — Severe deforestation detected', 'date': '2026-09-18',
        'description': 'The Swedish boreal forest (taiga) covers approximately 60% of Sweden land area. CanopySat satellite monitoring detects a CRITICAL alert with a severe 3-year NDVI decline of -0.203 — the worst in our European database. This alarming trend likely reflects intensive logging and bark beetle infestations amplified by climate change.',
    },
    'romanian-carpathian': {
        'slug': 'romanian-carpathian', 'name': 'Romanian Carpathian Forest', 'country': 'Romania',
        'lat': 45.5, 'lng': 25.0, 'size': 50,
        'score': 68, 'ndvi': 0.732, 'cover': 92.6, 'height': 11.7,
        'fires': 370, 's1': -9.184, 'trend_3y': '-0.009', 'trend_10y': '+0.424', 'trend_40y': '+0.467',
        'ai_type': 'Temperate Forest', 'agb': 61.6, 'stage': 'Mature forest (60-120 years)',
        'alert': 'CAUTION — Light forest degradation', 'date': '2026-09-18',
        'description': 'The Romanian Carpathians contain the largest old-growth forest in Europe outside of Russia, with beech, oak and spruce as dominant species. CanopySat satellite monitoring shows 92.6% forest cover with a CAUTION alert. Romania faces significant illegal logging pressure, and the negative 3-year trend (-0.009) confirms ongoing forest degradation.',
    },
    'belgium-forest': {
        'slug': 'belgium-forest',
        'name': 'Belgian Ardennes Forest',
        'country': 'Belgium',
        'lat': 50.5039, 'lng': 4.4699, 'size': 50,
        'score': 68, 'ndvi': 0.629, 'cover': 90.1,
        'height': 4.2, 'fires': 237, 's1': -9.404,
        'trend_3y': '+0.022', 'trend_10y': '+0.098', 'trend_40y': '+0.156',
        'ai_type': 'Temperate Forest', 'agb': 7.9, 'stage': 'Mature forest (60-120 years)',
        'alert': 'POSITIVE — Forest recovery detected',
        'date': '2026-09-16',
        'description': 'The Belgian Ardennes is one of Western Europe most important temperate forest regions, covering the southern part of Belgium. CanopySat satellite monitoring shows 90.1% forest cover with a positive recovery trend (+0.156 over 40 years). The forest is dominated by spruce, oak and beech, and plays a critical role in water regulation for the Meuse and Semois river basins.',
    },
}

# ═══ FOREST GUARDIAN — User Authentication ═══
import sqlite3 as sq_guard
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

def get_guardian_db():
    conn = sq_guard.connect('/home/canopysat/app/guardian.db')
    conn.row_factory = sq_guard.Row
    return conn

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return redirect('/guardian/login')
        return f(*args, **kwargs)
    return decorated

@app.route('/guardian')
@login_required
def guardian_dashboard():
    user_id = session.get('user_id')
    lang = request.args.get('lang', 'en')
    conn = get_guardian_db()
    user = conn.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
    zones = conn.execute('SELECT * FROM guardian_zones WHERE user_id=? AND active=1 ORDER BY created_at DESC', (user_id,)).fetchall()
    zone_data = []
    for zone in zones:
        analyses = conn.execute('SELECT * FROM guardian_analyses WHERE zone_id=? ORDER BY created_at DESC LIMIT 12', (zone['id'],)).fetchall()
        zone_data.append({'zone': dict(zone), 'analyses': [dict(a) for a in analyses]})
    conn.close()
    return render_template('guardian_dashboard.html', user=dict(user), zones=zone_data, lang=lang)

@app.route('/guardian/register', methods=['GET', 'POST'])
def guardian_register():
    if request.method == 'GET':
        return render_template('guardian_register.html')
    data = request.get_json() or request.form
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()
    name = data.get('name', '').strip()
    if not email or not password or len(password) < 6:
        return jsonify({'error': 'Email and password (min 6 chars) required'}), 400
    conn = get_guardian_db()
    try:
        conn.execute('INSERT INTO users (email, password_hash, name) VALUES (?,?,?)',
            (email, generate_password_hash(password), name))
        conn.commit()
        user = conn.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
        session['user_id'] = user['id']
        session['user_email'] = email
        
        # Send welcome email
        welcome_body = "<html><body style='font-family:Arial,sans-serif;background:#0D3B2E;padding:20px;'>"
        welcome_body += "<div style='max-width:600px;margin:0 auto;background:#1B4332;border-radius:12px;padding:25px;border:1px solid #1B6B45;'>"
        welcome_body += "<h1 style='color:#3DAA6B;text-align:center;font-size:18px;'>🛡️ CANOPYSAT FOREST GUARDIAN</h1>"
        welcome_body += "<p style='color:#D6EFE1;text-align:center;'>Welcome to Forest Guardian — Satellite Forest Monitoring</p>"
        welcome_body += f"<p style='color:#D6EFE1;'>Hello {name or email},</p>"
        welcome_body += "<p style='color:#D6EFE1;'>Your free Forest Guardian account is ready. You can now:</p>"
        welcome_body += "<ul style='color:#D6EFE1;line-height:2;'>"
        welcome_body += "<li>🌿 Add 1 forest zone (Free plan)</li>"
        welcome_body += "<li>🛰️ Get monthly satellite analysis</li>"
        welcome_body += "<li>📧 Receive email alerts when changes are detected</li>"
        welcome_body += "<li>📄 Download PDF reports</li>"
        welcome_body += "<li>📏 NASA GEDI LiDAR canopy height data</li>"
        welcome_body += "</ul>"
        welcome_body += "<div style='text-align:center;margin-top:20px;'>"
        welcome_body += "<a href='https://www.canopysat.org/guardian' style='display:inline-block;padding:12px 25px;background:#2D8A5A;color:white;border-radius:8px;text-decoration:none;font-size:13px;font-weight:bold;'>🛡️ Go to Dashboard</a>"
        welcome_body += "</div>"
        welcome_body += "<p style='color:#2D6A4F;font-size:10px;text-align:center;margin-top:20px;'>CanopySat Forest Guardian · canopysat.org · contact@canopysat.org</p>"
        welcome_body += "</div></body></html>"
        send_email(email, '🌿 Welcome to CanopySat Forest Guardian', welcome_body)
        
        return jsonify({'success': True, 'redirect': '/guardian'})
    except sq_guard.IntegrityError:
        return jsonify({'error': 'Email already registered'}), 400
    finally:
        conn.close()

@app.route('/guardian/login', methods=['GET', 'POST'])
def guardian_login():
    if request.method == 'GET':
        return render_template('guardian_login.html')
    data = request.get_json() or request.form
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()
    conn = get_guardian_db()
    user = conn.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
    conn.close()
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Invalid email or password'}), 401
    session['user_id'] = user['id']
    session['user_email'] = email
    return jsonify({'success': True, 'redirect': '/guardian'})

@app.route('/guardian/logout')
def guardian_logout():
    session.clear()
    return redirect('/guardian/login')

@app.route('/guardian/zone/add', methods=['POST'])
@login_required
def guardian_zone_add():
    user_id = session.get('user_id')
    data = request.get_json()
    conn = get_guardian_db()
    user = conn.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
    zone_count = conn.execute('SELECT COUNT(*) FROM guardian_zones WHERE user_id=? AND active=1', (user_id,)).fetchone()[0]
    max_zones = {'free': 1, 'pro': 5, 'business': 20}.get(user['plan'], 1)
    if zone_count >= max_zones:
        conn.close()
        return jsonify({'error': f'Plan {user["plan"]} allows max {max_zones} zone(s). Upgrade to add more.'}), 403
    conn.execute('INSERT INTO guardian_zones (user_id, name, lat, lng, size, frequency) VALUES (?,?,?,?,?,?)',
        (user_id, data.get('name'), data.get('lat'), data.get('lng'),
         data.get('size', 10), data.get('frequency', 'monthly')))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/guardian/zone/delete/<int:zone_id>', methods=['POST'])
@login_required
def guardian_zone_delete(zone_id):
    user_id = session.get('user_id')
    conn = get_guardian_db()
    conn.execute('UPDATE guardian_zones SET active=0 WHERE id=? AND user_id=?', (zone_id, user_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/guardian/analyze/<int:zone_id>', methods=['POST'])
@login_required
def guardian_analyze_zone(zone_id):
    import threading
    user_id = session.get('user_id')
    conn = get_guardian_db()
    zone = conn.execute('SELECT * FROM guardian_zones WHERE id=? AND user_id=?', (zone_id, user_id)).fetchone()
    conn.close()
    if not zone:
        return jsonify({'error': 'Zone not found'}), 404

    def run_analysis():
        from gee_analysis import analyze_forest
        result = analyze_forest(zone['lat'], zone['lng'], zone['size'])
        if result and result.get('success') != False:
            db = get_guardian_db()
            db.execute('''INSERT INTO guardian_analyses
                (zone_id, user_id, score, ndvi, forest_cover, canopy_height,
                 deforestation_alert, active_fires, trend, biomass)
                VALUES (?,?,?,?,?,?,?,?,?,?)''',
                (zone_id, user_id, result.get('score'),
                 result.get('ndvi_current'), result.get('forest_cover'),
                 result.get('canopy_height'), result.get('deforestation_alert'),
                 result.get('active_fires'), result.get('trend'),
                 result.get('estimated_agb')))
            db.execute('UPDATE guardian_zones SET last_analysis=CURRENT_TIMESTAMP WHERE id=?', (zone_id,))
            db.commit()
            db.close()

    threading.Thread(target=run_analysis, daemon=True).start()
    return jsonify({'success': True, 'message': 'Analysis started — results in 2-3 minutes'})

@app.route('/report/guardian/<int:zone_id>')
@login_required
def guardian_pdf(zone_id):
    user_id = session.get('user_id')
    conn = get_guardian_db()
    zone = conn.execute('SELECT * FROM guardian_zones WHERE id=? AND user_id=?', (zone_id, user_id)).fetchone()
    conn.close()
    if not zone:
        return jsonify({'error': 'Zone not found'}), 404
    # Run full analysis for complete PDF
    from gee_analysis import analyze_forest
    from pdf_report import generate_pdf
    import os as os2
    result = analyze_forest(zone['lat'], zone['lng'], zone['size'])
    if not result or result.get('success') == False:
        return jsonify({'error': 'Analysis failed'}), 500
    result['size_km'] = zone['size']
    pdf_file = generate_pdf(result, 'en')
    pdf_path = os2.path.join('/home/canopysat/app/reports', pdf_file)
    from flask import send_file
    return send_file(pdf_path, as_attachment=True, download_name=f'CanopySat_Guardian_{zone["name"].replace(" ","_")}.pdf')

@app.route('/report/guardian/share/<int:zone_id>')
@login_required
def guardian_share(zone_id):
    import sqlite3 as sq, random, string
    user_id = session.get('user_id')
    conn = get_guardian_db()
    zone = conn.execute('SELECT * FROM guardian_zones WHERE id=? AND user_id=?', (zone_id, user_id)).fetchone()
    analysis = conn.execute('SELECT * FROM guardian_analyses WHERE zone_id=? ORDER BY created_at DESC LIMIT 1', (zone_id,)).fetchone()
    conn.close()
    if not zone or not analysis:
        return jsonify({'error': 'No data found'}), 404
    
    # Create shared report
    slug = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    rconn = sq.connect('/home/canopysat/app/community.db')
    rconn.execute('''INSERT INTO shared_reports 
        (slug, lat, lng, size, score, ndvi, forest_cover, canopy_height,
         deforestation_alert, active_fires, trend, ai_forest_type, lang)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
        slug, zone['lat'], zone['lng'], zone['size'],
        analysis['score'], analysis['ndvi'], analysis['forest_cover'],
        analysis['canopy_height'], analysis['deforestation_alert'],
        analysis['active_fires'], analysis['trend'],
        'Forest Zone', 'en'
    ))
    rconn.commit()
    rconn.close()
    return redirect(f'/report/{slug}')

@app.route('/guardian/upgrade')
def guardian_upgrade():
    lang = request.args.get('lang', 'en')
    return render_template('guardian_upgrade.html', lang=lang)

@app.route('/guardian/forgot', methods=['GET', 'POST'])
def guardian_forgot():
    if request.method == 'GET':
        return render_template('guardian_forgot.html')
    data = request.get_json() or request.form
    email = data.get('email', '').strip().lower()
    conn = get_guardian_db()
    user = conn.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
    if user:
        import secrets
        token = secrets.token_urlsafe(32)
        conn.execute('UPDATE users SET verify_token=? WHERE email=?', (token, email))
        conn.commit()
        reset_url = f'https://www.canopysat.org/guardian/reset/{token}'
        body = "<html><body style='font-family:Arial,sans-serif;background:#0D3B2E;padding:20px;'>"
        body += "<div style='max-width:500px;margin:0 auto;background:#1B4332;border-radius:12px;padding:25px;border:1px solid #1B6B45;'>"
        body += "<h2 style='color:#3DAA6B;text-align:center;'>Password Reset</h2>"
        body += f"<p style='color:#D6EFE1;'>Hello {user['name'] or email},</p>"
        body += "<p style='color:#D6EFE1;'>Click the button below to reset your password:</p>"
        body += f"<div style='text-align:center;margin:20px 0;'><a href='{reset_url}' style='display:inline-block;padding:12px 25px;background:#2D8A5A;color:white;border-radius:8px;text-decoration:none;font-weight:bold;'>Reset Password</a></div>"
        body += "<p style='color:#2D6A4F;font-size:11px;'>This link expires in 1 hour. If you did not request this, ignore this email.</p>"
        body += "</div></body></html>"
        send_email(email, 'CanopySat Guardian — Password Reset', body)
    conn.close()
    return jsonify({'success': True, 'message': 'If this email exists, a reset link has been sent.'})

@app.route('/guardian/reset/<token>', methods=['GET', 'POST'])
def guardian_reset(token):
    if request.method == 'GET':
        return render_template('guardian_reset.html', token=token)
    data = request.get_json() or request.form
    password = data.get('password', '').strip()
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    from werkzeug.security import generate_password_hash
    conn = get_guardian_db()
    user = conn.execute('SELECT * FROM users WHERE verify_token=?', (token,)).fetchone()
    if not user:
        conn.close()
        return jsonify({'error': 'Invalid or expired token'}), 400
    conn.execute('UPDATE users SET password_hash=?, verify_token=NULL WHERE id=?',
        (generate_password_hash(password), user['id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'redirect': '/guardian/login'})

@app.route('/guardian/zone/status/<int:zone_id>')
@login_required
def guardian_zone_status(zone_id):
    user_id = session.get('user_id')
    conn = get_guardian_db()
    zone = conn.execute('SELECT last_analysis FROM guardian_zones WHERE id=? AND user_id=?', (zone_id, user_id)).fetchone()
    conn.close()
    if not zone:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({'new_analysis': zone['last_analysis'] is not None})

@app.route('/guardian/profile', methods=['GET', 'POST'])
@login_required
def guardian_profile():
    user_id = session.get('user_id')
    if request.method == 'GET':
        conn = get_guardian_db()
        user = conn.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
        conn.close()
        return jsonify({'email': user['email'], 'name': user['name'], 'plan': user['plan']})
    data = request.get_json()
    conn = get_guardian_db()
    if data.get('name'):
        conn.execute('UPDATE users SET name=? WHERE id=?', (data['name'], user_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/dataset/<int:dataset_id>')
def dataset_detail(dataset_id):
    import sqlite3 as sq
    lang = request.args.get('lang', 'en')
    conn = sq.connect('/home/canopysat/app/library.db')
    conn.row_factory = sq.Row
    ds = conn.execute('SELECT * FROM datasets WHERE id=? AND approved=1', (dataset_id,)).fetchone()
    conn.close()
    if not ds:
        return '<h3 style="font-family:sans-serif;padding:20px;color:#E53935;">Dataset not found</h3>', 404
    return render_template('dataset_detail.html', ds=dict(ds), lang=lang)

@app.route('/validation')
def validation():
    import json as js
    lang = request.args.get('lang', 'en')
    try:
        with open('/home/canopysat/app/validation_results.json') as f:
            data = js.load(f)
    except:
        data = {}
    return render_template('validation.html', data=data, lang=lang)

@app.route('/sitemap.xml')
def sitemap():
    from flask import Response
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    
    urls = [
        ('https://www.canopysat.org/', '1.0', 'daily'),
        ('https://www.canopysat.org/about', '0.8', 'monthly'),
        ('https://www.canopysat.org/api-docs', '0.8', 'monthly'),
        ('https://www.canopysat.org/academy', '0.7', 'monthly'),
        ('https://www.canopysat.org/community', '0.7', 'weekly'),
        ('https://www.canopysat.org/resources', '0.6', 'monthly'),
        ('https://www.canopysat.org/library', '0.6', 'weekly'),
        ('https://www.canopysat.org/field', '0.7', 'monthly'),
        ('https://www.canopysat.org/forest', '0.9', 'weekly'),
        ('https://www.canopysat.org/forest/amazon-brazil', '0.9', 'weekly'),
        ('https://www.canopysat.org/forest/congo-basin', '0.9', 'weekly'),
        ('https://www.canopysat.org/forest/black-forest-germany', '0.8', 'weekly'),
        ('https://www.canopysat.org/forest/borneo-indonesia', '0.8', 'weekly'),
        ('https://www.canopysat.org/forest/siberia-russia', '0.8', 'weekly'),
        ('https://www.canopysat.org/forest/kenya-forest', '0.8', 'weekly'),
        ('https://www.canopysat.org/forest/cameroon-forest', '0.8', 'weekly'),
        ('https://www.canopysat.org/forest/turkey-forest', '0.8', 'weekly'),
        ('https://www.canopysat.org/forest/rwanda-forest', '0.8', 'weekly'),
        ('https://www.canopysat.org/forest/france-forest', '0.8', 'weekly'),
        ('https://www.canopysat.org/forest/belgium-forest', '0.8', 'weekly'),
        ('https://www.canopysat.org/forest/mayombe-congo', '0.8', 'weekly'),
        ('https://www.canopysat.org/forest/gabon-forest', '0.8', 'weekly'),
        ('https://www.canopysat.org/forest/madagascar-forest', '0.8', 'weekly'),
        ('https://www.canopysat.org/forest/ivory-coast-forest', '0.8', 'weekly'),
        ('https://www.canopysat.org/forest/western-ghats-india', '0.8', 'weekly'),
        ('https://www.canopysat.org/forest/atlantic-forest-brazil', '0.8', 'weekly'),
        ('https://www.canopysat.org/forest/philippines-forest', '0.8', 'weekly'),
        ('https://www.canopysat.org/forest/malaysian-forest', '0.8', 'weekly'),
        ('https://www.canopysat.org/forest/colombian-amazon', '0.8', 'weekly'),
        ('https://www.canopysat.org/forest/peruvian-amazon', '0.8', 'weekly'),
        ('https://www.canopysat.org/forest/canadian-boreal', '0.8', 'weekly'),
        ('https://www.canopysat.org/forest/pacific-northwest-usa', '0.8', 'weekly'),
        ('https://www.canopysat.org/forest/bialowieza-poland', '0.8', 'weekly'),
        ('https://www.canopysat.org/forest/swedish-boreal', '0.8', 'weekly'),
        ('https://www.canopysat.org/forest/romanian-carpathian', '0.8', 'weekly'),
        ('https://www.canopysat.org/validation', '0.9', 'monthly'),
        ('https://www.canopysat.org/platform', '0.8', 'monthly'),
        ('https://www.canopysat.org/carbon', '0.8', 'monthly'),
        ('https://www.canopysat.org/science', '0.8', 'monthly'),
        ('https://www.canopysat.org/science/methodology', '0.7', 'monthly'),
        ('https://www.canopysat.org/science/forest-integrity-score', '0.7', 'monthly'),
        ('https://www.canopysat.org/science/limitations', '0.7', 'monthly'),
        ('https://www.canopysat.org/explore', '0.8', 'monthly'),
        ('https://www.canopysat.org/learn', '0.7', 'monthly'),
        ('https://www.canopysat.org/map', '0.8', 'weekly'),
        ('https://www.canopysat.org/dataset/1', '0.8', 'monthly'),
        ('https://www.canopysat.org/dataset/2', '0.8', 'monthly'),
        ('https://www.canopysat.org/guardian/register', '0.7', 'monthly'),
        ('https://www.canopysat.org/contact', '0.6', 'monthly'),
    ]
    
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url, priority, freq in urls:
        xml += f'  <url>\n'
        xml += f'    <loc>{url}</loc>\n'
        xml += f'    <lastmod>{today}</lastmod>\n'
        xml += f'    <changefreq>{freq}</changefreq>\n'
        xml += f'    <priority>{priority}</priority>\n'
        xml += f'  </url>\n'
    xml += '</urlset>'
    
    return Response(xml, mimetype='application/xml')

@app.route('/robots.txt')
def robots():
    from flask import Response
    content = "User-agent: *\nAllow: /\nSitemap: https://www.canopysat.org/sitemap.xml\n"
    return Response(content, mimetype='text/plain')

@app.route('/about/team')
def about_team():
    lang = request.args.get('lang', 'en')
    return render_template('about_team.html', lang=lang)

@app.route('/about/open-source')
def about_opensource():
    lang = request.args.get('lang', 'en')
    return render_template('about_opensource.html', lang=lang)

@app.route('/carbon')
def carbon():
    lang = request.args.get('lang', 'en')
    return render_template('carbon.html', lang=lang)

@app.route('/explore')
def explore():
    lang = request.args.get('lang', 'en')
    return render_template('explore.html', lang=lang)

@app.route('/learn')
def learn():
    lang = request.args.get('lang', 'en')
    return render_template('learn.html', lang=lang)

@app.route('/science')
def science():
    lang = request.args.get('lang', 'en')
    return render_template('science.html', lang=lang)

@app.route('/science/methodology')
def science_methodology():
    lang = request.args.get('lang', 'en')
    return render_template('science_methodology.html', lang=lang)

@app.route('/science/forest-integrity-score')
def science_score():
    lang = request.args.get('lang', 'en')
    return render_template('science_score.html', lang=lang)

@app.route('/science/limitations')
def science_limitations():
    lang = request.args.get('lang', 'en')
    return render_template('science_limitations.html', lang=lang)

@app.route('/platform')
def platform():
    lang = request.args.get('lang', 'en')
    return render_template('platform.html', lang=lang)

@app.route('/map')
def forest_map():
    lang = request.args.get('lang', 'en')
    forests = list(FOREST_CASES.values())
    return render_template('forest_map.html', forests=forests, lang=lang)

@app.route('/forest')
def forest_index():
    lang = request.args.get('lang', 'en')
    cases = list(FOREST_CASES.values())
    return render_template('forest_index.html', cases=cases, lang=lang)

@app.route('/forest/<slug>')
def forest_case(slug):
    lang = request.args.get('lang', 'en')
    forest = FOREST_CASES.get(slug)
    if not forest:
        return '<h3 style="font-family:sans-serif;padding:20px;color:#E53935;">Forest case not found</h3>', 404
    related = [v for k,v in FOREST_CASES.items() if k != slug][:4]
    return render_template('forest_case.html', forest=forest, related=related, lang=lang)

@app.route('/field')
def field():
    lang = request.args.get('lang', 'en')
    return render_template('field.html', lang=lang)

@app.route('/library')
def library():
    import sqlite3 as sq
    conn = sq.connect('/home/canopysat/app/library.db')
    c = conn.cursor()
    pubs = c.execute('SELECT * FROM publications WHERE approved=1 ORDER BY created_at DESC').fetchall()
    datasets = c.execute('SELECT * FROM datasets WHERE approved=1 ORDER BY created_at DESC').fetchall()
    conn.close()
    lang = request.args.get('lang', 'en')
    return render_template('library.html', publications=pubs, datasets=datasets, lang=lang)

@app.route('/compare', methods=['POST'])
def compare():
    import threading
    data = request.get_json()
    lat = float(data.get('lat', 0))
    lng = float(data.get('lng', 0))
    size = float(data.get('size', 10))
    date1_start = data.get('date1_start')
    date1_end = data.get('date1_end')
    date2_start = data.get('date2_start')
    date2_end = data.get('date2_end')
    if not all([lat, lng, date1_start, date1_end, date2_start, date2_end]):
        return jsonify({'error': 'All fields are required'}), 400
    from gee_analysis import compare_forest_dates
    result = compare_forest_dates(lat, lng, size, date1_start, date1_end, date2_start, date2_end)
    return jsonify(result)

@app.route('/compare/maps', methods=['POST'])
def compare_maps():
    import threading, uuid
    data = request.get_json()
    lat = float(data.get('lat', 0))
    lng = float(data.get('lng', 0))
    size = float(data.get('size', 10))
    date1_start = data.get('date1_start')
    date1_end = data.get('date1_end')
    date2_start = data.get('date2_start')
    date2_end = data.get('date2_end')
    job_id = str(uuid.uuid4())[:8]
    
    import json as json_mod
    job_file = f'/home/canopysat/app/static/comparison_maps/job_{job_id}.json'
    with open(job_file, 'w') as f:
        json_mod.dump({'status': 'processing'}, f)
    
    def generate():
        try:
            from gee_analysis import generate_comparison_maps
            maps = generate_comparison_maps(lat, lng, size, date1_start, date1_end, date2_start, date2_end)
            with open(job_file, 'w') as f:
                json_mod.dump({'status': 'done', 'maps': maps}, f)
        except Exception as e:
            with open(job_file, 'w') as f:
                json_mod.dump({'status': 'error', 'error': str(e)}, f)
    
    t = threading.Thread(target=generate)
    t.daemon = True
    t.start()
    return jsonify({'job_id': job_id, 'status': 'processing'})

@app.route('/report/create', methods=['POST'])
def report_create():
    import sqlite3 as sq, random, string
    data = request.get_json()
    
    # Generate unique slug
    slug = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    
    conn = sq.connect('/home/canopysat/app/community.db')
    try:
        conn.execute('''INSERT INTO shared_reports 
            (slug, lat, lng, size, score, ndvi, forest_cover, canopy_height,
             canopy_height_rh50, gedi_cover, ai_forest_type, ai_forest_type_fr,
             deforestation_alert, deforestation_alert_fr, active_fires,
             sentinel1_vv, trend, trend_fr, country, lang)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
            slug,
            data.get('lat'), data.get('lng'), data.get('size', 10),
            data.get('score'), data.get('ndvi_current'),
            data.get('forest_cover'), data.get('canopy_height'),
            data.get('canopy_height_rh50'), data.get('gedi_cover'),
            data.get('ai_forest_type'), data.get('ai_forest_type_fr'),
            data.get('deforestation_alert'), data.get('deforestation_alert_fr'),
            data.get('active_fires'), data.get('sentinel1_vv'),
            data.get('trend'), data.get('trend_fr'),
            data.get('country', ''), data.get('lang', 'en')
        ))
        conn.commit()
        return jsonify({'success': True, 'slug': slug, 'url': f'/report/{slug}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/report/<slug>')
def shared_report_view(slug):
    import sqlite3 as sq
    conn = sq.connect('/home/canopysat/app/community.db')
    r = conn.execute('SELECT * FROM shared_reports WHERE slug=?', (slug,)).fetchone()
    conn.close()
    if not r:
        return '<h3 style="font-family:sans-serif;padding:20px;color:#E53935;">Report not found</h3>', 404
    report = {
        'slug': r[1], 'lat': r[2], 'lng': r[3], 'size': r[4],
        'score': r[5], 'ndvi': r[6], 'forest_cover': r[7],
        'canopy_height': r[8], 'canopy_height_rh50': r[9], 'gedi_cover': r[10],
        'ai_forest_type': r[11], 'ai_forest_type_fr': r[12],
        'deforestation_alert': r[13], 'deforestation_alert_fr': r[14],
        'active_fires': r[15], 'sentinel1_vv': r[16],
        'trend': r[17], 'trend_fr': r[18],
        'country': r[19], 'lang': r[20], 'created_at': r[21]
    }
    return render_template('report.html', report=report)

@app.route('/geotiff', methods=['POST'])
def geotiff():
    data = request.get_json()
    lat = float(data.get('lat', 0))
    lng = float(data.get('lng', 0))
    size = float(data.get('size', 10))
    date_start = data.get('date_start')
    date_end = data.get('date_end')
    map_type = data.get('map_type', 'ndvi')
    from gee_analysis import generate_geotiff
    result = generate_geotiff(lat, lng, size, date_start, date_end, map_type)
    return jsonify(result)

@app.route('/compare/maps/status/<job_id>')
def compare_maps_status(job_id):
    import json as json_mod
    job_file = f'/home/canopysat/app/static/comparison_maps/job_{job_id}.json'
    try:
        with open(job_file) as f:
            return jsonify(json_mod.load(f))
    except:
        return jsonify({'status': 'not_found'})

@app.route('/alerts/register', methods=['POST'])
def alerts_register():
    import sqlite3 as sq
    data = request.get_json()
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    country = data.get('country', '').strip()
    lat = float(data.get('lat', 0))
    lng = float(data.get('lng', 0))
    zone_size = float(data.get('size', 10))
    zone_name = data.get('zone_name', '').strip()
    if not all([first_name, last_name, email, lat, lng]):
        return jsonify({'error': 'First name, last name, email and coordinates are required'}), 400
    try:
        from gee_analysis import analyze_forest
        result = analyze_forest(lat, lng, zone_size)
        current_score = result.get('score', 0)
        current_ndvi = result.get('ndvi_current', 0)
        conn = sq.connect('/home/canopysat/app/alerts.db')
        conn.execute('''INSERT INTO alerts 
            (first_name, last_name, email, phone, country, lat, lng, 
             zone_size, zone_name, last_score, last_ndvi, last_checked)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)''',
            (first_name, last_name, email, phone, country, lat, lng,
             zone_size, zone_name, current_score, current_ndvi))
        conn.commit()
        conn.close()
        return jsonify({
            'success': True,
            'message': f'Alert registered! You will receive an email at {email} when significant forest changes are detected.',
            'current_score': current_score,
            'zone_name': zone_name or f'Zone at {lat:.4f}, {lng:.4f}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/community/admin')
def community_admin():
    auth = request.args.get('key', '')
    if auth != 'canopysat2026admin':
        return '<h3 style="font-family:sans-serif;color:#E53935;padding:20px;">Access denied — invalid key</h3>', 403
    return render_template('community_admin.html')

@app.route('/community/event/delete/<int:event_id>', methods=['DELETE', 'POST'])
def community_event_delete(event_id):
    import sqlite3 as sq
    conn = sq.connect('/home/canopysat/app/community.db')
    conn.execute('DELETE FROM events WHERE id=?', (event_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/community/event/add', methods=['POST'])
def community_event_add():
    import sqlite3 as sq
    data = request.get_json()
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    date = data.get('date', '').strip()
    event_type = data.get('type', 'event').strip()
    link = data.get('link', '/contact').strip()
    
    if not title or not date:
        return jsonify({'error': 'Title and date required'}), 400
    
    conn = sq.connect('/home/canopysat/app/community.db')
    conn.execute('INSERT INTO events (title, description, date, type, link) VALUES (?,?,?,?,?)',
                (title, description, date, event_type, link))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/library/admin')
def library_admin():
    auth = request.args.get('key', '')
    if auth != 'canopysat2026admin':
        return '<h3 style="font-family:sans-serif;color:#E53935;padding:20px;">Access denied — invalid key</h3>', 403
    return render_template('library_admin.html')

@app.route('/library/admin/data')
def library_admin_data():
    import sqlite3 as sq
    conn = sq.connect('/home/canopysat/app/library.db')
    c = conn.cursor()
    pubs = c.execute('SELECT * FROM publications WHERE approved=0 ORDER BY created_at DESC').fetchall()
    datasets = c.execute('SELECT * FROM datasets WHERE approved=0 ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify({
        'pending_publications': [{'id':p[0],'title':p[1],'authors':p[2],'org':p[3],
            'country':p[4],'abstract':p[5],'type':p[6],'doi':p[7],'url':p[8],
            'file':p[9],'keywords':p[10],'date':p[12]} for p in pubs],
        'pending_datasets': [{'id':d[0],'title':d[1],'authors':d[2],'org':d[3],
            'country':d[4],'description':d[5],'format':d[6],'file':d[8],
            'keywords':d[9],'date':d[11]} for d in datasets]
    })

@app.route('/library/approve/<ltype>/<int:item_id>')
def library_approve(ltype, item_id):
    import sqlite3 as sq
    conn = sq.connect('/home/canopysat/app/library.db')
    if ltype == 'publication':
        conn.execute('UPDATE publications SET approved=1 WHERE id=?', (item_id,))
    else:
        conn.execute('UPDATE datasets SET approved=1 WHERE id=?', (item_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/library/reject/<ltype>/<int:item_id>')
def library_reject(ltype, item_id):
    import sqlite3 as sq
    conn = sq.connect('/home/canopysat/app/library.db')
    if ltype == 'publication':
        conn.execute('DELETE FROM publications WHERE id=?', (item_id,))
    else:
        conn.execute('DELETE FROM datasets WHERE id=?', (item_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/library/submit', methods=['POST'])
def library_submit():
    import sqlite3 as sq
    import os
    data = request.form
    file = request.files.get('file')
    
    title = data.get('title', '').strip()
    authors = data.get('authors', '').strip()
    sub_type = data.get('type', 'publication')
    
    if not title or not authors:
        return jsonify({'error': 'Title and authors are required'}), 400
    
    file_path = None
    if file and file.filename:
        safe_name = file.filename.replace(' ', '_')
        file_path = f'static/resources/library/{safe_name}'
        file.save(f'/home/canopysat/app/{file_path}')
    
    conn = sq.connect('/home/canopysat/app/library.db')
    try:
        if sub_type == 'dataset':
            conn.execute('''INSERT INTO datasets 
                (title, authors, organization, country, description, format, file_path, keywords)
                VALUES (?,?,?,?,?,?,?,?)''',
                (title, authors, data.get('organization',''), data.get('country',''),
                 data.get('description',''), data.get('format',''), file_path,
                 data.get('keywords','')))
        else:
            conn.execute('''INSERT INTO publications
                (title, authors, organization, country, abstract, type, doi, url, file_path, keywords)
                VALUES (?,?,?,?,?,?,?,?,?,?)''',
                (title, authors, data.get('organization',''), data.get('country',''),
                 data.get('abstract',''), sub_type, data.get('doi',''),
                 data.get('url',''), file_path, data.get('keywords','')))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Submitted successfully! Your contribution will be reviewed within 48 hours and published with full credit.'})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

def get_country_from_coords(lat, lng):
    countries = [
        (51, 58, 2, 7, 'Belgium'), (42, 52, -5, 10, 'France'),
        (47, 56, 6, 15, 'Germany'), (36, 42, 26, 45, 'Turkey'),
        (24, 50, -125, -65, 'United States'), (42, 83, -141, -53, 'Canada'),
        (-35, 5, -74, -35, 'Brazil'), (-5, 5, 15, 32, 'DR Congo'),
        (-3, 5, 29, 35, 'Rwanda/Uganda'), (-5, 4, 33, 42, 'Tanzania'),
        (8, 24, 36, 48, 'Ethiopia'), (28, 37, 73, 88, 'India'),
        (18, 54, 73, 135, 'China'), (-8, 8, 95, 141, 'Indonesia'),
        (-18, 5, -81, -68, 'Peru'), (-56, -21, -75, -53, 'Argentina'),
        (-12, 5, -78, -66, 'Bolivia'), (35, 48, 44, 65, 'Iran'),
        (24, 32, 25, 37, 'Egypt'), (50, 70, 30, 180, 'Russia'),
        (37, 44, -9, 4, 'Spain'), (42, 48, 10, 19, 'Italy'),
        (50, 54, 14, 24, 'Poland'), (55, 71, 4, 32, 'Scandinavia'),
        (51, 61, -10, 2, 'United Kingdom'), (4, 14, 2, 15, 'Nigeria'),
        (-35, 35, -20, 55, 'Africa'), (-56, 13, -85, -30, 'South America'),
        (5, 85, -170, -50, 'North America'), (35, 75, -15, 65, 'Europe'),
        (-10, 55, 60, 150, 'Asia'), (-50, 5, 110, 180, 'Oceania'),
    ]
    for lat_min, lat_max, lng_min, lng_max, name in countries:
        if lat_min <= lat <= lat_max and lng_min <= lng <= lng_max:
            return name
    return 'Unknown'

@app.route('/community')
def community():
    lang = request.args.get('lang', 'en')
    return render_template('community.html', lang=lang)

@app.route('/community/stats')
def community_stats():
    import sqlite3 as sq
    try:
        cc = sq.connect('/home/canopysat/app/community.db')
        c = cc.cursor()
        
        # Total analyses
        total = c.execute('SELECT COUNT(*) FROM analyses_log').fetchone()[0]
        
        # Countries (unique based on coordinates)
        countries = c.execute('SELECT COUNT(DISTINCT ROUND(lat,0)||ROUND(lng,0)) FROM analyses_log').fetchone()[0]
        
        # Get country list from coordinates using reverse geocoding approximation
        coords = c.execute('SELECT DISTINCT ROUND(lat,0) as la, ROUND(lng,0) as lo FROM analyses_log LIMIT 50').fetchall()
        country_list = list(set([get_country_from_coords(float(r[0]), float(r[1])) for r in coords if r[0] and r[1]]))
        country_list = [c for c in country_list if c]
        
        # Deforestation alerts
        alerts = c.execute("SELECT COUNT(*) FROM analyses_log WHERE deforestation_alert LIKE '%CRITICAL%' OR deforestation_alert LIKE '%WARNING%'").fetchone()[0]
        
        # Hectares monitored (each 10km zone = 100 sq km = 10000 ha)
        hectares = total * 10000
        
        # Recent analyses
        recent = c.execute('''SELECT lat, lng, score, ai_forest_type, 
            deforestation_alert, forest_cover, created_at 
            FROM analyses_log ORDER BY created_at DESC LIMIT 10''').fetchall()
        
        # Testimonials approved
        testimonials = c.execute('SELECT name, role, organization, country, message, created_at FROM testimonials WHERE approved=1 ORDER BY created_at DESC').fetchall()
        
        # Partners approved
        partners = c.execute('SELECT name, type, country FROM partners WHERE approved=1').fetchall()
        
        # Events
        events = c.execute("SELECT id, title, description, date, type, link FROM events WHERE active=1 ORDER BY date ASC").fetchall()
        
        cc.close()
        
        return jsonify({
            'total_analyses': total,
            'countries_covered': min(countries, 150),
            'country_list': country_list[:20],
            'deforestation_alerts': alerts,
            'hectares_monitored': hectares,
            'recent_analyses': [{'lat': r[0], 'lng': r[1], 'score': r[2], 
                'ai_type': r[3], 'alert': r[4], 'cover': r[5], 'date': r[6]} for r in recent],
            'testimonials': [{'name': t[0], 'role': t[1], 'org': t[2], 
                'country': t[3], 'message': t[4], 'date': t[5]} for t in testimonials],
            'partners': [{'name': p[0], 'type': p[1], 'country': p[2]} for p in partners],
            'events': [{'id': e[0], 'title': e[1], 'description': e[2], 'date': e[3], 
                'type': e[4], 'link': e[5]} for e in events]
        })
    except Exception as ex:
        return jsonify({'error': str(ex)}), 500

@app.route('/community/testimonial', methods=['POST'])
def submit_testimonial():
    import sqlite3 as sq
    data = request.get_json()
    name = data.get('name', '').strip()
    role = data.get('role', '').strip()
    organization = data.get('organization', '').strip()
    country = data.get('country', '').strip()
    message = data.get('message', '').strip()
    
    if not name or not message:
        return jsonify({'error': 'Name and message are required'}), 400
    
    if len(message) < 20:
        return jsonify({'error': 'Message too short (min 20 characters)'}), 400
    
    try:
        cc = sq.connect('/home/canopysat/app/community.db')
        cc.execute('INSERT INTO testimonials (name, role, organization, country, message) VALUES (?,?,?,?,?)',
                  (name, role, organization, country, message))
        cc.commit()
        cc.close()
        return jsonify({'success': True, 'message': 'Thank you! Your testimonial will be reviewed and published within 48 hours.'})
    except Exception as ex:
        return jsonify({'error': str(ex)}), 500

@app.route('/community/partner', methods=['POST'])
def submit_partner():
    import sqlite3 as sq
    data = request.get_json()
    name = data.get('name', '').strip()
    ptype = data.get('type', '').strip()
    country = data.get('country', '').strip()
    website = data.get('website', '').strip()
    email = data.get('email', '').strip()
    
    if not name or not email:
        return jsonify({'error': 'Organization name and email are required'}), 400
    
    try:
        cc = sq.connect('/home/canopysat/app/community.db')
        cc.execute('INSERT INTO partners (name, type, country, website, contact_email) VALUES (?,?,?,?,?)',
                  (name, ptype, country, website, email))
        cc.commit()
        cc.close()
        return jsonify({'success': True, 'message': 'Thank you! We will review your partnership request within 5 business days.'})
    except Exception as ex:
        return jsonify({'error': str(ex)}), 500

@app.route('/contact')
def contact():
    lang = request.args.get('lang', 'en')
    return render_template('contact.html', lang=lang)

# ═══ CANOPYSAT API SYSTEM ═══
import sqlite3
import secrets
import time
from functools import wraps

API_DB = '/home/canopysat/app/api_keys.db'

def get_api_db():
    return sqlite3.connect(API_DB)

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not api_key:
            api_key = request.args.get('api_key', '')
        
        if not api_key:
            return jsonify({'error': 'API key required', 'docs': 'https://canopysat.org/api'}), 401
        
        conn = get_api_db()
        c = conn.cursor()
        c.execute('SELECT * FROM api_keys WHERE key=? AND active=1', (api_key,))
        key_data = c.fetchone()
        
        if not key_data:
            conn.close()
            return jsonify({'error': 'Invalid API key'}), 401
        
        # Check rate limit
        calls_used = key_data[5]
        calls_limit = key_data[6]
        plan = key_data[4]
        
        if calls_used >= calls_limit:
            conn.close()
            return jsonify({
                'error': 'Rate limit exceeded',
                'plan': plan,
                'calls_used': calls_used,
                'calls_limit': calls_limit,
                'upgrade': 'https://canopysat.org/api/pricing'
            }), 429
        
        # Update usage
        c.execute('UPDATE api_keys SET calls_used=calls_used+1, last_used=CURRENT_TIMESTAMP WHERE key=?', (api_key,))
        conn.commit()
        conn.close()
        
        request.api_key_data = key_data
        return f(*args, **kwargs)
    return decorated

@app.route('/api/v1/analyze', methods=['POST', 'GET'])
@require_api_key
def api_analyze():
    start_time = time.time()
    try:
        if request.method == 'POST':
            data = request.get_json()
        else:
            data = request.args
        
        lat = float(data.get('lat', 0))
        lng = float(data.get('lng', 0))
        size = float(data.get('size', 10))
        lang = data.get('lang', 'en')
        
        if not lat or not lng:
            return jsonify({'error': 'lat and lng are required'}), 400
        
        if size > 100:
            return jsonify({'error': 'Maximum zone size is 100km'}), 400
        
        from gee_analysis import analyze_forest
        result = analyze_forest(lat, lng, size)
        
        response_time = round(time.time() - start_time, 2)
        
        # Log the call
        api_key = request.headers.get('Authorization', '').replace('Bearer ', '')
        conn = get_api_db()
        conn.execute('INSERT INTO api_logs (api_key, lat, lng, response_time, success) VALUES (?,?,?,?,?)',
                    (api_key, lat, lng, response_time, 1 if result.get('success') else 0))
        conn.commit()
        conn.close()
        
        result['api_version'] = 'v1'
        result['response_time'] = response_time
        result['powered_by'] = 'CanopySat Forest Intelligence API'

        # Log to community DB
        try:
            import sqlite3 as sq
            cc = sq.connect('/home/canopysat/app/community.db')
            cc.execute('''INSERT INTO analyses_log 
                (lat, lng, score, ai_forest_type, deforestation_alert, forest_cover)
                VALUES (?,?,?,?,?,?)''',
                (lat, lng, result.get('score'), result.get('ai_forest_type'),
                 result.get('deforestation_alert'), result.get('forest_cover')))
            cc.commit()
            cc.close()
        except: pass

        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/key/create', methods=['POST'])
def api_create_key():
    data = request.get_json()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    plan = data.get('plan', 'free')
    
    if not name or not email:
        return jsonify({'error': 'name and email are required'}), 400
    
    plans = {
        'free': 10,
        'developer': 500,
        'enterprise': 999999
    }
    
    if plan not in plans:
        plan = 'free'
    
    api_key = 'csat_' + secrets.token_urlsafe(32)
    calls_limit = plans[plan]
    
    conn = get_api_db()
    try:
        conn.execute(
            'INSERT INTO api_keys (key, name, email, plan, calls_limit) VALUES (?,?,?,?,?)',
            (api_key, name, email, plan, calls_limit)
        )
        conn.commit()
        conn.close()
        return jsonify({
            'success': True,
            'api_key': api_key,
            'plan': plan,
            'calls_limit': calls_limit,
            'message': 'Keep your API key safe — it will not be shown again'
        })
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/key/status', methods=['GET'])
@require_api_key
def api_key_status():
    key_data = request.api_key_data
    return jsonify({
        'name': key_data[2],
        'email': key_data[3],
        'plan': key_data[4],
        'calls_used': key_data[5],
        'calls_limit': key_data[6],
        'calls_remaining': key_data[6] - key_data[5],
        'created_at': key_data[7],
        'last_used': key_data[8]
    })

@app.route("/api")
def api_docs():
    return jsonify({
        'name': 'CanopySat Forest Intelligence API',
        'version': 'v1',
        'description': 'Satellite-based forest verification API using ESA Sentinel-2, Sentinel-1, NASA Landsat and FIRMS',
        'endpoints': {
            'POST /api/v1/analyze': 'Analyze a forest zone',
            'GET /api/v1/key/status': 'Check your API key status',
            'POST /api/v1/key/create': 'Create a new API key'
        },
        'parameters': {
            'lat': 'Latitude (required)',
            'lng': 'Longitude (required)',
            'size': 'Zone size in km (default: 10, max: 100)',
            'lang': 'Language: en or fr (default: en)'
        },
        'authentication': 'Bearer token in Authorization header or api_key parameter',
        'plans': {
            'free': '10 analyses/month — Free',
            'developer': '500 analyses/month — 29€/month',
            'enterprise': 'Unlimited — 299€/month'
        },
        'example': {
            'request': 'POST /api/v1/analyze',
            'headers': {'Authorization': 'Bearer csat_your_api_key'},
            'body': {'lat': -3.4653, 'lng': -62.2159, 'size': 10, 'lang': 'en'}
        },
        'website': 'https://canopysat.org',
        'contact': 'contact@canopysat.org'
    })

@app.route('/favicon.ico')
def favicon():
    from flask import send_file
    return send_file('/home/canopysat/app/static/img/logo.png', mimetype='image/png')

@app.route('/manifest.json')
def manifest():
    from flask import send_file
    return send_file('/home/canopysat/app/static/manifest.json',
                     mimetype='application/manifest+json')

@app.route('/sw.js')
def service_worker():
    from flask import send_file, make_response
    response = make_response(send_file('/home/canopysat/app/static/sw.js',
                             mimetype='application/javascript'))
    response.headers['Service-Worker-Allowed'] = '/'
    return response

@app.route('/health')
def health():
    return jsonify({
        'status': 'online',
        'project': 'CanopySat',
        'gee': 'connected',
        'version': '1.0.0'
    })

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8002)


# Email configuration — Zoho Mail
SMTP_HOST = 'smtppro.zoho.eu'
SMTP_PORT = 465
SMTP_USER = 'contact@canopysat.org'
SMTP_PASS = '3Dq5yjzesH3N'

def send_email(to, subject, body_html):
    import smtplib, ssl
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = 'CanopySat Forest Guardian <contact@canopysat.org>'
        msg['To'] = to
        msg.attach(MIMEText(body_html, 'html'))
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as s:
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
        return True
    except Exception as e:
        print(f'Email error: {e}')
        return False
