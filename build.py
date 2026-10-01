# -*- coding: utf-8 -*-
"""Builds the static site from docs/*.md.  Run:  python3 build.py"""
import re, html, pathlib
import markdown

ROOT = pathlib.Path(__file__).parent
DOCS = ROOT / "docs"
TODAY = "1.10.2026"

# Reading order of the site: letter and summary, then constitution -> guidelines -> the three laws -> 100 days; disputes cover all.
# title=None takes the document's own H1.
PAGES = [
    dict(slug="letter", md="letter.md", label="מכתב הסבר", title=None,
         lede="על מה המסמכים, איך נוסחו, עיקרי התוצרים ומה הלאה — בשפה לא משפטית.", pdf="מכתב-הסבר.pdf"),
    dict(slug="summary", md="summary.md", label="תקציר", title=None,
         lede="עמוד אחד: כל תוצר במבט אחד, עיקרי החוקה ומה נשאר להכרעת ראשי המפלגות.", pdf="תקציר-החוקה.pdf"),
    dict(slug="constitution", md="constitution.md", label="החוקה", title="חוקה למדינת ישראל — טיוטה",
         lede="100 סעיפים ב-12 פרקים, ונספח מקורות המציין לכל סעיף על איזו עמדה מפלגתית הוא נשען.", pdf="חוקה-טיוטה.pdf"),
    dict(slug="guidelines", md="guidelines.md", label="קווי היסוד", title=None,
         lede="68 סעיפים — מבוא, חמישה פרקי ליבה ושבעה פרקי תחום — עם רמת ההסכמה על כל סעיף, מה לא נכלל ולמה, ונספח מקורות.", pdf="קווי-היסוד-לממשלה.pdf"),
    dict(slug="term-limits", md="term-limits.md", label="הגבלת כהונה", group="laws", title=None,
         lede="נוסח ההצעה, דברי הסבר, הכרעות ניסוח, ההתאמות בחוקה, נקודות פתוחות ונספח מקורות.", pdf="הצעת-חוק-יסוד-הגבלת-כהונה.pdf"),
    dict(slug="inquiry", md="inquiry.md", label="ועדת חקירה", group="laws", title=None,
         lede="טיוטת החלטת ממשלה לפי חוק ועדות חקירה, נוסחים חלופיים, הצעת חוק ייעודית כחלופה, דברי הסבר ונספח מקורות.", pdf="ועדת-חקירה-ממלכתית.pdf"),
    dict(slug="equal-burden", md="equal-burden.md", label="שוויון בנטל", group="laws", title=None,
         lede="הצעת חוק שירות ממלכתי: 32 סעיפים ותוספת, דברי הסבר, הכרעות ניסוח, נקודות פתוחות ונספח מקורות.", pdf="הצעת-חוק-השוויון-בנטל.pdf"),
    dict(slug="deferral-decision", md="deferral-decision.md", label="ההכרעה על היקף הדחייה", group="laws", title=None,
         lede="תוצאות המשא ומתן בין נציגי ארבע המפלגות על חוק השוויון בנטל: הנוסח המוסכם, ההכרעה בדחייה בשל לימוד תורה ומצוינות, החלופות שנרשמו והאישורים החסרים.", pdf="הכרעה-היקף-הדחייה.pdf"),
    dict(slug="100-days", md="100-days.md", label="100 הימים", title=None,
         lede="29 פעולות, משלב 0 (מהבחירות ועד כינון הממשלה) ועד יום 100 — לכל פעולה מועד ומקור — ומה לא נכלל ולמה.", pdf="תוכנית-100-הימים.pdf"),
    dict(slug="disputes", md="disputes.md", label="מחלוקות", title="מחלוקות וחלופות — בכל התוצרים",
         lede="כל נושא שנוי במחלוקת: עמדת כל מפלגה עם מקור, הנוסח שנבחר, החלופות, ורשימת ההכרעות הנדרשות מראשי המפלגות.", pdf="מחלוקות-וחלופות.pdf"),
]
PAGE = {p["slug"]: p for p in PAGES}
NAV = [("index", "בית"), ("letter", "מכתב הסבר"), ("summary", "תקציר"), ("constitution", "החוקה"),
       ("guidelines", "קווי היסוד"), ("laws", "שלושת החוקים"), ("100-days", "100 הימים"), ("disputes", "מחלוקות")]
