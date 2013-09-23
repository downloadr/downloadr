# encoding: utf-8

import re, urllib
from dateutil.parser import parse
from datetime import datetime
from ... import hoster

@hoster.host
class this:
    model = hoster.HttpHoster
    name = "torrentz.eu"
    search = dict(display="list", tags="video", empty=True, default_phrase="verifiedP added:3d seeds>1000")    
    patterns = [
        hoster.Matcher('http', '*.'+name, "!/<id>"),
    ]
    config = [
        hoster.cfg("qual", "good", str, enum={"any": "any", "good": "good", "verified": "verified"}, description="Select default group"),
        hoster.cfg("sort", "P", str, enum={"P": "Peers", "S": "Size", "N": "Rating", "A": "Date"}, description="Default sorting by")
    ]

def on_check_http(file, resp):
    args = [("xt", "urn:btih:" + file.pmatch.id)]
    args += [("tr", urllib.quote(i.text.strip())) for i in resp.soup("a", href=re.compile("/tracker.*"))]    
    magnet = "magnet:?" + "&".join("{}={}".format(k, v) for k, v in args)
    return [magnet]

def on_search(ctx, query):
    try:
        t, s, query = re.match("(verified|good|any)?([PSNA])? (.*)", query).groups()
    except AttributeError:
        t = None
        s = None
    t = this.config.qual if not t else t
    if t == "good":
        a = ""
    elif t=="any":
        a = "_any"
    else:
        a = "_verified"
    a += this.config.sort if not s else s
    payload = {
        "q": query,
        "p": ctx.position,
    }
    added = False
    resp = ctx.account.get("http://torrentz.eu/feed"+a, params=payload)
    for item in resp.soup("item"):
        d = parse(item.find("pubdate").text) + (datetime.now() - datetime.utcnow())
        c = item.find("category").text.strip()
        desc = u"{} {} {}".format(d.strftime(u"%d.%m.%y %H:%M"), c, item.find("description").text.strip().split("Hash:")[0])
        ctx.add_result(
            url=item.find("guid").text.strip(),
            title=item.find("title").text.strip(),
            description=desc
        )
        added = True
    if added:
        ctx.next = ctx.position + 1