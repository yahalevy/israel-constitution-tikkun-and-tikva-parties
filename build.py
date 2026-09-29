# -*- coding: utf-8 -*-
"""Builds the static site from docs/*.md.  Run:  python3 build.py"""
import re, html, datetime, pathlib
import markdown

ROOT = pathlib.Path(__file__).parent
DOCS = ROOT / "docs"
TODAY = "29.9.2026"

PAGES = [
    # slug, md file, nav label, page title, lede, pdf name
    ("letter", "letter.md", "מכתב הסבר", "מכתב הסבר — החוקה והתהליך שמאחוריה", "למה חוקה ולמה עכשיו, איך נוסח המסמך, עיקרי החוקה ומה הלאה.", "מכתב-הסבר.pdf"),
    ("summary", "summary.md", "תקציר", "תקציר החוקה", "עמוד אחד: מה המסמך, מבנה החוקה פרק-פרק, ומה נשאר להכרעה.", "תקציר-החוקה.pdf"),
    ("constitution", "constitution.md", "החוקה", "חוקה למדינת ישראל — טיוטה", "100 סעיפים ב-12 פרקים, ונספח מקורות המציין לכל סעיף על איזו עמדה מפלגתית הוא נשען.", "חוקה-טיוטה.pdf"),
    ("disputes", "disputes.md", "מחלוקות וחלופות", "מחלוקות וחלופות — מה לא נכנס לחוקה ולמה", "כל נושא שנוי במחלוקת: עמדת כל מפלגה עם מקור, הנוסח שנבחר, החלופות, ורשימת ההכרעות הנדרשות.", "מחלוקות-וחלופות.pdf"),
]

