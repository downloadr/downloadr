# encoding: utf-8
"""
serienjunkies_org.py
"""
from functools import partial
from collections import defaultdict
import bs4, re
import gevent
from gevent import pool
from ... import hoster, container

@hoster.host 
class this:
    model = hoster.HttpHoster
    name = 'serienjunkies.org'
    patterns = [
        hoster.Matcher('https?', name, "!/<descriptor>/<name>/").set_tag("page"),
        hoster.Matcher('https?', 'download.serienjunkies.org', '!/<id>/<name>.html').set_tag("download"),
    ]
    search = dict(display='thumbs', tags="video, other", empty=True)
    favicon_url = "http://serienjunkies.org/media/img/favicon.ico"
    set_user_agent = True
    use_cache = False
    
def download_link(file, retries=5):
    if not retries:
        file.set_infos(name=file.pmatch.name)
        file.input_aborted()
        return
    resp = file.account.get(file.url)
    soup = resp.soup
    form = soup.find("form")
    img = form.find("img")
    if not img or not img.get("src", None):
        return file.no_download_link()
    img = img["src"]
    if img == "/help/nocaptcha/nc.gif":
        return download_link(file, retries=retries-1)
    payload = {x["name"]: x["value"] for x in form.find_all("input")}
    img_resp = file.account.get("http://download.serienjunkies.org" + img)
    for text in file.solve_captcha(message=None, data=img_resp.content, mime=img_resp.headers["content_type"], retries=5):
        payload["c"] = text
        resp = file.account.post(file.url, data=payload)
        form = resp.soup.find("form", attrs={"name": "cnlform"})
        if form is None:
            return download_link(file, retries-1)
        cnl = {x["name"]: x["value"] for x in form("input")}
        links = container.decrypt_clickandload(cnl)
        return links, None, [this.name]

    file.set_infos(name=file.pmatch.name)
    file.input_aborted()
    
def get_children(soup):
    return [c for c in soup.find("div", class_="post-content").children if not isinstance(c, bs4.element.NavigableString)]

def get_mirrors(soup, index):
    hosters = defaultdict(list)
    for c in get_children(soup)[index:]:
        t = c.text
        if "Dauer:" in t and "Format:" in t:
            break
        for mirror in c("a"):
            hoster_name = mirror.next_sibling[3:].strip()
            hosters[hoster_name].append((c.find("strong").text, mirror["href"]))
    return hosters

def new_search_input(name):
    return hoster.search.Input(name, "list", "serienjunkies.org")

def get_title(soup):
    return soup.find("h2").text

def on_check(file):
    p = file.pmatch
    if p.tag == "download":
        return download_link(file)
    else:
        extra = file.extra
        resp = file.account.get(file.url)
        if not extra:
            # scrape sidebar
            seasons = resp.soup.select("div.bkname a")
            if not seasons:
                file.no_download_link()
            with new_search_input(p.descriptor) as add:
                for link in seasons:
                    desc = None if file.url != link["href"] else "selected"
                    add(title=link.text, url=link["href"], extra=-1, description=desc)
        elif extra == -1:
            # quality selection
            with new_search_input(p.name) as add:
                children = get_children(resp.soup)
                for i in children:
                    if i.find("img"):
                        continue
                    t = i.text
                    if "Dauer:" in t and "Format:" in t:
                        continue
                    add(title=get_title(resp.soup), description=i.text)
                    break
                    
                for i, c in enumerate(children):
                    t = c.text
                    if "Dauer:" in t and "Format:" in t:
                        mirrors = get_mirrors(resp.soup, i+1)
                        links = sorted((ls for ls in mirrors.itervalues()), key=lambda k: -len(k))
                        filenames = [name for name, _ in links[0]]
                        hosters = ", ".join(mirrors.keys())
                        desc = u"First file: {} | Last file: {} | Mirrors: {}".format(filenames[0], filenames[-1], hosters)
                        add(title=t, 
                            description=desc,
                            url=file.url, extra=i+1)
                        
        elif isinstance(extra, int) and extra > 0:
            # hoster selection
            hosters = get_mirrors(resp.soup, extra)
            print "index is", extra, hosters.keys()
            print "hosters", hosters
            with new_search_input(p.name + " Hoster:") as add:
                add(title=u"Select Hoster for " + get_title(resp.soup), description="Found {} different mirrors, {} links.".format(len(hosters), max(len(i) for i in hosters.itervalues())))
                for i in hosters:
                    add(title=i, description="{} Links".format(len(hosters[i])), url=file.url, extra=[extra, i, False])

        elif isinstance(extra, list):
            # episode selection
            index, hoster_name, download = extra
            print "index is", index, "hostername", hoster_name
            hosters = get_mirrors(resp.soup, index)
            links = hosters[hoster_name]
            print len(links)
            print links
            if download:
                # download all links
                return [i[1] for i in links], p.name
            with new_search_input(p.name + " Hoster: "+hoster_name) as add:
                add(title=u"Download all of: " + get_title(resp.soup),
                    description="you have to type captchas for every link", 
                    url=file.url, 
                    extra=[index, hoster_name, True])
                for filename, link in links:
                    add(title=filename, description=hoster_name, url=link)
        else:
            file.file_offline()
        file.delete_after_greenlet()

def _load(ctx, (cat, name), retry=3):
    if not retry:
        return
    if cat.startswith("http"):
        url = cat
        params = None
    else:
        url = "http://{}/".format(this.name)
        params = dict(cat=cat)
    resp = ctx.account.get(url, params=params, use_cache=True)
    if resp.status_code == 503:
        gevent.sleep(0.1)
        return _load(ctx, (cat, name), retry-1)
    d = dict(url=resp.url, title=name)
    for i in get_children(resp.soup):
        if i.find("img"):
            d["thumb"] = i.find("img")["src"]
            continue
        t = i.text
        if u"Dauer:" in t or u"Format:" in t:
            continue
        d["description"] = t
        return d

def on_search(ctx, query):
    resp = ctx.account.post("http://{}/media/ajax/search/search.php".format(this.name), data={"string": query})
    for d in pool.IMap.spawn(partial(_load, ctx), resp.json(), pool.Pool(5).spawn):
        if not d: continue
        ctx.add_result(**d)

def on_search_empty(ctx):
    resp = ctx.account.get("http://serienjunkies.org/xml/feeds/{}.xml".format("episoden"), use_cache=True)
    max_crawl = 10
    ctx.next = ctx.position+max_crawl
    all_items = re.findall("<item>.*?<title>(.*?)</title>.*?<pubDate>(.*?)</pubDate>.*?<link>(.*?)</link>.*?</item>", resp.text, re.DOTALL)[ctx.position:]
    items = dict()
    for name, pub, link in all_items:
        name = u"{} Released: {}".format(name, pub)
        items[link] = name
        if len(items) >= max_crawl:
            break
    
    for d in pool.IMap.spawn(partial(_load, ctx), items.iteritems(), pool.Pool(5).spawn):
        if not d:
            continue
        ctx.add_result(**d)