LAWS = [  # slug, kind, short name, what it sets (from the summary)
    ("term-limits", "הצעת חוק-יסוד", "הגבלת כהונת ראש הממשלה",
     "שמונה שנים או שתי תקופות כהונה מלאות, לפי הארוך מביניהם; צינון של שמונה שנים וחסימת עקיפה; שריון ברוב 80."),
    ("inquiry", "טיוטת החלטת ממשלה", "ועדת חקירה ממלכתית לטבח 7 באוקטובר",
     "ההחלטה הראשונה של הממשלה, לפי חוק ועדות חקירה; מה שקדם לטבח, הטבח והמלחמה שבעקבותיו; החברים — בידי נשיא בית המשפט העליון."),
    ("equal-burden", "הצעת חוק", "חוק השוויון בנטל",
     "חובת שירות צבאי או אזרחי לכל, בלי פטור קבוצתי ובלי מכסות; לימוד תורה במסלול בתוך השירות; סנקציות בכפוף לפסקת ההגבלה."),
]


def group_of(slug):
    return PAGE.get(slug, {}).get("group", slug)


def nav(current):
    cur_group = "laws" if current == "laws" else group_of(current)
    items = []
    for slug, label in NAV:
        href = "index.html" if slug == "index" else slug + ".html"
        cur = ' aria-current="page"' if slug == cur_group else ""
        items.append('<a href="%s"%s>%s</a>' % (href, cur, label))
    return '<header class="topbar"><div class="topbar-inner"><a class="brand" href="index.html">החוקה ותוצרי קבוצה ב\'</a><nav class="nav">%s</nav></div></header>' % "".join(items)


def shell(title, body, current, description=""):
    return f'''<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
{nav(current)}
{body}
<footer>טיוטות לדיון, {TODAY}. נוסחו מתוך המצעים, העקרונות וההצהרות הפומביות של ביחד, ישראל ביתנו, הדמוקרטים וישר!, ברוח מסמך העקרונות של ראשי המפלגות מיום 26.9.2026. אינן נוסח סופי ואינן מחייבות את המפלגות.</footer>
</body>
</html>'''


# ---------- cross-references to constitution sections ----------
# "סעיף 23", "ס' 92(א)", "סעיפים 43 ו-92" — but not "ס' 6א", "סעיף 0.4".
XREF = re.compile(r"(?<![\w-])(סעיפים|סעיף|ס')\s+(\d{1,3})(?!\d)(?!\.\d)(?![א-ת])((?:\([א-ת]\))?(?:\(\d+\))?)")
CHAIN = re.compile(r"((?:,\s*|\s+ו-)\d{1,3}(?!\d)(?!\.\d)(?![א-ת])(?:\([א-ת]\))?)+")
RANGE = r"(?:[–-]\d{1,3}(?:\([א-ת]\))?)?"
# a reference followed by another instrument ("ס' 14 להצעת החוק", "ס' 46 לחוק שירות ביטחון") is not to the constitution
NOT_CONST_AFTER = re.compile(r"^" + RANGE + r"\s+(?:ל|ב|של\s+)(?:חוק(?!ה)|הצעת|הצעה|ההצעה|החלטה|ההחלטה|קווי|תוכנית|פקודת|תקנון|מתווה|מסמך|נוסח)")
# ... and so is one that directly follows a law's name ("חוק יסוד: הכנסת ס' 4")
NOT_CONST_BEFORE = re.compile(r"(?:חוק[- ]יסוד:?[^;()|,.]{0,40}|חוק [^;()|,.]{2,40}|פקודת [^;()|,.]{2,30}|תקנון הכנסת)\s*$")
# in documents other than the constitution family, link only what is explicitly the constitution
CONST_AFTER = re.compile(r"^" + RANGE + r"\s+(?:ל|ב)(?:טיוטת\s+)?(?:ה)?חוקה(?![א-ת])")


def is_const_ref(before, tail, mode):
    if mode == "strict":
        return bool(CONST_AFTER.match(tail))
    if NOT_CONST_AFTER.match(tail):
        return False
    if mode == "default" and NOT_CONST_BEFORE.search(before[-60:]):
        return False
    return True


