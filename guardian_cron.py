#!/usr/bin/env python3
"""Forest Guardian — Automatic monthly analysis cron job"""
import sqlite3, sys, os, ssl
import os.path
sys.path.insert(0, '/home/canopysat/app')
SMTP_PASS = '3Dq5yjzesH3N'

os.environ['GEE_PROJECT'] = 'canopysat-platform'

import ee, json
sa_path = '/home/canopysat/app/canopysat-service-account.json'
with open(sa_path) as f:
    sa_info = json.load(f)
credentials = ee.ServiceAccountCredentials(sa_info['client_email'], sa_path)
ee.Initialize(credentials, project='canopysat-platform')

from gee_analysis import analyze_forest
from datetime import datetime, timedelta

def send_guardian_alert(email, name, zone_name, score, alert, ndvi, cover, height, fires, pdf_path=None):
    import smtplib, ssl
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    
    if score >= 80:
        color = '#3DAA6B'
        status = 'Healthy Forest'
    elif score >= 60:
        color = '#F9A825'
        status = 'Moderate Forest'
    else:
        color = '#E53935'
        status = 'Critical Forest'
    
    fire_color = '#E53935' if fires > 100 else '#3DAA6B'
    alert_color = '#E53935' if 'CRITICAL' in alert else ('#1565C0' if 'POSITIVE' in alert else '#3DAA6B')
    
    subject = f"Forest Guardian Report — {zone_name} · Score {score}/100"
    
    body = "<html><body style='font-family:Arial,sans-serif;background:#0D3B2E;padding:20px;'>"
    body += "<div style='max-width:600px;margin:0 auto;background:#1B4332;border-radius:12px;padding:25px;border:1px solid #1B6B45;'>"
    body += "<h1 style='color:#3DAA6B;text-align:center;font-size:18px;'>CANOPYSAT FOREST GUARDIAN</h1>"
    body += "<p style='color:#D6EFE1;text-align:center;font-size:11px;'>Satellite Forest Monitoring Report</p>"
    body += f"<p style='color:#D6EFE1;'>Hello {name},</p>"
    body += f"<p style='color:#D6EFE1;'>Latest satellite analysis for <strong style='color:#3DAA6B;'>{zone_name}</strong>:</p>"
    body += f"<div style='background:#0D3B2E;border-radius:8px;padding:20px;text-align:center;margin:15px 0;'>"
    body += f"<div style='font-size:52px;font-weight:bold;color:{color};'>{score}</div>"
    body += "<div style='font-size:12px;color:#D6EFE1;'>Forest Integrity Score / 100</div>"
    body += f"<div style='font-size:14px;font-weight:bold;color:{color};margin-top:5px;'>{status}</div>"
    body += "</div>"
    body += "<table style='width:100%;border-collapse:collapse;margin:15px 0;'><tr>"
    body += f"<td style='background:#0D3B2E;border-radius:6px;padding:10px;text-align:center;width:25%;'><div style='font-size:18px;color:#3DAA6B;'>{ndvi}</div><div style='font-size:10px;color:#D6EFE1;'>NDVI</div></td>"
    body += f"<td style='background:#0D3B2E;border-radius:6px;padding:10px;text-align:center;width:25%;'><div style='font-size:18px;color:#3DAA6B;'>{cover}%</div><div style='font-size:10px;color:#D6EFE1;'>Forest Cover</div></td>"
    body += f"<td style='background:#0D3B2E;border-radius:6px;padding:10px;text-align:center;width:25%;'><div style='font-size:18px;color:#3DAA6B;'>{height}m</div><div style='font-size:10px;color:#D6EFE1;'>Canopy Height</div></td>"
    body += f"<td style='background:#0D3B2E;border-radius:6px;padding:10px;text-align:center;width:25%;'><div style='font-size:18px;color:{fire_color};'>{fires}</div><div style='font-size:10px;color:#D6EFE1;'>Fire Pixels</div></td>"
    body += "</tr></table>"
    body += f"<div style='background:#0D3B2E;border:1px solid {alert_color};border-radius:6px;padding:10px;text-align:center;margin:15px 0;'>"
    body += f"<strong style='color:{alert_color};'>{alert}</strong></div>"
    body += "<div style='text-align:center;margin-top:20px;'>"
    body += "<a href='https://www.canopysat.org/guardian' style='display:inline-block;padding:12px 25px;background:#2D8A5A;color:white;border-radius:8px;text-decoration:none;font-size:13px;font-weight:bold;'>View Dashboard</a>"
    body += "</div>"
    body += "<p style='color:#2D6A4F;font-size:10px;text-align:center;margin-top:20px;'>CanopySat Forest Guardian · canopysat.org · Data: ESA Sentinel-2, NASA Landsat, NASA GEDI LiDAR</p>"
    body += "</div></body></html>"
    
    try:
        msg = MIMEMultipart('mixed')
        msg['Subject'] = subject
        msg['From'] = 'CanopySat Forest Guardian <contact@canopysat.org>'
        msg['To'] = email
        
        # HTML body
        alt_part = MIMEMultipart('alternative')
        alt_part.attach(MIMEText(body, 'html'))
        msg.attach(alt_part)
        
        # Attach PDF if available
        if pdf_path and os.path.exists(pdf_path):
            from email.mime.base import MIMEBase
            from email import encoders
            with open(pdf_path, 'rb') as f:
                pdf_data = f.read()
            pdf_part = MIMEBase('application', 'pdf')
            pdf_part.set_payload(pdf_data)
            encoders.encode_base64(pdf_part)
            pdf_name = os.path.basename(pdf_path)
            pdf_part.add_header('Content-Disposition', f'attachment; filename="{pdf_name}"')
            msg.attach(pdf_part)
        
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtppro.zoho.eu', 465, context=context) as s:
            s.login('contact@canopysat.org', SMTP_PASS)
            s.send_message(msg)
        print(f'  Email sent to {email}')
        return True
    except Exception as e:
        print(f'  Email error: {e}')
        return False

