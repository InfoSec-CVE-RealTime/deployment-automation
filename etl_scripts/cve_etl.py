import os
import random
import pymongo
import requests
from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth

# MongoDB connection
MONGO_URI = os.environ.get("MONGO_URI")
CVE_URI = os.environ.get("CVE_URI")
START_AT = os.environ.get("START_AT")

client = pymongo.MongoClient(MONGO_URI)
db = client["InfoSec-CVE-RealTime"]
cve_collection = db["cve"]

START_DATE = datetime.strptime(START_AT, '%Y-%m-%dT%H:%M:%S.%f')
END_TIME = datetime.now()

iter_date = START_DATE
while iter_date < END_TIME:
    forward_date = iter_date + timedelta(days=90)
    if forward_date > END_TIME: forward_date = END_TIME
    print("Fetching data from {} to {}...".format(iter_date.strftime("%Y-%m-%dT%H:%M:%S.000"), forward_date.strftime("%Y-%m-%dT%H:%M:%S.000")))
    resp = requests.get(CVE_URI, params={"pubStartDate": iter_date.strftime("%Y-%m-%dT%H:%M:%S.000"),
                                    "pubEndDate": forward_date.strftime("%Y-%m-%dT%H:%M:%S.000")})
    
    if resp.status_code != 200: print("Error: Unable to fetch data from {} to {}; error code: {}".format(iter_date.strftime("%Y-%m-%dT%H:%M:%S.000"), forward_date.strftime("%Y-%m-%dT%H:%M:%S.000"), resp.status_code)); continue
    for vulnerability in resp.json()["vulnerabilities"]:
        if vulnerability['cve']['vulnStatus'] in {'Rejected', 'Deferred'}: continue
        cve_id = vulnerability["cve"]["id"]
        mod_date = datetime.strptime(vulnerability['cve']["lastModified"], '%Y-%m-%dT%H:%M:%S.%f')
        mod_day = mod_date.day
        mod_month = mod_date.month
        mod_year = mod_date.year

        pub_date = datetime.strptime(vulnerability['cve']["published"], '%Y-%m-%dT%H:%M:%S.%f')
        pub_day = pub_date.day
        pub_month = pub_date.month
        pub_year = pub_date.year

        cvss = -1
        cvss_key = ''
        access_authentication = ""
        access_complexity = ""
        access_vector = ""
        impact_availability = ""
        impact_confidentiality = ""
        impact_integrity = ""

        for metric in vulnerability['cve']['metrics']:
            if 'cvss' in metric and cvss_key < metric:
                cvss_key = metric
        if cvss_key == '':
            continue
        cvss_data = vulnerability['cve']['metrics'][cvss_key][0]['cvssData']
        if 'baseScore' in cvss_data and cvss < cvss_data['baseScore']:
            cvss = cvss_data['baseScore']
        if 'authentication' in cvss_data:
            access_authentication = cvss_data['authentication']
        if 'accessComplexity' in cvss_data:
            access_complexity = cvss_data['accessComplexity']
        if 'accessVector' in cvss_data:
            access_vector = cvss_data['accessVector']
        if 'availabilityImpact' in cvss_data:
            impact_availability = cvss_data['availabilityImpact']
        if 'confidentialityImpact' in cvss_data:
            impact_confidentiality = cvss_data['confidentialityImpact']
        if 'integrityImpact' in cvss_data:
            impact_integrity = cvss_data['integrityImpact']

        cwe_code = random.randrange(3,100)
        all_tags = []
        cwe_name = ""
        for reference in vulnerability['cve']['references']:
            if 'tags' in reference:
                all_tags.extend(reference['tags'])
        if len(all_tags) == 0: 
            try: cwe_name = vulnerability['cve']['references'][0]['url']
            except: pass
        else:
            while len(all_tags) > 3: all_tags.pop(-1)
            cwe_name = ":".join(all_tags)
        summary = vulnerability['cve']['descriptions'][0]['value']

        cve_dict = {
            "cve_id": cve_id,
            "mod_date": mod_date,
            "pub_date": pub_date,
            "mod_day": mod_day,
            "mod_month": mod_month,
            "mod_year": mod_year,
            "pub_day": pub_day,
            "pub_month": pub_month,
            "pub_year": pub_year,
            "cvss": cvss,
            "access_authentication": access_authentication,
            "access_complexity": access_complexity,
            "access_vector": access_vector,
            "impact_availability": impact_availability,
            "impact_confidentiality": impact_confidentiality,
            "impact_integrity": impact_integrity,
            "cwe_code": cwe_code,
            "cwe_name": cwe_name,
            "summary": summary
        }
    cve_collection.insert_one(cve_dict)
    print('--------------------')
    iter_date = forward_date