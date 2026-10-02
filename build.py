# -*- coding: utf-8 -*-
"""Builds the static site from docs/*.md.  Run:  python3 build.py"""
import re, html, pathlib
import markdown

ROOT = pathlib.Path(__file__).parent
DOCS = ROOT / "docs"
TODAY = "1.10.2026"

# The home page is the summary of Group B's work, in the order of the mandate:
# the guidelines as the frame, then their five core chapters, each with its own page.
# glance: (label, value, tag) tiles taken from the guidelines' own clauses and the summary.
PAGES = [
    dict(slug="guidelines", md="guidelines.md", label="קווי היסוד", title="קווי היסוד של ממשלת התיקון",
         kind="מסמך מאגד · 68 סעיפים", dispute="קווי היסוד", pdf="קווי-היסוד-לממשלה.pdf",
         lede="המסגרת של כל התוצרים: מבוא, חמישה פרקי ליבה — חמשת נושאי המנדט — ושבעה פרקי תחום, עם רמת ההסכמה על כל סעיף, מה לא נכלל ולמה, ונספח מקורות.",
         glance=[("מה זה", "68 סעיפים: מבוא, חמישה פרקי ליבה ושבעה פרקי תחום", ""),
                 ("מחייב את", "ארבע המפלגות, שיקימו יחד את ממשלת התיקון (0.1)", "4/4"),
                 ("מה שלא הוכרע", "בהסכמת ראשי ארבע המפלגות; עד אז — נוסח ברירת המחדל (0.4)", "הוכרע במטה"),
                 ("המחלוקת המדינית", "הליך בלבד; אין הכרעה בריבונות, בגבולות ובמדינה פלסטינית (12.5)", "הליך")]),
    dict(slug="constitution", md="constitution.md", label="חוקה", title="חוקה למדינת ישראל — טיוטה", chapter=1,
         kind="טיוטת חוקה · 100 סעיפים ב-12 פרקים", dispute="מחלוקות חוקתיות", pdf="חוקה-טיוטה.pdf",
         lede="100 סעיפים ב-12 פרקים, ונספח מקורות המציין לכל סעיף על איזו עמדה מפלגתית הוא נשען.",
         glance=[("מבוא", "הכרזת העצמאות; החוקה תפורש לאורה", ""),
                 ("תיקון", "ברוב 80 בקריאה השנייה והשלישית (ס' 92)", "הוכרע במטה"),
                 ("כינון", "בכנסת ברוב 80, ואחר כך במשאל עם (ס' 95)", "הוכרע במטה"),
                 ("השפיטה", "ביטול התיקון לחוק-יסוד: השפיטה מ-2025 (ס' 99(א))", "4/4")]),
    dict(slug="inquiry", md="inquiry.md", label="ועדת חקירה", title=None, chapter=2,
         kind="טיוטת החלטת ממשלה", dispute="ועדת חקירה ממלכתית", pdf="ועדת-חקירה-ממלכתית.pdf",
         lede="טיוטת החלטת ממשלה לפי חוק ועדות חקירה, נוסחים חלופיים, הצעת חוק ייעודית כחלופה, דברי הסבר ונספח מקורות.",
         glance=[("מתי", "ההחלטה הראשונה של הממשלה (קווי היסוד 2.1)", "4/4"),
                 ("לפי", "חוק ועדות חקירה, התשכ\"ט–1968 — בהחלטת ממשלה, בלי חוק ייעודי (2.5)", "הוכרע במטה"),
                 ("הרכב", "שלושה חברים שימנה נשיא בית המשפט העליון; חמישה, אם יודיע הנשיא שראוי כך (2.5)", "הוכרע במטה"),
                 ("נושא החקירה", "מה שקדם לטבח, הטבח והמלחמה שבעקבותיו — כולל הדרג המדיני ואחריות אישית (2.3)", "4/4")]),
    dict(slug="equal-burden", md="equal-burden.md", label="שוויון בנטל", title=None, chapter=3,
         kind="הצעת חוק · 32 סעיפים ותוספת", dispute="חוק השוויון בנטל", pdf="הצעת-חוק-השוויון-בנטל.pdf",
         lede="הצעת חוק שירות ממלכתי: נוסח ההצעה, דברי הסבר, הכרעות ניסוח, נקודות פתוחות ונספח מקורות.",
         glance=[("חובה", "שירות צבאי או אזרחי לכל אזרח (קווי היסוד 3.1)", "4/4"),
                 ("פטור", "אין פטור לציבור שלם או לסוג שלם של אזרחים (3.2)", "4/4"),
                 ("לימוד תורה", "מסלול בתוך השירות — שנה אחת לכל היותר, וצה\"ל קובע את המספר (3.5)", "4/4, גישור"),
                 ("מתי", "ההצעה הראשונה שהממשלה מניחה; השלמה במושב הראשון (5.4)", "הוכרע במטה")]),
    dict(slug="deferral-decision", md="deferral-decision.md", label="ההכרעה על היקף הדחייה", title=None, parent="equal-burden",
         kind="מסמך הכרעה לחוק השוויון בנטל", dispute="חוק השוויון בנטל", pdf="הכרעה-היקף-הדחייה.pdf",
         lede="תוצאות המשא ומתן בין נציגי ארבע המפלגות: הנוסח המוסכם, ההכרעה בדחייה בשל לימוד תורה ומצוינות, החלופות שנרשמו והאישורים החסרים.",
         glance=[("התוצאה", "אין דחייה בשל לימוד או הישגים; לימוד תורה במסלול בתוך השירות", "4/4, גישור"),
                 ("הדרך", "שישה סבבי משא ומתן, נציג מטה לכל מפלגה", ""),
                 ("מעמד", "הצעת מטה; טעונה אישור ראשי המפלגות", "")]),
    dict(slug="term-limits", md="term-limits.md", label="הגבלת כהונה", title=None, chapter=4,
         kind="הצעת חוק-יסוד", dispute="הגבלת כהונת ראש הממשלה", pdf="הצעת-חוק-יסוד-הגבלת-כהונה.pdf",
         lede="נוסח ההצעה, דברי הסבר, הכרעות ניסוח, ההתאמות בחוקה, נקודות פתוחות ונספח מקורות.",
         glance=[("עצם ההגבלה", "כל ארבע המפלגות (קווי היסוד 4.1)", "4/4"),
                 ("המשך", "שמונה שנים או שתי תקופות כהונה מלאות, לפי הארוך מביניהם (4.2)", "הוכרע במטה"),
                 ("שריון", "שינוי רק ברוב 80 (4.3)", "הוכרע במטה"),
                 ("מתי", "אישור בישיבת הממשלה הראשונה; חקיקה במושב הראשון (4.4)", "הוכרע במטה")]),
    dict(slug="100-days", md="100-days.md", label="100 הימים", title=None, chapter=5,
         kind="תוכנית · 29 פעולות", dispute="תוכנית 100 הימים", pdf="תוכנית-100-הימים.pdf",
         lede="משלב 0 (מהבחירות ועד כינון הממשלה) ועד יום 100 — לכל פעולה מועד, אחראי ומקור — ומה לא נכלל ולמה.",
         glance=[("יום 1", "ועדת החקירה — ההחלטה הראשונה של הממשלה (קווי היסוד 5.2)", "4/4"),
                 ("לפני כינון הממשלה", "אין חקיקה; חוק היועץ המשפטי לממשלה יבוטל בהקדם אחרי הכינון (5.3)", "הוכרע במטה"),
                 ("סדר החקיקה", "חוק השוויון בנטל ראשון; ביטולי החקיקה במקביל (5.4)", "הוכרע במטה"),
                 ("עד יום 100", "ביטול התיקון לחוק-יסוד: השפיטה, הנחת תקציב 2027, ורשימת חוקי הכנסת ה-25 לבחינה", "")]),
    dict(slug="disputes", md="disputes.md", label="מחלוקות", title="מחלוקות וחלופות — בכל התוצרים",
         kind="מסמך מחלוקות", pdf="מחלוקות-וחלופות.pdf",
         lede="כל נושא שנוי במחלוקת: עמדת כל מפלגה עם מקור, הנוסח שנבחר, החלופות, ורשימת ההכרעות הנדרשות מראשי המפלגות."),
    dict(slug="letter", md="letter.md", label="על המסמכים", title=None,
         kind="מכתב הסבר", pdf="מכתב-הסבר.pdf",
         lede="על מה המסמכים, איך נוסחו, עיקרי התוצרים ומה הלאה — בשפה לא משפטית."),
    # the summary is now the home page; the page stays so old links and its PDF keep working
    dict(slug="summary", md="summary.md", label="תקציר", title=None, nav=False,
         kind="תקציר", pdf="תקציר-התוצרים.pdf",
         lede="עמוד אחד: כל תוצר במבט אחד, עיקרי החוקה ומה נשאר להכרעת ראשי המפלגות."),
]
PAGE = {p["slug"]: p for p in PAGES}
NAV = ["index", "guidelines", "constitution", "inquiry", "equal-burden", "term-limits", "100-days", "disputes", "letter"]
CHAPTER_ORDER = ["guidelines", "constitution", "inquiry", "equal-burden", "term-limits", "100-days"]
# chapter cards on the home page: what each sets (from the summary) and when (from the guidelines)
CARDS = {
    "constitution": ("חוקה", "מבוא: הכרזת העצמאות. מגילת זכויות, חובת שירות, הכנסת, הממשלה, השפיטה, שומרי הסף, דת ומדינה, שלטון מקומי, ביטחון וחירום.",
                     "דרך הכינון", "תיקון ברוב 80; כינון בכנסת ואחר כך במשאל עם", "לחוקה"),
    "inquiry": ("ועדת חקירה ממלכתית", "לפי חוק ועדות חקירה. נושא החקירה: מה שקדם לטבח, הטבח והמלחמה שבעקבותיו, כולל הדרג המדיני ואחריות אישית. החברים — בידי נשיא בית המשפט העליון.",
                "מתי", "ההחלטה הראשונה של הממשלה", "לטיוטת ההחלטה"),
    "equal-burden": ("שוויון בנטל", "חובת שירות צבאי או אזרחי לכל, בלי פטור קבוצתי ובלי מכסות. דחייה רק בשל נסיבות אישיות, ובסופה שירות מלא. לימוד תורה — במסלול בתוך השירות, שנה אחת לכל היותר.",
                     "מתי", "ההצעה הראשונה שהממשלה מניחה על שולחן הכנסת", "להצעת החוק"),
    "term-limits": ("הגבלת כהונת ראש הממשלה", "שמונה שנים או שתי תקופות כהונה מלאות, לפי הארוך מביניהם; צינון של שמונה שנים וחסימת עקיפה; שריון ברוב 80.",
                    "מתי", "אישור בישיבת הממשלה הראשונה; חקיקה במושב הראשון", "להצעת חוק-היסוד"),
    "100-days": ("100 הימים הראשונים", "משלב 0 (מהבחירות ועד כינון הממשלה) ועד יום 100. יום 1: ועדת החקירה, ואישור חוק הגבלת הכהונה וחוק השוויון בנטל. עד יום 100: ביטול התיקון לחוק-יסוד: השפיטה והנחת תקציב 2027.",
                 "לכל פעולה", "מועד, אחראי ומקור", "לתוכנית"),
}


