"""The module's templates have nothing a strict Content Security Policy blocks, so its
pages work in any project that installs it.

The policy checked is capy-project's (config/settings/security.py), the strictest a
module meets: scripts and styles only from the project's own site, or inline with the
page's nonce; images from the site or data: URLs; no frames, video, audio, objects or
manifests; forms post and pings go only to the site. So these are blocked:
- inline <script> and <style> without the page's nonce. A script with a src and code
  inside is reported too: browsers skip that code, but a conditional src would run it.
- style="..." attributes and on...= attributes (onclick and the like)
- javascript: URLs
- loading from another site, or from a data: URL (except images and icons). A nonce
  doesn't excuse a script from another site: modules load everything from the project.
- frames, video, audio, objects, embeds and manifests

Checked: the module's HTML, SVG, XML and Jinja templates (TEMPLATE_SUFFIXES) under
templates/ and jinja2/, except HTML emails in templates/<package>/emails/ and
jinja2/<package>/emails/ (emails aren't web pages, so the site's policy doesn't apply
to them).

This is a safety net that reads template source, not a browser. It can't see CSS and
JavaScript files, what inline code loads, what template variables hold, a block a
project's template fills in, HTML built in Python, code that needs eval (htmx's hx-on,
Alpine's x-on), or markup opened in one {% if %} branch and closed in another (except
<script> and <style>). It reports an absolute URL to the project's own site as another
site, and a nonce'd script whose code contains the text "<script" or "<style" (it can't
tell that text from a tag opened in another branch). The project's own CSP is what
finally blocks these in a browser.

Each template is read the way a browser reads the page Django renders: Django's
template code first (a tag, variable or comment counts only if it fits on one line, as
in Django's lexer; one that spans lines is printed as text), then the HTML, with
Python's own HTML parser.
"""

import re
from html.parser import HTMLParser
from pathlib import Path
from typing import NamedTuple

import pytest
from django.apps import apps

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
TEMPLATE_FOLDERS = ("templates", "jinja2")
TEMPLATE_SUFFIXES = {
    ".html", ".htm", ".xhtml", ".djhtml", ".svg", ".xml", ".jinja", ".jinja2", ".j2",
}  # fmt: skip
EMAILS_FOLDER = "emails"

# --- Django's template code ------------------------------------------------------------
# One piece of template code: a {% tag %}, a {{ variable }} or a {# comment #}.
TEMPLATE_CODE = re.compile(r"\{%.*?%\}|\{\{.*?\}\}|\{#.*?#\}")
# Blocks whose content isn't template code: {% comment %}, {% verbatim %} (which may be
# named, {% verbatim js %}...{% endverbatim js %}) and Jinja's {% raw %}.
BLOCK_START = re.compile(r"\{%-?[ \t]*(comment|verbatim|raw)\b[ \t]*([\w-]*)")
# The page's nonce, as Django provides it (Jinja spelling too).
NONCE_VARIABLE = re.compile(r"\{\{-?[ \t]*csp_nonce[ \t]*-?\}\}")
NONCE_TAG = re.compile(r"\{%-?[ \t]*csp_nonce_attr[ \t]*-?%\}")
NONCE = "\x00nonce\x00"  # marks the real nonce; a template can't contain it
QUOTED_STRING = re.compile(r"\"([^\"]*)\"|'([^']*)'")
# Stands in for other template code: the Unicode "object replacement character", which
# never appears in a template. Strings kept from the code sit between two of them.
PLACEHOLDER = "\ufffc"
OUTPUT = "output"  # what printing template code without a quoted string prints
TAG_NAME = "tpl"  # stands in for a tag name that template code prints
HTML_SPECIAL = re.compile(r"[<>\"'\s]")
# Template tags that print nothing themselves.
STRUCTURAL_TAGS = {
    "if", "elif", "else", "endif", "for", "empty", "endfor", "with", "endwith", "load",
    "block", "endblock", "spaceless", "endspaceless", "autoescape", "endautoescape",
    "set", "endset",
}  # fmt: skip
# After these, template code joins the text around it instead of standing apart.
JOINS_AFTER = re.compile(r"[^\s\"'>]\Z")

