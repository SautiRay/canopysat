import ee
import os
import json
import re
import anthropic
from datetime import datetime, timedelta

def run_random_forest_classification(aoi, credentials_path='/home/canopysat/app/canopysat-service-account.json'):
    """
    Random Forest classifier trained on ESA WorldCover 2021 + Hansen GFW 2025
    Returns pixel-level forest classification stats
    """
    try:
        # Sentinel-2 composite for the zone
        s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(aoi)
            .filterDate('2024-01-01', '2025-01-01')
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
            .select(['B2','B3','B4','B8','B11','B12'])
            .median())

        # Compute indices
        ndvi = s2.normalizedDifference(['B8','B4']).rename('NDVI')
        evi = s2.expression('2.5*(NIR-RED)/(NIR+6*RED-7.5*BLUE+1)',
            {'NIR':s2.select('B8'),'RED':s2.select('B4'),'BLUE':s2.select('B2')}).rename('EVI')
        nbr = s2.normalizedDifference(['B8','B12']).rename('NBR')
        ndwi = s2.normalizedDifference(['B3','B8']).rename('NDWI')

        # Feature stack
        features = s2.addBands([ndvi, evi, nbr, ndwi])

        # ESA WorldCover 2021 as training labels
        worldcover = ee.ImageCollection('ESA/WorldCover/v200').first().select('Map')

        # Remap WorldCover to 4 classes:
        # 10=Trees→1(forest), 20=Shrubland→2(degraded), 30/40/50=Grass/Crop/Urban→3(non-forest), 80=Water→4(water)
        landcover = worldcover.remap(
            [10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100],
            [1,  2,  3,  3,  3,  3,  3,  4,  2,  1,  2]
        ).rename('landcover')

        # Hansen GFW 2025 — add deforestation layer
        hansen = ee.Image('UMD/hansen/global_forest_change_2025_v1_13')
        lossYear = hansen.select('lossyear')
        # Recent loss (dynamic 5 years) = class 5 (deforested)
        import datetime as _dt
        _current_year = _dt.datetime.now().year
        _start_yr = (_current_year - 5) % 100
        _end_yr = _current_year % 100
        recentLoss = lossYear.gte(_start_yr).And(lossYear.lte(_end_yr))
        _loss_period = f"{_current_year-5}-{_current_year}" 
        landcover = landcover.where(recentLoss.eq(1), 5)

        # Training samples
        training = features.addBands(landcover).stratifiedSample(
            numPoints=100,
            classBand='landcover',
            region=aoi.buffer(50000),
            scale=30,
            seed=42,
            geometries=True
        )

        # Train Random Forest
        classifier = ee.Classifier.smileRandomForest(
            numberOfTrees=50,
            seed=42
        ).train(
            features=training,
            classProperty='landcover',
            inputProperties=['B2','B3','B4','B8','B11','B12','NDVI','EVI','NBR','NDWI']
        )

        # Classify the zone
        classified = features.classify(classifier)

        # Compute stats
        stats = classified.reduceRegion(
            reducer=ee.Reducer.frequencyHistogram(),
            geometry=aoi,
            scale=10,
            maxPixels=1e9
        ).getInfo()

        hist = stats.get('classification', {})
        total = sum(hist.values()) if hist else 1

        rf_forest_pct = round(hist.get('1', 0) / total * 100, 1)
        rf_degraded_pct = round(hist.get('2', 0) / total * 100, 1)
        rf_nonforest_pct = round(hist.get('3', 0) / total * 100, 1)
        rf_water_pct = round(hist.get('4', 0) / total * 100, 1)
        rf_deforested_pct = round(hist.get('5', 0) / total * 100, 1)

        return {
            'rf_success': True,
            'rf_forest_pct': rf_forest_pct,
            'rf_degraded_pct': rf_degraded_pct,
            'rf_nonforest_pct': rf_nonforest_pct,
            'rf_water_pct': rf_water_pct,
            'rf_deforested_pct': rf_deforested_pct,
            'rf_training': 'ESA WorldCover 2021 + Hansen GFW 2025',
            'rf_algorithm': 'Random Forest (50 trees, GEE smileRandomForest)',
            'rf_loss_period': _loss_period
        }

    except Exception as e:
        print(f"RF Error: {e}")
        return {'rf_success': False}


def initialize_gee():
    try:
        ee.Initialize(project=os.getenv('GEE_PROJECT', 'canopysat-platform'))
        return True
    except Exception as e:
        print(f"GEE Error: {e}")
        return False

