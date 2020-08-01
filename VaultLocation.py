import json
import os
import os.path
import urllib.request
import magic

import filetype
import preview_generator
import requests
from linkpreview import link_preview
from preview_generator.manager import PreviewManager

from pvault import PVault


def from_loc(location, loc_type):
    if loc_type == 'Web':
        return WebLocation(location)
    elif loc_type == 'File':
        return FileLocation(location)


class VaultLocation:
    loc_type = 'None'
    name = ''
    uuid = ''

    def __init__(self, location):
        self.location = location

    def to_dict(self):
        di = {'name': self.name, 'uuid': self.uuid, 'type': self.loc_type, 'location': self.location}
        return di

    def get_preview(self):
        return self.name, '', PVault.default_preview


class FileLocation(VaultLocation):
    loc_type = 'File'

    def __init__(self, path):
        super().__init__(path)

        mime = magic.Magic(mime=True)
        ft = mime.from_file(self.location)
        # ft, _ = get_file_type(self.location)
        self.mime = ft.split('/')[0]
        prev = self.get_preview()
        self.preview = prev[1:]

    def get_preview(self):
        if self.mime == 'image':
            return self.name, '', self.location
        try:
            pv_mgr = PreviewManager(PVault.cache_path, create_folder=True)
            return self.name, '', pv_mgr.get_jpeg_preview(self.location)
        except preview_generator.exception.UnsupportedMimeType:
            print('Unsuported mime type!', self.location)
        return super().get_preview()

    '''
    def retrieve_element(self):
        with open(self.location, 'rb') as f:
            return f
    '''


def get_file_type(path):
    kind = filetype.guess(path)
    if kind is None:
        return 'doc', os.path.splitext(path)[1]
    return kind.mime, kind.extension


def check_url_type(image_url, t):
    r = requests.head(image_url)
    return t in r.headers.get("content-type", '')


class WebLocation(VaultLocation):
    loc_type = 'Web'

    def __init__(self, url, archive=False, archive_dir=None):
        self.location = url
        url2 = urllib.parse.urlparse(self.location)
        # self.name = os.path.basename(url2.path)
        prev = self.get_preview()
        self.name = prev[0]
        self.preview = prev[1:]

        # usar mime types (https://stackoverflow.com/questions/4776924/how-to-safely-get-the-file-extension-from-a-url)        
        ext = os.path.splitext(url2.path)[1]
        self.filename = self.name + ext

        self.archive = archive
        self.archive_dir = archive_dir
        self.arch_loc = None

    def to_dict(self):
        di = super().to_dict()
        di['archived'] = self.archive
        return di

    def get_preview(self):
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:39.0) Gecko/20100101 Firefox/39.0'}
        parsed = urllib.parse.urlparse(self.location)
        if parsed.netloc == 'www.reddit.com':
            return self.get_reddit_preview(headers)

        pv = link_preview(self.location)
        title = pv.title if pv.title is not None else self.name  # otra cosa
        # asegurarse de que la url dirige a una imagen
        image = pv.image if pv.image is not None else self.location
        desc = pv.description if pv.description is not None else ''

        # title, desc, image = web_preview(self.location, headers=headers, parser='html.parser')
        return title, desc, image

    def get_reddit_preview(self, headers={}):
        s = self.location.rstrip('/')
        res = requests.get(s + '.json', headers=headers)
        jn = json.loads(res.content)
        data = jn[0]['data2']['children'][0]['data2']
        title = data['title']
        desc = data['subreddit_name_prefixed']
        image = data['url'] if check_url_type(data['url'], 'image') else data['thumbnail']
        return title, desc, image

    '''
    def retrieve_element(self):
        if self.arch_loc:
            if self.archive:
                print('data2 found in archive!!!')
                return self.arch_loc.retrieve_element()
            self.arch_loc = None  # and delete file!!!

        print('requesting data2...')
        data2 = requests.get(self.location)
        if self.archive:
            # save file at archive dir, then add it as a file location
            path = PVault.archive_dir + self.filename
            self.arch_loc = FileLocation(path)
        else:
            path = PVault.temp_dir + self.filename

        with open(path, 'wb') as f:
            f.write(data2.content)
            f.close()

        return path
    '''