# --- The policy ------------------------------------------------------------------------
INLINE_SCRIPT, INLINE_STYLE, WRONG_NONCE = "inline script", "inline style", "wrong nonce"
STYLE_ATTRIBUTE, EVENT_HANDLER, JAVASCRIPT_URL = (
    "style attribute", "event handler", "javascript: link",
)  # fmt: skip
ELSEWHERE = "other site or data: URL"
NOT_ALLOWED = "frame, media, object or manifest"

URL_ATTRIBUTES = {
    "href", "src", "action", "formaction", "xlink:href", "data", "poster", "ping",
    "to", "from", "values",  # SVG animation can set an href
}  # fmt: skip
# Where each tag loads something from, posts to or pings; a link only loads for these
# rel values.
LOADS_FROM = {
    "script": {"src", "href", "xlink:href"},
    "img": {"src", "srcset"},
    "source": {"srcset"},
    "input": {"src", "formaction"},
    "image": {"src", "href", "xlink:href"},
    "feimage": {"href", "xlink:href"},
    "use": {"href", "xlink:href"},
    "link": {"href", "imagesrcset"},
    "form": {"action"},
    "button": {"formaction"},
    "base": {"href"},
    "a": {"ping"},
    "area": {"ping"},
}
LINK_RELS_THAT_LOAD = {"stylesheet", "preload", "modulepreload", "prefetch", "icon"}
IMAGE_TAGS = {"img", "source", "input", "image", "feimage"}  # may use data: URLs
NEVER_ALLOWED = {"iframe", "frame", "fencedframe", "video", "audio", "object", "embed"}
OTHER_SITE = ("http:", "https:", "//", "mailto:", "ftp:", "blob:", "ws:", "wss:")
# Script types a browser runs (plus any JavaScript MIME type); others are data.
RUNNING_SCRIPT_TYPES = {"", "module", "importmap", "speculationrules"}
JAVASCRIPT_MIME_WORDS = ("javascript", "ecmascript", "jscript", "livescript")
CODE_TAGS = ("script", "style")
NESTED_CODE_TAG = re.compile(r"<(script|style)(?=[\s/>])", re.IGNORECASE)
FOREIGN_CONTENT = {"svg", "math"}  # inside them, only <script> holds plain text
# Comments browsers end at once; Python's parser would read on to the next -->.
EMPTY_COMMENT = re.compile(r"<!---?>")
SNIPPET_LENGTH = 80


def prints(code):
    """Whether this template code puts something on the page itself."""
    if code.startswith("{{"):
        return True
    words = code.strip("{}%-# \t").split()
    return bool(words) and words[0] not in STRUCTURAL_TAGS


def placeholder_for(code):
    """Printing template code becomes placeholders around its quoted strings (a URL can
    be one), with nothing in them that could end an attribute or a tag; code that
    prints nothing becomes bare placeholders."""
    strings = []
    if prints(code):
        strings = [HTML_SPECIAL.sub(PLACEHOLDER, a or b) for a, b in QUOTED_STRING.findall(code)]
        strings = strings or [OUTPUT]
    return f"{PLACEHOLDER}{PLACEHOLDER.join(strings)}{PLACEHOLDER}"


def replacement(code, before):
    """What a piece of template code becomes, given the HTML just before it."""
    if NONCE_VARIABLE.fullmatch(code):
        return NONCE
    if NONCE_TAG.fullmatch(code):
        return f' nonce="{NONCE}" '
    if code.startswith("{#"):
        return " "
    if before.endswith(("<", "</")):
        return TAG_NAME  # code printing a tag name
    if JOINS_AFTER.search(before):  # inside a word, an attribute name or a bare value
        return placeholder_for(code)
    return f" {placeholder_for(code)} "


