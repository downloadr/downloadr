# encoding: utf-8

def get_items(ctx, url, **kwargs):
    resp = ctx.account.get(url, **kwargs)
    items = resp.soup.find_all("item")
    for item in items:
        link = item.find("link")
        if link and not link.text:
            link = link.next_sibling.strip()
        elif link:
            link = link.text.strip()
        else:
            raise ValueError("no link")
        desc = item.find("description").text.split(u"Links:")[0]
        content = item.find("content:encoded")
        title = item.find("title").text
        try:
            thumb = item.find("img")["src"] # just use 1st image
        except TypeError:
            thumb = ""
        yield locals()
        
def get_items_paged(ctx, feedurl):
    if ctx.position >= 2:
        payload = {
            "paged": ctx.position,
        }
        ctx.next = ctx.position + 1
    else:
        payload = {}
        ctx.next = 2
    url = feedurl
    return get_items(ctx, feedurl, params=payload) 