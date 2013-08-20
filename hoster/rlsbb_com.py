# encoding: utf-8
"""
rlsbb_com.py
"""
from bs4 import BeautifulSoup
from ... import hoster

@hoster.host
class this:
    model = hoster.HttpHoster
    name = "rlsbb.com"
    #search = dict(display="thumbs", tags="audio, video, other")    
    patterns = [
        hoster.Matcher('http', '*.rlsbb.com', "!/<name>/").set_tag("entry"),
    ]
    favicon_data = hoster.generate_icon("BB")
    
def on_search(ctx, query, domain="www.rlsbb.com"):
    payload = {
        "s": query,
        "submit": "Find",
        "feed": "rss2",
    }
    url = "http://{}/page/{}".format(domain, str(ctx.position or 1))
    resp = ctx.account.get(url, params=payload)
    items = resp.soup.find_all("item")
    for item in items:
        content = BeautifulSoup(item.find("content:encoded").text)
        description = content.text.split("Links:")[0]
        ctx.add_result(
            url=item.find("link").text,
            title = item.find("title").text,
            description=description,
            thumb=content.find("img").get("src", " "),
        )
    if len(items):
        ctx.next = (ctx.position or 1)+1
    else:
        ctx.next = None