def esc(s):
    return html.escape(s, quote=True)


def stripe():
    return '<div class="stripe" aria-hidden="true"><span></span><span></span><span></span><span></span></div>'


def nav(current):
    cur = PAGE.get(current, {}).get("parent", current)
    items = []
    for slug in NAV:
        href = "index.html" if slug == "index" else slug + ".html"
        label = "בית" if slug == "index" else PAGE[slug]["label"]
        mark = ' aria-current="page"' if slug == cur else ""
        items.append('<a href="%s"%s>%s</a>' % (href, mark, label))
    return ('<header class="topbar"><div class="topbar-inner">'
            '<a class="brand" href="index.html"><b>קווי היסוד לממשלה הבאה</b><span>טיוטה עצמאית · לא מטעם המפלגות</span></a>'
            '<nav class="nav" aria-label="ניווט ראשי">%s</nav></div>%s</header>' % ("".join(items), stripe() if current != "index" else ""))


def shell(title, body, current, description=""):
    return f'''<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title if current == 'index' else title + ' — טיוטה עצמאית')}</title>
<meta name="description" content="{esc(description + ' טיוטה עצמאית, לא מטעם המפלגות.')}">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
{nav(current)}
<div class="notice" role="note"><div class="wrap"><b>טיוטה עצמאית — אין לה קשר למפלגות.</b> האתר אינו מטעם ביחד, ישראל ביתנו, הדמוקרטים או ישר!, והטקסטים בו לא אושרו על ידן. הם נוסחו מתוך עמדותיהן הפומביות, ברוח מסמך העקרונות של ראשי המפלגות (26.9.2026). <a href="letter.html">איך נוסחו</a></div></div>
{body}
<footer class="site-footer"><div class="wrap"><b>טיוטה עצמאית לדיון · {TODAY}</b><p>אין לאתר קשר למפלגות: הוא אינו מטעם ביחד, ישראל ביתנו, הדמוקרטים או ישר!, ולא אושר על ידן. הטקסטים נוסחו מתוך המצעים, העקרונות וההצהרות הפומביות שלהן, ברוח מסמך העקרונות של ראשי המפלגות מיום 26.9.2026. הם אינם נוסח סופי ואינם מחייבים את המפלגות.</p></div></footer>
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


LIST_ITEM = re.compile(r"(?:[-*]|\d+\.) ")


def loosen_lists(text):
    """Python-Markdown needs a blank line before a list; the documents often start one right after a line of text."""
    lines, out = text.split("\n"), []
    for i, line in enumerate(lines):
        if i:
            prev = lines[i - 1]
            q = "> " if line.startswith("> ") else ""
            if (prev.startswith("> ") == bool(q)) and LIST_ITEM.match(line[len(q):]):
                pb = prev[len(q):]
                if pb.strip() and not pb[0].isspace() and not LIST_ITEM.match(pb) and not pb.startswith(("|", "#")):
                    out.append(q.rstrip())
        out.append(line)
    return "\n".join(out)


def md_to_html(text):
    md = markdown.Markdown(extensions=["tables", "sane_lists"])
    return md.convert(loosen_lists(text))


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


def tag_level(txt):
    if txt.startswith("4/4"): return "all4"
    if txt.startswith("3+"): return "three"
    if txt == "צר": return "narrow"
    if txt in ("גישור", "הצעת גישור", "טכני"): return "bridge"
    if txt.startswith("הוכרע"): return "decided"
    return "sq"


def tag_html(txt):
    return '<span class="tag lvl-%s"><span class="dot" aria-hidden="true"></span>%s</span>' % (tag_level(txt), txt)


def tag_fragment(t):
    t = t.replace("[הכרעה נדרשת]", "הכרעה נדרשת")
    t = re.sub(r"\[(הוכרע במטה(?: \([^\[\]]{1,40}\))?)\]", lambda m: tag_html(m.group(1)), t)
    return TAG.sub(lambda m: tag_html(m.group(1)), t)


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
    """Heading ids d-1.. in document order; section -> [(id, title)] for headings whose text cites it; and all headings."""
    body = text.split("\n", 1)[1]
    refmap, heads, cur, buf, i = {}, [], None, [], 0
    def flush():
        if cur and cur[1] not in EXCL_DISPUTES:
            for n in extract_refs("".join(buf)):
                refmap.setdefault(n, [])
                if cur not in refmap[n]:
                    refmap[n].append(cur)
    for line in body.split("\n"):
        m = re.match(r"^#{2,3} (.+)$", line)
        if m:
            flush(); i += 1; cur = ("d-%d" % i, m.group(1).strip()); buf = []; heads.append(cur)
        else:
            buf.append(line + "\n")
    flush()
    return refmap, heads


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
                         % (tone(s), href_prefix, n, n, esc(label), esc(label)))
        short = full.split(" — ")[0]
        rows.append('<div class="map-row"><a class="map-ch" href="%s#ch-%s" title="%s">%s <span>%s</span></a><div class="map-cells">%s</div></div>'
                    % (href_prefix, key, esc(full), short, esc(full.split(" — ")[1]), "".join(cells)))
    return '<div class="map" role="group" aria-label="מפת ההסכמה">%s</div>' % "".join(rows)


def legend(secs, as_buttons):
    counts = {k: sum(1 for s in secs.values() if k in s["lvls"]) for k, _, _ in LEVELS}
    items = []
    for k, label, desc in LEVELS:
        inner = '%s<span class="chip-label">%s</span><span class="chip-n">%d</span>' % (dot(k), label, counts[k])
        if as_buttons:
            items.append('<button type="button" class="chip" data-lvl="%s" aria-pressed="false" title="%s">%s</button>' % (k, esc(desc), inner))
        else:
            items.append('<span class="chip static" title="%s">%s</span>' % (esc(desc), inner))
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
        parts.append('<div><dt>רמת הסכמה</dt><dd><b>%s</b> · %s</dd></div>' % (lvl_text(s), linkify(esc(s.get("level_text", "")), "")))
        parts.append('<div><dt>מה נקבע</dt><dd>%s</dd></div>' % linkify(esc(s.get("what", "")), ""))
        parts.append('<div><dt>מקורות</dt><dd>%s</dd></div>' % linkify(esc(s.get("sources", "")), ""))
        if refmap.get(n):
            links = " · ".join('<a href="disputes.html#%s">%s</a>' % (i, esc(t)) for i, t in refmap[n])
            parts.append('<div><dt>במסמך המחלוקות</dt><dd>%s</dd></div>' % links)
        parts.append('</dl><div class="src-actions"><button type="button" class="copy-link" data-sec="%d">העתקת קישור לסעיף</button><span class="copy-status" role="status"></span></div></div>' % n)
        return m.group(1) + "".join(parts)
    h = re.sub(r'(<p class="sec" id="s-(\d+)".*?</p>)', panel, h, flags=re.S)
    chap_list = re.findall(r'<h2 id="(ch-[^"]+)">([^<]+)</h2>', h)
    rail = '<nav class="rail" aria-label="פרקים"><h2>תוכן החוקה</h2><ol><li><a href="#preamble">מבוא</a></li>%s<li><a href="#appendix">נספח מקורות</a></li></ol></nav>' % "".join('<li data-ch="%s"><a href="#%s">%s</a></li>' % (i, i, t) for i, t in chap_list)
    mobile = '<details class="toc no-print"><summary>תוכן העניינים</summary><ol>%s</ol></details>' % "".join('<li><a href="#%s">%s</a></li>' % (i, t) for i, t in [("preamble", "מבוא")] + chap_list + [("appendix", "נספח מקורות")])
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
    """Document body, plus a side rail and a collapsible table of contents built from its H2s."""
    body_md = text.split("\n", 1)[1]
    h = id_headings(md_to_html(body_md))
    mode = "default" if slug in ("letter", "summary", "disputes") else "strict"
    h = wrap_tables(pills(tags(linkify(h, "constitution.html", mode))))
    heads = [(i, re.sub(r"<[^>]+>", "", t)) for i, t in re.findall(r'<h2 id="(d-\d+)">(.+?)</h2>', h)]
    if len(heads) < 4:
        return "", "", h
    items = "".join('<li><a href="#%s">%s</a></li>' % (i, t) for i, t in heads)
    rail = '<nav class="rail" aria-label="תוכן המסמך"><h2>תוכן המסמך</h2><ol>%s</ol></nav>' % items
    toc = '<details class="toc no-print"><summary>תוכן העניינים</summary><ol>%s</ol></details>' % items
    return rail, toc, h


def crumbs(p):
    parts = ['<a href="index.html">בית</a>']
    if p["slug"] in CHAPTER_ORDER or p.get("parent"):
        if p["slug"] != "guidelines":
            parts.append('<a href="guidelines.html">קווי היסוד</a>')
        if p.get("parent"):
            par = PAGE[p["parent"]]
            parts.append('<a href="%s.html">פרק %d · %s</a>' % (par["slug"], par["chapter"], par["label"]))
        elif p.get("chapter"):
            parts.append('<span>פרק %d</span>' % p["chapter"])
    return '<nav class="crumbs" aria-label="מיקום באתר">%s</nav>' % '<span aria-hidden="true">›</span>'.join(parts)


def glance(p, extra=None):
    tiles = extra or p.get("glance")
    if not tiles:
        return ""
    out = []
    for label, value, tg in tiles:
        t = tag_html(tg) if tg else ""
        out.append('<div class="tile"><span class="tile-label">%s</span><span class="tile-value">%s</span>%s</div>' % (label, value, t))
    return '<section class="glance" aria-labelledby="glance-h"><h2 id="glance-h">במבט אחד</h2><div class="tiles">%s</div></section>' % "".join(out)


def page_head(p, title, dispute_href):
    actions = '<a class="btn btn-ink" href="pdf/%s" download>הורדה כקובץ</a>' % p["pdf"]
    if dispute_href:
        actions += '<a class="btn btn-outline" href="%s">המחלוקות בנושא</a>' % dispute_href
    if p["slug"] == "equal-burden":
        actions += '<a class="btn btn-outline" href="deferral-decision.html">ההכרעה על היקף הדחייה</a>'
    if p.get("parent"):
        actions += '<a class="btn btn-outline" href="%s.html">להצעת החוק</a>' % p["parent"]
    main_t, sep, sub_t = title.partition(" — ")
    if not sep or len(main_t) < 12:
        main_t, sub_t = title, ""
    sub_html = '<p class="subtitle">%s</p>' % sub_t if sub_t else ""
    return ('<section class="page-head"><div class="wrap">%s<span class="kicker">%s · עודכן %s</span><h1>%s</h1>%s<p class="lede">%s</p><div class="actions no-print">%s</div></div></section>'
            % (crumbs(p), p["kind"], TODAY, main_t, sub_html, p["lede"], actions))


def chapter_nav(slug):
    if slug not in CHAPTER_ORDER:
        return ""
    i = CHAPTER_ORDER.index(slug)
    def label(s):
        q = PAGE[s]
        return ("פרק %d" % q["chapter"]) if q.get("chapter") else "המסגרת"
    cells = []
    if i > 0:
        s = CHAPTER_ORDER[i - 1]
        cells.append('<a class="prev" href="%s.html"><span>→ הקודם · %s</span><b>%s</b></a>' % (s, label(s), PAGE[s]["label"]))
    else:
        cells.append('<span></span>')
    if i < len(CHAPTER_ORDER) - 1:
        s = CHAPTER_ORDER[i + 1]
        cells.append('<a class="next" href="%s.html"><span>הבא · %s ←</span><b>%s</b></a>' % (s, label(s), PAGE[s]["label"]))
    else:
        cells.append('<a class="next" href="disputes.html"><span>לכל התוצרים ←</span><b>מחלוקות וחלופות</b></a>')
    return '<nav class="chapter-nav no-print" aria-label="פרקים סמוכים">%s</nav>' % "".join(cells)


def write(name, content):
    (ROOT / name).write_text(content, encoding="utf-8")


def redirect(name, target, label):
    write(name, f'''<!doctype html>
