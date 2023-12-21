# ACS HelloAsso invoicing tool

The ACS HelloAsso invoicing tool query HelloAsso API V5 and generate invoices for ACS members.

## Requirements

You must have the `requests` Python package installed:

```
$ pip install requests
```

Also to send invoices by email, you'll need to install following packages:

```
$ sudo apt install make jq sendemail libio-socket-ssl-perl ca-certificates libpangocairo-1.0-0
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
    },
    "sendemail": {
      "username": "<YOUR_MAIL_PROVIDER_USERNAME>",
      "password": "<YOUR_MAIL_PROVIDER_PASSWORD>"
    }
  },
  "conf": {
    "helloasso": {
      "api_url": "https://api.helloasso.com",
      "organization_name": "acs-savoie-technolac",
      "formSlug": "inscription-acs-saison-2023-2024",
      "formType": "MemberShip"
    },
    "sendemail": {
      "smtp": "smtp.gmail.com:587",
      "from": "bruno.binet@gmail.com",
      "subject": "Facture adhésion ACS",
      "message": "Veuillez trouver ci-joint la facture de votre adhésion à l'ACS.\nBien cordialement,\nBruno, pour l'ACS"
    }
  }
}
```

## Query HelloAsso data

To start using the tool, run the `helloasso.py` python script:

```
$ python3 helloasso.py --help

usage: helloasso [-h] [-d] [-m] [-j] [-s] [-w SUMMARY_WORD] [-r]
                 [-u USER_FILTER] [-f FROM_FILTER] [-t TO_FILTER]
                 [-a ACTIVITY_FILTER]
                 conf

positional arguments:
  conf                  path to a config file

optional arguments:
  -h, --help            show this help message and exit
  -d, --dump            dump data to files
  -m, --member-show     show member data to standard output
  -j, --json-show       show json data to standard output
  -s, --summary-show    show summary data to standard output
  -w SUMMARY_WORD, --summary-word SUMMARY_WORD
                        show only <word> field in summary data to standard
                        output
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

So for example, if you want to show the list of people in you membership
campaign, please do:

```
$ python3 helloasso.py path/to/conf.json -m
```

Or a summary of all people registered grouped by activity and excluding
memberships which have been refunded:
```
$ python3 helloasso.py path/to/conf.json -s -r
```

Then you can play with the various filtering options of the tool to search and
filter data.

## Generate invoices for your members

Before actually generating invoices you need to dump HelloAsso data to disk
using the `--dump` option:

```
$ python3 helloasso.py path/to/conf.json -r --dump
```

This will generate a JSON file in `invoicing/<membership campaign>/` for each
of your member.

Then you can go to the `invoicing/<membership campaign>/` directory, and run
the following command:

```
$ ln -sf ../Makefile ./
$ ln -sf path/to/signature.png ./signature.png
$ ln -sf ../../<path/to/conf>.json ./conf.json
$ make pdf
```

This will generate a PDF invoice for every JSON file in the directory.

Then you can also send an email (with the invoice attached) to each of your
members by running the following command:

```
$ make sendemail
```

## Docker

A docker container (with a ssh server included and everything pre-installed)
has been created to allow to easily host this tool online so that windows
people just need to connect to the container through putty and be ready to
query HelloAsso, generate pdf invoices, and send those by email to the members.

### Build

To create the image `bbinet/acs_helloasso_invoicing`, execute the following
command:

    docker build -t bbinet/acs_helloasso_invoicing .

You can now push the new image to the public registry:

    docker push bbinet/acs_helloasso_invoicing

### Run

Then, when starting your acs_helloasso_invoicing container, you will want to
bind ports `22` from the acs_helloasso_invoicing container to a host external
port.

You may also want to provide a read-only `authorized_keys` file that will be
use to allow some users to connect with their public ssh key.

For example:

    $ docker pull bbinet/acs_helloasso_invoicing

    $ docker run --name acs_helloasso_invoicing \
        -v authorized_keys:/etc/ssh/authorized_keys:ro \
        -p 22:22 \
        bbinet/acs_helloasso_invoicing
