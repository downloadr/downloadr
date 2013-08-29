# encoding: utf-8
"""
mov_world_net.py
"""
import json
import io

from PIL import Image

from ... import hoster, container, core
from ...javascript import PyV8


@hoster.host
class this:
    model = hoster.HttpHoster
    name = "mov-world.net"
    search = dict(display="list", tags="video, other", empty=True)
    patterns = [
    hoster.Matcher('https?', '*.mov-world.net', "!/<cat>/<sub>/<names>/<name>-<id>.html"),
        hoster.Matcher('https?', '*.mov-world.net', "!/<cat>/<sub>/<name>-<id>.html"),
        hoster.Matcher('https?', '*.mov-world.net', "!/<cat>/<name>-<id>.html"),
    ]
    set_user_agent = True

def get_image(file, url):
    data = file.account.get("http://{}{}".format(this.name, url))
    if not data.headers["Content-Type"].startswith("image"):
        file.no_download_link()
    data = Image.open(io.BytesIO(data.content))
    data = data.resize((data.size[0]*2, data.size[1]*2), Image.ANTIALIAS)
    output = io.BytesIO()
    data.save(output, "PNG")
    return output.getvalue()

def on_check_http(file, resp):
    title = resp.soup.find("title").text
    form = resp.soup.find("form", action="")
    if not form:
        file.no_download_link()
    _, form = hoster.serialize_html_form(form)
    img = resp.soup.find("img", alt="Captcha")
    if not img:
        file.no_download_link()
    for text in file.solve_captcha(message=None, data=get_image(file, img["src"]), mime="image/png"):
        form["code"] = text.lower()
        resp2 = file.account.get(file.url + "?mirror={mirror}&data={data}&code={code}&uid={uid}".format(**form))
        if resp2.headers["content-type"] != "application/json":
            file.no_download_link()
            return
        data = resp2.json()
        if not "cnl" in data:
            if data.get("message", "").startswith("Der Sicherheits Code"):
                continue
            else:
                file.fatal(data.get("message", "error"))
        if "error" in data:
            file.fatal(repr(data["error"]))
            return
        cnl = json.loads(decode(data["cnl"]))
        for hostname, cnldata in cnl.iteritems():
            links = container.decrypt_clickandload(cnldata)
            core.add_links(links, title + " - " + hostname, cnldata.get("passwords"))
        break
    else:
        file.input_aborted()
    
    file.delete_after_greenlet()

def on_search(ctx, query):
    payload = {
        "q": query,
        "p": ctx.position or 1
    }
    resp = ctx.account.get("http://{}/".format(this.name), params=payload)
    rows = []
    for rows in resp.soup.find_all("tr", class_="even"):
        link = rows.find("a")
        if not link:
            continue
        ctx.add_result(url="http://{}{}".format(this.name, link["href"]), title=link.text)
    
    try:
        page = resp.soup.find("p", class_="navigation").find("a", class_="selected").text
    except AttributeError:
        return
    else:
        if page == "Letzte":
            return
        elif page == "Erste":
            ctx.next = 2
        else:
            ctx.next = int(page) + 1

def _g(x, t):
    try:
        return t.find("a")[t]
    except AttributeError:
        return ""

def _scrape_cat(li):
    if li == "\n":
        return None, None
    catname = li.find("a").text
    if catname in {"XXX", "Musik", "Programme"}:
        return None, None
    return catname, [(u"http://{}{}".format(this.name, lii.find("a")["href"]), lii.find("a")["title"], lii.text) for lii in li("li")]
            
def on_search_empty(ctx):
    resp = ctx.account.get("http://mov-world.net/news/index.html")
    li = resp.soup.find("div", class_="update").find("ul").find("li")
    cat, res = _scrape_cat(li)
    for li in li.next_siblings:
        cat, results = _scrape_cat(li)
        if not cat:
            continue
        for url, filename, title in results:
            t, title = title.split(" ", 1)
            ctx.add_result(url=url, title=title, description=u"{} - {} - {}".format(t.strip("[]"), filename, cat))
            

# reimplement in python?
# copied from browser cache
script = """
function LZW_decompress (a) {
    for (var b = [], dict_count = 256, bits = 8, rest = 0, rest_length = 0, i = 0; i < a.length; i++) {
        rest = (rest << 8) + a.charCodeAt(i);
        rest_length += 8;
        if (rest_length >= bits) {
            rest_length -= bits;
            b.push(rest >> rest_length);
            rest &= (1 << rest_length) - 1;
            dict_count++;
            if (dict_count >> bits) {
                bits++
            }
        }
    };
    for (var c = [], i = 0; i <= 255; i++) {
        c.push(String.fromCharCode(i))
    };
    for (var d = [], element = null, word = '', i = 0; i < b.length; i++) {
        element = c[b[i]];
        if (element == undefined) {
            element = word + word.charAt(0)
        };
        d.push(element);
        if (i) {
            c.push(word + element.charAt(0))
        };
        word = element
    };
    return (d.join(''))
}

var b64Chr = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";
var b64Dec = [];
for (var i = 0, n = 0; i <= 255; i++) {
    if ((n = b64Chr.indexOf(String.fromCharCode(i))) === (-1)) {
        b64Dec[i] = 0
    } else {
        b64Dec[i] = n
    }
}

function base64_decode(a) {
    for (var b = [], i = 0, chr1, chr2, chr3, enc1, enc2, enc3, enc4; i < a.length; i += 4) {
        enc1 = b64Dec[a.charCodeAt(i + 0)];
        enc2 = b64Dec[a.charCodeAt(i + 1)];
        enc3 = b64Dec[a.charCodeAt(i + 2)];
        enc4 = b64Dec[a.charCodeAt(i + 3)];
        b.push((enc1 << 2) | (enc2 >> 4));
        if (enc3 !== 64) {
            b.push(((enc2 & 15) << 4) | (enc3 >> 2))
        };
        if (enc4 !== 64) {
            b.push(((enc3 & 3) << 6) | enc4)
        }
    };
    return (String.fromCharCode.apply(null, b))
}
"""

javascript = None

def decode(s, retry=5):
    global javascript
    if not retry:
        raise RuntimeError("Could not decode")
    if javascript is None:
        javascript = PyV8.JSContext()
        javascript.enter()
        javascript.eval(script)
    try:
        return javascript.eval('LZW_decompress(base64_decode("{}"));'.format(s))
    except:
        javascript = None
        return decode(s, retry-1)