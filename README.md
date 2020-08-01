# PVault

## Installation

1. ```pip install -r requirements.txt```

### Known Issues

* ```AttributeError: module 'enum' has no attribute 'IntFlag'```:```pip uninstall -y enum34```
* ```AttributeError: type object 'Callable' has no attribute '_abc_registry'```: ```pip uninstall typing```
* ```FileNotFoundError: [Errno 2] No such file or directory: 'ffprobe'```: ```pip install ffmpeg```
```brew install ffmpeg```
`apt-get install zlib1g-dev libjpeg-dev python3-pythonmagick inkscape xvfb poppler-utils libfile-mimeinfo-perl qpdf libimage-exiftool-perl ufraw-batch ffmpeg`

`brew install qpdf, poppler, scribus, libreoffice`

## 