def link_sections(fragment, prefix, mode):
    """Turn constitution references into links to #s-N. mode: internal (constitution text), default, strict."""
    out, pos = [], 0
    for m in XREF.finditer(fragment):
        if m.start() < pos:
            continue
        word, num, sub = m.group(1), m.group(2), m.group(3)
        chain = ""
        if word == "סעיפים":
            cm = CHAIN.match(fragment[m.end():])
            if cm:
                chain = cm.group(0)
        tail = fragment[m.end() + len(chain):]
        if not is_const_ref(fragment[:m.start()], tail, mode):
            continue
        out.append(fragment[pos:m.start()])
        out.append('%s <a class="xref" href="%s#s-%s">%s%s</a>' % (word, prefix, num, num, sub))
        if chain:
            out.append(re.sub(r"(\d{1,3})(\([א-ת]\))?", lambda x: '<a class="xref" href="%s#s-%s">%s%s</a>' % (prefix, x.group(1), x.group(1), x.group(2) or ""), chain))
        pos = m.end() + len(chain)
    out.append(fragment[pos:])
    return "".join(out)


def text_parts(html_text, fn):
    parts = re.split(r"(<[^>]+>)", html_text)
    return "".join(p if p.startswith("<") else fn(p) for p in parts)


def linkify(html_text, prefix, mode="default"):
    return text_parts(html_text, lambda p: link_sections(p, prefix, mode))


def md_to_html(text):
    md = markdown.Markdown(extensions=["tables", "sane_lists"])
    return md.convert(text)


def wrap_tables(h):
    return h.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")


def pills(h):
    h = h.replace("הכרעה נדרשת", '<span class="pill open">הכרעה נדרשת</span>')
    h = re.sub(r"<strong>הוכרע (\d{1,2}\.\d{1,2}\.\d{4})</strong>", r'<span class="pill done">הוכרע \1</span>', h)
    h = re.sub(r"✓ הוכרע", '<span class="pill done">הוכרע</span>', h)
    h = re.sub(r"<li>\[x\] ", '<li><span class="pill done">הוכרע</span> ', h)
    h = re.sub(r"<li>\[ \] ", '<li><span class="pill open">פתוח</span> ', h)
    return h


# agreement tags used in the guidelines, the laws and the 100-day plan: [4/4], [3+], [צר], [גישור] ...
TAG = re.compile(r"\[(4/4[^\[\]]{0,24}|3\+|צר|גישור|הצעת גישור|טכני|סטטוס קוו|הליך)\]")
TAG_LVL = {"4": "all4", "3": "three", "צ": "narrow", "ג": "bridge", "ה": "sq", "ט": "bridge", "ס": "sq"}


def tag_fragment(t):
    t = t.replace("[הכרעה נדרשת]", "הכרעה נדרשת")
    t = re.sub(r"\[(הוכרע במטה(?: \([^\[\]]{1,40}\))?)\]", r'<span class="pill done">\1</span>', t)
    def rep(m):
        txt = m.group(1)
        lvl = "bridge" if txt.startswith("הצעת") else ("sq" if txt == "הליך" else TAG_LVL.get(txt[0], "sq"))
        return '<span class="tag lvl-%s"><span class="dot" aria-hidden="true"></span>%s</span>' % (lvl, txt)
    return TAG.sub(rep, t)


def tags(h):
    return text_parts(h, tag_fragment)


# ---------- data: agreement levels, parties, disputes cross-links ----------
LEVELS = [
    ("all4", "כל 4", "מוסכם על ארבע המפלגות"),
    ("three", "3 מתוך 4", "שלוש מסכימות, הרביעית ללא עמדה"),
    ("narrow", "מכנה צר", "עמדה מפורשת של פחות משלוש מפלגות, אף אחת אינה מתנגדת; הנוסח צומצם או הופנה לחוק"),
    ("bridge", "הצעת גישור", "נוסח שאינו של אף מפלגה אך נדרש כדי שהסעיף יעבוד"),
    ("sq", "סטטוס קוו", "אין עמדה מפלגתית: נשמר הדין הקיים או הופנה לחוק"),
]
LEVEL_LABEL = {k: l for k, l, _ in LEVELS}
PARTIES = [
    ("beyahad", "ביחד", ["ביחד", "בנט", "לפיד", "יש עתיד", "אלהרר"]),
    ("beytenu", "ישראל ביתנו", ["ישראל ביתנו", "ליברמן"]),
    ("democrats", "הדמוקרטים", ["הדמוקרטים", "גולן", "רייטן"]),
    ("yashar", "ישר!", ["ישר!", "איזנקוט"]),
]

LEVEL_ORDER = [k for k, _, _ in LEVELS]