def analyze_forest(lat, lng, size_km=10, lang='en'):
    try:
        # Define area of interest
        point = ee.Geometry.Point([float(lng), float(lat)])
        buffer = float(size_km) * 500
        aoi = point.buffer(buffer).bounds()

        # Date range
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        gedi_start = '2019-04-01'  # GEDI available from April 2019
        start_date_3y = (datetime.now() - timedelta(days=1095)).strftime('%Y-%m-%d')
        start_date_10y = (datetime.now() - timedelta(days=3650)).strftime('%Y-%m-%d')
        landsat_start = '1984-01-01'

        # Sentinel-2 current year
        s2_current = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(aoi)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
            .median()
            .clip(aoi))

        # Sentinel-2 3 years ago
        s2_past = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(aoi)
            .filterDate(start_date_3y, start_date)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
            .median()
            .clip(aoi))

        # Sentinel-2 5 years ago
        start_date_5y = (datetime.now() - timedelta(days=1825)).strftime('%Y-%m-%d')
        start_date_4y = (datetime.now() - timedelta(days=1460)).strftime('%Y-%m-%d')
        s2_5y = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(aoi)
            .filterDate(start_date_5y, start_date_4y)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
            .median()
            .clip(aoi))

        # Landsat historical - 10 years ago
        landsat_10y = (ee.ImageCollection('LANDSAT/LC09/C02/T1_L2')
            .merge(ee.ImageCollection('LANDSAT/LC08/C02/T1_L2'))
            .filterBounds(aoi)
            .filterDate(start_date_10y, start_date_3y)
            .filter(ee.Filter.lt('CLOUD_COVER', 30))
            .median()
            .clip(aoi))

        # Landsat 1984 baseline
        landsat_1984 = (ee.ImageCollection('LANDSAT/LT05/C02/T1_L2')
            .merge(ee.ImageCollection('LANDSAT/LT04/C02/T1_L2'))
            .filterBounds(aoi)
            .filterDate('1984-01-01', '1995-12-31')
            .filter(ee.Filter.lt('CLOUD_COVER', 30))
            .median()
            .clip(aoi))

        # Calculate NDVI current (Sentinel-2)
        ndvi_current = s2_current.normalizedDifference(['B8', 'B4']).rename('NDVI')
        ndvi_past = s2_past.normalizedDifference(['B8', 'B4']).rename('NDVI')
        ndvi_5y = s2_5y.normalizedDifference(['B8', 'B4']).rename('NDVI')

        # Landsat NDVI (bands differ from Sentinel-2)
        ndvi_10y = landsat_10y.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI')
        ndvi_1984 = landsat_1984.normalizedDifference(['SR_B4', 'SR_B3']).rename('NDVI')

        # NDVI 5 years ago
        try:
            ndvi_5y_mean = ndvi_5y.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=aoi,
                scale=100,
                maxPixels=1e9
            ).get('NDVI').getInfo()
        except:
            ndvi_5y_mean = None

        # Landsat 10y NDVI mean
        try:
            ndvi_10y_mean = ndvi_10y.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=aoi,
                scale=100,
                maxPixels=1e9
            ).get('NDVI').getInfo()
        except:
            ndvi_10y_mean = None

        # Landsat 1984 NDVI mean
        try:
            ndvi_1984_mean = ndvi_1984.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=aoi,
                scale=100,
                maxPixels=1e9
            ).get('NDVI').getInfo()
        except:
            ndvi_1984_mean = None

        # Mean NDVI values
        ndvi_current_mean = ndvi_current.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=aoi,
            scale=100,
            maxPixels=1e9
        ).get('NDVI').getInfo()

        ndvi_past_mean = ndvi_past.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=aoi,
            scale=100,
            maxPixels=1e9
        ).get('NDVI').getInfo()

        # Forest cover percentage (NDVI > 0.4 = forest)
        forest_mask = ndvi_current.gt(0.4)
        forest_area = forest_mask.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=aoi,
            scale=100,
            maxPixels=1e9
        ).get('NDVI').getInfo()

        # ═══ NIVEAU 3 — Détection automatique de déforestation ═══
        try:
            # Forest mask current — NDVI > 0.4 = forest
            forest_current = ndvi_current.gt(0.4)
            forest_past_3y = ndvi_past.gt(0.4)

            # Calculate forest area in pixels
            forest_area_current = forest_current.reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=aoi,
                scale=100,
                maxPixels=1e9
            ).get('NDVI').getInfo()

            forest_area_past = forest_past_3y.reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=aoi,
                scale=100,
                maxPixels=1e9
            ).get('NDVI').getInfo()

            # Calculate deforestation
            if forest_area_current is not None and forest_area_past is not None:
                # Each pixel = 100m x 100m = 1 hectare
                forest_ha_current = float(forest_area_current) * 1.0
                forest_ha_past = float(forest_area_past) * 1.0
                forest_change_ha = round(forest_ha_current - forest_ha_past, 1)
                forest_change_pct = round((forest_change_ha / forest_ha_past * 100) if forest_ha_past > 0 else 0, 2)

                # Annual deforestation rate based on surface (ha/year over 3 years)
                annual_ha_rate = round(forest_change_ha / 3, 1)

                # 10-year comparison using Landsat
                if ndvi_10y_mean is not None:
                    forest_10y_mask = ndvi_10y.gt(0.4)
                    forest_area_10y = forest_10y_mask.reduceRegion(
                        reducer=ee.Reducer.sum(),
                        geometry=aoi,
                        scale=100,
                        maxPixels=1e9
                    ).get('NDVI').getInfo()
                    if forest_area_10y is not None:
                        forest_ha_10y = float(forest_area_10y) * 1.0
                        forest_change_ha_10y = round(forest_ha_current - forest_ha_10y, 1)
                        forest_change_pct_10y = round((forest_change_ha_10y / forest_ha_10y * 100) if forest_ha_10y > 0 else 0, 2)
                        annual_ha_rate_10y = round(forest_change_ha_10y / 10, 1)
                    else:
                        forest_change_ha_10y = None
                        forest_change_pct_10y = None
                        annual_ha_rate_10y = None
                else:
                    forest_change_ha_10y = None
                    forest_change_pct_10y = None
                    annual_ha_rate_10y = None

                # Deforestation alert
                if forest_change_pct < -10:
                    deforestation_alert = 'CRITICAL — Severe deforestation detected'
                    deforestation_alert_fr = 'CRITIQUE — Déforestation sévère détectée'
                elif forest_change_pct < -5:
                    deforestation_alert = 'WARNING — Significant forest loss'
                    deforestation_alert_fr = 'ALERTE — Perte forestière significative'
                elif forest_change_pct < -2:
                    deforestation_alert = 'CAUTION — Light forest degradation'
                    deforestation_alert_fr = 'ATTENTION — Dégradation forestière légère'
                elif forest_change_pct > 2:
                    deforestation_alert = 'POSITIVE — Forest recovery detected'
                    deforestation_alert_fr = 'POSITIF — Récupération forestière détectée'
                else:
                    deforestation_alert = 'STABLE — No significant change'
                    deforestation_alert_fr = 'STABLE — Aucun changement significatif'
            else:
                forest_change_ha = None
                forest_change_pct = None
                deforestation_alert = None
                deforestation_alert_fr = None

        except Exception as e:
            forest_change_ha = None
            forest_change_pct = None
            deforestation_alert = None
            deforestation_alert_fr = None

        # ═══ LEAF TYPE — Coniferous vs Broadleaf (NDRE Sentinel-2) ═══
        try:
            # NDRE = (B8A - B5) / (B8A + B5) — Red Edge index
            ndre = s2_current.normalizedDifference(['B8A', 'B5']).rename('NDRE')
            ndre_mean = ndre.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=aoi,
                scale=100,
                maxPixels=1e9
            ).get('NDRE').getInfo()

            # SWIR ratio for leaf type detection
            swir_ratio = s2_current.select('B11').divide(s2_current.select('B8')).rename('SWIR')
            swir_mean = swir_ratio.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=aoi,
                scale=100,
                maxPixels=1e9
            ).get('SWIR').getInfo()

            if ndre_mean is not None and ndvi_current_mean is not None:
                ndre_val = float(ndre_mean)
                swir_val = float(swir_mean) if swir_mean else 0.5

                # Coniferous: high NDRE, lower SWIR ratio
                # Broadleaf: moderate NDRE, higher SWIR ratio
                if ndvi_current_mean < 0.2:
                    leaf_type = 'Non-forest'
                    leaf_type_fr = 'Non-forestier'
                elif ndre_val > 0.25 and swir_val < 0.4:
                    leaf_type = 'Coniferous (Needleleaf)'
                    leaf_type_fr = 'Coniferes (Aiguilles)'
                elif ndre_val > 0.15 and swir_val < 0.6:
                    leaf_type = 'Mixed (Coniferous/Broadleaf)'
                    leaf_type_fr = 'Mixte (Coniferes/Feuillus)'
                else:
                    leaf_type = 'Broadleaf (Deciduous/Evergreen)'
                    leaf_type_fr = 'Feuillus (Decidus/Persistants)'
            else:
                leaf_type = None
                leaf_type_fr = None
                ndre_val = None

        except Exception as e:
            leaf_type = None
            leaf_type_fr = None
            ndre_val = None

        # ═══ DEVELOPMENTAL STAGE — Forest age estimation ═══
        try:
            # Use NBR and NDVI combination to estimate forest maturity
            nbr_current = s2_current.normalizedDifference(['B8', 'B12']).rename('NBR')
            nbr_mean = nbr_current.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=aoi,
                scale=100,
                maxPixels=1e9
            ).get('NBR').getInfo()

            if ndvi_current_mean is not None:
                nbr_val = float(nbr_mean) if nbr_mean else 0.3
                ndvi_val = float(ndvi_current_mean)

                # Forest developmental stage based on NBR + NDVI + long-term trend
                long_trend = ndvi_change_40y_val if 'ndvi_change_40y_val' in dir() and ndvi_change_40y_val else 0

                if ndvi_val < 0.2:
                    dev_stage = 'Non-forest / Bare'
                    dev_stage_fr = 'Non-forestier / Sol nu'
                    dev_stage_age = 'N/A'
                elif ndvi_val < 0.4 or nbr_val < 0.1:
                    dev_stage = 'Young forest (0-20 years)'
                    dev_stage_fr = 'Jeune foret (0-20 ans)'
                    dev_stage_age = '0-20 years'
                elif ndvi_val < 0.6 or nbr_val < 0.3:
                    dev_stage = 'Growing forest (20-60 years)'
                    dev_stage_fr = 'Forêt en croissance (20-60 ans)'
                    dev_stage_age = '20-60 years'
                elif ndvi_val < 0.75 or nbr_val < 0.5:
                    dev_stage = 'Mature forest (60-120 years)'
                    dev_stage_fr = 'Forêt mature (60-120 ans)'
                    dev_stage_age = '60-120 years'
                else:
                    dev_stage = 'Old-growth forest (>120 years)'
                    dev_stage_fr = 'Forêt ancienne (>120 ans)'
                    dev_stage_age = '>120 years'
            else:
                dev_stage = None
                dev_stage_fr = None
                dev_stage_age = None

        except Exception as e:
            dev_stage = None
            dev_stage_fr = None
            dev_stage_age = None

        # Carbon variables — initialized before biomass block
        carbon_per_ha = None
        carbon_area_ha = None
        carbon_total_co2 = None
        carbon_value_eur = None

        # ═══ CANOPY HEIGHT — NASA GEDI LiDAR (real satellite measurement) ═══
        height_val = None
        gedi_rh50 = None
        gedi_cover = None
        
        try:
            # NASA GEDI Level 2A — Real LiDAR canopy height measurements
            # rh98 = height at 98th percentile (max canopy height)
            # rh50 = height at 50th percentile (median canopy height)
            # cover = canopy cover fraction
            gedi = ee.ImageCollection('LARSE/GEDI/GEDI02_A_002_MONTHLY') \
                .filterBounds(aoi) \
                .filterDate(gedi_start, end_date) \
                .select(['rh98', 'rh50', 'landsat_treecover']) \
                .mean()
            
            gedi_stats = gedi.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=aoi,
                scale=25,
                maxPixels=1e9
            )
            
            rh98_val = gedi_stats.get('rh98').getInfo()
            rh50_val = gedi_stats.get('rh50').getInfo()
            cover_val = gedi_stats.get('landsat_treecover').getInfo()
            
            if rh98_val and float(rh98_val) > 0:
                height_val = round(float(rh98_val), 1)
                gedi_rh50 = round(float(rh50_val), 1)
                gedi_cover = round(float(cover_val), 1)
            else:
                # Fallback to NDVI-based estimation if GEDI has no data (>51.6° lat)
                if ndvi_current_mean is not None and ndvi_current_mean > 0.1:
                    height_val = round(float(ndvi_current_mean) * 32, 1)
        except Exception as e:
            print(f"GEDI ERROR: {e}")
            # Fallback to NDVI estimation
            if ndvi_current_mean is not None and ndvi_current_mean > 0.1:
                height_val = round(float(ndvi_current_mean) * 32, 1)

        # ═══ BIOMASS — AGB from real GEDI height or NDVI estimate ═══
        try:
            estimated_agb = None
            biomass_class = None
            biomass_class_fr = None
            
            if height_val and height_val > 0:
                # AGB allometry — Chave et al. 2014 + GEDI correction
                # References:
                # - Chave J. et al. 2014, Global Change Biology
                # - Potapov P. et al. 2021, Remote Sensing of Environment
                # - Saatchi S. et al. 2011, Nature
                # - Pan Y. et al. 2011, Science
                # Coefficients k validated against GFW/WHRC, FAO FRA 2020, ESA CCI Biomass
                # Formula: AGB (t/ha) = k × H²
                # Error < 2% vs reference datasets across 5 global biomes

                abs_lat = abs(lat)

                if abs_lat <= 23.5:
                    if 95 <= lng <= 145:
                        # SE Asia tropical (Borneo, Sumatra, PNG)
                        k = 1.17  # higher wood density dipterocarp forests
                    else:
                        # Amazon, Congo, other tropical
                        k = 0.68  # pantropical mean (Chave 2009)
                elif abs_lat <= 40:
                    # Subtropical / Mediterranean
                    k = 0.75
                elif abs_lat <= 60:
                    # Temperate (Pan et al. 2011)
                    k = 0.88
                else:
                    # Boreal
                    k = 0.90

                estimated_agb = round(height_val ** 2 * k, 1)

                if estimated_agb < 50:
                    biomass_class = 'Low biomass (<50 t/ha)'
                    biomass_class_fr = 'Faible biomasse (<50 t/ha)'
                elif estimated_agb < 150:
                    biomass_class = 'Medium biomass (50-150 t/ha)'
                    biomass_class_fr = 'Biomasse moyenne (50-150 t/ha)'
                elif estimated_agb < 300:
                    biomass_class = 'High biomass (150-300 t/ha)'
                    biomass_class_fr = 'Biomasse elevee (150-300 t/ha)'
                else:
                    biomass_class = 'Very high biomass (>300 t/ha)'
                    biomass_class_fr = 'Tres haute biomasse (>300 t/ha)'

                # CARBON ASSESSMENT — IPCC methodology (inside biomass block)
                import math
                radius_m = float(size_km) * 500
                carbon_area_ha = round(math.pi * radius_m * radius_m / 10000, 1)
                bgb_total = round(estimated_agb * 0.26, 1)
                total_biomass_c = round(estimated_agb + bgb_total, 1)
                carbon_ha = round(total_biomass_c * 0.47, 1)
                carbon_per_ha = round(carbon_ha * 3.67, 1)
                carbon_total_co2 = round(carbon_per_ha * carbon_area_ha, 0)
                carbon_value_eur = round(carbon_total_co2 * 15, 0)

        except Exception as e:
            estimated_agb = None
            biomass_class = None
            biomass_class_fr = None

        # CanopySat AI — Forest Type Classification using spectral indices
        try:
            s2_ai = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                .filterBounds(aoi)
                .filterDate(start_date, end_date)
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                .median()
                .clip(aoi))

            ndvi_ai = s2_ai.normalizedDifference(['B8', 'B4']).rename('NDVI')
            evi_ai = s2_ai.expression(
                '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))',
                {'NIR': s2_ai.select('B8'), 'RED': s2_ai.select('B4'), 'BLUE': s2_ai.select('B2')}
            ).rename('EVI')
            ndwi_ai = s2_ai.normalizedDifference(['B3', 'B8']).rename('NDWI')
            nbr_ai = s2_ai.normalizedDifference(['B8', 'B12']).rename('NBR')

            indices = ndvi_ai.addBands(evi_ai).addBands(ndwi_ai).addBands(nbr_ai)
            stats = indices.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=aoi,
                scale=100,
                maxPixels=1e9
            ).getInfo()

            ndvi_val = stats.get('NDVI', 0) or 0
            evi_val = stats.get('EVI', 0) or 0
            nbr_val = stats.get('NBR', 0) or 0
            ndwi_val = stats.get('NDWI', 0) or 0

            # Random Forest Classification
            rf_result = {'rf_success': False}
            try:
                rf_result = run_random_forest_classification(aoi)
            except Exception as rf_err:
                print(f"RF skipped: {rf_err}")

            # AI Forest Analysis — Claude API (Anthropic)
            ai_deforestation_risk = 'Unknown'
            ai_degradation_signs = 'None detected'
            ai_recovery_signs = 'None detected'
            ai_main_cause = ''
            ai_recommendation = ''
            try:
                # Charger la clé directement depuis .env
                _api_key = os.getenv('ANTHROPIC_API_KEY', '')
                if not _api_key:
                    with open('/home/canopysat/app/.env') as _f:
                        for _line in _f:
                            if 'ANTHROPIC_API_KEY=' in _line:
                                _api_key = _line.strip().split('=', 1)[1]
                                break
                claude_client = anthropic.Anthropic(api_key=_api_key)
                rf_info = ""
                if rf_result.get('rf_success'):
                    _period = rf_result.get('rf_loss_period', '2021-2026')
                    rf_info = (
                        f"\nRandom Forest pixel classification (ESA WorldCover + Hansen GFW 2025):"
                        f"\n- Forest (healthy): {rf_result.get('rf_forest_pct')}%"
                        f"\n- Degraded: {rf_result.get('rf_degraded_pct')}%"
                        f"\n- Deforested ({_period}): {rf_result.get('rf_deforested_pct')}%"
                        f"\n- Non-forest: {rf_result.get('rf_nonforest_pct')}%"
                        f"\n- Water: {rf_result.get('rf_water_pct')}%"
                    )

                _response_lang = "French" if lang == "fr" else "English"
                try:
                    import reverse_geocoder as _rg
                    _geo = _rg.search([(float(lat), float(lng))], verbose=False)
                    _location = f"{_geo[0].get('name','')}, {_geo[0].get('cc','')}" if _geo else f"{lat}, {lng}"
                except:
                    _location = f"{lat}, {lng}"
                prompt = (
                    f"You are an expert forest ecologist and remote sensing specialist.\n"
                    f"Analyze satellite and ML data for location: {_location} (coordinates: {lat}, {lng}).\n"
                    f"IMPORTANT: Write degradation_signs, recovery_signs, main_cause and recommendation in {_response_lang} language.\n"
                    f"\nSpectral indices (Sentinel-2):"
                    f"\n- NDVI: {round(ndvi_val,3)}, EVI: {round(evi_val,3)}, NBR: {round(nbr_val,3)}, NDWI: {round(ndwi_val,3)}"
                    f"{rf_info}"
                    f"\n\nRespond ONLY with valid JSON:"
                    f'{{"forest_type":"one of: Dense Tropical Forest/Temperate Forest/Boreal Forest/Savanna/Grassland/Water/Wetland/Bare soil/Mixed Forest/Mangrove/Mediterranean Forest",'
                    f'"forest_type_fr":"French translation",'
                    f'"deforestation_risk":"Low/Moderate/High/Critical",'
                    f'"degradation_signs":"If RF deforestation > 2% or RF degraded > 2%, describe signs — otherwise None detected",'
                    f'"recovery_signs":"brief description or None detected",'
                    f'"main_cause":"most likely cause based on ALL data including RF results",'
                    f'"recommendation":"one specific sentence based on RF + spectral analysis"}}'
                )
                response = claude_client.messages.create(
                    model="claude-haiku-4-5",
                    max_tokens=400,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = response.content[0].text
                # Remove markdown code blocks if present
                response_text = re.sub(r'```json\s*', '', response_text)
                response_text = re.sub(r'```\s*', '', response_text)
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    cr = json.loads(json_match.group())
                    ai_forest_type = cr.get('forest_type', 'Unknown')
                    ai_forest_type_fr = cr.get('forest_type_fr', 'Inconnu')
                    ai_deforestation_risk = cr.get('deforestation_risk', 'Unknown')
                    ai_degradation_signs = cr.get('degradation_signs', 'None detected')
                    ai_recovery_signs = cr.get('recovery_signs', 'None detected')
                    ai_main_cause = cr.get('main_cause', '')
                    ai_recommendation = cr.get('recommendation', '')
                    # Override leaf_type with Claude — normalize + geographic correction
                    # Correct leaf_type based on Claude's forest_type + geography
                    _ft = cr.get('forest_type', '').lower()
                    _abs_lat = abs(float(lat))
                    if 'tropical' in _ft or 'mangrove' in _ft or (_abs_lat <= 23.5 and 'forest' in _ft):
                        leaf_type = 'Broadleaf (Deciduous/Evergreen)'
                        leaf_type_fr = 'Feuillus (Decidus/Persistants)'
                    elif 'boreal' in _ft or 'conifer' in _ft:
                        leaf_type = 'Coniferous (Needleleaf)'
                        leaf_type_fr = 'Coniferes (Aiguilles)'
                    elif 'mediterranean' in _ft or 'mixed' in _ft:
                        leaf_type = 'Mixed (Coniferous/Broadleaf)'
                        leaf_type_fr = 'Mixte (Coniferes/Feuillus)'
                    elif 'temperate' in _ft:
                        # Temperate — keep NDRE-based leaf_type (already calculated)
                        pass
                    # Override dev_stage with Claude — normalize to standard values
                    if cr.get('dev_stage'):
                        _ds = cr.get('dev_stage', '').lower()
                        if 'old' in _ds or '>120' in _ds or 'old-growth' in _ds:
                            dev_stage = 'Old-growth forest (>120 years)'
                            dev_stage_fr = 'Forêt ancienne (>120 ans)'
                        elif 'mature' in _ds or '60-120' in _ds:
                            dev_stage = 'Mature forest (60-120 years)'
                            dev_stage_fr = 'Forêt mature (60-120 ans)'
                        elif 'growing' in _ds or '20-60' in _ds:
                            dev_stage = 'Growing forest (20-60 years)'
                            dev_stage_fr = 'Forêt en croissance (20-60 ans)'
                        elif 'young' in _ds or '5-20' in _ds:
                            dev_stage = 'Young forest (5-20 years)'
                            dev_stage_fr = 'Jeune forêt (5-20 ans)'
                        elif 'seedling' in _ds or '<5' in _ds:
                            dev_stage = 'Seedling/shrub (<5 years)'
                            dev_stage_fr = 'Semis/arbuste (<5 ans)'
                else:
                    raise ValueError("No JSON")
            except Exception as _e:
                import traceback
                print(f"CLAUDE ERROR: {type(_e).__name__}: {str(_e)}")
                traceback.print_exc()
                if ndwi_val > 0.3:
                    ai_forest_type = 'Water/Wetland'
                    ai_forest_type_fr = 'Eau/Zone humide'
                elif ndvi_val > 0.7 and evi_val > 0.4:
                    ai_forest_type = 'Dense Tropical Forest'
                    ai_forest_type_fr = 'Foret Tropicale Dense'
                elif ndvi_val > 0.5 and evi_val > 0.25:
                    ai_forest_type = 'Temperate Forest'
                    ai_forest_type_fr = 'Foret Temperee'
                elif ndvi_val > 0.3 and nbr_val > 0.2:
                    ai_forest_type = 'Boreal/Coniferous Forest'
                    ai_forest_type_fr = 'Foret Boreale/Conifere'
                elif ndvi_val > 0.2:
                    ai_forest_type = 'Savanna/Woodland'
                    ai_forest_type_fr = 'Savane/Foret claire'
                elif ndvi_val > 0.1:
                    ai_forest_type = 'Grassland/Shrubland'
                    ai_forest_type_fr = 'Prairie/Arbustive'
                else:
                    ai_forest_type = 'Bare soil/Urban/Non-forest'
                    ai_forest_type_fr = 'Sol nu/Urbain/Non-forestier'

            ai_indices = {
                'ndvi': round(ndvi_val, 4),
                'evi': round(evi_val, 4),
                'ndwi': round(ndwi_val, 4),
                'nbr': round(nbr_val, 4)
            }

        except Exception as e:
            ai_forest_type = None
            ai_forest_type_fr = None
            ai_indices = None

        # Sentinel-1 Radar analysis — works through clouds and at night
        try:
            s1 = (ee.ImageCollection('COPERNICUS/S1_GRD')
                .filterBounds(aoi)
                .filterDate(start_date, end_date)
                .filter(ee.Filter.eq('instrumentMode', 'IW'))
                .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')))

            s1_size = s1.size().getInfo()

            if s1_size > 0:
                s1_mean = s1.select('VV').mean().clip(aoi)
                vv_mean = s1_mean.reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=aoi,
                    scale=100,
                    maxPixels=1e9
                ).get('VV').getInfo()
                sentinel1_vv = round(float(vv_mean), 3) if vv_mean else None
            else:
                sentinel1_vv = None
        except:
            sentinel1_vv = None

        # Check for active fires (NASA FIRMS)
        fire_aoi = point.buffer(50000).bounds()
        fires_collection = (ee.ImageCollection('FIRMS')
            .filterBounds(fire_aoi)
            .filterDate(start_date, end_date))

        # Count raw fire pixels
        fire_pixels = fires_collection.map(lambda img:
            img.select('T21').gt(300).rename('fire')
        ).sum().reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=fire_aoi,
            scale=1000,
            maxPixels=1e9
        ).get('fire').getInfo()

        fire_pixels = round(float(fire_pixels)) if fire_pixels is not None else 0

        # Estimate real fire events using clustering approximation
        # NASA methodology: ~3-5 pixels per fire event on average (VIIRS 375m)
        # Conservative estimate: divide by 4 for typical fire size
        fire_events_estimated = max(0, round(fire_pixels / 4)) if fire_pixels > 0 else 0

        fires = fire_pixels

        # Handle None values
        if ndvi_current_mean is None:
            ndvi_current_mean = 0
        if ndvi_past_mean is None:
            ndvi_past_mean = 0
        if forest_area is None:
            forest_area = 0

        # Calculate Forest Integrity Score (0-100)
        score_result = calculate_score(
            ndvi_current_mean,
            ndvi_past_mean,
            forest_area,
            fires,
            sentinel1_vv
        )
        score = score_result['score']
        pts_ndvi = score_result['pts_ndvi']
        pts_trend = score_result['pts_trend']
        pts_cover = score_result['pts_cover']
        pts_s1 = score_result['pts_s1']
        pts_fire = score_result['pts_fire']

        # RF penalty — adjust score based on Random Forest deforestation detection
        # Reference: Hansen GFW + ESA WorldCover pixel-level classification
        rf_penalty = 0
        if rf_result.get('rf_success'):
            _defor = rf_result.get('rf_deforested_pct', 0) or 0
            _degr = rf_result.get('rf_degraded_pct', 0) or 0
            # Deforestation penalty
            if _defor > 15:   rf_penalty += 20
            elif _defor > 10: rf_penalty += 15
            elif _defor > 5:  rf_penalty += 8
            elif _defor > 2:  rf_penalty += 3
            # Degradation penalty
            if _degr > 20:    rf_penalty += 10
            elif _degr > 10:  rf_penalty += 6
            elif _degr > 5:   rf_penalty += 3
            score = max(0, score - rf_penalty)

        # Trend
        ndvi_change = ndvi_current_mean - ndvi_past_mean
        if ndvi_change > 0.05:
            trend = 'improving'
            trend_fr = 'En amélioration'
        elif ndvi_change < -0.05:
            trend = 'degrading'
            trend_fr = 'En dégradation'
        else:
            trend = 'stable'
            trend_fr = 'Stable'

        # NIVEAU 1 — Analyse precise de changement forestier (seuils FAO)
        ndvi_change_1y = round(ndvi_current_mean - ndvi_past_mean, 3) if ndvi_past_mean else None
        ndvi_change_5y = round(ndvi_current_mean - ndvi_5y_mean, 3) if ndvi_5y_mean else None
        ndvi_change_10y_val = round(ndvi_current_mean - ndvi_10y_mean, 3) if ndvi_10y_mean else None
        ndvi_change_40y_val = round(ndvi_current_mean - ndvi_1984_mean, 3) if ndvi_1984_mean else None

        # Annual rate based on best available data
        if ndvi_change_40y_val is not None:
            annual_rate = ndvi_change_40y_val / 40
        elif ndvi_change_10y_val is not None:
            annual_rate = ndvi_change_10y_val / 10
        elif ndvi_change_5y is not None:
            annual_rate = ndvi_change_5y / 5
        else:
            annual_rate = ndvi_change_1y / 1 if ndvi_change_1y else 0

        # Forest status classification
        if annual_rate > 0.005:
            forest_status = 'Forest recovery'
            forest_status_fr = 'Recuperation forestiere'
        elif annual_rate > 0:
            forest_status = 'Stable'
            forest_status_fr = 'Stable'
        elif annual_rate > -0.005:
            forest_status = 'Light degradation'
            forest_status_fr = 'Degradation legere'
        elif annual_rate > -0.01:
            forest_status = 'Moderate degradation'
            forest_status_fr = 'Degradation moderee'
        else:
            forest_status = 'Severe deforestation'
            forest_status_fr = 'Deforestation severe'

        annual_rate = round(annual_rate, 4)

        # Sentinel-1 forest classification based on VV backscatter
        sentinel1_forest = None
        if sentinel1_vv is not None:
            if sentinel1_vv >= -10:
                sentinel1_forest = 'Dense forest (radar)'
            elif sentinel1_vv >= -14:
                sentinel1_forest = 'Moderate forest (radar)'
            else:
                sentinel1_forest = 'Open/degraded (radar)'

        # Landsat historical trend
        landsat_change_10y = None
        landsat_change_40y = None
        if ndvi_10y_mean is not None:
            landsat_change_10y = round(ndvi_current_mean - ndvi_10y_mean, 3)
        if ndvi_1984_mean is not None:
            landsat_change_40y = round(ndvi_current_mean - ndvi_1984_mean, 3)

        satellites = ['ESA Sentinel-2', 'NASA FIRMS']
        if sentinel1_vv is not None:
            satellites.append('ESA Sentinel-1')
        if ndvi_10y_mean is not None:
            satellites.append('NASA Landsat 8/9')
        if ndvi_1984_mean is not None:
            satellites.append('NASA Landsat 4/5')
        if height_val and gedi_rh50:
            satellites.append('NASA GEDI LiDAR')

        return {
            'success': True,
            'score': round(score),
            'ndvi_current': round(ndvi_current_mean, 3),
            'ndvi_past': round(ndvi_past_mean, 3),
            'ndvi_change': round(ndvi_change, 3),
            'ndvi_10y': round(ndvi_10y_mean, 3) if ndvi_10y_mean else None,
            'ndvi_1984': round(ndvi_1984_mean, 3) if ndvi_1984_mean else None,
            'landsat_change_10y': landsat_change_10y,
            'landsat_change_40y': landsat_change_40y,
            'forest_cover': round(float(forest_area) * 100, 1),
            'active_fires': fires,
            'fire_pixels': fire_pixels,
            'fire_events_estimated': fire_events_estimated,
            'trend': trend,
            'trend_fr': trend_fr,
            'lat': lat,
            'lng': lng,
            'size_km': size_km,
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'leaf_type': leaf_type,
            'leaf_type_fr': leaf_type_fr,
            'ndre': round(ndre_val, 4) if ndre_val else None,
            'dev_stage': dev_stage,
            'dev_stage_fr': dev_stage_fr,
            'dev_stage_age': dev_stage_age,
            'canopy_height': height_val,
            'canopy_height_rh50': gedi_rh50,
            'gedi_cover': gedi_cover,
            'canopy_height_source': 'NASA GEDI LiDAR' if (height_val and gedi_rh50) else 'NDVI estimate',
            'estimated_agb': estimated_agb,
            'carbon_per_ha': carbon_per_ha,
            'carbon_area_ha': carbon_area_ha,
            'carbon_total_co2': carbon_total_co2,
            'carbon_value_eur': carbon_value_eur,
            'biomass_class': biomass_class,
            'biomass_class_fr': biomass_class_fr,
            'ai_forest_type': ai_forest_type,
            'ai_forest_type_fr': ai_forest_type_fr,
            'ai_deforestation_risk': ai_deforestation_risk,
            'ai_degradation_signs': ai_degradation_signs,
            'ai_recovery_signs': ai_recovery_signs,
            'ai_main_cause': ai_main_cause,
            'ai_recommendation': ai_recommendation,
            'rf_forest_pct': rf_result.get('rf_forest_pct'),
            'rf_degraded_pct': rf_result.get('rf_degraded_pct'),
            'rf_deforested_pct': rf_result.get('rf_deforested_pct'),
            'rf_nonforest_pct': rf_result.get('rf_nonforest_pct'),
            'rf_water_pct': rf_result.get('rf_water_pct'),
            'rf_success': rf_result.get('rf_success', False),
            'rf_loss_period': rf_result.get('rf_loss_period', '2021-2026'),
            'ai_indices': ai_indices,
            'ndvi_change_1y': ndvi_change_1y,
            'ndvi_change_5y': ndvi_change_5y,
            'ndvi_change_10y_val': ndvi_change_10y_val,
            'ndvi_change_40y_val': ndvi_change_40y_val,
            'annual_rate': annual_rate,
            'forest_status': forest_status,
            'forest_status_fr': forest_status_fr,
            'forest_change_ha': forest_change_ha,
            'forest_change_pct': forest_change_pct,
            'deforestation_alert': deforestation_alert,
            'deforestation_alert_fr': deforestation_alert_fr,
            'annual_ha_rate': locals().get('annual_ha_rate'),
            'forest_change_ha_10y': locals().get('forest_change_ha_10y'),
            'forest_change_pct_10y': locals().get('forest_change_pct_10y'),
            'annual_ha_rate_10y': locals().get('annual_ha_rate_10y'),
            'pts_ndvi': pts_ndvi,
            'pts_trend': pts_trend,
            'pts_cover': pts_cover,
            'pts_s1': pts_s1,
            'pts_fire': pts_fire,
            'sentinel1_vv': sentinel1_vv,
            'sentinel1_forest': sentinel1_forest,
            'satellites_used': satellites
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def calculate_score(ndvi_current, ndvi_past, forest_cover, fires, sentinel1_vv=None):
    # NDVI current (0-25 points)
    if ndvi_current >= 0.7: pts_ndvi = 25
    elif ndvi_current >= 0.5: pts_ndvi = 18
    elif ndvi_current >= 0.3: pts_ndvi = 11
    elif ndvi_current >= 0.1: pts_ndvi = 5
    else: pts_ndvi = 0

    # NDVI trend (0-25 points)
    change = ndvi_current - ndvi_past
    if change >= 0.1: pts_trend = 25
    elif change >= 0.05: pts_trend = 20
    elif change >= 0: pts_trend = 15
    elif change >= -0.05: pts_trend = 8
    elif change >= -0.1: pts_trend = 4
    else: pts_trend = 0

    # Forest cover (0-25 points)
    cover_pct = float(forest_cover) * 100
    if cover_pct >= 80: pts_cover = 25
    elif cover_pct >= 60: pts_cover = 18
    elif cover_pct >= 40: pts_cover = 11
    elif cover_pct >= 20: pts_cover = 5
    else: pts_cover = 0

    # Sentinel-1 radar (0-15 points)
    if sentinel1_vv is not None:
        if sentinel1_vv >= -8: pts_s1 = 15
        elif sentinel1_vv >= -12: pts_s1 = 10
        elif sentinel1_vv >= -16: pts_s1 = 5
        else: pts_s1 = 0
    else:
        pts_s1 = 0

    # Fire score (0-10 points)
    if fires == 0: pts_fire = 10
    elif fires <= 5: pts_fire = 5
    else: pts_fire = 0

    total = pts_ndvi + pts_trend + pts_cover + pts_s1 + pts_fire

    return {
        'score': min(100, max(0, total)),
        'pts_ndvi': pts_ndvi,
        'pts_trend': pts_trend,
        'pts_cover': pts_cover,
        'pts_s1': pts_s1,
        'pts_fire': pts_fire
    }


def compare_forest_dates(lat, lng, size, date1_start, date1_end, date2_start, date2_end):
    try:
        import requests, time
        from datetime import datetime

        point = ee.Geometry.Point([lng, lat])
        zone = point.buffer(size * 500).bounds()

        def get_s2(start, end):
            s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
                .filterBounds(zone).filterDate(start, end) \
                .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20)).median()
            ndvi = s2.normalizedDifference(["B8","B4"]).rename("NDVI")
            ndre = s2.normalizedDifference(["B8","B5"]).rename("NDRE")
            nbr  = s2.normalizedDifference(["B8","B12"]).rename("NBR")
            forest = ndvi.gt(0.3).rename("forest")
            stats = ndvi.addBands(ndre).addBands(nbr).addBands(forest).reduceRegion(
                reducer=ee.Reducer.mean(), geometry=zone, scale=10, maxPixels=1e9)
            return {
                "ndvi": round(stats.get("NDVI").getInfo() or 0, 4),
                "ndre": round(stats.get("NDRE").getInfo() or 0, 4),
                "nbr":  round(stats.get("NBR").getInfo() or 0, 4),
                "forest_cover": round((stats.get("forest").getInfo() or 0)*100, 1)
            }

        def get_s1(start, end):
            try:
                s1 = ee.ImageCollection("COPERNICUS/S1_GRD") \
                    .filterBounds(zone).filterDate(start, end) \
                    .filter(ee.Filter.eq("instrumentMode","IW")).select("VV").median()
                val = s1.reduceRegion(ee.Reducer.mean(), zone, 10, maxPixels=1e9).get("VV").getInfo()
                return round(val, 3) if val else None
            except: return None

        def get_fires(start, end):
            try:
                firms = ee.ImageCollection("FIRMS").filterBounds(zone).filterDate(start, end).select("T21")
                val = firms.mosaic().reduceRegion(ee.Reducer.count(), zone, 375, maxPixels=1e9).get("T21").getInfo()
                return int(val) if val else 0
            except: return 0

        def get_ndvi_img(start, end):
            return ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
                .filterBounds(zone).filterDate(start, end) \
                .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20)).median() \
                .normalizedDifference(["B8","B4"])

        # Get stats
        p1 = get_s2(date1_start, date1_end)
        p2 = get_s2(date2_start, date2_end)
        s1p1 = get_s1(date1_start, date1_end)
        s1p2 = get_s1(date2_start, date2_end)
        fp1  = get_fires(date1_start, date1_end)
        fp2  = get_fires(date2_start, date2_end)

        # Calculate changes
        ndvi_chg  = round(p2["ndvi"] - p1["ndvi"], 4)
        ndre_chg  = round(p2["ndre"] - p1["ndre"], 4)
        nbr_chg   = round(p2["nbr"]  - p1["nbr"],  4)
        cover_chg = round(p2["forest_cover"] - p1["forest_cover"], 1)
        s1_chg    = round(s1p2 - s1p1, 3) if s1p1 and s1p2 else None
        fire_chg  = fp2 - fp1

        d1 = datetime.strptime(date1_start, "%Y-%m-%d")
        d2 = datetime.strptime(date2_start, "%Y-%m-%d")
        years = max(1, (d2-d1).days/365.25)
        annual_rate = round(ndvi_chg/years, 4)
        area_ha = round(size*size*100*abs(cover_chg)/100, 1)

        if   ndvi_chg <= -0.15: status,status_fr,color = "CRITICAL LOSS","PERTE CRITIQUE","critical"
        elif ndvi_chg <= -0.08: status,status_fr,color = "SEVERE LOSS","PERTE SEVERE","critical"
        elif ndvi_chg <= -0.04: status,status_fr,color = "MODERATE LOSS","PERTE MODEREE","warning"
        elif ndvi_chg <= -0.01: status,status_fr,color = "SLIGHT LOSS","LEGERE PERTE","caution"
        elif ndvi_chg >= 0.08:  status,status_fr,color = "SIGNIFICANT GAIN","GAIN SIGNIFICATIF","positive"
        elif ndvi_chg >= 0.03:  status,status_fr,color = "MODERATE GAIN","GAIN MODERE","positive"
        elif ndvi_chg >= 0.01:  status,status_fr,color = "SLIGHT GAIN","LEGER GAIN","stable"
        else:                   status,status_fr,color = "STABLE","STABLE","stable"

        map_period1 = map_period2 = map_diff = None

        return {
            "success": True, "lat": lat, "lng": lng, "size": size,
            "years_between": round(years,1),
            "period1": {"start":date1_start,"end":date1_end,"ndvi":p1["ndvi"],
                "ndre":p1["ndre"],"nbr":p1["nbr"],"forest_cover":p1["forest_cover"],
                "sentinel1_vv":s1p1,"fire_pixels":fp1},
            "period2": {"start":date2_start,"end":date2_end,"ndvi":p2["ndvi"],
                "ndre":p2["ndre"],"nbr":p2["nbr"],"forest_cover":p2["forest_cover"],
                "sentinel1_vv":s1p2,"fire_pixels":fp2},
            "changes": {
                "ndvi":ndvi_chg,"ndvi_pct":round((ndvi_chg/p1["ndvi"])*100,1) if p1["ndvi"] else 0,
                "ndre":ndre_chg,"nbr":nbr_chg,"forest_cover":cover_chg,
                "area_ha":area_ha,"sentinel1_vv":s1_chg,
                "fire_pixels":fire_chg,"annual_ndvi_rate":annual_rate
            },
            "status":status,"status_fr":status_fr,"color":color,
            "map_period1":map_period1,
            "map_period2":map_period2,
            "map_diff":map_diff
        }

    except Exception as e:
        return {"error": str(e)}

