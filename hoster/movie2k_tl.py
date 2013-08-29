# encoding: utf-8
"""
movie2k_tl.py
"""
import re
from ... import hoster

@hoster.host
class this:
    model = hoster.HttpHoster
    name = "movie2k.tl"
    search = dict(display="thumbs", tags="other", empty=True)
    favicon_data = hoster.generate_icon("2K")
    patterns = [
        hoster.Matcher('https?', '*.movie2k.*', "!/<name>-<id>-online-film.html"),
    ]
    config = [
        hoster.cfg("add_mirrors", True, bool, description="Add mirrors"),
        hoster.cfg("ask_mirrors", True, bool, description="Ask if you want to add mirrors")
    ]

def on_check_http(file, resp):
    extra = file.extra
    add_mirrors = this.config.add_mirrors
    if not extra:
        if this.config.ask_mirrors:
            remember, result = file.input_remember_boolean("Add Mirrors for movie2k link?")
            print "INPUT:", remember, result
            if remember:
                with hoster.transaction:
                    this.config["add_mirrors"] = result
                    this.config["ask_mirrors"] = False
            add_mirrors = result
    else:
        add_mirrors = False
    
    if add_mirrors or (extra and extra.get("add_all")):
        return dict(links=[hoster.add_extra(i.find("a")["href"], dict(add_all=False)) for i in resp.soup("tr", id="tablemoviesindex2")], ignore_plugins=["http"])
    else:
        element = resp.soup.find("div", id="help1").next_sibling.next_sibling.next_sibling
        url = element.get("href", element.get("src"))
        return dict(links=[url], ignore_plugins=["http"])
        
def on_search(ctx, query):
    payload = {
        "searchquery": query,
    }
    url = "http://www.movie2k.tl/search"
    resp= ctx.account.post(url, data=payload)
    items = resp.soup.find("tbody")
    if items:
        items = items.find_all("tr")
    else:
        return
    for item in items:
        coverid = item["id"]
        tds = item.find_all("td")
        a = tds[0].find("a")
        title = a.text
        url = a.url
        thumb = re.search(r"""\#{}.*?append\(\".*?src\=\'(.*?)\'""".format(coverid), resp.content, re.DOTALL)
        if thumb:
            thumb = thumb.group(1)
        else:
            thumb = None
        ctx.add_result(
            url=item.find("a")["href"],
            title = title,
            thumb=thumb,
            extra=dict(add_all=True)
        )
        
def on_search_empty(ctx):
    resp = ctx.account.get("http://www.movie2k.tl/")
    images = resp.soup.select("div#maincontent a img")
    for i in images:
        ctx.add_result(
            url=i.parent["href"],
            title=i["title"].replace(" kostenlos", ""),
            thumb=i["src"],
            extra=dict(add_all=True),
        )