def nav(current):
    items = ['<a href="index.html"%s>בית</a>' % (' aria-current="page"' if current == "index" else "")]
    for slug, _, label, *_ in PAGES:
        cur = ' aria-current="page"' if slug == current else ""
        items.append('<a href="%s.html"%s>%s</a>' % (slug, cur, label))
    return '<header class="topbar"><div class="topbar-inner"><a class="brand" href="index.html">חוקה ברוח מסמך העקרונות</a><nav class="nav">%s</nav></div></header>' % "".join(items)

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
<footer>טיוטה לדיון, {TODAY}. נוסחה מתוך המצעים, העקרונות וההצהרות הפומביות של ביחד, ישראל ביתנו, הדמוקרטים וישר!, בהתאם למסמך העקרונות של ראשי המפלגות מיום 26.9.2026. אינה נוסח סופי ואינה מחייבת את המפלגות.</footer>
</body>
</html>'''

XREF = re.compile(r"(?<![\w-])(סעיפים|סעיף|ס')\s+(\d{1,3})((?:\([א-ת]\))?(?:\(\d+\))?)")
CHAIN = re.compile(r"(?<=[,\s])(ו-|-)?(\d{1,3})(\([א-ת]\))?(?=[,\s.;:)]|$)")

def link_sections(fragment, prefix):
    """Turn 'סעיף 23', 'ס' 92(א)' and chains like 'סעיפים 43 ו-92' into links to #s-N."""
    out = []
    pos = 0
    for m in XREF.finditer(fragment):
        out.append(fragment[pos:m.start()])
        word, num, sub = m.group(1), m.group(2), m.group(3)
        out.append('%s <a class="xref" href="%s#s-%s">%s%s</a>' % (word, prefix, num, num, sub))
        pos = m.end()
        if word == "סעיפים":
            # continue the chain: ", 38(ד) ו-52(ב)"
            tail = fragment[pos:]
            cm = re.match(r"((?:,\s*|\s+ו-)\d{1,3}(?:\([א-ת]\))?)+", tail)
            if cm:
                chain = cm.group(0)
                chain = re.sub(r"(\d{1,3})(\([א-ת]\))?", lambda x: '<a class="xref" href="%s#s-%s">%s%s</a>' % (prefix, x.group(1), x.group(1), x.group(2) or ""), chain)
                out.append(chain)
                pos += cm.end()
    out.append(fragment[pos:])
    return "".join(out)

def linkify(html_text, prefix):
    # only outside tags
    parts = re.split(r"(<[^>]+>)", html_text)
    return "".join(p if p.startswith("<") else link_sections(p, prefix) for p in parts)

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
        nums.add(int(m.group(2)))
        if m.group(1) == "סעיפים":
            cm = re.match(r"((?:,\s*|\s+ו-)\d{1,3}(?:\([א-ת]\))?)+", text[m.end():])
            if cm:
                nums.update(int(x) for x in re.findall(r"\d{1,3}", cm.group(0)))
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
    h = linkify(h, "")
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

def build_generic(text, slug):
    body_md = text.split("\n", 1)[1]
    h = md_to_html(body_md)
    if slug == "disputes":
        h = id_headings(h)
    h = wrap_tables(pills(linkify(h, "constitution.html")))
    return h

def page_meta(pdf):
    return '<div class="meta"><span>טיוטה לדיון · %s</span><a class="pdf" href="pdf/%s" download>הורדה כ-PDF</a></div>' % (TODAY, pdf)

def write(name, content):
    (ROOT / name).write_text(content, encoding="utf-8")

CONST_TEXT = (DOCS / "constitution.md").read_text(encoding="utf-8")
DISP_TEXT = (DOCS / "disputes.md").read_text(encoding="utf-8")
SECS, CHAPTERS = load_sections(CONST_TEXT)
REFMAP = disputes_index(DISP_TEXT)

for slug, fname, label, title, lede, pdf in PAGES:
    text = (DOCS / fname).read_text(encoding="utf-8")
    if slug == "constitution":
        rail, mobile, explorer, h, ah = build_constitution(text, SECS, CHAPTERS, REFMAP)
        body = f'<main class="page with-rail">{rail}<article class="doc legal"><h1>{title}</h1><p class="lede">{lede}</p>{page_meta(pdf)}{explorer}{mobile}{h}{ah}</article></main><div class="toast" id="toast" role="status" hidden></div><script src="assets/app.js" defer></script>'
    else:
        h = build_generic(text, slug)
        body = f'<main class="page"><article class="doc"><h1>{title}</h1><p class="lede">{lede}</p>{page_meta(pdf)}{h}</article></main>'
    write(slug + ".html", shell(title, body, slug, lede))

# --- home ---
disp = DISP_TEXT
open_n = disp.count("- [ ] ")
done_n = disp.count("- [x] ")
cards = ""
home_legend, _ = legend(SECS, False)
home_map = agreement_map(SECS, CHAPTERS, "constitution.html")
for i, (slug, fname, label, title, lede, pdf) in enumerate(PAGES, 1):
    cards += f'<div class="card"><span class="num">מסמך {i}</span><h2><a href="{slug}.html">{label}</a></h2><p>{lede}</p><div class="links"><a href="{slug}.html">לקריאה</a><a href="pdf/{pdf}" download>PDF</a></div></div>'
home = f'''<main class="page" style="grid-template-columns: minmax(0, 1120px)">
<section class="hero">
<div class="stamp">טיוטה לדיון · {TODAY}</div>
<h1>חוקה למדינת ישראל ברוח מסמך העקרונות של ראשי מפלגות התיקון והתקווה</h1>
<p>ביום 26.9.2026 הסכימו ראשי ביחד, ישראל ביתנו, הדמוקרטים וישר! שקבוצת עבודה אחת תנסח חוקה. הטיוטה כאן נבנתה אך ורק מהמצעים, מהעקרונות ומההצהרות הפומביות של ארבע המפלגות: מה שמוסכם נכנס, מה ששנוי במחלוקת נוסח לפי המכנה המשותף הצר או הופנה לחוק, ומה שאין עליו עמדה נשאר כדין הקיים.</p>
</section>
<div class="facts">
<div class="fact"><b>100</b><span>סעיפים ב-12 פרקים</span></div>
<div class="fact"><b>4</b><span>מפלגות — כל סעיף עם מקור</span></div>
<div class="fact"><b>{open_n}</b><span>הכרעות פתוחות לראשי המפלגות</span></div>
<div class="fact"><b>{done_n}</b><span>הכרעות שכבר התקבלו</span></div>
</div>
<div class="cards">{cards}</div>
<section class="home-map">
<h2>מפת ההסכמה</h2>
<p>כל ריבוע הוא סעיף בחוקה, צבוע לפי רמת ההסכמה עליו. ריבוע בשני צבעים הוא סעיף שחלקיו ברמות שונות, למשל סעיף קטן (א) מוסכם על כל 4 וסעיף קטן (ב) לפי מכנה צר; לכן סעיף נספר בכל רמה שמופיעה בו. לחיצה פותחת את הסעיף עם המקורות.</p>
<div class="chips">{home_legend}</div>
{home_map}
</section>
<section class="method">
<h2>איך לקרוא</h2>
<ol>
<li><a href="letter.html">מכתב ההסבר</a> — למה חוקה ולמה עכשיו, איך נוסחה ועיקרי הדברים, בשפה לא משפטית.</li>
<li><a href="summary.html">התקציר</a> — עמוד אחד עם מבנה החוקה פרק-פרק ומה נשאר להכרעה.</li>
<li><a href="constitution.html">החוקה</a> עצמה: כל סעיף ממוספר, ההפניות בין סעיפים לחיצות, ובסוף נספח מקורות עם רמת ההסכמה על כל סעיף.</li>
<li><a href="disputes.html">מסמך המחלוקות</a>: לכל נושא — עמדת כל מפלגה עם מקור ותאריך, הנוסח שנבחר, החלופות, ובסוף רשימת ההכרעות.</li>
</ol>
<h2>מה זה לא</h2>
<p>לא נוסח סופי ולא מסמך מטעם המפלגות. חלק מהעמדות לקוח מתשובות לשאלוני עיתונים ומראיונות, לא מהתחייבויות מחייבות; כל ציטוט מובא עם הדובר, המקור והתאריך. תיקונים והערות — דרך הריפו ב-GitHub.</p>
</section>
</main>'''
write("index.html", shell("חוקה ברוח מסמך העקרונות — טיוטה לדיון", home, "index", "טיוטת חוקה למדינת ישראל שנוסחה מעמדות ביחד, ישראל ביתנו, הדמוקרטים וישר!"))
print("built: index +", ", ".join(p[0] for p in PAGES), "| open:", open_n, "done:", done_n)
