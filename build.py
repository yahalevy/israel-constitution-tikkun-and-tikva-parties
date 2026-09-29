# -*- coding: utf-8 -*-
"""Builds the static site from docs/*.md.  Run:  python3 build.py"""
import re, html, datetime, pathlib
import markdown

ROOT = pathlib.Path(__file__).parent
DOCS = ROOT / "docs"
TODAY = "29.9.2026"

PAGES = [
    # slug, md file, nav label, page title, lede, pdf name
    ("summary", "summary.md", "תקציר", "תקציר החוקה", "עמוד אחד: מה המסמך, מבנה החוקה פרק-פרק, ומה נשאר להכרעה.", "תקציר-החוקה.pdf"),
    ("constitution", "constitution.md", "החוקה", "חוקה למדינת ישראל — טיוטה", "100 סעיפים ב-12 פרקים, ונספח מקורות המציין לכל סעיף על איזו עמדה מפלגתית הוא נשען.", "חוקה-טיוטה.pdf"),
    ("disputes", "disputes.md", "מחלוקות וחלופות", "מחלוקות וחלופות — מה לא נכנס לחוקה ולמה", "כל נושא שנוי במחלוקת: עמדת כל מפלגה עם מקור, הנוסח שנבחר, החלופות, ורשימת ההכרעות הנדרשות.", "מחלוקות-וחלופות.pdf"),
    ("letter", "letter.md", "מכתב הסבר", "מכתב הסבר — החוקה והתהליך שמאחוריה", "למה חוקה ולמה עכשיו, איך נוסח המסמך, עיקרי החוקה ומה הלאה.", "מכתב-הסבר.pdf"),
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

def build_constitution(text):
    body_md = text.split("\n", 1)[1]  # drop H1
    # split off appendix
    main_md, _, appx_md = body_md.partition("\n## נספח מקורות")
    h = md_to_html(main_md)
    # section paragraphs
    def sec(m):
        n = m.group(1)
        return '<p class="sec" id="s-%s"><strong><a href="#s-%s">%s.</a> %s</strong>' % (n, n, n, m.group(2))
    h = re.sub(r'<p><strong>(\d{1,3})\. ([^<]+?)</strong>', sec, h)
    h = h.replace('<h2>מבוא</h2>', '<h2 id="preamble">מבוא</h2>')
    h = re.sub(r"<h2>(פרק ([א-ת\"']+) — [^<]+)</h2>", lambda m: '<h2 id="ch-%s">%s</h2>' % (m.group(2).replace('"', '').replace("'", ""), m.group(1)), h)
    # preamble paragraph
    h = re.sub(r'(<h2 id="preamble">מבוא</h2>\s*)<p>', r'\1<p class="preamble">', h)
    h = linkify(h, "")
    chapters = re.findall(r'<h2 id="(ch-[^"]+)">([^<]+)</h2>', h)
    rail = '<nav class="rail" aria-label="פרקים"><h2>תוכן</h2><ol><li><a href="#preamble">מבוא</a></li>%s<li><a href="#appendix">נספח מקורות</a></li></ol></nav>' % "".join('<li><a href="#%s">%s</a></li>' % (i, t) for i, t in chapters)
    mobile = '<details class="rail-mobile no-print"><summary>תוכן העניינים</summary><ol>%s</ol></details>' % "".join('<li><a href="#%s">%s</a></li>' % (i, t) for i, t in [("preamble", "מבוא")] + chapters + [("appendix", "נספח מקורות")])
    ah = md_to_html("## נספח מקורות" + appx_md)
    ah = ah.replace("<h2>נספח מקורות</h2>", '<h2 id="appendix">נספח מקורות</h2>')
    ah = wrap_tables(pills(linkify(ah, "")))
    return rail, mobile, h, ah

def build_generic(text, slug):
    body_md = text.split("\n", 1)[1]
    h = md_to_html(body_md)
    h = wrap_tables(pills(linkify(h, "constitution.html")))
    return h

def page_meta(pdf):
    return '<div class="meta"><span>טיוטה לדיון · %s</span><a class="pdf" href="pdf/%s" download>הורדה כ-PDF</a></div>' % (TODAY, pdf)

def write(name, content):
    (ROOT / name).write_text(content, encoding="utf-8")

for slug, fname, label, title, lede, pdf in PAGES:
    text = (DOCS / fname).read_text(encoding="utf-8")
    if slug == "constitution":
        rail, mobile, h, ah = build_constitution(text)
        body = f'<main class="page with-rail">{rail}<article class="doc legal"><h1>{title}</h1><p class="lede">{lede}</p>{page_meta(pdf)}{mobile}{h}{ah}</article></main>'
    else:
        h = build_generic(text, slug)
        body = f'<main class="page"><article class="doc"><h1>{title}</h1><p class="lede">{lede}</p>{page_meta(pdf)}{h}</article></main>'
    write(slug + ".html", shell(title, body, slug, lede))

# --- home ---
disp = (DOCS / "disputes.md").read_text(encoding="utf-8")
open_n = disp.count("- [ ] ")
done_n = disp.count("- [x] ")
cards = ""
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
<section class="method">
<h2>איך לקרוא</h2>
<ol>
<li>מתחילים מ<a href="summary.html">התקציר</a> — עמוד אחד עם מבנה החוקה ומה נשאר להכרעה.</li>
<li><a href="constitution.html">החוקה</a> עצמה: כל סעיף ממוספר, ההפניות בין סעיפים לחיצות, ובסוף נספח מקורות עם רמת ההסכמה על כל סעיף.</li>
<li><a href="disputes.html">מסמך המחלוקות</a>: לכל נושא — עמדת כל מפלגה עם מקור ותאריך, הנוסח שנבחר, החלופות, ובסוף רשימת ההכרעות.</li>
<li><a href="letter.html">מכתב ההסבר</a> נועד לפרסום: התהליך ועיקרי הדברים בשפה לא משפטית.</li>
</ol>
<h2>מה זה לא</h2>
<p>לא נוסח סופי ולא מסמך מטעם המפלגות. חלק מהעמדות לקוח מתשובות לשאלוני עיתונים ומראיונות, לא מהתחייבויות מחייבות; כל ציטוט מובא עם הדובר, המקור והתאריך. תיקונים והערות — דרך הריפו ב-GitHub.</p>
</section>
</main>'''
write("index.html", shell("חוקה ברוח מסמך העקרונות — טיוטה לדיון", home, "index", "טיוטת חוקה למדינת ישראל שנוסחה מעמדות ביחד, ישראל ביתנו, הדמוקרטים וישר!"))
print("built: index +", ", ".join(p[0] for p in PAGES), "| open:", open_n, "done:", done_n)
