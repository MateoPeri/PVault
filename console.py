import json
import os
import re

from flask import Flask, request, render_template, send_file, redirect, url_for
from tinydb import Query

import VaultLocation
from VaultLocation import FileLocation, WebLocation
from pvault import PVault, VaultElement, remove_diacritics

app = Flask(__name__, static_folder='static', static_url_path='/static')

pv = PVault('data/settings.ini')


@app.route('/')
def index():
    if pv.authorized:
        return render_template('index.html')
    return redirect('login')


@app.route('/get_elems', methods=['POST'])
def get_elems():
    jn = request.get_json(force=True)
    tags_and = False
    n_query = Query()
    t_query = Query()

    q = jn.get('q')
    t = jn.get('t')

    if q is None and t is None:
        elems = pv.elements.all()
        return json.dumps(elems)

    if q is None:
        q = '.+'
    else:
        q = remove_diacritics(q)
    q1 = n_query.index_name.search(q, flags=re.IGNORECASE | re.UNICODE)
    if t is None:
        q2 = t_query.tags.all([])
    else:
        q2 = t_query.tags.all(t) if tags_and else t_query.tags.any(t)

    # elems = pv.elements.all()
    elems = pv.elements.search(q1 & q2)
    return json.dumps(elems)


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/login/auth', methods=['POST'])
def auth():
    key = request.get_json(force=True)
    # key = jn['key']  # maybe encrypt the key or something
    if pv.log_in(key):
        return url_for('index')  # render_template('index.html')
    return 'Unauthorized', 503


@app.route('/logout', methods=['GET'])
def logout():
    pv.log_out()
    return redirect('login')


@app.route('/purge/<table>')
def purge(table):
    if table == 'all':
        pv.db.drop_tables()
        return 'Purged ALL tables'
    pv.db.drop_table(table)
    return 'Purged ' + table


@app.route('/reload_all')
def reload_all():
    pv.reload_all_elements()
    return 'Reloaded ALL!'


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/data/<path:filepath>')
def download_file(filepath):
    path = os.path.join('data', filepath)
    # send_from_directory(pv.data_dir, filename=filepath, as_attachment=True)
    return send_file(path)


@app.route('/edit', methods=['POST'])
def edit():
    jn = request.get_json(force=True)
    uuid = jn['uuid']
    pv.elements.update(jn, Query().uuid == uuid)

    return 'Edited element with uuid ' + uuid


@app.route('/del', methods=['POST'])
def del_elem():
    uuid = request.get_json(force=True)
    pv.elements.remove(Query().uuid == uuid)
    return 'Removed element with uuid ' + uuid


@app.route('/add_url', methods=['POST'])
def add_url():
    di = request.get_json(force=True)
    url = 'https://' + di['elem'].lstrip('https').lstrip('://')

    uuid = pv.get_uuid()
    webloc = WebLocation(url, uuid=uuid)
    arch = None
    if di['archive']:
        arch = VaultLocation.archive_from_web(webloc, fetch=False)

    pv.add_element(VaultElement(webloc, uuid=uuid, arch_loc=arch, name=di["name"], tags=di["tags"]))
    return 'Sucess!'


def save_file(file, data):
    name, ext = os.path.splitext(file.filename)
    # date = datetime.now().astimezone().replace(microsecond=0).isoformat()
    destination = os.path.join(pv.upload_dir, name + ext)
    file.save(destination)
    fl = FileLocation(destination)
    # pv.elements.upsert(VaultElement(fl).to_dict(), Query().location.location == destination)
    return pv.add_element(VaultElement(fl, name=data['name'], tags=data['tags']))


@app.route('/file-upload', methods=['POST'])
def upload_file():
    ids = []
    data = dict(request.form)
    data['tags'] = data['tags'].split(',')
    print(data)
    for file in request.files.getlist("file"):
        ids.append(save_file(file, data))
    if len(ids) == 0:
        return 'no files :/'
    return 'File uploaded!' + ids[0]
    # return url_for('view_file', file_id=ids[0])


if __name__ == '__main__':
    app.run(pv.get_setting('APP', 'url'), pv.get_setting('APP', 'port'), debug=True)
