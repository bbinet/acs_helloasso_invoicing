FROM debian:buster

MAINTAINER Bruno Binet <bruno.binet@helioslite.com>

RUN apt-get update && \
  DEBIAN_FRONTEND=noninteractive apt-get install -yq --no-install-recommends \
    dumb-init openssh-server sendemail libio-socket-ssl-perl ca-certificates \
    jq make bash-completion vim python3 python3-pip python3-venv \
    libpangocairo-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY docker-pre-start.sh /usr/local/sbin/docker-pre-start.sh
COPY invoicing/style.css /usr/local/share/acs_helloasso_invoicing/invoicing/style.css
COPY invoicing/logo.svg /usr/local/share/acs_helloasso_invoicing/invoicing/logo.svg
COPY invoicing/Makefile /usr/local/share/acs_helloasso_invoicing/invoicing/Makefile
COPY invoicing/template.jinja2 /usr/local/share/acs_helloasso_invoicing/invoicing/template.jinja2
COPY helloasso.py /usr/local/share/acs_helloasso_invoicing/helloasso.py

RUN chmod 750 /usr/local/sbin/docker-pre-start.sh && \
    chmod 755 /usr/local/share/acs_helloasso_invoicing/helloasso.py && \
    ln -s /usr/local/share/acs_helloasso_invoicing/helloasso.py /usr/local/bin/helloasso && \
    pip3 install requests argcomplete && \
    activate-global-python-argcomplete && \
    mkdir /var/run/sshd

EXPOSE 22

ENTRYPOINT ["/usr/bin/dumb-init", "--"]

CMD ["bash", "-c", "/usr/local/sbin/docker-pre-start.sh && /usr/sbin/sshd -D"]