def block_end(match):
    kind, name = match[1], match[2] if match[1] == "verbatim" else ""
    return re.compile(rf"\{{%-?[ \t]*end{kind}[ \t]*{re.escape(name)}[ \t]*-?%\}}")


def as_rendered(template):
    """The template as HTML: comments gone, the page's nonce marked, verbatim text kept
    as it is, other template code reduced to placeholders. Line numbers stay the same."""
    html, position = [], 0
    while match := TEMPLATE_CODE.search(template, position):
        html.append(template[position : match.start()])
        block = BLOCK_START.match(match[0])
        end = block_end(block).search(template, match.end()) if block else None
        if end and block[1] == "comment":
            html.append("\n" * template.count("\n", match.start(), end.end()))
        elif end:  # verbatim or raw: printed as it is
            html.append(template[match.end() : end.start()])
        else:
            html.append(replacement(match[0], "".join(html[-1:])))
        position = end.end() if end else match.end()
    html.append(template[position:])
    return EMPTY_COMMENT.sub("<!---->", "".join(html))


class UrlUse(NamedTuple):
    runs_javascript: bool
    other_site: bool
    data: bool


def url_use(value):
    """What a URL does, read as the browser reads it: control characters and spaces
    dropped, backslashes as slashes, lowercase. Each piece between template code is
    checked, and the pieces joined (template code can split a URL)."""
    clean = re.sub(r"[\x00-\x20]", "", value).replace("\\", "/").lower()
    pieces = clean.split(PLACEHOLDER)
    candidates = [*pieces, "".join(piece for piece in pieces if piece != OUTPUT)]
    before_query = re.split(r"[?#]", clean.replace(PLACEHOLDER, ""))[0]
    return UrlUse(
        runs_javascript=any(c.startswith("javascript:") for c in candidates),
        other_site=any(c.startswith(OTHER_SITE) for c in candidates) or "://" in before_query,
        data=any(c.startswith("data:") for c in candidates),
    )


def runs(attrs):
    kind = (attrs.get("type") or "").split(";")[0].strip().lower()
    if PLACEHOLDER in kind:  # set by template code: it may well run
        return True
    return kind in RUNNING_SCRIPT_TYPES or any(w in kind for w in JAVASCRIPT_MIME_WORDS)


def code_problems(tag, attrs, code):
    """What's wrong with the code inside a <script> or <style> element."""
    if not code.replace(PLACEHOLDER, "").strip() or (tag == "script" and not runs(attrs)):
        return []
    nonce = attrs.get("nonce") or ""
    if nonce == NONCE:
        return []
    if nonce.strip():
        return [WRONG_NONCE]
    return [INLINE_SCRIPT if tag == "script" else INLINE_STYLE]


def loads(tag, attrs):
    """The URLs this tag loads something from, posts to or pings."""
    rels = set((attrs.get("rel") or "").lower().split())
    if tag == "link" and not LINK_RELS_THAT_LOAD & rels:
        return []
    values = [attrs[name] or "" for name in LOADS_FROM.get(tag, set()) & attrs.keys()]
    return [source for value in values for source in value.split(",")]  # srcset: several


def is_event_handler(name):
    rest = name[2:]
    return name.startswith("on") and bool(rest) and (rest.isalpha() or PLACEHOLDER in rest)


def tag_problems(tag, attrs):
    """What's wrong with one opening tag."""
    problems = []
    rels = set((attrs.get("rel") or "").lower().split())
    if "style" in attrs:
        problems.append(STYLE_ATTRIBUTE)
    if any(is_event_handler(name) for name in attrs):
        problems.append(EVENT_HANDLER)
    urls = [attrs[name] or "" for name in URL_ATTRIBUTES & attrs.keys()]
    if any(url_use(value).runs_javascript for value in urls):
        problems.append(JAVASCRIPT_URL)
    if tag in NEVER_ALLOWED or (tag == "link" and "manifest" in rels):
        problems.append(NOT_ALLOWED)
    data_allowed = tag in IMAGE_TAGS or (tag == "link" and "icon" in rels)
    uses = [url_use(source) for source in loads(tag, attrs)]
    if any(use.other_site or (use.data and not data_allowed) for use in uses):
        problems.append(ELSEWHERE)
    return problems