<html lang="he" dir="rtl"><head><meta charset="utf-8"><title>{label}</title>
<meta http-equiv="refresh" content="0; url={target}"><link rel="canonical" href="{target}"></head>
<body><p>העמוד עבר: <a href="{target}">{label}</a></p></body></html>''')


def main():
    const_text = (DOCS / "constitution.md").read_text(encoding="utf-8")
    disp_text = (DOCS / "disputes.md").read_text(encoding="utf-8")
    secs, chapters = load_sections(const_text)
    refmap, disp_heads = disputes_index(disp_text)
    open_n = disp_text.count("- [ ] ")
    done_n = disp_text.count("- [x] ")

    def dispute_href(key):
        if not key:
            return ""
        for i, t in disp_heads:
            if t.startswith(key):
                return "disputes.html#" + i
        return "disputes.html"

    for p in PAGES:
        slug = p["slug"]
        text = (DOCS / p["md"]).read_text(encoding="utf-8")
        title = p["title"] or doc_title(text)
        head = page_head(p, title, dispute_href(p.get("dispute")))
        if slug == "constitution":
            rail, toc, explorer, h, ah = build_constitution(text, secs, chapters, refmap)
            body = (f'{head}<main class="wrap page-main">{glance(p)}<div class="doc-layout">{rail}'
                    f'<article class="doc legal">{toc}{explorer}{h}{ah}</article></div>{chapter_nav(slug)}</main>'
                    '<div class="toast" id="toast" role="status" hidden></div><script src="assets/app.js" defer></script>')
        else:
            rail, toc, h = build_generic(text, slug)
            extra = None
            if slug == "disputes":
                extra = [("פתוחות", "%d נקודות להכרעת ראשי המפלגות" % open_n, ""), ("סגורות", "%d נקודות שהוכרעו במטה או הוסכמו בין הנציגים" % done_n, ""),
                         ("לכל נקודה", "ברירת המחדל, עמדת כל מפלגה והחלופות", "")]
            layout = f'<div class="doc-layout">{rail}<article class="doc">{toc}{h}</article></div>' if rail else f'<div class="doc-layout single"><article class="doc">{h}</article></div>'
            body = f'{head}<main class="wrap page-main">{glance(p, extra)}{layout}{chapter_nav(slug)}</main>'
        write(slug + ".html", shell(title, body, slug, p["lede"]))

    redirect("laws.html", "index.html#chapters", "חמשת פרקי הליבה")

    # --- home: the summary of Group B's work ---
    guide_text = (DOCS / "guidelines.md").read_text(encoding="utf-8")
    summary_text = (DOCS / "summary.md").read_text(encoding="utf-8")
    guide_n = len(re.findall(r"^\*\*\d{1,2}\.\d{1,2}\*\*", guide_text, flags=re.M))
    domains = [t for n, t in re.findall(r"^### פרק (\d+) — (.+)$", guide_text, flags=re.M) if int(n) >= 6]
    actions_n = re.search(r"(\d+) פעולות", summary_text).group(1)
    mandate = re.search(r'הטיל על קבוצה ב\' את "([^"]+)"', summary_text).group(1)
    open_part = summary_text.split("## מה נשאר להכרעת ראשי המפלגות", 1)[1]
    open_items = [l[2:].strip().rstrip(".") for l in open_part.split("\n") if l.startswith("- ")]

    chips = "".join('<li>%s</li>' % esc(d) for d in domains)
    cards = []
    for slug in CHAPTER_ORDER[1:]:
        p = PAGE[slug]
        name, what, when_label, when, cta = CARDS[slug]
        extra = '<a href="deferral-decision.html">ההכרעה על היקף הדחייה</a>' if slug == "equal-burden" else ""
        cards.append(f'''<article class="chapter-card"><div class="cc-top"><span class="cc-num">{p["chapter"]}</span><span class="cc-kind">{p["kind"]}</span></div>
