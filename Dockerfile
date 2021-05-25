# Build image
FROM python:3.8-slim AS compile-image
RUN apt-get update
# RUN apt-get install -y --no-install-recommends git
RUN apt-get install -y --no-install-recommends build-essential gcc
RUN apt-get install -y --no-install-recommends libyaml-dev

ADD requirements.txt .
RUN pip install --user -r requirements.txt


# Run image
FROM python:3-alpine AS run-image

RUN apk add tzdata libstdc++
RUN apk add nim nimble
RUN ln -fs /usr/share/zoneinfo/Etc/UTC /etc/localtime

COPY --from=compile-image /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

ADD . /src
RUN rm -rf /src/data/
WORKDIR /src

ENV PRODUCTION=true

CMD [ "python", "-m", "src" ]
