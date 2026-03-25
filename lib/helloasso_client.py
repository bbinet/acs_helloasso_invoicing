import re

import requests


class HelloAssoClient:
    """HelloAsso API client.

    Takes a config dict (as returned by load_config) with 'credentials' and 'conf' keys.
    """

    def __init__(self, config):
        self.conf_global = config
        self.conf = config["conf"]
        self.access_token = None
        self.refresh_token = None
        self.Authenticate()
        self.headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + self.access_token,
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
        data = r.json()
        self.access_token = data["access_token"]
        self.refresh_token = data.get("refresh_token")
        self._update_auth_header()

    def RefreshToken(self):
        """Use the refresh_token to obtain a new access_token.

        Raises RuntimeError if the refresh request fails (non-2xx status).
        """
        headers = {
            'content-type': 'application/x-www-form-urlencoded'
        }
        payload = {
            'grant_type': 'refresh_token',
            'client_id': self.conf_global["credentials"]["helloasso"]["id"],
            'client_secret': self.conf_global["credentials"]["helloasso"]["secret"],
            'refresh_token': self.refresh_token,
        }
        url = '{}/oauth2/token'.format(self.conf["helloasso"]["api_url"])
        r = requests.post(url, data=payload, headers=headers)
        if r.status_code >= 400:
            raise RuntimeError("Token refresh failed with status {}".format(r.status_code))
        data = r.json()
        self.access_token = data["access_token"]
        self.refresh_token = data.get("refresh_token", self.refresh_token)
        self._update_auth_header()

    def _update_auth_header(self):
        """Sync Authorization header with current access_token."""
        if self.access_token:
            self.headers = {
                'Accept': 'application/json',
                'Authorization': 'Bearer ' + self.access_token,
            }

    def _request(self, method, url, **kwargs):
        """Make an HTTP request, refreshing tokens on 401.

        On 401: try RefreshToken() then retry.
        If refresh fails: try full Authenticate() then retry.
        """
        fn = getattr(requests, method.lower())
        resp = fn(url, headers=self.headers, **kwargs)

        if resp.status_code == 401:
            # Try token refresh first
            try:
                self.RefreshToken()
            except RuntimeError:
                # Refresh failed — fall back to full re-authentication
                self.Authenticate()

            resp = fn(url, headers=self.headers, **kwargs)

        return resp

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
            resp_json = self._request('get', url, params=payload).json()
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
