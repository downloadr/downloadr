# encoding: utf-8
"""
beemp3_com.py
"""
from ... import hoster
from bs4 import BeautifulSoup

@hoster.host
class this:
    model = hoster.HttpHoster
    name = "beemp3.com"
    #search = dict(display="list", tags="audio")
    patterns = [
        hoster.Matcher('https?', '*.beemp3.com', "!/download.php", song="name", file="id"),
    ]
    max_files = 1
    set_user_agent = True

def on_check_http(file, resp):
    soup = resp.soup
    try:
        filename = soup.find("h1", class_="h1-title-sing").text
        approx_size = soup.find("b", itemprop="contentSize").text
    except AttributeError:
        file.no_download_link()
    else:
        link = dict(name=filename, approx_size=approx_size)
    try:
        show_url = hoster.between(resp.text, u"show_url('", u"')")
    except ValueError:
        pass
    else:
        link["url"] = show_url
        return [link]
    
    captcha_html = hoster.between(resp.text, u"document.getElementById(\"cod_ck\").innerHTML='", "';")
    captcha_soup = BeautifulSoup(captcha_html)
    captcha = captcha_soup.find("img", id="image_c")
    print "captcha:", captcha
    if not captcha:
        file.no_download_link()
    image = file.account.get("http://beemp3.com/" + captcha["src"])
    for code in file.solve_captcha(message="Calculate:", data=image.content, mime=image.headers["Content-Type"]):
        data = file.account.get("http://beemp3.com/chk_cd.php", params=dict(id=file.pmatch.id, code=code))
        data.raise_for_status()
        data = data.content
        if not data.startswith("Done"):
            continue
        link["url"] = data[data.find("http"):]
        return [link]
    else:
        file.input_aborted()
            
def on_search(ctx, query):
    resp = ctx.account.get("http://beemp3.com/index.php", params=dict(q=query, st="all", page=ctx.position or 1))
    soup = resp.soup
    table = soup.find("ol", class_="results-list")
    if not table:
        return
    rows = table.find_all("li")
    for row in rows:
        try:
            name = row.find("div", class_="file-name").find("a")
            ctx.add_result(
                url = u"http://beemp3.com/" + name["href"],
                title = name.text.split("File name:")[1].strip(),
                description = " ".join(i.text for i in row.find_all("div", class_="line"))
            )
        except:
            import traceback
            traceback.print_exc()
            continue
            
    pagebar = soup.find("div", class_="pagebar")
    links = [i.text for i in pagebar.find_all("a")]
    active = pagebar.find("a", class_="active").text
    last = links[-1]
    if last == active:
        return
    else:
        ctx.next = int(active) + 1