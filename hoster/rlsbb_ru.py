# encoding: utf-8
"""
rlsbb_ru.py
"""
import re
from ... import hoster, core

@hoster.host
class this:
    model = hoster.HttpHoster
    name = "rlsbb.ru"
    search = dict(display="thumbs", tags="audio, video, other", empty=True)    
    patterns = [
        hoster.Matcher('http', '*.rlsbb.ru', "!/<name>/").set_tag("entry"),
    ]
    favicon_data = hoster.generate_icon("BB")
    config = [
        hoster.cfg("feed_category", "tv-shows", str, description="Default feed for start page. For example `movies`. Leave empty for all.")
    ]
    
def on_check_http(file, resp):
    title = resp.soup.find("h3", class_="postTitle").text.strip()
    item = resp.soup.find("div", class_="postContent")
    added = 0
    for quality, links in scrape_links(item).iteritems():
        added += len(core.add_links([i[1] for i in links], u"{}{}".format(quality, title)))
    if not added:
        file.no_download_link()
    else:
        file.delete_after_greenlet()

def have_plugin(url):
    try:
        h = hoster.find(url)[0]
    except ValueError:
        return False
    return h.name != "http"

def scrape_links(item):
    ret = {}
    for p in item("p"):
        quality = None
        try:
            quality = p.find("br").next_siblings
            quality_text = quality.next().strip().rsplit("|", 1)[0]
            if not quality_text:
                continue
        except AttributeError:
            continue
        l = []
        for i in quality:
            t = re.search(r'href\=\"(.*?)\">(.*?)</a>', unicode(i))
            if t and t.group(2).lower() != "torrent search":
                l.append((t.group(2).lower(), t.group(1)))
        if l:
            ret[quality_text] = l
    if not ret:
        return {"": [(a.text, a["href"]) for a in item("a") if a.get("href") and have_plugin(a["href"])]}
    return ret

def on_search(ctx, query):
    from .external_downloadr_wordpress import get_items_paged
    if query:
        url = "http://www.rlsbb.ru/search/{}/feed/".format(query)
    else:
        if this.config.get("feed_category"):
            feed = "category/" + this.config.feed_category.strip("/ ") + "/"
        else:
            feed = ""
        url = "http://www.rlsbb.ru/{}feed/".format(feed)
        
    for item in get_items_paged(ctx, url):
        con = item["content"]
        links = scrape_links(con)
        desc = ""
        for i in links:
            desc += u"{} on: {}\n".format(i, u", ".join(i[0].lower() for i in links[i]))
        desc += u"\n" + con("p")[1].text.strip()
        ctx.add_result(
            url=item["link"],
            title=item["title"],
            description=desc,
            thumb=item["thumb"],
        )

def on_search_empty(ctx):
    return on_search(ctx, "")