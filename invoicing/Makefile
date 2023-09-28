USERNAME ?= $(shell jq .credentials.sendemail.username conf.json)
PASSWORD ?= $(shell jq .credentials.sendemail.password conf.json)
SMTP ?= $(shell jq .conf.sendemail.smtp conf.json)
FROM ?= $(shell jq .conf.sendemail.from conf.json)
SUBJECT ?= $(shell jq .conf.sendemail.subject conf.json)
MESSAGE ?= $(shell jq .conf.sendemail.message conf.json)
TO = $(shell jq .payer.email $(word 2,$^))

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
	rm -rf ../.venv *.pdf *.json *.mail.log

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
		-l $@

%.pdf: %.html ../.venv
	@echo "Generating PDF invoice from HTML file"
	../.venv/bin/weasyprint $< $@

#.PRECIOUS: %.html
%.html: %.json ../.venv ../template.jinja2 ../style.css
	@echo "Generating HTML file from Jinja2 template"
	../.venv/bin/jinja2 -D date=$(shell date +%d/%m/%Y) --format=json ../template.jinja2 $< > $@
