FROM tiangolo/uwsgi-nginx-flask:python3.7

RUN curl -L "https://github.com/docker/compose/releases/download/1.25.3/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && \
    chmod 755 /usr/local/bin/docker-compose && \
    curl -L https://storage.googleapis.com/kubernetes-release/release/v1.17.0/bin/linux/amd64/kubectl -o /usr/local/bin/kubectl && \
    chmod 755 /usr/local/bin/kubectl && \
    curl -L https://get.helm.sh/helm-v3.0.3-linux-amd64.tar.gz | tar -xz && \
    mv linux-amd64/helm /usr/local/bin && \
    chmod 755 /usr/local/bin/helm && \ 
    cd / && git clone https://github.com/instana/robot-shop.git && \
    mkdir -p /config

COPY ./app/requirements.txt /app/requirements.txt
RUN cd /app && pip install -r requirements.txt
COPY ./app /app