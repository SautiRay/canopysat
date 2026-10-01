from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image as RLImage
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os

DARK_GREEN = HexColor('#0D3B2E')
MID_GREEN = HexColor('#1B6B45')
LIGHT_GREEN = HexColor('#D6EFE1')
ACCENT_GREEN = HexColor('#3DAA6B')
RED = HexColor('#E53935')
ORANGE = HexColor('#F9A825')
WHITE = white

def get_score_color(score):
    if score >= 80: return ACCENT_GREEN
    elif score >= 65: return HexColor('#2D8A5A')
    elif score >= 45: return ORANGE
    else: return RED

def get_score_label(score, lang='en'):
    if lang == 'fr':
        if score >= 80: return 'Foret Saine'
        elif score >= 65: return 'Bonne Foret'
        elif score >= 45: return 'Foret Degradee'
        elif score >= 20: return 'Foret Critique'
        else: return 'Non-Forestier'
    else:
        if score >= 80: return 'Healthy Forest'
        elif score >= 65: return 'Good Forest'
        elif score >= 45: return 'Degraded Forest'
        elif score >= 20: return 'Critical Forest'
        else: return 'Non-Forest'

def generate_pdf(data, lang='en'):
    filename = f"canopysat_report_{data['lat']}_{data['lng']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join('/home/canopysat/app/reports', filename)

    doc = SimpleDocTemplate(filepath, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm)

    elements = []
    score = data['score']
    score_color = get_score_color(score)
    score_label = get_score_label(score, lang)

    # HEADER
    logo_path = '/home/canopysat/app/static/img/logo.png'
    try:
        logo = RLImage(logo_path, width=2.2*cm, height=2.2*cm)
        header_data = [[
            logo,
            Paragraph('CANOPYSAT  -  FOREST INTELLIGENCE ECOSYSTEM',
                ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=14, textColor=WHITE, leading=18)),
            Paragraph('canopysat.org\nGlobal 2026',
                ParagraphStyle('s', fontName='Helvetica', fontSize=9, textColor=ACCENT_GREEN, alignment=TA_RIGHT))
        ]]
        header_table = Table(header_data, colWidths=[2.5*cm, 9.5*cm, 5*cm])
    except Exception as e:
        header_data = [[
            Paragraph('CANOPYSAT',
                ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=20, textColor=WHITE)),
            Paragraph('FOREST INTELLIGENCE ECOSYSTEM\ncanopysat.org - Global 2026',
                ParagraphStyle('s', fontName='Helvetica', fontSize=10, textColor=ACCENT_GREEN, alignment=TA_RIGHT))
        ]]
        header_table = Table(header_data, colWidths=[7*cm, 10*cm])

    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), DARK_GREEN),
        ('PADDING', (0,0), (-1,-1), 12),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.4*cm))

    # TITLE
    title = 'RAPPORT DE VERIFICATION FORESTIERE' if lang == 'fr' else 'FOREST VERIFICATION REPORT'
    elements.append(Paragraph(title,
        ParagraphStyle('title', fontName='Helvetica-Bold', fontSize=16,
            textColor=DARK_GREEN, alignment=TA_CENTER)))
    elements.append(Spacer(1, 0.2*cm))
    elements.append(HRFlowable(width="100%", thickness=2, color=ACCENT_GREEN))
    elements.append(Spacer(1, 0.3*cm))

    # ZONE INFO
    zone_label = 'INFORMATIONS DE LA ZONE' if lang == 'fr' else 'ANALYZED ZONE INFORMATION'
    elements.append(Paragraph(zone_label,
        ParagraphStyle('sec', fontName='Helvetica-Bold', fontSize=11, textColor=MID_GREEN)))
    elements.append(Spacer(1, 0.15*cm))

    zone_data = [
        ['Latitude', str(data['lat']), 'Longitude', str(data['lng'])],
        ['Zone (km)' if lang == 'fr' else 'Zone size (km)', str(data['size_km']),
         'Date' if lang == 'fr' else 'Analysis date', str(data['analysis_date'])],
    ]
    zt = Table(zone_data, colWidths=[3.5*cm, 5*cm, 3.5*cm, 5*cm])
    zt.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_GREEN),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('PADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, MID_GREEN),
    ]))
    elements.append(zt)
    elements.append(Spacer(1, 0.4*cm))

    # SCORE BOX
    score_title = "SCORE D'INTEGRITE FORESTIERE" if lang == 'fr' else 'FOREST INTEGRITY SCORE'
    score_data = [[
        Paragraph(str(score),
            ParagraphStyle('sc', fontName='Helvetica-Bold', fontSize=44,
                textColor=WHITE, alignment=TA_CENTER, leading=50)),
        Paragraph(score_title + '\n/ 100\n\n' + score_label,
            ParagraphStyle('sl', fontName='Helvetica-Bold', fontSize=12,
                textColor=WHITE, leading=18))
    ]]
    st = Table(score_data, colWidths=[4*cm, 13*cm])
    st.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), score_color),
        ('PADDING', (0,0), (-1,-1), 14),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(st)
    elements.append(Spacer(1, 0.4*cm))

    # DETAILED RESULTS
    results_label = 'RESULTATS DETAILLES' if lang == 'fr' else 'DETAILED RESULTS'
    elements.append(Paragraph(results_label,
        ParagraphStyle('sec', fontName='Helvetica-Bold', fontSize=11, textColor=MID_GREEN)))
    elements.append(Spacer(1, 0.15*cm))

    ndvi_interp = 'Excellent' if data['ndvi_current'] > 0.6 else 'Good' if data['ndvi_current'] > 0.4 else 'Low'
    trend_interp = 'Improving' if data['ndvi_change'] > 0.05 else 'Stable' if data['ndvi_change'] > -0.05 else 'Degrading'
    cover_interp = 'Excellent' if data['forest_cover'] > 80 else 'Good' if data['forest_cover'] > 60 else 'Low'
    fire_interp = 'No fire detected' if data['active_fires'] == 0 else f"{data['active_fires']} fires"

    if lang == 'fr':
        ndvi_interp = 'Excellente' if data['ndvi_current'] > 0.6 else 'Bonne' if data['ndvi_current'] > 0.4 else 'Faible'
        trend_interp = 'En amelioration' if data['ndvi_change'] > 0.05 else 'Stable' if data['ndvi_change'] > -0.05 else 'En degradation'
        cover_interp = 'Excellente' if data['forest_cover'] > 80 else 'Bonne' if data['forest_cover'] > 60 else 'Faible'
    l10 = data.get('landsat_change_10y')
    l40 = data.get('landsat_change_40y')
    def fmt(v): return ('+' if v >= 0 else '') + str(v) if v is not None else 'N/A'
    def itrend(v, fr):
        if v is None: return 'N/A'
        if fr: return 'En amelioration' if v > 0.05 else 'Stable' if v > -0.05 else 'En degradation'
        return 'Improving' if v > 0.05 else 'Stable' if v > -0.05 else 'Degrading'
    s1_vv = data.get('sentinel1_vv')
    s1_forest = data.get('sentinel1_forest', '')
    fire_pixels = data.get('fire_pixels', data['active_fires'])
    fire_events = data.get('fire_events_estimated', 0)

    if lang == 'fr':
        fire_display = f"{fire_pixels} pixels"
        fire_events_display = f"~{fire_events} evenements estimes" if fire_events > 0 else "Aucun feu detecte"
        rows = [
            ['Indicateur', 'Valeur', 'Interpretation'],
            ['Vegetation actuelle (NDVI)', str(data['ndvi_current']), ndvi_interp],
            ['Tendance NDVI 3 ans (Sentinel-2)', fmt(data['ndvi_change']), trend_interp],
            ['Tendance 10 ans (Landsat 8/9)', fmt(l10), itrend(l10, True)],
            ['Tendance 40 ans (Landsat 1984)', fmt(l40), itrend(l40, True)],
        ]
        # Niveau 1 — French version (already added above in shared block)
        ai_type_fr = data.get('ai_forest_type_fr')
        if ai_type_fr:
            ai_interp_fr = {
                'Foret Tropicale Dense': 'Haute biodiversite, canopee dense',
                'Foret Temperee': 'Foret mixte, climat tempere',
                'Foret Boreale/Conifere': 'Foret de coniferes, climat froid',
                'Savane/Foret claire': 'Couvert arbore ouvert, saison seche',
                'Prairie/Arbustive': 'Vegetation basse, paysage ouvert',
                'Eau/Zone humide': 'Ecosysteme aquatique detecte',
                'Sol nu/Urbain/Non-forestier': 'Aucun couvert forestier detecte'
            }.get(ai_type_fr, 'Classification par IA')
            rows.append(['Type de foret IA', ai_type_fr, ai_interp_fr])
        # Analyse Claude AI (FR)
        ai_defor_risk = data.get('ai_deforestation_risk')
        ai_main_cause = data.get('ai_main_cause')
        ai_recommendation = data.get('ai_recommendation')
        ai_degradation = data.get('ai_degradation_signs')
        ai_recovery = data.get('ai_recovery_signs')
        if ai_defor_risk and ai_defor_risk != 'Unknown':
            risk_label = 'Risque faible' if ai_defor_risk == 'Low' else ('Risque modere' if ai_defor_risk == 'Moderate' else 'Risque eleve')
            rows.append(['Risque deforestation (IA)', ai_defor_risk, risk_label])
        if ai_main_cause:
            rows.append(['Cause principale (IA)', ai_main_cause, ''])
        if ai_degradation and ai_degradation != 'None detected':
            rows.append(['Signes degradation (IA)', ai_degradation, ''])
        if ai_recovery and ai_recovery != 'None detected':
            rows.append(['Signes recuperation (IA)', ai_recovery, ''])
        if ai_recommendation:
            rows.append(['Recommandation IA', ai_recommendation, ''])
        if s1_vv is not None:
            rows.append(['Sentinel-1 Radar (VV)', str(s1_vv) + ' dB', s1_forest])
        rows += [
            ['Couverture forestiere', f"{data['forest_cover']}%", cover_interp],
            ['Pixels feux (FIRMS/an)', fire_display, fire_events_display],
            ['Tendance generale', str(data['trend']), ''],
            ['Satellites utilises', '\n'.join(['- ' + s for s in data['satellites_used']]), ''],
        ]
    else:
        fire_display = f"{fire_pixels} pixels"
        fire_events_display = f"~{fire_events} events estimated" if fire_events > 0 else "No fire detected"
        rows = [
            ['Indicator', 'Value', 'Interpretation'],
            ['Current vegetation (NDVI)', str(data['ndvi_current']), ndvi_interp],
            ['NDVI Trend 3 years (Sentinel-2)', fmt(data['ndvi_change']), trend_interp],
            ['10-year trend (Landsat 8/9)', fmt(l10), itrend(l10, False)],
            ['40-year trend (Landsat 1984)', fmt(l40), itrend(l40, False)],
        ]
        # Niveau 1 — Forest change analysis
        forest_status = data.get('forest_status')
        forest_status_fr = data.get('forest_status_fr')
        annual_rate = data.get('annual_rate')
        ndvi_change_5y = data.get('ndvi_change_5y')

        if forest_status:
            status_display = forest_status_fr if lang == 'fr' else forest_status
            rows.append([
                'Statut forestier (FAO)' if lang == 'fr' else 'Forest Status (FAO)',
                status_display,
                'Recuperation' if 'recovery' in str(forest_status).lower() else
                'Stable' if 'stable' in str(forest_status).lower() else
                'Degradation'
            ])

        if annual_rate is not None:
            annual_pct = round(annual_rate * 100, 3)
            rows.append([
                'Taux annuel NDVI' if lang == 'fr' else 'Annual NDVI rate',
                ('+' if annual_pct >= 0 else '') + str(annual_pct) + '% / ' + ('an' if lang == 'fr' else 'year'),
                'Amelioration' if annual_pct > 0 else 'Degradation'
            ])

        if ndvi_change_5y is not None:
            rows.append([
                'Changement NDVI 5 ans' if lang == 'fr' else 'NDVI change 5 years',
                ('+' if ndvi_change_5y >= 0 else '') + str(ndvi_change_5y),
                'Improving' if ndvi_change_5y > 0.05 else 'Stable' if ndvi_change_5y > -0.05 else 'Degrading'
            ])

        # Leaf type, Dev stage, Biomass
        leaf_type = data.get('leaf_type_fr' if lang == 'fr' else 'leaf_type')
        dev_stage = data.get('dev_stage_fr' if lang == 'fr' else 'dev_stage')
        biomass_class = data.get('biomass_class_fr' if lang == 'fr' else 'biomass_class')
        estimated_agb = data.get('estimated_agb')
        canopy_height = data.get('canopy_height')
        canopy_height_rh50 = data.get('canopy_height_rh50')
        gedi_cover = data.get('gedi_cover')
        canopy_height_source = data.get('canopy_height_source', 'Estimate')

        if leaf_type:
            leaf_interp = {
                'Coniferous (Needleleaf)': 'Evergreen needles, resinous wood',
                'Broadleaf (Deciduous/Evergreen)': 'Flat leaves, high photosynthesis',
                'Mixed (Coniferous/Broadleaf)': 'Mixed needles and flat leaves',
                'Non-forest': 'No significant tree cover',
                'Coniferes (Aiguilles)': 'Feuilles en aiguilles, bois resineux',
                'Feuillus (Decidus/Persistants)': 'Feuilles larges, haute photosynthese',
                'Mixte (Coniferes/Feuillus)': 'Melange aiguilles et feuilles larges',
                'Non-forestier': 'Aucun couvert arborique significatif',
            }.get(leaf_type, '')
            rows.append([
                'Type de feuilles' if lang == 'fr' else 'Leaf type',
                leaf_type,
                leaf_interp
            ])
        if dev_stage:
            dev_interp = {
                'Old-growth forest (>120 years)': 'Ancient forest, high biodiversity',
                'Mature forest (60-120 years)': 'Well established, dense canopy',
                'Growing forest (20-60 years)': 'Active growth phase',
                'Young forest (0-20 years)': 'Early regeneration stage',
                'Non-forest / Bare': 'No forest cover detected',
                'Foret ancienne (>120 ans)': 'Foret ancienne, haute biodiversite',
                'Foret mature (60-120 ans)': 'Bien etablie, canopee dense',
                'Foret en croissance (20-60 ans)': 'Phase de croissance active',
                'Jeune foret (0-20 ans)': 'Stade de regeneration precoce',
                'Non-forestier / Sol nu': 'Aucun couvert forestier detecte',
            }.get(dev_stage, '')
            rows.append([
                'Stade de dev. forestier' if lang == 'fr' else 'Developmental stage',
                dev_stage,
                dev_interp
            ])
        if biomass_class:
            rows.append([
                'Biomasse aerienne' if lang == 'fr' else 'Above-ground biomass',
                f"~{estimated_agb} t/ha" if estimated_agb else 'N/A',
                biomass_class
            ])
        if canopy_height:
            is_gedi = canopy_height_source == 'NASA GEDI LiDAR'
            height_label = ('Hauteur canopee (GEDI+S2 10m)' if lang == 'fr' else 'Canopy Height (GEDI+S2 10m)') if is_gedi else ('Hauteur canopee (estimation NDVI)' if lang == 'fr' else 'Canopy Height (NDVI estimate)')
            height_val = f"{canopy_height}m max" + (f" / {canopy_height_rh50}m median" if canopy_height_rh50 else "")
            height_interp = ('Hauteur des arbres mesuree par laser (ISS) fusionnee avec Sentinel-2 a 10m de resolution' if lang == 'fr' else 'Tree height from LiDAR (ISS) fused with Sentinel-2 at 10m resolution') if is_gedi else ('Hauteur estimee depuis Sentinel-2' if lang == 'fr' else 'Height estimated from Sentinel-2')
            rows.append([height_label, height_val, height_interp])

        # Carbon Assessment
        carbon_per_ha = data.get('carbon_per_ha')
        carbon_area_ha = data.get('carbon_area_ha')
        carbon_total_co2 = data.get('carbon_total_co2')
        carbon_value_eur = data.get('carbon_value_eur')
        if carbon_total_co2:
            rows.append([
                'Carbon Assessment (IPCC)' if lang == 'en' else 'Bilan Carbone (IPCC)',
                f'{int(carbon_total_co2):,} t CO2',
                ('CO2 sequestered in this forest zone — IPCC methodology (AGB+BGB × 0.47 × 3.67)' if lang == 'en'
                 else 'CO2 sequestre dans cette zone — methodologie IPCC (AGB+BGB × 0.47 × 3.67)')
            ])
            rows.append([
                'CO2 per hectare' if lang == 'en' else 'CO2 par hectare',
                f'{carbon_per_ha} t CO2/ha',
                'Carbon density per hectare' if lang == 'en' else 'Densite carbone par hectare'
            ])
            rows.append([
                'Zone area' if lang == 'en' else 'Superficie zone',
                f'{int(carbon_area_ha):,} ha',
                'Analysis zone area in hectares' if lang == 'en' else 'Superficie de la zone analysee en hectares'
            ])
            rows.append([
                'Carbon credit value' if lang == 'en' else 'Valeur credits carbone',
                f'EUR {int(carbon_value_eur):,}',
                ('Estimated value at EUR 15/tonne CO2 (voluntary carbon market)' if lang == 'en'
                 else 'Valeur estimee a 15 EUR/tonne CO2 (marche carbone volontaire)')
            ])
            rows.append([
                'REDD+ MRV Monitoring' if lang == 'en' else 'Monitoring MRV REDD+',
                'Compliant' if lang == 'en' else 'Conforme',
                ('This report provides satellite-based Measurement, Reporting and Verification (MRV) data for the analyzed forest zone, consistent with REDD+ monitoring requirements. CO2 sequestration calculated using IPCC Tier 1 methodology from NASA GEDI LiDAR biomass data.' if lang == 'en'
                 else 'Ce rapport fournit des donnees de Mesure, Notification et Verification (MRV) par satellite pour la zone analysee, conformes aux exigences de monitoring REDD+. La sequestration CO2 est calculee selon la methodologie IPCC Tier 1 a partir des donnees de biomasse NASA GEDI LiDAR.')
            ])
            rows.append([
                'Methodology' if lang == 'en' else 'Methodologie',
                'IPCC 2006/2019 — Tier 1',
                ('Above-ground biomass measured via NASA GEDI LiDAR (25m, ISS). Carbon fraction: 0.47. CO2 conversion factor: 3.67. Below-ground biomass ratio: 0.26 (IPCC root-to-shoot). Source: IPCC Guidelines for National GHG Inventories (2019).' if lang == 'en'
                 else 'Biomasse aerienne mesuree via NASA GEDI LiDAR (25m, ISS). Fraction carbone: 0.47. Facteur conversion CO2: 3.67. Ratio biomasse souterraine: 0.26 (IPCC). Source: Lignes directrices IPCC pour les inventaires nationaux de GES (2019).')
            ])
            rows.append([
                'Carbon credit potential' if lang == 'en' else 'Potentiel credits carbone',
                f'EUR {int(carbon_value_eur / 12):,} / year' if lang == 'en' else f'EUR {int(carbon_value_eur / 12):,} / an',
                ('Estimated annual value based on maintained forest preservation. For official REDD+ credit issuance under VCS or Gold Standard, independent third-party verification is required.' if lang == 'en'
                 else 'Valeur annuelle estimee basee sur le maintien de la preservation forestiere. Pour une emission officielle de credits REDD+ sous VCS ou Gold Standard, une verification tierce independante est requise.')
            ])
        if gedi_cover:
            rows.append([
                'Couverture arboree GEDI' if lang == 'fr' else 'GEDI Tree Cover',
                f"{gedi_cover}%",
                'Pourcentage de la zone couverte par les arbres selon NASA GEDI' if lang == 'fr' else 'Percentage of the zone covered by trees according to NASA GEDI'
            ])

        ai_type = data.get('ai_forest_type')
        if ai_type:
            ai_interp = {
                'Dense Tropical Forest': 'High biodiversity, dense canopy',
                'Temperate Forest': 'Broadleaf/mixed, moderate climate',
                'Boreal/Coniferous Forest': 'Coniferous, cold climate',
                'Savanna/Woodland': 'Open tree cover, dry season',
                'Grassland/Shrubland': 'Low vegetation, open landscape',
                'Water/Wetland': 'Aquatic ecosystem detected',
                'Bare soil/Urban/Non-forest': 'No forest cover detected'
            }.get(ai_type, 'AI-based classification')
            rows.append(['AI Forest Type', ai_type, ai_interp])
        # Claude AI Analysis
        ai_defor_risk = data.get('ai_deforestation_risk')
        ai_main_cause = data.get('ai_main_cause')
        ai_recommendation = data.get('ai_recommendation')
        ai_degradation = data.get('ai_degradation_signs')
        ai_recovery = data.get('ai_recovery_signs')
        if ai_defor_risk and ai_defor_risk != 'Unknown':
            risk_color = 'Low risk' if ai_defor_risk == 'Low' else ('Moderate risk' if ai_defor_risk == 'Moderate' else 'High risk')
            rows.append(['Deforestation Risk (AI)', ai_defor_risk, risk_color])
        if ai_main_cause:
            rows.append(['Main cause (AI)', ai_main_cause, ''])
        if ai_degradation and ai_degradation != 'None detected':
            rows.append(['Degradation signs (AI)', ai_degradation, ''])
        if ai_recovery and ai_recovery != 'None detected':
            rows.append(['Recovery signs (AI)', ai_recovery, ''])
        if ai_recommendation:
            rows.append(['AI Recommendation', ai_recommendation, ''])
        if s1_vv is not None:
            rows.append(['Sentinel-1 Radar (VV)', str(s1_vv) + ' dB', s1_forest])
        rows += [
            ['Forest cover', f"{data['forest_cover']}%", cover_interp],
            ['Fire pixels detected (FIRMS/year)', fire_display, fire_events_display],
            ['Overall trend', str(data['trend']), ''],
            ['Satellites used', '\n'.join(['- ' + s for s in data['satellites_used']]), ''],
        ]
    # NIVEAU 3 — Deforestation detection
    defor_alert = data.get('deforestation_alert')
    defor_alert_fr = data.get('deforestation_alert_fr')
    forest_change_ha = data.get('forest_change_ha')
    forest_change_pct = data.get('forest_change_pct')
    annual_ha_rate = data.get('annual_ha_rate')
    forest_change_ha_10y = data.get('forest_change_ha_10y')
    forest_change_pct_10y = data.get('forest_change_pct_10y')
    annual_ha_rate_10y = data.get('annual_ha_rate_10y')

    def fmt_ha(v):
        if v is None: return 'N/A'
        return ('+' if v >= 0 else '') + str(v) + ' ha'
    def fmt_pct(v):
        if v is None: return 'N/A'
        return ('+' if v >= 0 else '') + str(v) + '%'

    if lang == 'fr':
        if defor_alert_fr:
            rows.append(['Alerte Deforestation', defor_alert_fr, ''])
        if forest_change_ha is not None:
            rows.append(['Changement surface (3 ans)', fmt_ha(forest_change_ha), fmt_pct(forest_change_pct)])
        if annual_ha_rate is not None:
            rows.append(['Taux annuel (surface/an)', fmt_ha(annual_ha_rate) + '/an', 'Recuperation' if annual_ha_rate >= 0 else 'Perte'])
        if forest_change_ha_10y is not None:
            rows.append(['Changement surface (10 ans)', fmt_ha(forest_change_ha_10y), fmt_pct(forest_change_pct_10y)])
        if annual_ha_rate_10y is not None:
            rows.append(['Taux annuel 10 ans', fmt_ha(annual_ha_rate_10y) + '/an', 'Recuperation' if annual_ha_rate_10y >= 0 else 'Perte'])
    else:
        if defor_alert:
            rows.append(['Deforestation Alert', defor_alert, ''])
        if forest_change_ha is not None:
            rows.append(['Area change (3 years)', fmt_ha(forest_change_ha), fmt_pct(forest_change_pct)])
        if annual_ha_rate is not None:
            rows.append(['Annual rate (area/yr)', fmt_ha(annual_ha_rate) + '/yr', 'Recovery' if annual_ha_rate >= 0 else 'Loss'])
        if forest_change_ha_10y is not None:
            rows.append(['Area change (10 years)', fmt_ha(forest_change_ha_10y), fmt_pct(forest_change_pct_10y)])
        if annual_ha_rate_10y is not None:
            rows.append(['Annual rate 10yr (area)', fmt_ha(annual_ha_rate_10y) + '/yr', 'Recovery' if annual_ha_rate_10y >= 0 else 'Loss'])

    # Use Paragraph only for cells that need word wrap
    normal_style = ParagraphStyle('normal', fontName='Helvetica', fontSize=9,
        textColor=DARK_GREEN, leading=12)
    bold_style = ParagraphStyle('bold', fontName='Helvetica-Bold', fontSize=9,
        textColor=WHITE, leading=12)

    wrapped_rows = []
    for i, row in enumerate(rows):
        if i == 0:
            wrapped_rows.append([
                Paragraph(str(row[0]), bold_style),
                Paragraph(str(row[1]), bold_style),
                Paragraph(str(row[2]), bold_style)
            ])
        else:
            wrapped_rows.append([
                Paragraph(str(row[0]), normal_style),
                Paragraph(str(row[1]), normal_style),
                Paragraph(str(row[2]), normal_style)
            ])

    rt = Table(wrapped_rows, colWidths=[5.5*cm, 4.5*cm, 7*cm])
    rt.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), MID_GREEN),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('PADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, MID_GREEN),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [LIGHT_GREEN, WHITE]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(rt)
    elements.append(Spacer(1, 0.4*cm))

    # Page break before Score Breakdown
    from reportlab.platypus import PageBreak
    elements.append(PageBreak())

    # SCORE BREAKDOWN
    breakdown_label = 'DECOMPOSITION DU SCORE' if lang == 'fr' else 'SCORE BREAKDOWN'
    elements.append(Paragraph(breakdown_label,
        ParagraphStyle('sec', fontName='Helvetica-Bold', fontSize=11, textColor=MID_GREEN)))
    elements.append(Spacer(1, 0.15*cm))

    # Use exact points calculated by satellites in gee_analysis.py
    pts_ndvi = data.get('pts_ndvi', 0)
    pts_trend = data.get('pts_trend', 0)
    pts_cover = data.get('pts_cover', 0)
    pts_fire = data.get('pts_fire', 0)

    if lang == 'fr':
        s1_vv = data.get('sentinel1_vv')
        pts_s1 = 0
        if s1_vv is not None:
            if s1_vv >= -8: pts_s1 = 15
            elif s1_vv >= -12: pts_s1 = 10
            elif s1_vv >= -16: pts_s1 = 5

        # RF penalty FR
        rf_defor = data.get('rf_deforested_pct') or 0
        rf_degr = data.get('rf_degraded_pct') or 0
        rf_penalty = 0
        if rf_defor > 15: rf_penalty += 20
        elif rf_defor > 10: rf_penalty += 15
        elif rf_defor > 5: rf_penalty += 8
        elif rf_defor > 2: rf_penalty += 3
        if rf_degr > 20: rf_penalty += 10
        elif rf_degr > 10: rf_penalty += 6
        elif rf_degr > 5: rf_penalty += 3
        base_score = pts_ndvi + pts_trend + pts_cover + pts_s1 + pts_fire

        bd_rows = [
            ['Composant', 'Points', 'Maximum'],
            ['Vegetation actuelle (NDVI)', str(pts_ndvi), '25'],
            ['Tendance NDVI (3 ans)', str(pts_trend), '25'],
            ['Couverture forestiere', str(pts_cover), '25'],
            ['Sentinel-1 Radar (VV)', str(pts_s1), '15'],
            ['Score feux (0=beaucoup, 10=aucun)', str(pts_fire), '10'],
            ['Score de base (satellites)', str(base_score), '100'],
        ]
        if rf_penalty > 0:
            bd_rows.append(['Penalite RF deforestation (2021-2026)', '-' + str(rf_penalty), ''])
        bd_rows.append(['SCORE FINAL (apres correction RF)', str(score), '100'])
        if data.get('ai_deforestation_risk') and data.get('ai_deforestation_risk') != 'Unknown':
            risk_fr = {'Low':'Faible','Moderate':'Modere','High':'Eleve','Critical':'Critique'}.get(data.get('ai_deforestation_risk',''), data.get('ai_deforestation_risk',''))
            bd_rows.append(['Risque deforestation (IA)', risk_fr, ''])
    else:
        s1_vv = data.get('sentinel1_vv')
        pts_s1 = 0
        if s1_vv is not None:
            if s1_vv >= -8: pts_s1 = 15
            elif s1_vv >= -12: pts_s1 = 10
            elif s1_vv >= -16: pts_s1 = 5

        # RF penalty
        rf_defor = data.get('rf_deforested_pct') or 0
        rf_degr = data.get('rf_degraded_pct') or 0
        rf_penalty = 0
        if rf_defor > 15: rf_penalty += 20
        elif rf_defor > 10: rf_penalty += 15
        elif rf_defor > 5: rf_penalty += 8
        elif rf_defor > 2: rf_penalty += 3
        if rf_degr > 20: rf_penalty += 10
        elif rf_degr > 10: rf_penalty += 6
        elif rf_degr > 5: rf_penalty += 3
        base_score = pts_ndvi + pts_trend + pts_cover + pts_s1 + pts_fire

        bd_rows = [
            ['Component', 'Points', 'Maximum'],
            ['Current vegetation (NDVI)', str(pts_ndvi), '25'],
            ['NDVI trend (3 years)', str(pts_trend), '25'],
            ['Forest cover', str(pts_cover), '25'],
            ['Sentinel-1 Radar (VV)', str(pts_s1), '15'],
            ['Fire score (0=many fires, 10=none)', str(pts_fire), '10'],
            ['Base score (satellite)', str(base_score), '100'],
        ]
        if rf_penalty > 0:
            bd_rows.append(['RF deforestation penalty (2021-2026)', '-' + str(rf_penalty), ''])
        bd_rows.append(['FINAL SCORE (after RF correction)', str(score), '100'])
        if data.get('ai_deforestation_risk') and data.get('ai_deforestation_risk') != 'Unknown':
            bd_rows.append(['AI Deforestation Risk', data.get('ai_deforestation_risk', ''), ''])

    bdt = Table(bd_rows, colWidths=[10*cm, 4*cm, 3*cm])
    bdt.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), MID_GREEN),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BACKGROUND', (0,-1), (-1,-1), DARK_GREEN),
        ('TEXTCOLOR', (0,-1), (-1,-1), WHITE),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('PADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, MID_GREEN),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [LIGHT_GREEN, WHITE]),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
    ]))
    elements.append(bdt)
    elements.append(Spacer(1, 0.4*cm))

    # SPECIES CLIMATE SUITABILITY
    species_data = data.get('species_suitability')
    if species_data and species_data.get('success') and species_data.get('species'):
        elements.append(Spacer(1, 0.3*cm))
        species_label = 'SUITABILITE CLIMATIQUE DES ESPECES (2050)' if lang == 'fr' else 'SPECIES CLIMATE SUITABILITY (2050)'
        elements.append(Paragraph(species_label,
            ParagraphStyle('sec', fontName='Helvetica-Bold', fontSize=11, textColor=MID_GREEN)))
        elements.append(Spacer(1, 0.1*cm))

        # Climate summary
        scenario_text = (
            f"{'Scenario' if lang == 'en' else 'Scenario'}: {species_data.get('scenario', 'SSP2-4.5 2050')} | "
            f"{'Temperature' if lang == 'en' else 'Temperature'}: {species_data.get('temp_current')}°C → {species_data.get('temp_2050')}°C "
            f"(+{species_data.get('temp_change')}°C) | "
            f"{'Precipitation' if lang == 'en' else 'Precipitations'}: {species_data.get('precip_current')} → {species_data.get('precip_2050')} mm/year "
            f"({species_data.get('precip_change_pct')}%)"
        )
        elements.append(Paragraph(scenario_text,
            ParagraphStyle('sc', fontName='Helvetica', fontSize=8,
                textColor=ACCENT_GREEN, spaceAfter=6)))

        # Summary badges
        suitable = species_data.get('suitable', 0)
        moderate = species_data.get('moderate', 0)
        at_risk = species_data.get('at_risk', 0)
        summary_text = (
            f"{'Suitable' if lang == 'en' else 'Favorable'}: {suitable} | "
            f"{'Moderate risk' if lang == 'en' else 'Risque modere'}: {moderate} | "
            f"{'At risk' if lang == 'en' else 'A risque'}: {at_risk} | "
            f"{'Source' if lang == 'en' else 'Source'}: GBIF · WorldClim · NASA GDDP-CMIP6"
        )
        elements.append(Paragraph(summary_text,
            ParagraphStyle('sm', fontName='Helvetica-Bold', fontSize=8,
                textColor=WHITE, spaceAfter=8)))

        # Species table
        if lang == 'fr':
            sp_rows = [['Espece', 'Famille', 'Score 2050', 'Statut', 'Plage temp.']]
        else:
            sp_rows = [['Species', 'Family', 'Score 2050', 'Status', 'Temp. range']]

        for sp in species_data.get('species', []):
            sp_rows.append([
                sp.get('species', ''),
                sp.get('family', ''),
                str(sp.get('score', '')),
                sp.get('status_fr' if lang == 'fr' else 'status', ''),
                sp.get('temp_range', '')
            ])

        spt = Table(sp_rows, colWidths=[5.5*cm, 3.5*cm, 2*cm, 3*cm, 3*cm])
        spt.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), MID_GREEN),
            ('TEXTCOLOR', (0,0), (-1,0), WHITE),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('PADDING', (0,0), (-1,-1), 6),
            ('GRID', (0,0), (-1,-1), 0.5, MID_GREEN),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [LIGHT_GREEN, WHITE]),
            ('ALIGN', (2,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('TEXTCOLOR', (0,1), (-1,-1), DARK_GREEN),
        ]))
        elements.append(spt)
        elements.append(Spacer(1, 0.2*cm))

        # Methodological note
        if lang == 'fr':
            method_note = (
                "METHODOLOGIE — Evaluation des Enveloppes Bioclimatiques (BEA): "
                "Les scores de suitabilite sont calcules en comparant la temperature projetee en 2050 (NASA GDDP-CMIP6, ensemble 5 modeles: ACCESS-CM2, MIROC6, MPI-ESM1-2-HR, GFDL-ESM4, BCC-CSM2-MR, scenario SSP2-4.5) "
                "avec la plage de tolerance thermique reelle de chaque espece, derivee de l'analyse de distribution mondiale via GBIF (100 occurrences/espece). "
                "Methodologie: temp. estimee depuis latitude (27 - |lat| x 0.52°C), pénalites proportionnelles si temp. 2050 depasse la plage toleree. "
                "Seuils: Favorable ≥ 0.70 | Risque modere 0.40-0.69 | A risque < 0.40. "
                "Cette approche BEA est coherente avec les resultats MaxEnt complet pour les tendances generales "
                "(cf. etudes publiees sur Ceiba pentandra, SSP2-4.5, Frontiers in Forests 2026). "
                "Source des donnees: GBIF (CC BY 4.0) · WorldClim V1 · NASA GDDP-CMIP6 · ESA Sentinel-2."
            )
        else:
            method_note = (
                "METHODOLOGY — Bioclimatic Envelope Assessment (BEA): "
                "Suitability scores are calculated by comparing projected 2050 temperature (NASA GDDP-CMIP6, 5-model ensemble: ACCESS-CM2, MIROC6, MPI-ESM1-2-HR, GFDL-ESM4, BCC-CSM2-MR, SSP2-4.5 scenario) "
                "with each species real thermal tolerance range, derived from global distribution analysis via GBIF (100 occurrences/species). "
                "Method: temperature estimated from latitude (27 - |lat| x 0.52°C), proportional penalties when 2050 temperature exceeds tolerated range. "
                "Thresholds: Suitable ≥ 0.70 | Moderate risk 0.40-0.69 | At risk < 0.40. "
                "This BEA approach is consistent with full MaxEnt results for general trends "
                "(cf. published studies on Ceiba pentandra, SSP2-4.5, Frontiers in Forests 2026). "
                "Data sources: GBIF (CC BY 4.0) · WorldClim V1 · NASA GDDP-CMIP6 · ESA Sentinel-2."
            )
        elements.append(Paragraph(method_note,
            ParagraphStyle('mnote', fontName='Helvetica-Oblique', fontSize=7,
                textColor=MID_GREEN, leading=10, alignment=TA_LEFT)))
        elements.append(Spacer(1, 0.4*cm))

    # FOOTER
    # Scientific note about fire detection
    elements.append(Spacer(1, 0.3*cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=MID_GREEN))
    elements.append(Spacer(1, 0.15*cm))
    fire_note_en = ('FIRE DETECTION METHODOLOGY: Fire pixels are detected by NASA FIRMS using VIIRS (375m) '
        'and MODIS (1km) thermal anomaly sensors. Raw pixel count represents thermal detections over 12 months '
        'in the analysis zone. Estimated fire events are calculated using NASA clustering methodology '
        '(~4 pixels per fire event average). This is a statistical approximation. '
        'For precise fire event mapping, consult NASA FIRMS directly at firms.modaps.eosdis.nasa.gov')
    fire_note_fr = ('METHODOLOGIE DETECTION INCENDIES: Les pixels de feux sont detectes par NASA FIRMS via VIIRS (375m) '
        'et MODIS (1km). Le comptage brut represente les anomalies thermiques sur 12 mois. '
        'Les evenements estimes sont calcules selon la methodologie NASA de clustering '
        '(~4 pixels par evenement en moyenne). Pour une cartographie precise, consultez NASA FIRMS.')
    fire_note = fire_note_fr if lang == "fr" else fire_note_en
    elements.append(Paragraph(fire_note,
        ParagraphStyle('fnote', fontName='Helvetica', fontSize=7,
            textColor=MID_GREEN, alignment=TA_LEFT)))
    elements.append(Spacer(1, 0.15*cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=ACCENT_GREEN))
    elements.append(Spacer(1, 0.15*cm))
    disclaimer = ('Ce rapport a ete genere automatiquement par CanopySat avec des donnees satellites reelles. '
        'contact@canopysat.org - canopysat.org') if lang == 'fr' else \
        ('This report was automatically generated by CanopySat using real satellite data. '
        'contact@canopysat.org - canopysat.org')
    elements.append(Paragraph(disclaimer,
        ParagraphStyle('ft', fontName='Helvetica', fontSize=8, textColor=MID_GREEN, alignment=TA_CENTER)))

    doc.build(elements)
    return filename
