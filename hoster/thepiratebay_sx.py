# encoding: utf-8
"""
thepiratebay_sx.py
"""
from ... import hoster

@hoster.host
class this:
    model = hoster.HttpHoster
    name = "thepiratebay.sx"
    search = dict(display="list", tags="audio, video, software, porn, other")
    patterns = [
        hoster.Matcher('https?', '*.thepiratebay.sx', "!/torrent/<id>/<name>"),
    ]
    
def load_icon(hostname):
    img = hoster.get_image("http://thepiratebay.sx/static/img/tpblogo_sm_ny.gif").convert("RGBA")
    pixaccess = img.load()
    transform_pixel = pixaccess[0,0]
    transparent_pixel = (255, 255, 255, 0)
    for y in xrange(img.size[1]):
        for x in xrange(img.size[0]):
            if pixaccess[x,y] == transform_pixel:
                pixaccess[x,y] = transparent_pixel
    return img

def on_check_http(file, resp):
    try:
        return [resp.soup.find("a", title="Get this torrent")["href"]]
    except TypeError:
        file.no_download_link()

def on_search(ctx, query):
    url = "http://thepiratebay.sx/search/{}/{}/99/0".format(query.encode("utf-8"), ctx.position)
    resp = ctx.account.get(url)
    table = resp.soup.find("table")
    if not table:
        return
    rows = table.find_all("tr", class_=None)
    for row in rows:
        link = row.find("a", title="Download this torrent using magnet")
        if link is None:
            continue
        ctx.add_result(
            url=link["href"],
            title=row.find("a", class_="detLink").text,
            description=row.find("font").text.split(", ULed")[0],
        )
    
    if resp.soup.find("img", alt="Next"):
        ctx.next = ctx.position + 1
    else:
        ctx.next = None