def levels_in(level_text):
    """All agreement levels a section's parts carry, strongest first."""
    t, s = level_text, set()
    if "כל 4" in t: s.add("all4")
    if "3 מתוך 4" in t: s.add("three")
    if "מכנה משותף" in t or "הכרעה נדרשת" in t: s.add("narrow")
    if "גישור" in t: s.add("bridge")
    if "סטטוס קוו" in t or "הפניה" in t or not s: s.add("sq")
    return [k for k in LEVEL_ORDER if k in s]


def parties_in(sources):
    found = []
    for seg in re.split(r"[;؛]", sources):
        if "ללא עמדה" in seg or "אין עמדה" in seg:
            continue
        for key, _, aliases in PARTIES:
            if key not in found and any(a in seg for a in aliases):
                found.append(key)
    return found


def extract_refs(text):
    nums = set()
    for m in XREF.finditer(text):
        chain = ""
        if m.group(1) == "סעיפים":
            cm = CHAIN.match(text[m.end():])
            if cm:
                chain = cm.group(0)
        if not is_const_ref(text[:m.start()], text[m.end() + len(chain):], "default"):
            continue
        nums.add(int(m.group(2)))
        nums.update(int(x) for x in re.findall(r"\d{1,3}", chain))
    return nums


def load_sections(text):
    """Section number -> dict(title, chapter, what, sources, level_text, lvl, parties)."""
    body, _, appx = text.partition("\n## נספח מקורות")
    secs, chapters, chap = {}, [], None
    for line in body.split("\n"):
        hm = re.match(r"^## (פרק ([א-ת\"']+) — .+)$", line)
        if hm:
            chap = (hm.group(2).replace('"', "").replace("'", ""), hm.group(1))
            chapters.append(chap)
            continue
        sm = re.match(r"^\*\*(\d{1,3})\. ([^*]+?)\.\*\*", line)
        if sm:
            secs[int(sm.group(1))] = {"title": sm.group(2), "chapter": chap}
    for line in appx.split("\n"):
        rm = re.match(r"^\|\s*(\d{1,3})\s*\|(.*)\|\s*$", line)
        if not rm:
            continue
        cells = [c.strip() for c in rm.group(2).split("|")]
        n = int(rm.group(1))
        if n in secs and len(cells) >= 3:
            what, sources, level_text = cells[0], cells[1], cells[2]
            secs[n].update(what=what, sources=sources, level_text=level_text,
                           lvls=levels_in(level_text), parties=parties_in(sources))
            secs[n]["lvl"] = secs[n]["lvls"][0]
    return secs, chapters


EXCL_DISPUTES = {"איך נקבע המכנה המשותף ומה נדרש להכרעה", "טבלת המחלוקות במבט אחד", "הכרעות נדרשות מראשי המפלגות"}


def disputes_index(text):
    """Heading ids d-1.. in document order, and section -> [(id, title)] for headings whose text cites it."""
    body = text.split("\n", 1)[1]
    refmap, cur, buf, i = {}, None, [], 0
    def flush():
        if cur and cur[1] not in EXCL_DISPUTES:
            for n in extract_refs("".join(buf)):
                refmap.setdefault(n, [])
                if cur not in refmap[n]:
                    refmap[n].append(cur)
    for line in body.split("\n"):
        m = re.match(r"^#{2,3} (.+)$", line)
        if m:
            flush(); i += 1; cur = ("d-%d" % i, m.group(1).strip()); buf = []
        else:
            buf.append(line + "\n")
    flush()
    return refmap


def id_headings(h):
    counter = [0]
    def rep(m):
        counter[0] += 1
        return '<h%s id="d-%d">' % (m.group(1), counter[0])
    return re.sub(r"<h([23])>", rep, h)


def dot(lvl):
    return '<span class="dot lvl-%s" aria-hidden="true"></span>' % lvl


def tone(s):
    l = s.get("lvls", ["sq"])
    return "--c1:var(--l-%s);--c2:var(--l-%s)" % (l[0], l[-1])


def lvl_text(s):
    l = s.get("lvls", ["sq"])
    return LEVEL_LABEL[l[0]] if len(l) == 1 else "%s / %s" % (LEVEL_LABEL[l[0]], LEVEL_LABEL[l[-1]])