<h3><a href="{slug}.html">{name}</a></h3><p>{what}</p><p class="cc-when"><b>{when_label}:</b> {when}</p>
<div class="cc-links"><a href="{slug}.html">{cta} ←</a>{extra}<a href="pdf/{p["pdf"]}" download>הורדה</a></div></article>''')
    cards.append('''<article class="chapter-card dark"><div class="cc-top"><span class="cc-kind">לכל התוצרים</span></div>
<h3><a href="disputes.html">מחלוקות וחלופות</a></h3><p>%s</p><div class="cc-links"><a href="disputes.html">למסמך המחלוקות ←</a><a href="pdf/%s" download>הורדה</a></div></article>''' % (PAGE["disputes"]["lede"], PAGE["disputes"]["pdf"]))
    legend_rows = "".join('<li>%s<span>%s</span></li>' % (tag_html(t), d) for t, d in [
        ("4/4", "ארבע המפלגות"), ("3+", "שלוש, והרביעית ללא עמדה ואינה מתנגדת"), ("צר", "מכנה משותף צר; החלופות במסמך המחלוקות"),
        ("גישור", "נוסח של המטה שנדרש כדי שהסעיף יעבוד"), ("סטטוס קוו", "אין עמדה מפלגתית; הדין הקיים"), ("הוכרע במטה", "הכרעה של כותבי הטיוטה; טעונה אישור ראשי המפלגות")])
    open_list = "".join("<li>%s</li>" % linkify(esc(i), "constitution.html") for i in open_items)
    home = f'''<section class="hero"><div class="wrap hero-grid">
