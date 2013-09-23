# encoding: utf-8
"""
adultbay_org.py
"""
from ... import hoster, core

@hoster.host
class this:
    model = hoster.HttpHoster
    name = "adultbay.org"
    search = dict(display="thumbs", tags="adult", empty=True)    
    patterns = [
        hoster.Matcher('http', '*.'+name, "!/<name>/").set_tag("entry"),
    ]
    
def load_icon(hostname):
    img = hoster.get_image("http://adultbay.org/wp-content/themes/o2/images/tab11.png")
    return img.crop((20, 0, 105, 85))

def on_check_http(file, resp):
    core.add_links([link["href"] for link in resp.soup.select("div.entry p a") if link.get("rel")], ignore_plugins=["http", "adultbay.org"])
    file.delete_after_greenlet()
    
def on_search(ctx, query):
    from .external_downloadr_wordpress import get_items_paged
    url = "http://{}/search/{}/feed/"
    for item in get_items_paged(ctx, url):
        ctx.add_result(
            url = item["link"],
            title = item["title"],
            description = item["content"].find("p").text.strip(),
            thumb = item["thumb"]
        )

def on_search_empty(ctx):
    from .external_downloadr_wordpress import get_items_paged
    url = "http://{}/feed/".format(this.name) 
    for item in get_items_paged(ctx, url):
        ctx.add_result(
            url = item["link"],
            title = item["title"],
            description = item["content"].find("p").text.strip(),
            thumb = item["thumb"]
        )