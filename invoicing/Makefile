.PHONY: clean
all: $(addsuffix .pdf,$(basename $(basename $(wildcard *.json))))

../.venv:
	python3 -m venv ../.venv
	../.venv/bin/pip install -U pip
	../.venv/bin/pip install jinja2-cli weasyprint==52.5

clean:
	rm -rf ../.venv

%.pdf: %.html ../.venv
	../.venv/bin/weasyprint $< $@

#.PRECIOUS: %.html
%.html: %.json ../.venv ../template.jinja2 ../style.css
	../.venv/bin/jinja2 -D date=$(shell date +%d/%m/%Y) --format=json ../template.jinja2 $< > $@