class CodeElement(NamedTuple):
    tag: str
    attrs: dict
    line: int
    start_tag: str
    code: list


class PolicyCheck(HTMLParser):
    """Reads the HTML and collects what the policy blocks, by kind."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.found = {}
        self.code_element = None  # the <script> or <style> being read
        self.foreign_depth = 0

    def report(self, problems, line, start_tag):
        snippet = start_tag.replace(NONCE, "{{ csp_nonce }}").replace(PLACEHOLDER, "")
        for problem in problems:
            self.found.setdefault(problem, []).append(f"line {line}: {snippet[:SNIPPET_LENGTH]}")

    def handle_starttag(self, tag, attr_list):
        tag = tag.split(":")[-1]  # svg:script is a script
        attrs = {}
        for name, value in attr_list:
            attrs.setdefault(name, value)  # like browsers, the first of a repeat counts
        line, start_tag = self.getpos()[0], self.get_starttag_text() or ""
        self.report(tag_problems(tag, attrs), line, start_tag)
        if tag in CODE_TAGS:
            self.code_element = CodeElement(tag, attrs, line, start_tag, [])
        if tag in FOREIGN_CONTENT:
            self.foreign_depth += 1

    def handle_startendtag(self, tag, attr_list):
        self.handle_starttag(tag, attr_list)
        name = tag.split(":")[-1]
        # In HTML, browsers ignore the "/" of <script/> and <style/>: the code follows.
        if name in CODE_TAGS and self.foreign_depth:
            self.handle_endtag(tag)
        elif name in FOREIGN_CONTENT:
            self.foreign_depth -= 1

    def handle_data(self, data):
        if self.code_element:
            self.code_element.code.append(data)

    def handle_endtag(self, tag):
        tag = tag.split(":")[-1]
        if self.code_element and tag == self.code_element.tag:
            self.finish_code_element()
        if tag in FOREIGN_CONTENT and self.foreign_depth:
            self.foreign_depth -= 1

    def finish_code_element(self):
        element, self.code_element = self.code_element, None
        code = "".join(element.code)
        problems = code_problems(element.tag, element.attrs, code)
        self.report(problems, element.line, element.start_tag)
        # A <script> or <style> opened in another {% if %} branch hides inside this one.
        if nested := NESTED_CODE_TAG.search(code):
            for problem, snippets in blocked_in(code[nested.start() :]).items():
                self.found.setdefault(problem, []).extend(snippets)

    def set_cdata_mode(self, elem, **kwargs):
        # Inside <svg> and <math>, only <script> holds plain text; the rest is markup.
        if self.foreign_depth and elem != "script":
            return
        super().set_cdata_mode(elem, **kwargs)


def blocked_in(template):
    """What in this template a strict CSP would block, by kind; empty when nothing would
    be."""
    check = PolicyCheck()
    check.feed(as_rendered(template))
    check.close()
    if check.code_element:  # a <script> or <style> never closed
        check.finish_code_element()
    return check.found


def is_checked(path, folder, package):
    """A page template, not one of the module's emails (templates/<package>/emails/)."""
    if not path.is_file() or path.suffix.lower() not in TEMPLATE_SUFFIXES:
        return False
    inside = path.relative_to(next(p for p in path.parents if p.name == folder))
    return inside.parts[:2] != (package, EMAILS_FOLDER)


def template_files(root, package):
    return sorted(
        path
        for folder in TEMPLATE_FOLDERS
        for path in root.rglob(f"{folder}/**/*")
        if is_checked(path, folder, package)
    )