def run_due_analyses():
    conn = sqlite3.connect('/home/canopysat/app/guardian.db')
    conn.row_factory = sqlite3.Row
    
    zones = conn.execute('''
        SELECT z.*, u.email, u.name, u.plan
        FROM guardian_zones z
        JOIN users u ON z.user_id = u.id
        WHERE z.active = 1
    ''').fetchall()
    
    now = datetime.now()
    analyzed = 0
    
    for zone in zones:
        # Check if analysis is due
        last = zone['last_analysis']
        freq = zone['frequency']
        
        due = False
        if not last:
            due = True
        else:
            last_dt = datetime.strptime(last[:19], '%Y-%m-%d %H:%M:%S')
            if freq == 'daily' and (now - last_dt).days >= 1:
                due = True
            elif freq == 'weekly' and (now - last_dt).days >= 7:
                due = True
            elif freq == 'monthly' and (now - last_dt).days >= 30:
                due = True
        
        if due:
            print(f"Analyzing zone {zone['name']} for {zone['email']}...")
            try:
                result = analyze_forest(zone['lat'], zone['lng'], zone['size'])
                if result and result.get('score'):
                    conn.execute('''INSERT INTO guardian_analyses
                        (zone_id, user_id, score, ndvi, forest_cover, canopy_height,
                         deforestation_alert, active_fires, trend)
                        VALUES (?,?,?,?,?,?,?,?,?)''',
                        (zone['id'], zone['user_id'], result.get('score'),
                         result.get('ndvi_current'), result.get('forest_cover'),
                         result.get('canopy_height'), result.get('deforestation_alert'),
                         result.get('active_fires'), result.get('trend')))
                    conn.execute('UPDATE guardian_zones SET last_analysis=CURRENT_TIMESTAMP WHERE id=?',
                        (zone['id'],))
                    conn.commit()
                    analyzed += 1
                    print(f"  ✅ Score: {result.get('score')}/100 — {result.get('deforestation_alert')}")
                    # Generate PDF
                    pdf_path = None
                    try:
                        sys.path.insert(0, '/home/canopysat/app')
                        from pdf_report import generate_pdf
                        result['size_km'] = zone['size']
                        pdf_file = generate_pdf(result, 'en')
                        pdf_path = os.path.join('/home/canopysat/app/reports', pdf_file)
                        print(f'  PDF generated: {pdf_file}')
                    except Exception as pe:
                        print(f'  PDF error: {pe}')
                    
                    # Send email report with PDF
                    send_guardian_alert(
                        zone['email'],
                        zone['name'] or zone['email'],
                        zone['name'],
                        result.get('score', 0),
                        result.get('deforestation_alert', 'STABLE'),
                        result.get('ndvi_current', 0),
                        result.get('forest_cover', 0),
                        result.get('canopy_height', 0),
                        result.get('active_fires', 0),
                        pdf_path=pdf_path
                    )
            except Exception as e:
                print(f"  ❌ Error: {e}")
    
    conn.close()
    print(f"\nDone — {analyzed} zones analyzed")

if __name__ == '__main__':
    run_due_analyses()
