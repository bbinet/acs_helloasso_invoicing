#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
import os
import json
import argparse
import re

try:
    import argcomplete
except ImportError:
    argcomplete=False

from lib.config import load_config, conf_get
from lib.helloasso_client import HelloAssoClient
from lib.models import parse_member, get_member_filename, build_summary, strip_accents_ponct
from lib.filesystem import get_member_filepath, dump_item

script_dir = os.path.dirname(os.path.realpath(__file__))

default_conf = 'conf.json'
if not os.path.isfile(default_conf):
    default_conf = os.path.join(script_dir, 'conf.json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('conf', help='path to a config file', nargs='?', default=default_conf)
    parser.add_argument('-d', '--dump', help='dump data to files', action='store_true')
    parser.add_argument('-m', '--member-show', help='show member data to standard output', choices=['txt', 'csv', 'json'])
    parser.add_argument('-p', '--txt-pattern', help='pattern to format txt output '
            '(available fields are: firstname, lastname, company, email, phone, activities, count, orderid, orderdate, ea).'
            ' Example: \'"{firstname} {lastname}" <{email}>\'')
    parser.add_argument('-s', '--summary-show', help='show summary data to standard output', choices=['min', 'member', 'pattern'])
    parser.add_argument('-r', '--refund-filtered', help='filter out refunded orders', action='store_true')
    parser.add_argument('-e', '--ea-filter', help='filter on Emile Allais members', action='store_true')
    parser.add_argument('-u', '--user-filter', help='filter on user name')
    parser.add_argument('-f', '--from-filter', help='filter on start date')
    parser.add_argument('-t', '--to-filter', help='filter on end date')
    parser.add_argument('-a', '--activity-filter', help='regex filter on activities')
    if argcomplete:
        argcomplete.autocomplete(parser)
    args = parser.parse_args()

    config = load_config(args.conf)
    helloasso = HelloAssoClient(config)
    count = 0
    items_and_members = []
    if args.member_show == "csv":
        print(f"Num,HelloAssoID,OrderDate,FirstName,LastName,Company,EmileAllais,Activities")
    for item in helloasso.GetData(args.user_filter, args.from_filter, args.to_filter, args.ea_filter, args.activity_filter, args.refund_filtered):
        count += 1
        orderdate = item['order']['date'].split('T')[0]
        filepath = get_member_filepath(config["conf"], item)
        filename = get_member_filename(item)
        member = parse_member(item)
        items_and_members.append((item, member))

        if args.member_show == "txt":
            if args.txt_pattern:
                print(args.txt_pattern.format(
                    count=count, orderid=item["id"], orderdate=orderdate, **member))
            else:
                print(f"{count:3}. Adh\u00e9sion {'EA ' if member['ea'] else ''}n\u00b0{item['id']} le {orderdate}:")
                print(f"     {member['firstname']} {member['lastname']} ({member['company']})")
                print(f"     {member['email']} - {member['phone']}")
                print(f"     {' - '.join(member['activities'])}")
                print("-" * 80)
        elif args.member_show == "csv":
            print(f"{count},{item['id']},{orderdate},{member['firstname']},{member['lastname']},{member['company']},{'Oui' if member['ea'] else 'Non'},{' - '.join(member['activities'])}")
        elif args.member_show == "json":
            print(json.dumps(item, indent=4))
            print("=" * 80)

        if not args.dump:
            continue

        if os.path.isfile(filepath):
            if 'payments' in item and len(item['payments'][0]['refundOperations']) > 0:
                print(f"/!\\ Attention refund operation : {filename}")
            else:
                print(f"Nothing to do: {filename} already exists")
        else:
            if 'payments' in item and len(item['payments'][0]['refundOperations']) > 0:
                print(f"Ignore {filename} (remboursement)")
                continue
            dump_item(filepath, item)
            print(f"Item data written to file: {filename}")
    if args.summary_show:
        sorted_summary = build_summary(items_and_members)
        print("\nSummary:")
        for activity, members in sorted_summary:
            if args.activity_filter and not re.search(
                    args.activity_filter, activity, flags=re.IGNORECASE):
                continue
            if args.summary_show != "min":
                print("")
            print(f"{activity}: {len(members)}")
            if args.summary_show != "min":
                print("-" * len(f"{activity}: {len(members)}"))

            if args.summary_show == "min":
                continue
            elif args.summary_show == "member":
                for m in sorted(members, key=lambda item: item['firstname']):
                    print(f"    {m['firstname']} {m['lastname']} ({m['company']})")
            elif args.summary_show == "pattern":
                for m in sorted(members, key=lambda item: item['firstname']):
                    print(args.txt_pattern.format(
                        count=count, orderid=item["id"], orderdate=orderdate, **m))
    print()
    print(f"{count} results returned.")
