FROM debian:trixie

MAINTAINER Bruno Binet <bruno.binet@gmail.com>

RUN apt-get update && \
  DEBIAN_FRONTEND=noninteractive apt-get install -yq --no-install-recommends \
    dumb-init openssh-server sendemail libio-socket-ssl-perl ca-certificates \
    jq make bash-completion vim python3 python3-pip python3-venv \
    python3-argcomplete python3-requests libpangocairo-1.0-0 \
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
    mkdir -p /etc/bash_completion.d && activate-global-python-argcomplete && \
    mkdir -p /var/run/sshd

# Install Python dependencies for the API
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --break-system-packages -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

# Copy API application code
COPY app/ /usr/local/share/acs_helloasso_invoicing/app/
COPY lib/ /usr/local/share/acs_helloasso_invoicing/lib/

ENV PYTHONPATH=/usr/local/share/acs_helloasso_invoicing

EXPOSE 22
EXPOSE 8000

ENTRYPOINT ["/usr/bin/dumb-init", "--"]

CMD ["bash", "-c", "/usr/local/sbin/docker-pre-start.sh && gunicorn app.main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --daemon && /usr/sbin/sshd -D"]
