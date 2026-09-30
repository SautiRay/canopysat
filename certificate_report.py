from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image as RLImage
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime
import os

def generate_certificate(data, lang='en'):
    os.makedirs('/home/canopysat/app/reports', exist_ok=True)

    lat = data.get('lat', 0)
    lng = data.get('lng', 0)
    size_km = data.get('size_km', 10)
    score = data.get('score', 0)
    analysis_date = data.get('analysis_date', datetime.now().strftime('%Y-%m-%d'))
    alert = data.get('deforestation_alert', 'N/A')
    forest_cover = data.get('forest_cover', 0)
    ndvi = data.get('ndvi_current', 0)
    canopy_height = data.get('canopy_height')
    carbon_total_co2 = data.get('carbon_total_co2')
    carbon_per_ha = data.get('carbon_per_ha')
    carbon_area_ha = data.get('carbon_area_ha')
    carbon_value_eur = data.get('carbon_value_eur')
    estimated_agb = data.get('estimated_agb')
    satellites = data.get('satellites_used', [])

    cert_num = f"CS-{analysis_date.replace('-','')}-{abs(int(lat*100))}{abs(int(lng*100))}"
    filename = f"CanopySat_Certificate_{cert_num}.pdf"
    output_path = f'/home/canopysat/app/reports/{filename}'

    doc = SimpleDocTemplate(output_path, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)

    DARK_GREEN = colors.HexColor('#0D3B2E')
    GREEN_MID = colors.HexColor('#1B4332')
    GREEN_ACCENT = colors.HexColor('#2D8A5A')
    GREEN_LIGHT = colors.HexColor('#3DAA6B')
    WHITE = colors.white
    BLACK = colors.HexColor('#111111')
    GRAY = colors.HexColor('#555555')
    LIGHT_GRAY = colors.HexColor('#F5FFF5')
    YELLOW = colors.HexColor('#F9A825')
    BLUE = colors.HexColor('#1565C0')

    elements = []

    # Header bar
    logo_path = '/home/canopysat/app/static/img/logo.png'
    try:
        logo = RLImage(logo_path, width=1.8*cm, height=1.8*cm)
        header_data = [[
            logo,
            Paragraph('<b>CANOPYSAT</b>',
                ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=16, textColor=WHITE)),
            Paragraph('FOREST INTELLIGENCE ECOSYSTEM<br/>canopysat.org · contact@canopysat.org',
                ParagraphStyle('s', fontName='Helvetica', fontSize=9, textColor=GREEN_LIGHT,
                    leading=13, alignment=2))
        ]]
        ht = Table(header_data, colWidths=[2.2*cm, 6*cm, 8.8*cm])
    except:
        header_data = [[
            Paragraph('<b>🛰️ CANOPYSAT</b>',
                ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=16, textColor=GREEN_LIGHT)),
            Paragraph('FOREST INTELLIGENCE ECOSYSTEM<br/>canopysat.org · contact@canopysat.org',
                ParagraphStyle('s', fontName='Helvetica', fontSize=9, textColor=GREEN_LIGHT,
                    leading=13, alignment=2))
        ]]
        ht = Table(header_data, colWidths=[8*cm, 9*cm])
    ht.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), DARK_GREEN),
        ('PADDING', (0,0), (-1,-1), 14),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(ht)
    elements.append(Spacer(1, 0.4*cm))

    # Certificate title
    elements.append(Paragraph(
        'SATELLITE FOREST MONITORING CERTIFICATE' if lang == 'en' else 'CERTIFICAT DE SURVEILLANCE FORESTIERE PAR SATELLITE',
        ParagraphStyle('title', fontName='Helvetica-Bold', fontSize=16,
            textColor=DARK_GREEN, alignment=TA_CENTER, spaceAfter=4)))
    elements.append(Paragraph(
        f'Certificate No. {cert_num}',
        ParagraphStyle('cert_num', fontName='Helvetica', fontSize=10,
            textColor=GRAY, alignment=TA_CENTER, spaceAfter=6)))
    elements.append(HRFlowable(width='100%', thickness=2, color=GREEN_LIGHT))
    elements.append(Spacer(1, 0.3*cm))

    # Certification statement
    if lang == 'en':
        stmt = (f"<b>CanopySat</b> hereby certifies that the forest zone located at coordinates "
                f"<b>{lat}°, {lng}°</b> (radius: {size_km} km) has been analyzed using "
                f"real satellite data from 6 independent satellite sources on <b>{analysis_date}</b>. "
                f"This certificate confirms the satellite-based forest monitoring data quality "
                f"and compliance with REDD+ MRV (Measurement, Reporting and Verification) requirements.")
    else:
        stmt = (f"<b>CanopySat</b> certifie par la presente que la zone forestiere situee aux coordonnees "
                f"<b>{lat}°, {lng}°</b> (rayon: {size_km} km) a ete analysee en utilisant "
                f"des donnees satellites reelles de 6 sources satellites independantes le <b>{analysis_date}</b>. "
                f"Ce certificat confirme la qualite des donnees de surveillance forestiere par satellite "
                f"et la conformite avec les exigences MRV REDD+ (Mesure, Notification et Verification).")

    elements.append(Paragraph(stmt,
        ParagraphStyle('stmt', fontName='Helvetica', fontSize=10,
            textColor=BLACK, leading=16, alignment=TA_JUSTIFY, spaceAfter=12)))

    # Score badge
    score_color = GREEN_LIGHT if score >= 70 else (YELLOW if score >= 50 else colors.HexColor('#E53935'))
    score_data = [[
        Paragraph(f'<b>{score}/100</b>',
            ParagraphStyle('sc', fontName='Helvetica-Bold', fontSize=24,
                textColor=score_color, alignment=TA_CENTER, leading=28)),
        Paragraph(
            f'<b>{"Forest Integrity Score" if lang == "en" else "Score Intégrité Forestière"}</b><br/>'
            f'<font color="#3DAA6B">{alert}</font>',
            ParagraphStyle('sl', fontName='Helvetica', fontSize=12,
                textColor=BLACK, leading=18))
    ]]
    st = Table(score_data, colWidths=[4*cm, 13*cm])
    st.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_GRAY),
        ('PADDING', (0,0), (-1,-1), 14),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (0,0), (-1,-1), 1.5, GREEN_LIGHT),
        ('ROUNDEDCORNERS', [8]),
    ]))
    elements.append(st)
    elements.append(Spacer(1, 0.3*cm))

    # Forest data table
    elements.append(Paragraph(
        'FOREST MONITORING DATA' if lang == 'en' else 'DONNEES DE SURVEILLANCE FORESTIERE',
        ParagraphStyle('sec', fontName='Helvetica-Bold', fontSize=10,
            textColor=GREEN_LIGHT, spaceBefore=8, spaceAfter=6)))

    forest_rows = [
        ['Indicator' if lang == 'en' else 'Indicateur',
         'Value' if lang == 'en' else 'Valeur',
         'Source'],
        ['Forest cover' if lang == 'en' else 'Couverture forestiere',
         f'{forest_cover}%', 'ESA Sentinel-2 (10m)'],
        ['Vegetation health (NDVI)' if lang == 'en' else 'Sante vegetation (NDVI)',
         f'{ndvi}', 'ESA Sentinel-2 (10m)'],
    ]
    if canopy_height:
        forest_rows.append([
            'Canopy height (GEDI+S2 10m)' if lang == 'en' else 'Hauteur canopee (GEDI+S2 10m)',
            f'{canopy_height} m', 'NASA GEDI LiDAR + Sentinel-2'
        ])
    if estimated_agb:
        forest_rows.append([
            'Above-ground biomass' if lang == 'en' else 'Biomasse aerienne',
            f'{estimated_agb} t/ha', 'NASA GEDI LiDAR (Chave 2014)'
        ])
    forest_rows.append([
        'Analysis date' if lang == 'en' else 'Date analyse',
        analysis_date, 'CanopySat'
    ])
    for i, sat in enumerate(satellites):
        label = ("Satellites used" if lang == "en" else "Satellites utilises") if i == 0 else ""
        src = "ESA" if "Sentinel" in sat else "NASA"
        forest_rows.append([label, sat, src])


    ft = Table(forest_rows, colWidths=[5*cm, 6*cm, 6*cm])
    ft.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), GREEN_MID),
        ('TEXTCOLOR', (0,0), (-1,0), GREEN_LIGHT),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TEXTCOLOR', (0,1), (-1,-1), BLACK),
        ('PADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [LIGHT_GRAY, WHITE]),
    ]))
    elements.append(ft)
    elements.append(Spacer(1, 0.3*cm))

    # Carbon section
    if carbon_total_co2:
        elements.append(Paragraph(
            'CARBON ASSESSMENT (IPCC METHODOLOGY)' if lang == 'en' else 'BILAN CARBONE (METHODOLOGIE IPCC)',
            ParagraphStyle('sec2', fontName='Helvetica-Bold', fontSize=10,
                textColor=GREEN_LIGHT, spaceBefore=8, spaceAfter=6)))

        carbon_rows = [
            ['Indicator' if lang == 'en' else 'Indicateur',
             'Value' if lang == 'en' else 'Valeur',
             'Methodology' if lang == 'en' else 'Methodologie'],
            ['Zone area' if lang == 'en' else 'Superficie zone',
             f'{int(carbon_area_ha):,} ha', 'GPS coordinates'],
            ['CO2 per hectare', f'{carbon_per_ha} t CO2/ha',
             'IPCC Tier 1 (AGB+BGB × 0.47 × 3.67)'],
            ['Total CO2 sequestered' if lang == 'en' else 'CO2 total sequestre',
             f'{int(carbon_total_co2):,} t CO2', 'IPCC 2006/2019'],
            ['Carbon credit value' if lang == 'en' else 'Valeur credits carbone',
             f'EUR {int(carbon_value_eur):,}',
             'EUR 15/tonne CO2 (voluntary market)'],
            ['Annual potential' if lang == 'en' else 'Potentiel annuel',
             f'EUR {int(carbon_value_eur/12):,} / year',
             'Based on maintained preservation'],
            ['REDD+ MRV compliance' if lang == 'en' else 'Conformite MRV REDD+',
             'Compliant' if lang == 'en' else 'Conforme',
             'VCS VM0007 / VM0009 compatible'],
        ]

        ct = Table(carbon_rows, colWidths=[6*cm, 4*cm, 7*cm])
        ct.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), GREEN_MID),
            ('TEXTCOLOR', (0,0), (-1,0), GREEN_LIGHT),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('TEXTCOLOR', (0,1), (-1,-1), BLACK),
            ('TEXTCOLOR', (1,-1), (1,-1), GREEN_LIGHT),
            ('FONTNAME', (1,-1), (1,-1), 'Helvetica-Bold'),
            ('PADDING', (0,0), (-1,-1), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [LIGHT_GRAY, WHITE]),
        ]))
        elements.append(ct)
        elements.append(Spacer(1, 0.3*cm))

    # Disclaimer
    elements.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#CCCCCC')))
    elements.append(Spacer(1, 0.2*cm))
    if lang == 'en':
        disc = ("DISCLAIMER: This certificate is issued by CanopySat based on satellite data analysis. "
                "It provides satellite-based MRV data consistent with REDD+ monitoring requirements. "
                "For official carbon credit issuance under VCS, Gold Standard or other recognized standards, "
                "independent third-party verification by an accredited auditor is required. "
                "Carbon values are estimates based on IPCC Tier 1 methodology.")
    else:
        disc = ("AVERTISSEMENT: Ce certificat est emis par CanopySat sur la base d'une analyse de donnees satellites. "
                "Il fournit des donnees MRV par satellite conformes aux exigences de monitoring REDD+. "
                "Pour l'emission officielle de credits carbone sous VCS, Gold Standard ou autres standards reconnus, "
                "une verification tierce independante par un auditeur accredite est requise. "
                "Les valeurs carbone sont des estimations basees sur la methodologie IPCC Tier 1.")

    elements.append(Paragraph(disc,
        ParagraphStyle('disc', fontName='Helvetica-Oblique', fontSize=7.5,
            textColor=GRAY, leading=11, alignment=TA_JUSTIFY)))
    elements.append(Spacer(1, 0.3*cm))

    # Signature block
    sig_data = [[
        Paragraph(
            f'<b>{"Issued by" if lang == "en" else "Emis par"}</b><br/>'
            f'Raymond Sauti<br/>'
            f'{"Founder & CEO" if lang == "en" else "Fondateur & CEO"} — CanopySat<br/>'
            f'contact@canopysat.org',
            ParagraphStyle('sig', fontName='Helvetica', fontSize=9,
                textColor=BLACK, leading=14)),
        Paragraph(
            f'<b>{"Issue date" if lang == "en" else "Date emission"}</b><br/>'
            f'{datetime.now().strftime("%d %B %Y")}<br/><br/>'
            f'<b>{"Valid for" if lang == "en" else "Valable pour"}</b><br/>'
            f'{"This analysis only" if lang == "en" else "Cette analyse uniquement"}',
            ParagraphStyle('sig2', fontName='Helvetica', fontSize=9,
                textColor=BLACK, leading=14)),
        Paragraph(
            f'<b>{"Scientific validation" if lang == "en" else "Validation scientifique"}</b><br/>'
            f'Zenodo DOI:<br/>'
            f'10.5281/zenodo.22872779<br/>'
            f'CC BY 4.0',
            ParagraphStyle('sig3', fontName='Helvetica', fontSize=9,
                textColor=BLACK, leading=14)),
    ]]
    sig_t = Table(sig_data, colWidths=[6*cm, 5*cm, 6*cm])
    sig_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_GRAY),
        ('PADDING', (0,0), (-1,-1), 10),
        ('BOX', (0,0), (-1,-1), 1, GREEN_LIGHT),
        ('LINEAFTER', (0,0), (1,-1), 0.5, colors.HexColor('#CCCCCC')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    elements.append(sig_t)
    elements.append(Spacer(1, 0.2*cm))

    # Footer
    elements.append(HRFlowable(width='100%', thickness=1, color=GREEN_LIGHT))
    elements.append(Paragraph(
        f'CanopySat Forest Intelligence · canopysat.org · {cert_num} · '
        f'{"Generated" if lang == "en" else "Genere"} {datetime.now().strftime("%Y-%m-%d %H:%M")} UTC',
        ParagraphStyle('foot', fontName='Helvetica', fontSize=7.5,
            textColor=GRAY, alignment=TA_CENTER)))

    doc.build(elements)
    return filename