<div class="hero-text"><span class="kicker">טיוטה עצמאית לדיון · {TODAY}</span>
<h1>קווי היסוד<br>לממשלה הבאה</h1>
<p>טיוטה עצמאית למשימה שמסמך העקרונות של ראשי מפלגות התיקון והתקווה הטיל על קבוצה ב'. היא אינה מטעם המפלגות ולא אושרה על ידן. כל סעיף נוסח מתוך העמדות הפומביות של ביחד, ישראל ביתנו, הדמוקרטים וישר! בלבד, ולכל סעיף יש מקור.</p>
<div class="actions"><a class="btn btn-sky" href="guidelines.html">לקווי היסוד</a><a class="btn btn-ghost" href="letter.html">למכתב ההסבר</a></div></div>
<figure class="mandate"><span class="kicker">המנדט</span><blockquote>"{mandate}"</blockquote><figcaption>מסמך העקרונות של ראשי מפלגות התיקון והתקווה, 26.9.2026</figcaption></figure>
</div><div class="wrap">{stripe()}</div></section>
<main class="wrap home">
<div class="facts">
<div class="fact"><b>{guide_n}</b><span>סעיפים בקווי היסוד</span></div>
<div class="fact"><b>{len(secs)}</b><span>סעיפים בחוקה</span></div>
<div class="fact"><b>3</b><span>נוסחים משפטיים: שתי הצעות חוק והחלטת ממשלה</span></div>
<div class="fact"><b>{actions_n}</b><span>פעולות בתוכנית 100 הימים</span></div>
<div class="fact"><b>{done_n}</b><span>הכרעות שכבר התקבלו</span></div>
<div class="fact open"><b>{open_n}</b><span>פתוחות להכרעת ראשי המפלגות</span></div>
</div>
<section class="home-sec" aria-labelledby="frame-h">
<div class="sec-head"><span class="kicker">המסגרת</span><h2 id="frame-h">קווי היסוד לממשלת התיקון</h2></div>
<div class="frame-card"><div class="frame-text">
<p class="big">{guide_n} סעיפים: מבוא, חמישה פרקי ליבה — חמשת נושאי המנדט — ושבעה פרקי תחום. ליד כל סעיף מסומנת רמת ההסכמה עליו, ובסוף המסמך — מה לא נכלל ולמה, ונספח מקורות.</p>
<p class="muted">מחלוקות ושאלות שקווי היסוד אינם מכריעים בהן יוכרעו בהסכמת ראשי ארבע המפלגות.</p>
<div class="actions"><a class="btn btn-ink" href="guidelines.html">לקווי היסוד המלאים</a><a class="btn btn-outline" href="pdf/{PAGE["guidelines"]["pdf"]}" download>הורדה כקובץ</a></div></div>
<div class="frame-domains"><span class="label">שבעת פרקי התחום</span><ul class="chiplist">{chips}</ul></div></div>
</section>
<section class="home-sec" id="chapters" aria-labelledby="core-h">
<div class="sec-head"><span class="kicker">ובהם</span><h2 id="core-h">חמשת פרקי הליבה</h2><p class="muted">כל פרק ליבה בקווי היסוד מפנה לתוצר מלא — נוסח, דברי הסבר, נקודות פתוחות ונספח מקורות.</p></div>
<div class="chapter-grid">{"".join(cards)}</div>
</section>
<section class="home-sec rule-panel" aria-labelledby="rule-h">
<div><span class="kicker">איך נוסח</span><h2 id="rule-h">כלל ההכרעה</h2>
<ol class="steps">
<li><span><b>מוסכם — נוסח מחייב.</b> ארבע המפלגות, או שלוש כשהרביעית ללא עמדה ואינה מתנגדת.</span></li>
<li><span><b>שנוי במחלוקת — מכנה משותף צר או הפניה לחוק,</b> והחלופות נרשמות במסמך המחלוקות.</span></li>
<li><span><b>אין עמדה לאף מפלגה — הדין הקיים,</b> בניסוח מינימלי, בלי להמציא מדיניות.</span></li>
<li><span><b>המחלוקת המדינית — הליך בלבד,</b> לא מהות.</span></li>
</ol></div>
<div><span class="label">כך מסומנת רמת ההסכמה בכל סעיף</span><ul class="legend-list">{legend_rows}</ul></div>
</section>
<section class="home-sec open-panel" aria-labelledby="open-h">
<div class="open-intro"><span class="kicker signal">מה נשאר פתוח</span><h2 id="open-h">להכרעת ראשי המפלגות</h2>
<p class="muted">לכל נקודה נרשמו ברירת המחדל, עמדת כל מפלגה והחלופות.</p>
<div class="counters"><div class="counter open"><b>{open_n}</b><span>נקודות פתוחות</span></div><div class="counter done"><b>{done_n}</b><span>נקודות סגורות</span></div></div>
<a class="btn btn-ink" href="disputes.html">למסמך המחלוקות</a></div>
<div class="open-list"><span class="label">העיקריות</span><ul>{open_list}</ul></div>
</section>
<section class="home-sec about" aria-label="על המסמכים">
<div><h2>על המסמכים</h2><p>איך נוסחו, מי בדק אותם ומה הלאה — במכתב ההסבר, בשפה לא משפטית.</p><a href="letter.html">למכתב ההסבר ←</a></div>
<div><h2>מה זה לא</h2><p>לא מסמך מטעם המפלגות ולא נוסח סופי. אין לאתר קשר לביחד, לישראל ביתנו, לדמוקרטים או לישר!, והוא לא אושר על ידן. ההכרעות שמסומנות "הוכרע במטה" הן הכרעות של כותבי הטיוטה, וכולן טעונות אישור ראשי המפלגות. חלק מהעמדות לקוח מתשובות לשאלוני עיתונים ומראיונות; כל ציטוט מובא עם הדובר, המקור והתאריך.</p></div>
</section>
</main>'''
    write("index.html", shell("קווי היסוד לממשלה הבאה — טיוטה עצמאית", home, "index",
                              "קווי היסוד לממשלה הבאה: החוקה, ועדת החקירה, חוק השוויון בנטל, הגבלת הכהונה ותוכנית 100 הימים — נוסחו מעמדות ביחד, ישראל ביתנו, הדמוקרטים וישר!"))
    print("built: index +", ", ".join(p["slug"] for p in PAGES), "| open:", open_n, "done:", done_n, "| clauses:", guide_n, "| open items:", len(open_items))


if __name__ == "__main__":
    main()
