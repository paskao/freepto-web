from flask import Flask, render_template, Response
from flask.ext.bootstrap import Bootstrap
import re
import requests
import logging
import functools
from collections import OrderedDict
log = logging.getLogger('freepto-web')

from discovery import lang_dirs

app = Flask(__name__)
app.config['DEBUG'] = True
Bootstrap(app)


@app.route('/')
def index():
    return render('it', 'index')


@app.route('/<lang>/')
def page_index(lang):
    return render(lang, 'index')


@app.route('/<lang>/<title>/')
def page(lang, title):
    return render(lang, title)


@app.route('/.htaccess')
def htaccess():
    DEFAULT = 'en'
    return Response(
        render_template('htaccess.html',
                        languages=[(l, l) for l in lang_dirs if l != DEFAULT],
                        default_dir=DEFAULT
                        ), content_type='application/octet-stream')


def render(lang, title):
    template = "%s/%s.html" % (lang, title)
    return render_template(template)


def memoize(obj):
    '''decorator to memoize things'''
    cache = obj.cache = {}

    @functools.wraps(obj)
    def memoizer(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in cache:
            cache[key] = obj(*args, **kwargs)
        return cache[key]
    return memoizer


@memoize
def get_images_data():
    log.info('getting images...')
    base_url = 'http://download.freepto.mx/latest/'

    latest = requests.get(base_url)
    if latest.status_code != 200:
        raise Exception('Can\'t download http://download.freepto.mx/latest/')

    latest_text = latest.text.replace('\n', '')
    locales = [l.strip('/') for l in
               re.findall('(freepto-v[^/]*/)', latest_text)]
    locales.sort()

    images_data = OrderedDict()
    for locale in locales:
        sha512_url = '{base}/{locale}/{locale}.img.sha512sum.txt'.format(
            base=base_url, locale=locale)
        sha512 = requests.get(sha512_url)
        if sha512.status_code != 200:
            raise Exception('Can\'t download %s' % sha512_url)

        images_data[locale] = {
            'http_download': '%s%s/%s.img' % (base_url, locale, locale),
            'torrent_download': '%s%s/%s.torrent' % (base_url, locale, locale),
            'sha512': sha512.text.split()[0],
            'sha512sig': sha512_url + '.asc'
        }
    return images_data

app.jinja_env.globals.update(get_images_data=get_images_data)
