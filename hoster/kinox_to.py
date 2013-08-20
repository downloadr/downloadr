# encoding: utf-8
"""
kinox_to.py
"""
import traceback
from functools import partial
from ... import hoster, javascript, core
from gevent import pool
from bs4 import BeautifulSoup
 
@hoster.host
class this:
    model = hoster.HttpHoster
    name = "kinox.to"
    search = dict(display="thumbs", tags="video")
    patterns = [
                hoster.Matcher('http?', '*.kinox.to', "!/Stream/<name>.html")
                ]
    favicon_url = "http://kinox.to/gr/favicon.ico"
    set_user_agent = True
    use_cache = False
    
def mirrors_ul(ul):
    return [i["rel"] for i in ul("li")]
    
def mirrors_page(file, soup):
    mirrors = soup.find("ul", id="HosterList")
    if not mirrors:
        return False
    return mirrors_ul(mirrors)

def get_link(file, rel):
    data = file.account.get("http://kinox.to/aGET/Mirror/"+rel)
    data.raise_for_status()
    ret = data.json()
    soup = BeautifulSoup(ret["Stream"])
    link = soup.find("a")["href"]
    print "got link lol", link
    if link.startswith("/Out/?s="):
        link = link[8:]
    return link
    
def solve_mirrors(file, soup):
    ul = soup.find("ul", id="HosterList")
    return list(pool.IMapUnordered.spawn(partial(get_link, file), mirrors_ul(ul), pool.Pool(5).spawn))
    
def mirrors_by_episode(file, rel, season, episode):
    data = file.account.get("http://kinox.to/aGET/MirrorByEpisode/{}&Season={}&Episode={}".format(rel, season, episode))
    return solve_mirrors(file, data.soup)

def on_check(file):
    if file.extra:
        extra = file.extra
        if extra.get("episodes"):
            title = "{title}, Staffel {season}".format(**extra)
            with hoster.search.Input(title, "list", this.name) as add:
                add(title="<- Alle laden, {title}, Staffel {season}, Episodenauswahl:".format(**extra), 
                    url=file.url, extra=dict(title=title, rel=extra["rel"], season=extra["season"], episode=extra["episodes"]))
                for i in extra["episodes"]:
                    add(title="Episode {}".format(i),
                        url=file.url, extra=dict(title=title, rel=extra["rel"], season=extra["season"], episode=[i]),
                    )
            file.delete_after_greenlet()
            return
        elif extra.get("episode"):
            count = 0
            print "Adding Episodes:", extra["episode"]
            for epi in extra["episode"]:
                print epi
                print "adding links"
                try:
                    count += len(core.add_links(mirrors_by_episode(file, extra["rel"], extra["season"], epi),
                                            "{} Episode {}".format(extra["title"], epi),
                                            ignore_plugins=["http"]))
                except:
                    print "error adding links"
                    traceback.print_exc()
            if not count:
                file.no_download_link()
            else:
                file.delete_after_greenlet()
            
    resp = file.account.get(file.url)
    try:
        title = resp.soup.find("div", class_="ModuleHead mHead").find("h1").text
    except AttributeError:
        resp = anti_check(file, resp)
        title = resp.soup.find("div", class_="ModuleHead mHead").find("h1").text
    
    seasonselect =  resp.soup.find("select", id="SeasonSelection")
    if seasonselect:
        with hoster.search.Input(title, "list", this.name) as add:
            add(title="{}, Staffelauswahl:".format(title))
            for season in seasonselect("option"):
                extra = {
                    "episodes": season["rel"].split(","),
                    "season": season["value"],
                    "title": title,
                    "rel": seasonselect["rel"],
                }
                add(title=season.text, url=hoster.add_extra(file.url, extra))
        file.delete_after_greenlet()
        return
    
    return dict(links=solve_mirrors(file, resp.soup), ignore_plugins=["http"])
    
def anti_check(file, resp):
    js = resp.soup.find("script").text.rsplit(";", 2)[0].replace("window.location.href=", "")
    return file.account.get("http://kinox.to"+javascript.execute(js))


_langmap = {
    '1':'DE',
    '2':'EN',
    '4':'CN',
    '5':'ESP',
}

def _load(ctx, row):
    link = row.find("a")
    if link is None:
        return
    resp = ctx.account.get("http://kinox.to" + link["href"])
    image = resp.soup.find("div", class_="Grahpics").find("img")
    try:
        language = hoster.between(row.find('img', height=11)['src'], '/lng/', '.png')
        language = "[{}] ".format(_langmap[language])
    except (ValueError, AttributeError, KeyError):
        language = ""
    ctx.add_result(
        url = u"http://kinox.to" + link["href"],
        title = language.decode("ascii") + row.find("a").text,
        description = resp.soup.find("div", class_="Descriptore").text,
        thumb = image["src"]
    )

def on_search(ctx, query):
    resp = ctx.account.get('http://kinox.to/Search.html', params=dict(q=query))
    table = resp.soup.find("table")
    if not table:
        print resp.content
        if resp.content.startswith("<html><head>"):
            resp = anti_check(ctx, resp)
            table = resp.soup.find("table")
        if not table:
            print "table not found"
            print resp.content
            return
   
    rows = table.find_all("tr", class_=None)
    p = pool.Pool(20)
    for row in rows:
        p.spawn(_load, ctx, row)
    p.join()
