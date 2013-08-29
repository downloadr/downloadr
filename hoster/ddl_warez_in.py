# encoding: utf-8
"""
ddl_warez_in.py
"""
import re, random
from ... import hoster, container

@hoster.host
class this:
    model = hoster.HttpHoster
    name = "ddl-warez.in"
    search = dict(display="thumbs", tags="video, audio, software, other", empty=True)
    patterns = [
        hoster.Matcher('https?', '*.ddl-warez.in', "!/download/cnl/<id>/").set_tag("cnl"),
        hoster.Matcher('https?', '*.ddl-warez.in', "!/download/cnl/<id>/mirror/<m>/").set_tag("cnl"),
        hoster.Matcher('https?', '*.ddl-warez.in', "!/download/<id>/<name>/"),
    ]
    set_user_agent = True
    config = [
        hoster.cfg("preferred_hoster", "", str, description="type in a preferred hoster mirror"),
    ]
    
def get_mirrors(soup):
    try:
        r = soup.find("tr", id="highspeed_ad").find_next_sibling()
    except AttributeError:
        return
    mirrors = dict()
    while "Fullspeed-Download:" not in r.text:
        try:
            host = hoster.between(r.find("td").text, "(", ")")
        except ValueError:
            break
        try:
            for a in r('a'):
                cnl = a["href"]
                if cnl.startswith("download/cnl/"):
                    mirrors[host] = "http://ddl-warez.in/"+cnl
                    break
        except IndexError:
            pass
        r = r.find_next_sibling()
    return mirrors
    
def unwrap_cnl(file, soup, link):
    captcha = soup.select("form img")[0]["src"]
    def _load():
        data = file.account.get("http://ddl-warez.in/" + captcha)
        return data.content
    for code in file.solve_captcha(message=None, data=_load, mime="image/png"):
        cnl_resp = file.account.post(link, data=dict(captcha=code, sent=1))
        if cnl_resp.soup.find("span", class_="fehler"):
            continue
        else:
            break
    else:
        file.input_aborted()
    
    links = []
    for url in re.findall(r'ajaxGet.\(\"(.*?)\"', cnl_resp.text):
        print "checking url", url
        resp = file.account.get("http://ddl-warez.in/" + url)
        cnl = {x["name"]: x["value"] for x in resp.soup.select("form input")}
        links.extend(container.decrypt_clickandload(cnl))
    print "links are", links
    return links
        
def unwrap(file, link):
    print "unwrapping", link
    return unwrap_cnl(file, file.account.get(link).soup, link)

def on_check_http(file, resp):
    print file.pmatch
    if file.pmatch.tag == "cnl":
        print "cnl link"
        return unwrap_cnl(file, resp.soup, file.url)
    mirrors = get_mirrors(resp.soup)
    if not mirrors:
        file.no_download_link()
    if this.config.preferred_hoster in mirrors:
        return unwrap(file, mirrors[this.config.preferred_hoster])
    title = hoster.between(resp.soup.find("title").text, "// ", " //")
    if file.extra and len(mirrors) > 1:
        if file.extra in mirrors:
            return unwrap(file, mirrors[file.extra])
        # search input
        with hoster.search.Input("title", "list") as add:
            add(title=u"Select hoster for {}:".format(title))
            for h in mirrors:
                add(title=h, url=file.url, extra=h)
        file.delete_after_greenlet()
    else:
        # input? add all for now
        return mirrors.values()

def scrape_rows(ctx, soup):
    rows = soup.select("table.downloads tr")
    if not rows:
        print "no rows"
        return
        
    for r in rows[1:]:
        link = r.find("a")
        thumb = r.find("img")
        if not link:
            continue
        if thumb:
            thumb = thumb.get('src2', thumb.get('src'))
            if not thumb.startswith("http"):
                thumb = "http://ddl-warez.in/"+thumb
        ctx.add_result(title=link.text, 
            thumb=thumb, url="http://ddl-warez.in/" + link["href"], 
            description=r.find("div").text.strip(), extra=True)

def on_search(ctx, query):
    resp = ctx.account.get("http://ddl-warez.in/", 
        params=dict(
            search=query.encode("ISO-8859-1"), 
            kat="", 
            seite=ctx.position or 1,
            sort='A'))
    scrape_rows(ctx, resp.soup)
    current = int(resp.soup.find("td", id="seitenfunktion_aktiv").text)
    pages = [int(i.text) for i in resp.soup.select("table#seitenfunktion td")]
    if current == pages[-1]:
        return
    else:
        ctx.next = current + 1
        
def on_search_empty(ctx):
    resp = ctx.account.get("http://ddl-warez.in/live.php", params=dict(live=random.randint(1000,9999)))
    scrape_rows(ctx, resp.soup)