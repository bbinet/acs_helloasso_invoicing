# ACS HelloAsso invoicing tool

The ACS HelloAsso invoicing tool query HelloAsso API V5 and generate invoices for ACS members.

## Requirements

You must have the `requests` Python packages installed:

```
$ pip install requests
```

## Configuration

A JSON configuration file is used to specify the parameters needed to connect
to the HelloAsso API.

Here is a sample configuration:

```
{
  "credentials": {
    "helloasso": {
      "id": "<YOUR_HELLOASSO_API_ID>",
      "secret": "<YOUR_HELLOASSO_API_SECRET>"
    }
  },
  "conf": {
    "helloasso": {
      "api_url": "https://api.helloasso.com",
      "organization_name": "acs-savoie-technolac",
      "formSlug": "inscription-acs-saison-2023-2024",
      "formType": "MemberShip"
    }
  }
}
```

## Query HelloAsso data

To start using the tool, run the `helloasso.py` python script:

```
$ python3 helloasso.py --help

usage: helloasso.py [-h] [-d] [-m] [-j] [-s] [-r] [-u USER_FILTER]
                    [-f FROM_FILTER] [-t TO_FILTER] [-a ACTIVITY_FILTER]
                    conf

positional arguments:
  conf                  path to a config file

optional arguments:
  -h, --help            show this help message and exit
  -d, --dump            dump data to files
  -m, --member-show     show member data to standard output
  -j, --json-show       show json data to standard output
  -s, --summary-show    show summary data to standard output
  -r, --refund-filtered
                        filter out refunded orders
  -u USER_FILTER, --user-filter USER_FILTER
                        filter on user name
  -f FROM_FILTER, --from-filter FROM_FILTER
                        filter on start date
  -t TO_FILTER, --to-filter TO_FILTER
                        filter on end date
  -a ACTIVITY_FILTER, --activity-filter ACTIVITY_FILTER
                        regex filter on activities
```

So for example, if you want to show the list of people in you membership campaign, please do:

```
$ python3 helloasso.py path/to/conf.json -m
```

Then you can play with the various filtering options of the tool to search and
filter data.

## Generate invoices for your members

Before actually generating invoices you need to dump HelloAsso data to disk
using the `--dump` option:

```
$ python3 helloasso.py path/to/conf.json -r -dump
```

This will generate a JSON file in the `invoicing/<membership campaign>/` for
each of you member.

Then you can go to the `invoicing/<membership campaign>/` directory, and run
the following command:

```
$ ln -sf ../Makefile ./
$ make all
```

This will generate a PDF invoice for every JSON file in the directory.