def agreement_map(secs, chapters, href_prefix):
    rows = []
    for key, full in chapters:
        cells = []
        for n in sorted(k for k, v in secs.items() if v["chapter"] and v["chapter"][0] == key):
            s = secs[n]
            label = "%d. %s — %s" % (n, s["title"], lvl_text(s))
            cells.append('<a class="cell" style="%s" href="%s#s-%d" data-sec="%d" title="%s" aria-label="%s"></a>'
                         % (tone(s), href_prefix, n, n, html.escape(label), html.escape(label)))
        short = full.split(" — ")[0]
        rows.append('<div class="map-row"><a class="map-ch" href="%s#ch-%s" title="%s">%s <span>%s</span></a><div class="map-cells">%s</div></div>'
                    % (href_prefix, key, html.escape(full), short, html.escape(full.split(" — ")[1]), "".join(cells)))
    return '<div class="map" role="group" aria-label="מפת ההסכמה">%s</div>' % "".join(rows)


def legend(secs, as_buttons):
    counts = {k: sum(1 for s in secs.values() if k in s["lvls"]) for k, _, _ in LEVELS}
    items = []
    for k, label, desc in LEVELS:
        inner = '%s<span class="chip-label">%s</span><span class="chip-n">%d</span>' % (dot(k), label, counts[k])
        if as_buttons:
            items.append('<button type="button" class="chip" data-lvl="%s" aria-pressed="false" title="%s">%s</button>' % (k, html.escape(desc), inner))
        else:
            items.append('<span class="chip static" title="%s">%s</span>' % (html.escape(desc), inner))
    return "".join(items), counts


def build_constitution(text, secs, chapters, refmap):
    body_md = text.split("\n", 1)[1]  # drop H1
    main_md, _, appx_md = body_md.partition("\n## נספח מקורות")
    h = md_to_html(main_md)
    def sec(m):
        n = int(m.group(1))
        s = secs.get(n, {})
        lv = s.get("lvls", ["sq"])
        dots = dot(lv[0]) + (dot(lv[-1]) if len(lv) > 1 else "")
        return ('<p class="sec" id="s-%d" data-lvls="%s" data-parties="%s"><strong><a href="#s-%d">%d.</a> %s</strong> '
                '<button type="button" class="lvl-pill" aria-expanded="false" aria-controls="src-%d" title="מקור ורמת הסכמה">%s%s</button>'
                % (n, " ".join(lv), " ".join(s.get("parties", [])), n, n, m.group(2), n, dots, lvl_text(s)))
    h = re.sub(r'<p><strong>(\d{1,3})\. ([^<]+?)</strong>', sec, h)
    h = h.replace('<h2>מבוא</h2>', '<h2 id="preamble">מבוא</h2>')
    h = re.sub(r"<h2>(פרק ([א-ת\"']+) — [^<]+)</h2>", lambda m: '<h2 id="ch-%s">%s</h2>' % (m.group(2).replace('"', '').replace("'", ""), m.group(1)), h)
    h = re.sub(r'(<h2 id="preamble">מבוא</h2>\s*)<p>', r'\1<p class="preamble">', h)
    h = linkify(h, "", "internal")
    # source panel after each section
    def panel(m):
        n = int(m.group(2))
        s = secs.get(n, {})
        lvl = s.get("lvl", "sq")
        parts = ['<div class="src lvl-%s" id="src-%d" hidden><dl>' % (lvl, n)]
        parts.append('<div><dt>רמת הסכמה</dt><dd><b>%s</b> · %s</dd></div>' % (lvl_text(s), linkify(html.escape(s.get("level_text", "")), "")))
        parts.append('<div><dt>מה נקבע</dt><dd>%s</dd></div>' % linkify(html.escape(s.get("what", "")), ""))
        parts.append('<div><dt>מקורות</dt><dd>%s</dd></div>' % linkify(html.escape(s.get("sources", "")), ""))
        if refmap.get(n):
            links = " · ".join('<a href="disputes.html#%s">%s</a>' % (i, html.escape(t)) for i, t in refmap[n])
            parts.append('<div><dt>במסמך המחלוקות</dt><dd>%s</dd></div>' % links)
        parts.append('</dl><div class="src-actions"><button type="button" class="copy-link" data-sec="%d">העתקת קישור לסעיף</button><span class="copy-status" role="status"></span></div></div>' % n)
        return m.group(1) + "".join(parts)
    h = re.sub(r'(<p class="sec" id="s-(\d+)".*?</p>)', panel, h, flags=re.S)
    chap_list = re.findall(r'<h2 id="(ch-[^"]+)">([^<]+)</h2>', h)
    rail = '<nav class="rail" aria-label="פרקים"><h2>תוכן</h2><ol><li><a href="#preamble">מבוא</a></li>%s<li><a href="#appendix">נספח מקורות</a></li></ol></nav>' % "".join('<li data-ch="%s"><a href="#%s">%s</a></li>' % (i, i, t) for i, t in chap_list)
    mobile = '<details class="rail-mobile no-print"><summary>תוכן העניינים</summary><ol>%s</ol></details>' % "".join('<li><a href="#%s">%s</a></li>' % (i, t) for i, t in [("preamble", "מבוא")] + chap_list + [("appendix", "נספח מקורות")])
    ah = md_to_html("## נספח מקורות" + appx_md)
    ah = ah.replace("<h2>נספח מקורות</h2>", '<h2 id="appendix">נספח מקורות</h2>')
    ah = '<section id="appendix-wrap">%s</section>' % wrap_tables(pills(linkify(ah, "")))
    # explorer
    lg, counts = legend(secs, True)
    pcounts = {k: sum(1 for s in secs.values() if k in s["parties"]) for k, _, _ in PARTIES}
    party_chips = "".join('<button type="button" class="chip" data-party="%s" aria-pressed="false"><span class="chip-label">%s</span><span class="chip-n">%d</span></button>' % (k, l, pcounts[k]) for k, l, _ in PARTIES)
    explorer = f"""<section class="explorer no-print" aria-label="חיפוש וסינון">
<div class="ex-search"><label for="q" class="sr">חיפוש בחוקה</label><input id="q" type="search" placeholder="חיפוש בחוקה: שירות, יועץ משפטי, שבת…" autocomplete="off" enterkeyhint="search"></div>
<div class="ex-row"><span class="ex-label">רמת הסכמה</span><div class="chips">{lg}</div></div>
<div class="ex-row"><span class="ex-label">מפלגה כמקור</span><div class="chips">{party_chips}</div></div>
{agreement_map(secs, chapters, "")}
<div class="ex-foot"><p class="ex-status" id="ex-status" aria-live="polite">כל ריבוע הוא סעיף; ריבוע בשני צבעים הוא סעיף שחלקיו ברמות הסכמה שונות. לחיצה על ריבוע, או על התווית שליד כותרת הסעיף, פותחת את המקורות.</p><button type="button" class="ex-clear" id="ex-clear" hidden>ניקוי הסינון</button></div>
</section>"""
    return rail, mobile, explorer, h, ah


