USERNAME ?= $(shell jq .credentials.sendemail.username conf.json)
PASSWORD ?= $(shell jq .credentials.sendemail.password conf.json)
SMTP ?= $(shell jq .conf.sendemail.smtp conf.json)
FROM ?= $(shell jq .conf.sendemail.from conf.json)
SUBJECT ?= $(shell jq .conf.sendemail.subject conf.json)
MESSAGE ?= $(shell jq .conf.sendemail.message conf.json)
TO = $(shell jq .payer.email $(word 2,$^))
MAKEFILE_DIR = $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
SIGNATURE_PATH = $(realpath signature.png)

.SILENT:
.PHONY: clean
pdf: $(addsuffix .pdf, $(basename $(filter-out conf.json, $(wildcard *.json))))
sendemail: $(addsuffix .mail.log, $(basename $(filter-out conf.json, $(wildcard *.json))))

../.venv:
	@echo "Creating Python virtual environment ../.venv"
	python3 -m venv ../.venv
	../.venv/bin/pip install -U pip
	../.venv/bin/pip install jinja2-cli weasyprint==52.5

clean:
	@echo "Cleaning up all files"
	find ./ -type f \( -name \*.pdf -o -name \*.json -o -name \*.mail.log \)
	rm -rf ../.venv

%.mail.log: %.pdf %.json
	@test -f $@ && echo "Mail was already sent (file $@ already exists)" || \
		echo "Sending invoice by email to member $(TO)"
	test -f $@ && touch $@ || sendemail \
		-f $(FROM) \
		-u $(SUBJECT) \
		-m $(MESSAGE) \
		-a $< \
		-t $(TO) \
		-s $(SMTP) \
		-o tls=auto \
		-xu $(USERNAME) \
		-xp $(PASSWORD) \
		-l $@ \
		|| (mv $@ error_$@; exit 1)

%.pdf: %.html ../.venv
	@echo "Generating PDF invoice from HTML file"
	../.venv/bin/weasyprint -u $(MAKEFILE_DIR) $< $@

#.PRECIOUS: %.html
%.html: %.json ../.venv $(MAKEFILE_DIR)/template.jinja2 $(MAKEFILE_DIR)/style.css
	@echo "Generating HTML file from Jinja2 template"
	@echo "signature=$(SIGNATURE_PATH) MAKEFILE_DIR=$(MAKEFILE_DIR)"
	../.venv/bin/jinja2 -D date=$(shell date +%d/%m/%Y) -D signature=$(SIGNATURE_PATH) --format=json $(MAKEFILE_DIR)/template.jinja2 $< > $@
