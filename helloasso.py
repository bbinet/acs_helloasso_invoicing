#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
import os
import json
import argparse
import unicodedata
import re
import requests
from collections import defaultdict

try:
    import argcomplete
except ImportError:
    argcomplete=False

script_dir = os.path.dirname(os.path.realpath(__file__))


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
            if unicodedata.category(c) != 'Mn')

class HelloAsso:
    def __init__(self, config_path):
        with open(config_path, "r") as jsonfile:
            config = json.load(jsonfile)
            self.conf_global = config
            self.conf = config["conf"]
            self.conf["dir"] = os.path.dirname(os.path.realpath(config_path))
        token = self.Authenticate()
        self.headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer '+token,
        }

    def ConfGet(self, *keys):
        obj = self.conf
        for k in keys:
            try:
                obj = obj[k]
            except (IndexError, KeyError) as e:
                return obj
            if not isinstance(obj, (dict, list)):
                break
        return obj

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

    def GetData(self, user_filter=None, from_filter=None, to_filter=None, ea_filter=None, activity_filter=None, refund_filter=False):
        page = 1
        payload = {
            'withDetails': True,
            'pageSize': '50'
        }
        if user_filter:
            payload['userSearchKey'] = user_filter
        if from_filter:
            payload['from'] = from_filter
        if to_filter:
            payload['to'] = to_filter
        while True:
            payload['pageIndex'] = page
            url = '{}/v5/organizations/{}/forms/{}/{}/items'.format(
                    self.conf["helloasso"]["api_url"],
                    self.conf["helloasso"]["organization_name"],
                    self.conf["helloasso"]["formType"],
                    self.conf["helloasso"]["formSlug"])
            resp_json = requests.get(url, params=payload, headers=self.headers).json()
            if "data" not in resp_json:
                break
            for item in resp_json["data"]:
                if refund_filter and len(item['payments'][0]['refundOperations']) > 0:
                    continue
                if ea_filter and item['name'] != "Adhésion à l'ACS avec accès à la salle Emile Allais":
                    continue
                if activity_filter and not any([
                        re.search(activity_filter, o['name'], flags=re.IGNORECASE)
                            for o in item.get('options', [])]):
                    continue
                yield item
            if page >= resp_json["pagination"]["totalPages"]:
                break
            page += 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('conf', help='path to a config file', nargs='?', default=os.path.join(script_dir, 'conf.json'))
    parser.add_argument('-d', '--dump', help='dump data to files', action='store_true')
    parser.add_argument('-m', '--member-show', help='show member data to standard output', action='store_true')
    parser.add_argument('-j', '--json-show', help='show json data to standard output', action='store_true')
    parser.add_argument('-s', '--summary-show', help='show summary data to standard output', action='store_true')
    parser.add_argument('-w', '--summary-word', help='show only <word> field in summary data to standard output')
    parser.add_argument('-r', '--refund-filtered', help='filter out refunded orders', action='store_true')
    parser.add_argument('-u', '--user-filter', help='filter on user name')
    parser.add_argument('-f', '--from-filter', help='filter on start date')
    parser.add_argument('-t', '--to-filter', help='filter on end date')
    parser.add_argument('-e', '--ea-filter', help='filter on Emile Allais members', action='store_true')
    parser.add_argument('-a', '--activity-filter', help='regex filter on activities')
    if argcomplete:
        argcomplete.autocomplete(parser)
    args = parser.parse_args()
    #import pdb; pdb.set_trace()

    helloasso = HelloAsso(args.conf)
    count = 0
    summary = defaultdict(list)
    for item in helloasso.GetData(args.user_filter, args.from_filter, args.to_filter, args.ea_filter, args.activity_filter, args.refund_filtered):
        count += 1
        firstname = strip_accents(item['user']['firstName'].lower().replace(" ", ""))
        lastname = strip_accents(item['user']['lastName'].lower().replace(" ", ""))
        orderdate = item['order']['date'].split('T')[0]
        filename = f"{firstname}_{lastname}_{orderdate}_{item['id']}.json"
        filepath = os.path.join(helloasso.ConfGet('dir'), 'invoicing',
                helloasso.ConfGet('helloasso', 'formSlug'), filename)
        member = {
                'ea': item['name'] == "Adhésion à l'ACS avec accès à la salle Emile Allais",
                'firstname': item['user']['firstName'].strip().title(),
                'lastname': item['user']['lastName'].strip().title(),
                'email': item['payer']['email'],
                'activities': [o['name'] for o in item.get('options', [])],
                }
        for field in item['customFields']:
            if field['name'] == "Soci\u00e9t\u00e9":
                member['company'] = field['answer'].upper()
            elif field['name'] == "T\u00e9l\u00e9phone":
                member['phone'] = field['answer']
        for o in item.get('options', []):
            summary[o['name']].append(member)

        if args.member_show:
            print(f"{count:3}. Adhésion {'EA ' if member['ea'] else ''}n°{item['id']} le {orderdate}:")
            print(f"     {member['firstname']} {member['lastname']} ({member['company']})")
            print(f"     {member['email']} - {member['phone']}")
            print(f"     {' - '.join(member['activities'])}")
            print("-" * 80)

        if args.json_show:
            print(json.dumps(item, indent=4))
            print("=" * 80)

        if not args.dump:
            continue

        if os.path.isfile(filepath):
            if len(item['payments'][0]['refundOperations']) > 0:
                print(f"/!\\ Attention refund operation : {filename}")
            else:
                print(f"Nothing to do: {filename} already exists")
        else:
            if len(item['payments'][0]['refundOperations']) > 0:
                print(f"Ignore {filename} (remboursement)")
                continue
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w") as f:
                json.dump(item, f, indent=4)
                print(f"Item data written to file: {filename}")
    if args.summary_show:
        print("\nSummary:")
        for activity, members in summary.items():
            if args.activity_filter and not re.search(
                    args.activity_filter, activity, flags=re.IGNORECASE):
                continue
            print("")
            print(f"{activity}: {len(members)}")
            print("-" * len(f"{activity}: {len(members)}"))
            if args.summary_word:
                for m in sorted(members, key=lambda item: item[args.summary_word]):
                    print(f"    {m[args.summary_word]}")
            else:
                for m in sorted(members, key=lambda item: item['firstname']):
                    print(f"    {m['firstname']} {m['lastname']} ({m['company']})")
    print()
    print(f"{count} results returned.")