def doc_title(text):
    first = text.split("\n", 1)[0]
    return first[2:].strip() if first.startswith("# ") else ""


def build_generic(text, slug):
    body_md = text.split("\n", 1)[1]
    h = id_headings(md_to_html(body_md))
    mode = "default" if slug in ("letter", "summary", "disputes") else "strict"
    h = wrap_tables(pills(tags(linkify(h, "constitution.html", mode))))
    heads = re.findall(r'<h2 id="(d-\d+)">(.+?)</h2>', h)
    toc = ""
    if len(heads) >= 4:
        toc = '<details class="toc no-print"><summary>תוכן העניינים</summary><ol>%s</ol></details>' % "".join(
            '<li><a href="#%s">%s</a></li>' % (i, re.sub(r"<[^>]+>", "", t)) for i, t in heads)
    return toc + h


def law_subnav(current):
    items = ['<a href="laws.html">שלושת החוקים</a>']
    for slug, kind, name, _ in LAWS:
        cur = ' aria-current="page"' if slug == current else ""
        items.append('<a href="%s.html"%s>%s</a>' % (slug, cur, PAGE[slug]["label"]))
    cur = ' aria-current="page"' if current == "deferral-decision" else ""
    items.append('<a href="deferral-decision.html"%s>%s</a>' % (cur, PAGE["deferral-decision"]["label"]))
    return '<nav class="subnav no-print" aria-label="שלושת החוקים">%s</nav>' % "".join(items)


def page_meta(pdf):
    return '<div class="meta"><span>טיוטה לדיון · %s</span><a class="pdf" href="pdf/%s" download>הורדה כ-PDF</a></div>' % (TODAY, pdf)


def write(name, content):
    (ROOT / name).write_text(content, encoding="utf-8")


def card(num, slug, label, desc, extra=""):
    p = PAGE[slug]
    num_html = f'<span class="num">{num}</span>' if num else ""
    return (f'<div class="card">{num_html}<h3><a href="{slug}.html">{label}</a></h3><p>{desc}</p>{extra}'
            f'<div class="links"><a href="{slug}.html">לקריאה</a><a href="pdf/{p["pdf"]}" download>PDF</a></div></div>')


