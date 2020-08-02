import base64
import configparser
import glob
import json
import os
import unicodedata

import shortuuid
import encryption
from tinydb import TinyDB


class PVault:
    data_dir = 'data/'
    vault_dir = os.path.join(data_dir, 'vault')
    temp_dir = os.path.join(vault_dir, 'tmp')
    upload_dir = os.path.join(vault_dir, 'uploads')
    cache_path = os.path.join(temp_dir, 'preview_cache')
    default_preview = os.path.join(vault_dir, 'default_preview.jpg')
    db_path = os.path.join(vault_dir, 'db.json')

    def __init__(self, settings_path, user='admin', pwd='admin', email=None, b64str=None):
        if b64str:
            self.b64str = b64str
        elif user and pwd:
            self.user = user
            self.pwd = pwd
            self.b64str = base64.b64encode(bytes('%s:%s' % (user, pwd), 'ascii'))
        else:
            raise ValueError('A user and password must be provided.')

        self.email = email
        self.settings_path = settings_path
        self.db = TinyDB(self.db_path)
        self.elements = self.db.table('elements')
        self.locations = self.db.table('locations')

        self.authorized = False
        self.parse_settings()
        self.secret_key = self.pwd

    def parse_settings(self):
        config = configparser.ConfigParser()
        config.read(self.settings_path)
        self.authorized = config['AUTH']['is_encrypted'] == 'no'

    def save_settings(self):
        config = configparser.ConfigParser()
        config.read(self.settings_path)
        config['AUTH']['is_encrypted'] = 'no' if self.authorized else 'yes'
        with open(self.settings_path, 'w') as configfile:
            config.write(configfile)

    def get_setting(self, section, name):
        config = configparser.ConfigParser()
        config.read(self.settings_path)
        return config.get(section, name)

    def set_setting(self, section, name, value):
        config = configparser.ConfigParser()
        config.read(self.settings_path)
        config.set(section, name, value)
        with open(self.settings_path, 'w') as configfile:
            config.write(configfile)

    def log_in(self, key):
        config = configparser.ConfigParser()
        config.read(self.settings_path)
        self.authorized = key == self.secret_key
        if config['AUTH']['is_encrypted'] == 'yes':
            if self.authorized:
                try:
                    encryption.decrypt(self.vault_dir, self.secret_key)
                except ValueError as e:
                    return str(e)
            self.save_settings()  # autorizado y encriptado no es lo mismo!!!
        return self.authorized

    def log_out(self):
        if self.authorized:
            # si la carpeta esta vacia, el zip tiene tamaño 0 y no se puede desencritar
            encryption.encrypt(self.vault_dir, self.secret_key)
            self.authorized = False
            self.save_settings()

    def add_element(self, elem):
        elem.set_uuid(self.get_uuid())
        self.elements.insert(elem.to_dict())
        elem.location.get_content()
        self.locations.insert(elem.location.to_dict())
        if elem.arch_loc:
            elem.arch_loc.get_content()
            self.locations.insert(elem.arch_loc.to_dict())

        return elem.uuid

    def clear_cache(self):
        files = glob.glob(self.temp_dir + '*')
        for f in files:
            os.remove(f)

    def reload_all_elements(self):
        from VaultLocation import from_loc
        new_elems = []
        print('reloading ALL elements!')
        for e in self.elements.all():
            loc = from_loc(e['location'], e['loc_type'])
            ve = VaultElement(loc, e['name'], e['tags'])
            new_elems.append(ve)
        self.elements.truncate()
        for ne in new_elems:
            self.add_element(ne)

    def get_uuid(self):
        # maybe check if uuid exists (rare)
        return shortuuid.uuid()


class VaultElement:
    def __init__(self, location, arch_loc=None, uuid=None, name=None, tags=None):
        self.location = location
        self.arch_loc = arch_loc
        self.uuid = uuid
        self.name = self.location.name if name is None else name
        self.index_name = remove_diacritics(self.name)
        self.tags = [] if tags is None else tags
        self.v_class = self.location.loc_type
        self.preview = None

    def edit(self, name=None, tags=None, v_class=None):
        self.name = name if name else self.name
        self.tags = tags if tags else self.tags
        self.v_class = v_class if v_class else self.v_class

    def set_uuid(self, u):
        if self.uuid is None:
            self.uuid = u
            self.location.uuid = u
            if self.arch_loc:
                self.arch_loc.uuid = u

    def to_dict(self):
        arch = self.arch_loc.to_dict() if self.arch_loc else {}
        di = {'name': self.name, 'index_name': self.index_name, 'uuid': self.uuid,
              'tags': self.tags, 'v_class': self.v_class,
              'location': self.location.to_dict(), 'arch_loc': arch}
        if self.location.loc_type == 'Web':
            di['archived'] = self.arch_loc is not None
        return di

    def to_json(self, save=False):
        data = json.dumps(self.to_dict())
        if save:
            with open(PVault.data_dir + self.name + '.json', 'w+') as f:
                f.write(data)
                f.close()
        return data


def remove_diacritics(text):
    """
    Returns a string with all diacritics (aka non-spacing marks) removed.
    For example "Héllô" will become "Hello".
    Useful for comparing strings in an accent-insensitive fashion.
    """
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")