def module_package():
    return next(c.name for c in apps.get_app_configs() if Path(c.path).is_relative_to(SRC_DIR))


def test_templates_have_nothing_a_strict_csp_blocks():
    # Inline scripts and styles need the page's nonce (nonce="{{ csp_nonce }}" or
    # {% csp_nonce_attr %}); better, put them in static files. Load everything from the
    # project's own site (images may also be data: URLs). See the README's rules.
    problems = {
        str(page.relative_to(SRC_DIR)): blocked
        for page in template_files(SRC_DIR, module_package())
        if (blocked := blocked_in(page.read_text(encoding="utf-8")))
    }
    assert problems == {}


# So an empty result above means "nothing blocked", not "the check finds nothing".
@pytest.mark.parametrize(
    ("html", "kind"),
    [
        ("<script>alert(1)</script>", INLINE_SCRIPT),
        ("<SCRIPT>alert(1)</SCRIPT>", INLINE_SCRIPT),
        ('<script data-src="x.js">alert(1)</script>', INLINE_SCRIPT),
        ('<script nonce="">alert(1)</script>', INLINE_SCRIPT),
        ('<script {% if a %}src="a.js"{% endif %}>alert(1)</script>', INLINE_SCRIPT),
        ('<script src="/x.js">alert(1)</script>', INLINE_SCRIPT),
        ("<script/>go()</script>", INLINE_SCRIPT),
        ('<script type="text/jscript">go()</script>', INLINE_SCRIPT),
        ('<script type="{{ t }}">go()</script>', INLINE_SCRIPT),
        ("<script>{{ data }}</script>", INLINE_SCRIPT),
        ('<script>{% include "m/inline.js" %}</script>', INLINE_SCRIPT),
        ("<script>{% include js_template %}</script>", INLINE_SCRIPT),
        ("<script>{% my_inline_js %}</script>", INLINE_SCRIPT),
        ("<script><!--\ngo();\n//--></script>", INLINE_SCRIPT),
        ("<svg><script>go()</script></svg>", INLINE_SCRIPT),
        ("<svg:script>go()</svg:script>", INLINE_SCRIPT),
        ("{% block extra_js %}<script>go()</script>{% endblock %}", INLINE_SCRIPT),
        ("{# start\n<script>go()</script>\nend #}", INLINE_SCRIPT),
        ("{%\n<script>go()</script>\n%}", INLINE_SCRIPT),
        ("{% verbatim %}{# <script>go()</script> #}{% endverbatim %}", INLINE_SCRIPT),
        ("{% verbatim js %}{# <script>go()</script> #}{% endverbatim js %}", INLINE_SCRIPT),
        ("{% raw %}{# <script>go()</script> #}{% endraw %}", INLINE_SCRIPT),
        ('<script nonce="{{ csp_nonce }}">ok()</script x><script>go()</script>', INLINE_SCRIPT),
        ('{% if csp_nonce %}<script nonce="{{ csp_nonce }}">{% else %}<script>{% endif %}'
         "go()</script>", INLINE_SCRIPT),
        ("<svg><title><script>go()</script></title></svg>", INLINE_SCRIPT),
        ("<!--><script>go()</script>-->", INLINE_SCRIPT),
        ("<!---><script>go()</script>-->", INLINE_SCRIPT),
        ('<script nonce="abc123">alert(1)</script>', WRONG_NONCE),
        ('<script nonce="CSP-NONCE">alert(1)</script>', WRONG_NONCE),
        ('<script nonce="{{ other }}">alert(1)</script>', WRONG_NONCE),
        ('<script nonce="{{ request.csp_nonce }}">go()</script>', WRONG_NONCE),
        ('<script nonce="{{\ncsp_nonce\n}}">go()</script>', WRONG_NONCE),
        ('{% verbatim %}<script nonce="{{ csp_nonce }}">go()</script>{% endverbatim %}',
         WRONG_NONCE),
        ("<style>p { color: red }</style>", INLINE_STYLE),
        ("<style/>p{}</style>", INLINE_STYLE),
        ("<style>{% theme_css %}</style>", INLINE_STYLE),
        ('{% if x %}<style nonce="{{ csp_nonce }}">{% else %}<style>{% endif %}p{}</style>',
         INLINE_STYLE),
        ('<style nonce="abc123">p {}</style>', WRONG_NONCE),
        ('<p style="color: red">', STYLE_ATTRIBUTE),
        ("<p style=color:red>", STYLE_ATTRIBUTE),
        ('<div/style="x">', STYLE_ATTRIBUTE),
        ('<p {% if n > 1 %}class="many"{% endif %} style="color: red">', STYLE_ATTRIBUTE),
        ('<p {% if a == ">" %}{% endif %} style="color:red">', STYLE_ATTRIBUTE),
        ('<div {% if a %}style="x"{% endif %}>', STYLE_ATTRIBUTE),
        ('<{{ tag }} style="color:red">x</{{ tag }}>', STYLE_ATTRIBUTE),
        ('<button onclick="go()">', EVENT_HANDLER),
        ("<BUTTON ONCLICK='go()'>", EVENT_HANDLER),
        ('<button\n  type="button"\n  onclick="go()"\n>Go</button>', EVENT_HANDLER),
        ('<div/onclick = "go()">', EVENT_HANDLER),
        ('<button {% if n > 0 %}disabled{% endif %} onclick="go()">', EVENT_HANDLER),
        ('<div {% if sep == ">" %}hidden{% endif %} onclick="go()">', EVENT_HANDLER),
        ('<div title="{% translate "a > b" %}" onclick="go()">', EVENT_HANDLER),
        ('<{% if a %}a{% else %}span{% endif %} onclick="go()">x</span>', EVENT_HANDLER),
        ('<p on{{ event }}="go()">', EVENT_HANDLER),
        ('<svg onload="go()"></svg>', EVENT_HANDLER),
        ("<svg><title><img src=x onerror=\"go()\"></title></svg>", EVENT_HANDLER),
        ('<svg><style nonce="{{ csp_nonce }}"><img src=x onerror="go()"></style></svg>',
         EVENT_HANDLER),
        ('<a href="javascript:go()">', JAVASCRIPT_URL),
        ("<a href=javascript:go()>x</a>", JAVASCRIPT_URL),
        ('<a href="  JavaScript:go()">', JAVASCRIPT_URL),
        ('<a href="javascript&#58;go()">', JAVASCRIPT_URL),
        ('<a href="javascript&colon;go()">x</a>', JAVASCRIPT_URL),
        ('<a href="java&Tab;script:go()">x</a>', JAVASCRIPT_URL),
        ('<a href="java\tscript:go()">', JAVASCRIPT_URL),
        ('<a href="javascript:go()" href="/">x</a>', JAVASCRIPT_URL),
        ('<a href="{% if x %}#{% else %}javascript:void(0){% endif %}">', JAVASCRIPT_URL),
        ('<a href="{% firstof a "javascript:void(0)" %}">', JAVASCRIPT_URL),
        ('<a href="java{% if x %}{% endif %}script:go()">', JAVASCRIPT_URL),
        ("<a href=\"{{ 'javascript' }}:go()\">", JAVASCRIPT_URL),
        ('<svg><a xlink:href="javascript:go()"><text>x</text></a></svg>', JAVASCRIPT_URL),
        ('<svg><animate attributeName="href" to="javascript:go()"/></svg>', JAVASCRIPT_URL),
        ('<form action="javascript:go()">', JAVASCRIPT_URL),
        ('<script src="https://cdn.example.com/x.js"></script>', ELSEWHERE),
        ('<script src="//cdn.example.com/x.js"></script>', ELSEWHERE),
        ('<script src="\\\\cdn.example.com/x.js"></script>', ELSEWHERE),
        ('<script src="/\\cdn.example.com/x.js"></script>', ELSEWHERE),
        ('<script src="/\t/cdn.example.com/x.js"></script>', ELSEWHERE),
        ('<script src="data:text/javascript,go()"></script>', ELSEWHERE),
        ('<script src="https://{{ host }}/x.js"></script>', ELSEWHERE),
        ('<script src="{{ request.scheme }}://cdn.example.com/x.js"></script>', ELSEWHERE),
        ('<script src="http{% if secure %}s{% endif %}://cdn.example.com/x.js"></script>',
         ELSEWHERE),
        ('<script src="{% if debug %}/x.js{% else %}https://cdn.example.com/x.js{% endif %}">'
         "</script>", ELSEWHERE),
        ("<script src={{ prefix }}//cdn.example.com/x.js></script>", ELSEWHERE),
        ('<script nonce="{{ csp_nonce }}" src="https://cdn.example.com/x.js"></script>',
         ELSEWHERE),
        ('<img src="{{ MEDIA_PREFIX }}//cdn.example.com/a.png" alt="">', ELSEWHERE),
        ('<image src="https://cdn.example.com/a.png">', ELSEWHERE),
        ('<link rel="stylesheet" href="https://fonts.example.com/css">', ELSEWHERE),
        ('<link rel="stylesheet" href="{{ scheme }}://fonts.example.com/css">', ELSEWHERE),
        ('<link rel="stylesheet" href="data:text/css,p{}">', ELSEWHERE),
        ('<link rel="shortcut icon" href="https://cdn.example.com/f.ico">', ELSEWHERE),
        ('<link rel="preload" as="font" href="https://fonts.example.com/f.woff2">', ELSEWHERE),
        ('<link rel="preload" as="image" imagesrcset="https://x.example.com/b 1x" href="/a">',
         ELSEWHERE),
        ('<img src="https://example.com/p.png" alt="">', ELSEWHERE),
        ('<img srcset="/a.png 1x, https://example.com/b.png 2x" alt="">', ELSEWHERE),
        ('<svg><image href="https://cdn.example.com/a.png"/></svg>', ELSEWHERE),
        ('<svg><use xlink:href="https://cdn.example.com/s.svg#i"/></svg>', ELSEWHERE),
        ('<svg><script href="https://cdn.example.com/x.js"/></svg>', ELSEWHERE),
        ('<form method="post" action="https://pay.example.com/">', ELSEWHERE),
        ('<form action="mailto:team@example.com">', ELSEWHERE),
        ('<button formaction="https://pay.example.com/">', ELSEWHERE),
        ('<base href="https://cdn.example.com/">', ELSEWHERE),
        ('<base href="data:text/html,x">', ELSEWHERE),
        ('<a href="/x" ping="https://t.example.com/">x</a>', ELSEWHERE),
        ('<iframe src="/embed/"></iframe>', NOT_ALLOWED),
        ('<iframe srcdoc="&lt;script&gt;go()&lt;/script&gt;"></iframe>', NOT_ALLOWED),
        ('<fencedframe src="/x"></fencedframe>', NOT_ALLOWED),
        ('<video src="/static/m/intro.mp4"></video>', NOT_ALLOWED),
        ('<object data="/static/m/x.pdf"></object>', NOT_ALLOWED),
        ('<embed src="/static/m/x.swf">', NOT_ALLOWED),
        ('<link rel="manifest" href="/manifest.json">', NOT_ALLOWED),
    ],
)  # fmt: skip
def test_the_csp_check_finds_blocked_code(html, kind):
    assert kind in blocked_in(html), html


