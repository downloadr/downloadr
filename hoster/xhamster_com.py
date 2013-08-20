# encoding: utf-8
import re
from ... import hoster

@hoster.host
class this:
    model = hoster.HttpHoster
    name = "xhamster.com"
    can_resume_free = True
    max_chunks_free = 3
    patterns = [
        hoster.Matcher('https?', "*.xhamster.com", "!/movies/<id>/<name>.html")
    ]
    search = dict(display='thumbs', tags="adult")

def on_check_http(file, resp):
    filename = resp.soup.find("title").text
    filename = filename[:filename.find(" - ")] + ".flv"
    runtime = re.search(r"\<span\>Runtime\:\<\/span\> (.*?)\<\/div\>", resp.text)
    if runtime:
        runtime = runtime.group(1)
    else:
        file.no_download_link()
    size = re.search(r"Download video \((.*?)\)", resp.text)
    if size:
        approx_size = size.group(1).upper()
    else:
        approx_size = 0
    file._check_resp = resp
    file.set_infos(approx_size=approx_size, name=filename)
    
def on_download(chunk):
    resp = chunk.account.get(chunk.url)
    url = re.search(r"\'srv\'\: \'(.*?)\'.*?\'file\'\: \'(.*?)\'\,", resp.text, re.DOTALL)
    if not url:
        chunk.no_download_link()
    server, f = url.groups()
    if f.startswith("http"):
        return f
    else:
        return "{}/key={}".format(server, f)

def on_search(ctx, query):
    payload = {
        "q": query,
        "qcat": "video",
        "page": ctx.position or 1
    }
    resp = ctx.account.get("http://xhamster.com/search.php", params=payload)
    for n in resp.soup("div", attrs={"class": "video"}):
        ctx.add_result(title=n.find("u")["title"],
            url=n.find("a")["href"],
            thumb=n.find("img")["src"],
            duration=n.find("b").text, description=" ")
    try:
        ctx.next = int(resp.soup.find("a", attrs={"class": "last"})["href"].rsplit("=", 1)[1])
    except (ValueError, TypeError):
        ctx.next = None
    