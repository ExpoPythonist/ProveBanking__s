import clearbit
import requests
from django.conf import settings


def retrieve_clearbit_data(domain):
    clearbit.key = settings.CLEARBIT_KEY
    return clearbit.Enrichment.find(domain=domain, stream=True)


def get_dnb_token(username, password, url="https://maxcvservices.dnb.com/rest/Authentication"):
    r = requests.post(
        url,
        headers={
            "x-dnb-user": username,
            "x-dnb-pwd": password,
        }
    )
    return r.headers["Authorization"]


def get_dun_code(token, name):
    url = "https://maxcvservices.dnb.com/V5.0/organizations?CountryISOAlpha2Code=US&SubjectName=INTUIT&match=true&MatchTypeText=Advanced"
    headers = {"Authorization": token}
    r = requests.get(url, headers=headers)
    duns = r.json().get('MatchResponse').get('MatchResponseDetail').get('MatchCandidate')[0].get('DUNSNumber')
    self.get_rtng_trnd(duns=duns, token=token)


def get_rtng_trnd(token):
    url = 'https://maxcvservices.dnb.com/V5.0/organizations/804735132/products/RTNG_TRND'.format(duns=None)
    headers = {"Authorization": token}
    r = requests.get(url, headers=headers)
    return r.json().get("OrderProductResponse").get('OrderProductResponseDetail').get('Product').get('Organization').get('Assessment')
