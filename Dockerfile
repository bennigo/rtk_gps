FROM alpine:3.19

RUN apk add gcc \
    libc-dev \
    libnfs-dev \
    python3-dev \
    py3-pip \
    poetry
COPY . .
RUN pip install --break-system-packages .

CMD ["rtk_scheduler"]