@pytest.mark.parametrize(
    "html",
    [
        '<script nonce="{{ csp_nonce }}">1</script>',
        "<script nonce={{ csp_nonce }}>go()</script>",
        '<script nonce="{{- csp_nonce }}">go()</script>',
        "<script {% csp_nonce_attr %}>go()</script>",
        "<style {% csp_nonce_attr %}>p {}</style>",
        '<script nonce="{{ csp_nonce }}">if (i<n) only = 1; if (n>2) {}</script>',
        "<script src=\"{% static 'x.js' %}\" defer></script>",
        '<script id="c" src="{% static "m/js/x.js" %}" {% if add %}data-model-name='
        '"{{ opts.model_name }}"{% endif %} async></script>',
        "<svg><script/></svg>",
        '<style nonce="{{ csp_nonce }}">p {}</style>',
        "<style-guide>x</style-guide><style nonce=\"{{ csp_nonce }}\">p{}</style>",
        '<script type="application/json">{"a": 1}</script>',
        '<script type="application/json; charset=utf-8">{"a": 1}</script>',
        '<script type="application/ld+json">{"logo": "https://example.com/l.png"}</script>',
        '<script type="text/x-template" id="t"><div>{{ x }}</div></script>',
        "<script>{% if a %}{% endif %}</script>",
        '{{ data|json_script:"m-data" }}',
        '<p {% if n > 1 %}class="many"{% endif %}>x</p>',
        '<input {% if form.x.value >= 1 %}checked{% endif %} type="checkbox">',
        '<p class="{{ "big" if n > 1 else "small" }}">x</p>',
        '<input data-style="x" data-onclick="y">',
        '<a href="/online=1">x</a>',
        '<a href="https://example.com/">A link to another site</a>',
        '<a href="/login/?next=https://example.com/x">x</a>',
        '<link rel="canonical" href="https://example.com/">',
        '<link rel="preconnect" href="https://example.com">',
        '<link rel="dns-prefetch" href="//cdn.example.com">',
        '<link rel="icon" href="data:image/svg+xml,%3Csvg%3E%3C/svg%3E">',
        '<img src="data:image/svg+xml,%3Csvg%3E" alt="">',
        "<form method=\"post\" action=\"{% url 'm:save' %}\">{% csrf_token %}</form>",
        '<form method="post" action="{% url "m:edit" obj.pk %}?next={{ request.path|urlencode }}"'
        ' {% if form.is_multipart %}enctype="multipart/form-data"{% endif %} novalidate>'
        "{% csrf_token %}{{ form }}</form>",
        '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">'
        '<use href="{% static "m/icons.svg" %}#x"/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" aria-hidden="true"><path d="M5 12h14"/></svg>',
        '<feed xmlns="http://www.w3.org/2005/Atom"><link href="https://example.com/"/>'
        '<link rel="alternate" href="https://example.com/x"/></feed>',
        '<textarea name="t"><p style="x"></textarea>',
        "<title>A <b onclick=x> title</title>",
        "<p>Turn this on = yes, javascript: off</p>",
        "<!-- <p onclick='x'> -->",
        "{# <script>commented out</script> #}",
        "{% comment %}<p style='x'>\n<script>go()</script>{% endcomment %}",
    ],
)  # fmt: skip
def test_the_csp_check_allows_what_a_strict_csp_allows(html):
    assert blocked_in(html) == {}, html


def test_every_template_file_is_checked_except_the_modules_emails(tmp_path):
    names = [
        "jinja2/m/page.html",
        "jinja2/m/page.j2",
        "templates/admin/emails/email/change_form.html",
        "templates/m/feed.xml",
        "templates/m/icon.svg",
        "templates/m/page.htm",
        "templates/m/page.html",
        "templates/m/page.jinja",
    ]
    for name in [*names, "templates/m/email.txt", "templates/m/emails/welcome.html"]:
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text("<script>alert(1)</script>", encoding="utf-8")
    checked = [str(path.relative_to(tmp_path)) for path in template_files(tmp_path, "m")]
    assert checked == names


def test_problems_name_their_line():
    found = blocked_in("<p>\n{# a #}\n{%\ncsp_nonce_attr\n%}\n<p style='x'>")
    assert found == {STYLE_ATTRIBUTE: ["line 6: <p style='x'>"]}
