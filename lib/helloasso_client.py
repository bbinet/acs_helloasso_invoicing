import re
import unicodedata

import requests


def strip_accents_ponct(s):
    """Remove accents and punctuation from a string."""
    return ''.join(c for c in unicodedata.normalize('NFD', s)
            if unicodedata.category(c) not in ('Mn', 'Po'))


class HelloAssoClient:
    """HelloAsso API client.

    Takes a config dict (as returned by load_config) with 'credentials' and 'conf' keys.
    """

    def __init__(self, config):
        self.conf_global = config
        self.conf = config["conf"]
        token = self.Authenticate()
        self.headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + token,
        }

    def Authenticate(self):
        headers = {
            'content-type': 'application/x-www-form-urlencoded'
        }
        payload = {
            'grant_type': 'client_credentials',
            'client_id': self.conf_global["credentials"]["helloasso"]["id"],
            'client_secret': self.conf_global["credentials"]["helloasso"]["secret"]
        }
        url = '{}/oauth2/token'.format(self.conf["helloasso"]["api_url"])
        r = requests.post(url, data=payload, headers=headers)
        return r.json()["access_token"]

    def GetData(self, user_filter=None, from_filter=None, to_filter=None,
                ea_filter=None, activity_filter=None, refund_filter=False):
        payload = {
            'withDetails': True,
            'pageSize': '100'
        }
        if user_filter:
            payload['userSearchKey'] = user_filter
        if from_filter:
            payload['from'] = from_filter
        if to_filter:
            payload['to'] = to_filter
        while True:
            url = '{}/v5/organizations/{}/forms/{}/{}/items'.format(
                    self.conf["helloasso"]["api_url"],
                    self.conf["helloasso"]["organization_name"],
                    self.conf["helloasso"]["formType"],
                    self.conf["helloasso"]["formSlug"])
            resp_json = requests.get(url, params=payload, headers=self.headers).json()
            payload['continuationtoken'] = resp_json['pagination']['continuationToken']
            if "data" not in resp_json or len(resp_json['data']) <= 0:
                break
            for item in resp_json["data"]:
                if refund_filter and 'payments' in item and len(item['payments'][0]['refundOperations']) > 0:
                    continue
                if ea_filter and item['name'] != "Adh\u00e9sion \u00e0 l'ACS avec acc\u00e8s \u00e0 la salle Emile Allais":
                    continue
                if activity_filter and not any([
                        re.search(activity_filter, o['name'], flags=re.IGNORECASE)
                            for o in item.get('options', [])]):
                    continue
                yield item