def main():
    const_text = (DOCS / "constitution.md").read_text(encoding="utf-8")
    disp_text = (DOCS / "disputes.md").read_text(encoding="utf-8")
    secs, chapters = load_sections(const_text)
    refmap = disputes_index(disp_text)

    for p in PAGES:
        slug = p["slug"]
        text = (DOCS / p["md"]).read_text(encoding="utf-8")
        title = p["title"] or doc_title(text)
        p["full_title"] = title
        if slug == "constitution":
            rail, mobile, explorer, h, ah = build_constitution(text, secs, chapters, refmap)
            body = f'<main class="page with-rail">{rail}<article class="doc legal"><h1>{title}</h1><p class="lede">{p["lede"]}</p>{page_meta(p["pdf"])}{explorer}{mobile}{h}{ah}</article></main><div class="toast" id="toast" role="status" hidden></div><script src="assets/app.js" defer></script>'
        else:
            h = build_generic(text, slug)
            sub = law_subnav(slug) if p.get("group") == "laws" else ""
            body = f'<main class="page"><article class="doc">{sub}<h1>{title}</h1><p class="lede">{p["lede"]}</p>{page_meta(p["pdf"])}{h}</article></main>'
        write(slug + ".html", shell(title, body, slug, p["lede"]))

    # --- the three laws: hub page ---
    law_cards = "".join(card(kind, slug, name, desc) for slug, kind, name, desc in LAWS)
    law_cards += card("מסמך נלווה לחוק השוויון בנטל", "deferral-decision", PAGE["deferral-decision"]["label"], PAGE["deferral-decision"]["lede"])
    laws_lede = "שלושת התוצרים המשפטיים של קבוצה ב'. לפי תוכנית 100 הימים, ביום הראשון שלה תחליט הממשלה על ועדת החקירה ותאשר את הצעת חוק הגבלת הכהונה ואת הצעת חוק השוויון בנטל."
    laws_body = f'<main class="page" style="grid-template-columns: minmax(0, 1120px)"><section class="hero"><h1>שלושת החוקים</h1><p>{laws_lede}</p></section><div class="cards">{law_cards}</div></main>'
    write("laws.html", shell("שלושת החוקים", laws_body, "laws", laws_lede))

    # --- home ---
    open_n = disp_text.count("- [ ] ")
    done_n = disp_text.count("- [x] ")
    guide_n = len(re.findall(r"^\*\*\d{1,2}\.\d{1,2}\*\*", (DOCS / "guidelines.md").read_text(encoding="utf-8"), flags=re.M))
    home_legend, _ = legend(secs, False)
    home_map = agreement_map(secs, chapters, "constitution.html")
    start = card("", "letter", "מכתב הסבר", PAGE["letter"]["lede"]) + card("", "summary", "תקציר", PAGE["summary"]["lede"])
    law_links = '<ul class="card-list">%s</ul>' % "".join('<li><a href="%s.html">%s</a> <span>· %s</span></li>' % (s, n, k) for s, k, n, _ in LAWS)
    order = (card("1", "constitution", "החוקה", PAGE["constitution"]["lede"])
             + card("2", "guidelines", "קווי היסוד לממשלה", "המבוא, חמשת פרקי הליבה — חוקה, ועדת חקירה, שוויון בנטל, הגבלת כהונה ו-100 הימים — ושבעה פרקי תחום.")
             + f'<div class="card"><span class="num">3</span><h3><a href="laws.html">שלושת החוקים</a></h3><p>הנוסחים שהממשלה תביא ביום הראשון שלה.</p>{law_links}<div class="links"><a href="laws.html">לכל השלושה</a></div></div>'
             + card("4", "100-days", "תוכנית 100 הימים", PAGE["100-days"]["lede"]))
    across = card("לכל התוצרים", "disputes", "מחלוקות וחלופות", PAGE["disputes"]["lede"])
    home = f'''<main class="page" style="grid-template-columns: minmax(0, 1120px)">
<section class="hero">
<div class="stamp">טיוטות לדיון · {TODAY}</div>
<h1>החוקה ותוצרי קבוצה ב', ברוח מסמך העקרונות של ראשי מפלגות התיקון והתקווה</h1>
<p>מסמך העקרונות של ראשי ביחד, ישראל ביתנו, הדמוקרטים וישר! (26.9.2026) הטיל על קבוצה ב' לגבש את קווי היסוד לממשלה הבאה, ובהם חוק השוויון בנטל, ועדת חקירה ממלכתית לטבח השבעה באוקטובר, הגבלת כהונה לראש הממשלה, חוקה ותוכנית פעולה ל-100 הימים הראשונים. המסמכים כאן נוסחו אך ורק מתוך העמדות הפומביות של ארבע המפלגות, ולכל סעיף יש מקור.</p>
<p>מה שמוסכם על כל הארבע, או על שלוש כשהרביעית אינה מתנגדת, נכנס כנוסח מחייב. מה ששנוי במחלוקת נוסח לפי המכנה המשותף הצר או הופנה לחוק, והחלופות נרשמו. מה שאין עליו עמדה של אף מפלגה נשאר כדין הקיים.</p>
</section>
<div class="facts">
<div class="fact"><b>100</b><span>סעיפים בחוקה</span></div>
<div class="fact"><b>{guide_n}</b><span>סעיפים בקווי היסוד</span></div>
<div class="fact"><b>3</b><span>נוסחים משפטיים: שתי הצעות חוק והחלטת ממשלה</span></div>
<div class="fact"><b>29</b><span>פעולות בתוכנית 100 הימים</span></div>
<div class="fact"><b>{open_n}</b><span>הכרעות פתוחות לראשי המפלגות</span></div>
<div class="fact"><b>{done_n}</b><span>הכרעות שכבר התקבלו</span></div>
</div>
<h2 class="home-h">להתחיל כאן</h2>
<div class="cards cards-2">{start}</div>
<h2 class="home-h">המסמכים, לפי הסדר</h2>
<div class="cards cards-4">{order}</div>
<div class="cards cards-1">{across}</div>
<section class="home-map">
<h2>מפת ההסכמה בחוקה</h2>
<p>כל ריבוע הוא סעיף בחוקה, צבוע לפי רמת ההסכמה עליו. ריבוע בשני צבעים הוא סעיף שחלקיו ברמות שונות, למשל סעיף קטן (א) מוסכם על כל 4 וסעיף קטן (ב) לפי מכנה צר; לכן סעיף נספר בכל רמה שמופיעה בו. לחיצה פותחת את הסעיף עם המקורות.</p>
<div class="chips">{home_legend}</div>
{home_map}
</section>
<section class="method">
<h2>איך לקרוא</h2>
<ol>
<li><a href="letter.html">מכתב ההסבר</a> ו<a href="summary.html">התקציר</a> — כל התוצרים במבט אחד, בשפה לא משפטית.</li>
<li><a href="constitution.html">החוקה</a>: כל סעיף ממוספר, ההפניות בין סעיפים לחיצות, ולכל סעיף — מקורות ורמת הסכמה.</li>
<li><a href="guidelines.html">קווי היסוד</a>, <a href="laws.html">שלושת החוקים</a> ו<a href="100-days.html">תוכנית 100 הימים</a>: ליד כל סעיף מסומנת רמת ההסכמה עליו (4/4, 3+, צר, גישור), ובסוף כל מסמך — נספח מקורות.</li>
<li><a href="disputes.html">מסמך המחלוקות</a>: לכל נושא — עמדת כל מפלגה עם מקור ותאריך, הנוסח שנבחר, החלופות, ובסוף רשימת ההכרעות.</li>
</ol>
<h2>מה זה לא</h2>
<p>לא נוסח סופי ולא מסמך מטעם המפלגות. ההכרעות שהתקבלו במטה מסומנות, וכולן טעונות אישור ראשי המפלגות. חלק מהעמדות לקוח מתשובות לשאלוני עיתונים ומראיונות, לא מהתחייבויות מחייבות; כל ציטוט מובא עם הדובר, המקור והתאריך. תיקונים והערות — דרך הריפו ב-GitHub.</p>
</section>
</main>'''
    write("index.html", shell("החוקה ותוצרי קבוצה ב' — טיוטות לדיון", home, "index", "החוקה, קווי היסוד לממשלה, שלושת החוקים ותוכנית 100 הימים — נוסחו מעמדות ביחד, ישראל ביתנו, הדמוקרטים וישר!"))
    print("built: index, laws +", ", ".join(p["slug"] for p in PAGES), "| open:", open_n, "done:", done_n, "| guideline clauses:", guide_n)


if __name__ == "__main__":
    main()