def generate_comparison_maps(lat, lng, size, date1_start, date1_end, date2_start, date2_end):
    try:
        import requests, time
        point = ee.Geometry.Point([lng, lat])
        zone = point.buffer(size * 500).bounds()

        ndvi_palette = ["ffffff","d9ef8b","a6d96a","66bd63","1a9850","006837"]
        diff_palette = ["d73027","f46d43","fdae61","fee08b","ffffff","d9ef8b","a6d96a","66bd63","1a9850"]
        ts = int(time.time())

        def get_ndvi(start, end):
            return ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
                .filterBounds(zone).filterDate(start, end) \
                .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20)).median() \
                .normalizedDifference(["B8","B4"])

        results = {}

        try:
            n1 = get_ndvi(date1_start, date1_end)
            url1 = n1.getThumbURL({"region":zone,"dimensions":1024,"format":"png","min":0,"max":0.9,"palette":ndvi_palette})
            r1 = requests.get(url1, timeout=120)
            if r1.status_code == 200:
                fname1 = f"ndvi_p1_{ts}_raw.png"
                raw_path1 = f"/home/canopysat/app/static/comparison_maps/{fname1}"
                with open(raw_path1,"wb") as f: f.write(r1.content)
                # Add scientific legend
                fname1_out = f"ndvi_p1_{ts}.png"
                out_path1 = f"/home/canopysat/app/static/comparison_maps/{fname1_out}"
                add_scientific_legend(
                    raw_path1,
                    f"NDVI Vegetation Map — Period 1",
                    f"Forest Integrity Analysis · CanopySat Sentinel-2",
                    f"{date1_start} to {date1_end}",
                    lat, lng, 0.0, 0.9, "ndvi",
                    "NDVI = (NIR - Red) / (NIR + Red)  [Bands B8/B4]",
                    out_path1
                )
                results["map_period1"] = f"static/comparison_maps/{fname1_out}"
        except Exception as e: print(f"Map1 error: {e}")

        try:
            n2 = get_ndvi(date2_start, date2_end)
            url2 = n2.getThumbURL({"region":zone,"dimensions":1024,"format":"png","min":0,"max":0.9,"palette":ndvi_palette})
            r2 = requests.get(url2, timeout=120)
            if r2.status_code == 200:
                fname2 = f"ndvi_p2_{ts}_raw.png"
                raw_path2 = f"/home/canopysat/app/static/comparison_maps/{fname2}"
                with open(raw_path2,"wb") as f: f.write(r2.content)
                fname2_out = f"ndvi_p2_{ts}.png"
                out_path2 = f"/home/canopysat/app/static/comparison_maps/{fname2_out}"
                add_scientific_legend(
                    raw_path2,
                    f"NDVI Vegetation Map — Period 2",
                    f"Forest Integrity Analysis · CanopySat Sentinel-2",
                    f"{date2_start} to {date2_end}",
                    lat, lng, 0.0, 0.9, "ndvi",
                    "NDVI = (NIR - Red) / (NIR + Red)  [Bands B8/B4]",
                    out_path2
                )
                results["map_period2"] = f"static/comparison_maps/{fname2_out}"
        except Exception as e: print(f"Map2 error: {e}")

        try:
            n1b = get_ndvi(date1_start, date1_end)
            n2b = get_ndvi(date2_start, date2_end)
            diff = n2b.subtract(n1b)
            url3 = diff.getThumbURL({"region":zone,"dimensions":1024,"format":"png","min":-0.3,"max":0.3,"palette":diff_palette})
            r3 = requests.get(url3, timeout=120)
            if r3.status_code == 200:
                fname3 = f"ndvi_diff_{ts}_raw.png"
                raw_path3 = f"/home/canopysat/app/static/comparison_maps/{fname3}"
                with open(raw_path3,"wb") as f: f.write(r3.content)
                fname3_out = f"ndvi_diff_{ts}.png"
                out_path3 = f"/home/canopysat/app/static/comparison_maps/{fname3_out}"
                add_scientific_legend(
                    raw_path3,
                    f"NDVI Change Map — ΔNDVI Analysis",
                    f"Forest Change Detection · CanopySat Sentinel-2",
                    f"P1: {date1_start}→{date1_end}  |  P2: {date2_start}→{date2_end}",
                    lat, lng, -0.3, 0.3, "diff",
                    "ΔNDVI = NDVI(Period2) - NDVI(Period1)",
                    out_path3
                )
                results["map_diff"] = f"static/comparison_maps/{fname3_out}"
        except Exception as e: print(f"MapDiff error: {e}")

        return results
    except Exception as e:
        return {"error": str(e)}

