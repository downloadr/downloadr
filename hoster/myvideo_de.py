# -*- coding: utf-8 -*-

import re

from ... import hoster, javascript

@hoster.host
class this:
    model = hoster.HttpHoster
    name = 'myvideo.de'
    search = dict(display='thumbs', tags='video', default_phrase="")
    patterns = [
        hoster.Matcher("https?", "*.myvideo.de", "!/watch/<id>/<name>").set_tag("de"),
        hoster.Matcher("https?", "*.myvideo.de", "!/watch/<id>").set_tag("de"),
    ]
    favicon_url = "http://network.myvideo.de/include/images/favicon/mv_favicon.ico"

def get_download_url(ctx, soup):
    thumburl = soup.find("meta", attrs=dict(property='og:image'))
    if not thumburl:
        print "no thumburl found"
        ctx.no_download_link()
    m = re.search("http://(.*?)/(.*?)/movie(.*?)/(.*?)/thumbs/(.*?)_", thumburl["content"])
    if not m:
        print "cannot match thumburl"
        ctx.no_download_link()
    return "http://{}/{}/movie{}/{}/{}.flv".format(*m.groups())
    
def on_check_http(file, resp):
    name = resp.soup.find("h1")
    if not name:
        print "name not found"
        file.no_download_link()
    hoster.check_download_url(file, get_download_url(file, resp.soup), name=name.text+".flv")

def on_download(chunk):
    resp = chunk.account.get(chunk.url)
    return get_download_url(chunk, resp.soup)

def on_search(ctx, query):
    params = dict(
        method="myvideo.videos.list_by_fulltext",
        dev_id="ead7a5f93c8b1ff4d22b86a3417f0460",
        website_id="0dd81e30cce2cf1da399f386d538e978",
        per_page=20,
        page=ctx.position,
        searchphrase=query,
        o_format="json")
    resp = ctx.account.get('https://api.myvideo.de/prod/mobile/api2_rest.php', params=params, referer='https://local.download.am')
    try:
        j = resp.json()
    except ValueError:
        print "json error"
        j = javascript.loads(resp.content) # they seem to deliver wrong json sometimes?
    try:
        for id, r in j['response']['myvideo']['movie_list']['movie'].iteritems():
            ctx.add_result(url='http://www.myvideo.de/watch/{}'.format(id), title=hoster.htmlunescape(r['movie_title'] or ''), thumb=r['movie_thumbnail'], duration=r['movie_length'])
    except KeyError:
        ctx.next = None
        
    if len(ctx.results) >= 20:
        ctx.next = ctx.position + 1
