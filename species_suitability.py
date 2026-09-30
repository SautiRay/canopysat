import requests
import ee

EXCLUDED_FAMILIES = {
    'Teiidae','Accipitridae','Theraphosidae','Psittacidae','Bradypodidae',
    'Hylidae','Icteridae','Colubridae','Viperidae','Felidae','Cricetidae',
    'Didelphidae','Cebidae','Pitheciidae','Sciuridae','Emballonuridae',
    'Strigidae','Trochilidae','Thraupidae','Tyrannidae','Anatidae',
    'Bufonidae','Dendrobatidae','Ranidae','Gekkonidae','Muscicapidae',
    'Formicariidae','Furnariidae','Pipridae','Cotingidae','Momotidae'
}

def get_species_temp_range(species_name):
    """Calcule la plage de température réelle d'une espèce via GBIF"""
    try:
        url = "https://api.gbif.org/v1/occurrence/search"
        params = {
            'scientificName': species_name,
            'hasCoordinate': 'true',
            'hasGeospatialIssue': 'false',
            'limit': 100,
            'occurrenceStatus': 'PRESENT'
        }
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        lats = [occ.get('decimalLatitude') for occ in data.get('results', [])
                if occ.get('decimalLatitude')]
        if len(lats) < 5:
            return None
        temp_from_lat = lambda l: 27 - abs(l) * 0.52
        temps = [temp_from_lat(l) for l in lats]
        return {
            'temp_min': round(min(temps) - 2, 1),
            'temp_max': round(max(temps) + 2, 1),
            'temp_mean': round(sum(temps)/len(temps), 1),
            'n': len(lats)
        }
    except:
        return None

def analyze_species_suitability(lat, lng, size_km=10):
    """
    Analyse la suitabilité climatique des espèces forestières
    pour une zone GPS donnée — mondial
    """
    try:
        aoi = ee.Geometry.Point([lng, lat]).buffer(size_km * 500)
        radius_deg = max(0.5, size_km * 0.01)

        # 1. GBIF — espèces locales
        params = {
            'decimalLatitude': f'{lat-radius_deg},{lat+radius_deg}',
            'decimalLongitude': f'{lng-radius_deg},{lng+radius_deg}',
            'kingdomKey': '6',
            'limit': 100,
            'hasCoordinate': 'true',
            'hasGeospatialIssue': 'false',
        }
        r = requests.get("https://api.gbif.org/v1/occurrence/search",
                         params=params, timeout=15)
        data = r.json()

        species_list = {}
        for occ in data.get('results', []):
            sp = occ.get('species')
            fam = occ.get('family', '')
            if sp and fam and fam not in EXCLUDED_FAMILIES:
                species_list[sp] = fam

        if not species_list:
            return None

        # 2. Climat actuel WorldClim
        worldclim = ee.Image('WORLDCLIM/V1/BIO')
        current = worldclim.select(['bio01','bio12']).reduceRegion(
            reducer=ee.Reducer.mean(), geometry=aoi,
            scale=1000, maxPixels=1e9
        ).getInfo()
        temp_current = current.get('bio01', 0) / 10
        precip_current = current.get('bio12', 0)

        # 3. Climat 2050 CMIP6 SSP2-4.5 — ensemble 5 modèles
        cmip6_models = ['ACCESS-CM2', 'MIROC6', 'MPI-ESM1-2-HR', 'GFDL-ESM4', 'BCC-CSM2-MR']
        
        temp_futures = []
        precip_futures = []
        
        for model in cmip6_models:
            try:
                cmip6 = ee.ImageCollection('NASA/GDDP-CMIP6') \
                    .filter(ee.Filter.eq('model', model)) \
                    .filter(ee.Filter.eq('scenario', 'ssp245')) \
                    .filterDate('2050-01-01', '2050-12-31') \
                    .select(['tas', 'pr']).mean()
                result = cmip6.reduceRegion(
                    reducer=ee.Reducer.mean(), geometry=aoi,
                    scale=25000, maxPixels=1e9
                ).getInfo()
                t = result.get('tas')
                p = result.get('pr')
                if t and p:
                    temp_futures.append(float(t) - 273.15)
                    precip_futures.append(float(p) * 86400 * 365)
            except:
                continue
        
        # Moyenne de l'ensemble multi-modèles
        if temp_futures:
            temp_future = sum(temp_futures) / len(temp_futures)
            precip_future = sum(precip_futures) / len(precip_futures)
        else:
            # Fallback ACCESS-CM2
            cmip6 = ee.ImageCollection('NASA/GDDP-CMIP6') \
                .filter(ee.Filter.eq('model', 'ACCESS-CM2')) \
                .filter(ee.Filter.eq('scenario', 'ssp245')) \
                .filterDate('2050-01-01', '2050-12-31') \
                .select(['tas', 'pr']).mean()
            future = cmip6.reduceRegion(
                reducer=ee.Reducer.mean(), geometry=aoi,
                scale=25000, maxPixels=1e9
            ).getInfo()
            temp_future = future.get('tas', 0) - 273.15
            precip_future = future.get('pr', 0) * 86400 * 365

        temp_change = round(temp_future - temp_current, 1)
        precip_change_pct = round((precip_future - precip_current) / precip_current * 100, 1) if precip_current else 0

        # 4. Calcul suitabilité par espèce
        results = []
        for sp, fam in list(species_list.items())[:15]:
            climate_range = get_species_temp_range(sp)
            if not climate_range:
                continue

            score = 1.0
            if temp_future > climate_range['temp_max']:
                excess = temp_future - climate_range['temp_max']
                score -= min(0.7, excess * 0.15)
            if temp_future < climate_range['temp_min']:
                deficit = climate_range['temp_min'] - temp_future
                score -= min(0.7, deficit * 0.1)
            temp_diff = abs(temp_future - climate_range['temp_mean'])
            if temp_diff > 3:
                score -= min(0.3, (temp_diff - 3) * 0.05)

            score = max(0, round(score, 2))

            if score >= 0.7:
                status = 'Suitable'
                status_fr = 'Favorable'
            elif score >= 0.4:
                status = 'Moderate risk'
                status_fr = 'Risque modéré'
            else:
                status = 'At risk'
                status_fr = 'A risque'

            results.append({
                'species': sp,
                'family': fam,
                'score': score,
                'status': status,
                'status_fr': status_fr,
                'temp_range': f"{climate_range['temp_min']}–{climate_range['temp_max']}°C"
            })

        results.sort(key=lambda x: x['score'], reverse=True)

        suitable = len([r for r in results if r['score'] >= 0.7])
        moderate = len([r for r in results if 0.4 <= r['score'] < 0.7])
        at_risk  = len([r for r in results if r['score'] < 0.4])

        return {
            'success': True,
            'species_total': len(species_list),
            'species_analyzed': len(results),
            'temp_current': round(temp_current, 1),
            'temp_2050': round(temp_future, 1),
            'temp_change': temp_change,
            'precip_current': round(precip_current),
            'precip_2050': round(precip_future),
            'precip_change_pct': precip_change_pct,
            'scenario': 'SSP2-4.5 (2050) — 5-model ensemble',
            'suitable': suitable,
            'moderate': moderate,
            'at_risk': at_risk,
            'species': results
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}