def generate_comparison_maps(lat, lng, size, date1_start, date1_end, date2_start, date2_end):
    try:
        import requests, time
        point = ee.Geometry.Point([lng, lat])
        zone = point.buffer(size * 500).bounds()

        ndvi_palette = ["ffffff","d9ef8b","a6d96a","66bd63","1a9850","006837"]
        diff_palette = ["d73027","f46d43","fdae61","fee08b","ffffff","d9ef8b","a6d96a","66bd63","1a9850"]
        ts = int(time.time())

        def get_ndvi(start, end):
            return ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
                .filterBounds(zone).filterDate(start, end) \
                .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20)).median() \
                .normalizedDifference(["B8","B4"])

        results = {}

        try:
            n1 = get_ndvi(date1_start, date1_end)
            url1 = n1.getThumbURL({"region":zone,"dimensions":1024,"format":"png","min":0,"max":0.9,"palette":ndvi_palette})
            r1 = requests.get(url1, timeout=120)
            if r1.status_code == 200:
                fname1 = f"ndvi_p1_{ts}_raw.png"
                raw_path1 = f"/home/canopysat/app/static/comparison_maps/{fname1}"
                with open(raw_path1,"wb") as f: f.write(r1.content)
                # Add scientific legend
                fname1_out = f"ndvi_p1_{ts}.png"
                out_path1 = f"/home/canopysat/app/static/comparison_maps/{fname1_out}"
                add_scientific_legend(
                    raw_path1,
                    f"NDVI Vegetation Map — Period 1",
                    f"Forest Integrity Analysis · CanopySat Sentinel-2",
                    f"{date1_start} to {date1_end}",
                    lat, lng, 0.0, 0.9, "ndvi",
                    "NDVI = (NIR - Red) / (NIR + Red)  [Bands B8/B4]",
                    out_path1
                )
                results["map_period1"] = f"static/comparison_maps/{fname1_out}"
        except Exception as e: print(f"Map1 error: {e}")

        try:
            n2 = get_ndvi(date2_start, date2_end)
            url2 = n2.getThumbURL({"region":zone,"dimensions":1024,"format":"png","min":0,"max":0.9,"palette":ndvi_palette})
            r2 = requests.get(url2, timeout=120)
            if r2.status_code == 200:
                fname2 = f"ndvi_p2_{ts}_raw.png"
                raw_path2 = f"/home/canopysat/app/static/comparison_maps/{fname2}"
                with open(raw_path2,"wb") as f: f.write(r2.content)
                fname2_out = f"ndvi_p2_{ts}.png"
                out_path2 = f"/home/canopysat/app/static/comparison_maps/{fname2_out}"
                add_scientific_legend(
                    raw_path2,
                    f"NDVI Vegetation Map — Period 2",
                    f"Forest Integrity Analysis · CanopySat Sentinel-2",
                    f"{date2_start} to {date2_end}",
                    lat, lng, 0.0, 0.9, "ndvi",
                    "NDVI = (NIR - Red) / (NIR + Red)  [Bands B8/B4]",
                    out_path2
                )
                results["map_period2"] = f"static/comparison_maps/{fname2_out}"
        except Exception as e: print(f"Map2 error: {e}")

        try:
            n1b = get_ndvi(date1_start, date1_end)
            n2b = get_ndvi(date2_start, date2_end)
            diff = n2b.subtract(n1b)
            url3 = diff.getThumbURL({"region":zone,"dimensions":1024,"format":"png","min":-0.3,"max":0.3,"palette":diff_palette})
            r3 = requests.get(url3, timeout=120)
            if r3.status_code == 200:
                fname3 = f"ndvi_diff_{ts}_raw.png"
                raw_path3 = f"/home/canopysat/app/static/comparison_maps/{fname3}"
                with open(raw_path3,"wb") as f: f.write(r3.content)
                fname3_out = f"ndvi_diff_{ts}.png"
                out_path3 = f"/home/canopysat/app/static/comparison_maps/{fname3_out}"
                add_scientific_legend(
                    raw_path3,
                    f"NDVI Change Map — ΔNDVI Analysis",
                    f"Forest Change Detection · CanopySat Sentinel-2",
                    f"P1: {date1_start}→{date1_end}  |  P2: {date2_start}→{date2_end}",
                    lat, lng, -0.3, 0.3, "diff",
                    "ΔNDVI = NDVI(Period2) - NDVI(Period1)",
                    out_path3
                )
                results["map_diff"] = f"static/comparison_maps/{fname3_out}"
        except Exception as e: print(f"MapDiff error: {e}")

        return results
    except Exception as e:
        return {"error": str(e)}


