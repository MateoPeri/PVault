FROM python:3.8
COPY . /app
WORKDIR /app
RUN apt-get update && apt-get install -y \
    zlib1g-dev \
    libjpeg-dev \
    python3-pythonmagick \
    inkscape \
    xvfb \
    poppler-utils \
    libfile-mimeinfo-perl \
    qpdf \
    libimage-exiftool-perl \
    ufraw-batch \
    ffmpeg
RUN pip install -r requirements.txt
ENTRYPOINT ["python"]
CMD ["console.py"]