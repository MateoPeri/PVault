import json
import mimetypes
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
    mime = ''
    preview = ()

    def __init__(self, location, fetch=True, uuid=None):
        self.location = location
        self.uuid = uuid
        if fetch:
            self.get_content()  # FIXME: ideally, this should only be called when necesary, not on creation

    def to_dict(self):
        prev = self.get_preview()
        return {'name': self.name, 'uuid': self.uuid,
                'loc_type': self.loc_type, 'location': self.location,
                'preview': {
                    'desc': prev[1],
                    'image': prev[2]
                }}

    def get_content(self):
        pass

    def get_preview(self):
        return self.name, '', PVault.default_preview


class WebLocation(VaultLocation):
    loc_type = 'Web'
    ext = ''  # REMOVE
    filename = ''  # REMOVE

    def __init__(self, url, fetch=True, uuid=None):
        super().__init__(url, fetch, uuid)

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

    def get_element(self):
        return requests.get(self.location)

    def get_content(self):
        response = requests.get(self.location)
        c_type = response.headers['content-type']
        # some content types are in the form 'text/hmtl; charset=UTF-8'
        # we only want 'text/html'
        self.mime = c_type.split()[0].rstrip(';')
        prev = self.get_preview()
        self.name = prev[0]
        # TODO: fails when url is a direct image (
        # https://upload.wikimedia.org/wikipedia/commons/thumb/1/1f/Oryctolagus_cuniculus_Rcdo.jpg/440px
        # -Oryctolagus_cuniculus_Rcdo.jpg)
        self.preview = prev[1:]


class FileLocation(VaultLocation):
    loc_type = 'File'

    def __init__(self, path, fetch=True, uuid=None):
        super().__init__(path, fetch, uuid)

    def get_preview(self):
        if self.mime == 'image':
            return self.name, '', self.location
        try:
            pv_mgr = PreviewManager(PVault.cache_path, create_folder=True)
            return self.name, '', pv_mgr.get_jpeg_preview(self.location)
        except preview_generator.exception.UnsupportedMimeType:
            print('Unsuported mime type!', self.location)
        return super().get_preview()

    def get_content(self):
        """
        Refresh the location.
        """
        mime = magic.Magic(mime=True)
        ft = mime.from_file(self.location)
        # ft, _ = get_file_type(self.location)
        self.mime = ft.split('/')[0]
        prev = self.get_preview()
        self.preview = prev[1:]


def archive_from_web(webloc: WebLocation, fetch=True):
    """
    Create a file location from a web location, for archiving purposes.
    """
    data = webloc.get_element()
    ext = mimetypes.guess_extension(webloc.mime)
    p = os.path.join(PVault.upload_dir, webloc.uuid + ext)
    with open(p, 'wb') as f:
        f.write(data.content)
        f.close()

    fl = FileLocation(p, fetch=fetch, uuid=webloc.uuid)
    return fl


def get_file_type(path):
    kind = filetype.guess(path)
    if kind is None:
        return 'doc', os.path.splitext(path)[1]
    return kind.mime, kind.extension


def check_url_type(image_url, t):
    r = requests.head(image_url)
    return t in r.headers.get("content-type", '')
