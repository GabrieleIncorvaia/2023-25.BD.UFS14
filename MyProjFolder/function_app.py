import azure.functions as func
import json
import logging
import requests
import urllib.parse

app = func.FunctionApp()

# Function to get the CID of an ingredient from PubChem
def get_pubchem_cid(session, ingredient_name):
    encoded_name = urllib.parse.quote(ingredient_name)
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{encoded_name}/cids/JSON"
    try:
        response = session.get(url)
        response.raise_for_status()
        data = response.json()
        cid = str(data['IdentifierList']['CID'][0])
        return cid
    except (requests.RequestException, KeyError, IndexError, ValueError) as e:
        logging.error(f"Error retrieving PubChem CID for {ingredient_name}: {e}")
        return None

# Function to get LD50 values from PubChem
def get_ld50_pubchem(session, cid):
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}/JSON/"
    try:
        response = session.get(url)
        response.raise_for_status()
        data = response.json()
        sections = data['Record']['Section']
        ld50_values = []
        def extract_ld50(sections):
            for section in sections:
                if 'Section' in section:
                    extract_ld50(section['Section'])
                if 'Information' in section:
                    for info in section['Information']:
                        if 'Value' in info and 'StringWithMarkup' in info['Value']:
                            for item in info['Value']['StringWithMarkup']:
                                if 'LD50' in item['String']:
                                    ld50_values.append(item['String'])
        extract_ld50(sections)
        return ld50_values if ld50_values else None
    except (requests.RequestException, KeyError, IndexError, ValueError) as e:
        logging.error(f"Error retrieving LD50 from PubChem for CID {cid}: {e}")
        return None