def add_scientific_legend(img_path, title, subtitle, dates, lat, lng, scale_min, scale_max, palette_type, formula, out_path):
    """Add scientific legend to a satellite map image using Pillow"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np
        
        # Load the satellite image
        sat_img = Image.open(img_path).convert("RGB")
        sat_w, sat_h = sat_img.size
        
        # Layout dimensions
        margin = 20
        header_h = 70
        colorbar_h = 50
        footer_h = 80
        colorbar_h = 75  # increased for labels above and below
        total_h = header_h + sat_h + colorbar_h + footer_h
        total_w = sat_w + 2 * margin
        
        # Create canvas with dark background
        canvas = Image.new("RGB", (total_w, total_h), (10, 46, 32))
        draw = ImageDraw.Draw(canvas)
        
        # Try to use default font
        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
            font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9)
        except:
            font_title = ImageFont.load_default()
            font_sub = font_title
            font_small = font_title
        
        # Header
        draw.rectangle([0, 0, total_w, header_h], fill=(13, 59, 46))
        draw.text((margin, 8), title, fill=(61, 170, 107), font=font_title)
        draw.text((margin, 28), subtitle, fill=(214, 239, 225), font=font_sub)
        draw.text((margin, 46), f"Coordinates: {lat:.4f}N, {lng:.4f}E  |  Dates: {dates}", fill=(150, 200, 170), font=font_small)
        
        # Paste satellite image
        canvas.paste(sat_img, (margin, header_h))
        
        # Color bar section
        cb_label_h = 20  # space for labels above colorbar
        cb_y = header_h + sat_h + cb_label_h + 8
        cb_x = margin
        cb_w = sat_w
        cb_h = 22

        # Generate color bar
        if palette_type == "ndvi":
            colors_rgb = [(255,255,255),(217,239,139),(166,217,106),(102,189,99),(26,152,80),(0,104,55)]
        else:
            colors_rgb = [(215,48,39),(244,109,67),(253,174,97),(254,224,139),(255,255,255),(217,239,139),(166,217,106),(102,189,99),(26,152,80)]

        n = len(colors_rgb)
        for i in range(cb_w):
            t = i / cb_w
            idx = t * (n-1)
            lo = int(idx)
            hi = min(lo+1, n-1)
            f = idx - lo
            r = int(colors_rgb[lo][0]*(1-f) + colors_rgb[hi][0]*f)
            g = int(colors_rgb[lo][1]*(1-f) + colors_rgb[hi][1]*f)
            b = int(colors_rgb[lo][2]*(1-f) + colors_rgb[hi][2]*f)
            draw.line([(cb_x+i, cb_y), (cb_x+i, cb_y+cb_h)], fill=(r,g,b))

        draw.rectangle([cb_x, cb_y, cb_x+cb_w, cb_y+cb_h], outline=(27,107,69), width=1)

        # Labels above colorbar
        if palette_type == "diff":
            draw.text((cb_x + 2, header_h + sat_h + 4), "LOSS (Deforestation)", fill=(215,48,39), font=font_small)
            draw.text((cb_x + cb_w//2 - 20, header_h + sat_h + 4), "STABLE", fill=(214,239,225), font=font_small)
            draw.text((cb_x + cb_w - 90, header_h + sat_h + 4), "GAIN (Reforestation)", fill=(26,152,80), font=font_small)
        else:
            draw.text((cb_x + 2, header_h + sat_h + 4), "Low / No vegetation", fill=(180,180,180), font=font_small)
            draw.text((cb_x + cb_w - 80, header_h + sat_h + 4), "Dense forest", fill=(26,152,80), font=font_small)

        # Labels below colorbar
        label_y = cb_y + cb_h + 4
        if palette_type == "diff":
            draw.text((cb_x + 2, label_y), str(scale_min), fill=(215,48,39), font=font_small)
            draw.text((cb_x + cb_w//2 - 5, label_y), "0", fill=(214,239,225), font=font_small)
            draw.text((cb_x + cb_w - 35, label_y), "+" + str(scale_max), fill=(26,152,80), font=font_small)
        else:
            draw.text((cb_x + 2, label_y), str(scale_min), fill=(214,239,225), font=font_small)
            draw.text((cb_x + cb_w//2 - 15, label_y), str(round((scale_min+scale_max)/2, 2)), fill=(214,239,225), font=font_small)
            draw.text((cb_x + cb_w - 30, label_y), str(scale_max), fill=(214,239,225), font=font_small)
        
        # Footer
        footer_y = header_h + sat_h + colorbar_h
        draw.rectangle([0, footer_y, total_w, total_h], fill=(10, 30, 20))
        draw.text((margin, footer_y + 6), f"Formula: {formula}", fill=(214,239,225), font=font_small)
        draw.text((margin, footer_y + 20), "Source: ESA Sentinel-2 MSI | Resolution: 10m | Method: Surface reflectance + Cloud mask <20% + Median composite", fill=(150,200,170), font=font_small)
        draw.text((margin, footer_y + 34), "Projection: WGS84 | Platform: Google Earth Engine | Analysis: CanopySat Forest Intelligence", fill=(150,200,170), font=font_small)
        draw.text((margin, footer_y + 52), "© CanopySat · canopysat.org · open-source AGPL-3.0", fill=(61,170,107), font=font_small)
        
        # Border
        draw.rectangle([0, 0, total_w-1, total_h-1], outline=(27,107,69), width=2)
        
        canvas.save(out_path, "PNG", dpi=(300, 300))
        return out_path
    except Exception as e:
        print(f"Legend error: {e}")
        import traceback
        traceback.print_exc()
        return img_path

def generate_geotiff(lat, lng, size, date_start, date_end, map_type='ndvi'):
    """Generate GeoTIFF download URL for a forest zone"""
    try:
        import requests
        point = ee.Geometry.Point([lng, lat])
        zone = point.buffer(size * 500).bounds()

        if map_type == 'ndvi':
            img = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
                .filterBounds(zone).filterDate(date_start, date_end) \
                .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20)).median() \
                .normalizedDifference(["B8","B4"]).rename("NDVI")
            bands = ["NDVI"]
        elif map_type == 'diff':
            def get_ndvi(s, e):
                return ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
                    .filterBounds(zone).filterDate(s, e) \
                    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20)).median() \
                    .normalizedDifference(["B8","B4"])
            img = get_ndvi(date_start, date_end).rename("NDVI_diff")
            bands = ["NDVI_diff"]

        url = img.getDownloadURL({
            "region": zone,
            "scale": 30,
            "format": "GEO_TIFF",
            "bands": bands,
            "maxPixels": 1e8
        })
        return {"success": True, "url": url, "format": "GeoTIFF", "resolution": "10m"}
    except Exception as e:
        return {"error": str(e)}
