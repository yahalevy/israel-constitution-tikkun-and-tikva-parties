import asyncio, pathlib
from playwright.async_api import async_playwright
SITE=pathlib.Path(__file__).resolve().parent.parent
PUBLIC='https://yahalevy.github.io/israel-constitution-tikkun-and-tikva-parties/'
PAGES={'constitution':'חוקה-טיוטה.pdf','summary':'תקציר-החוקה.pdf','disputes':'מחלוקות-וחלופות.pdf','letter':'מכתב-הסבר.pdf'}
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(color_scheme='light')
        for slug,pdf in PAGES.items():
            pg=await ctx.new_page(); await pg.goto((SITE/f'{slug}.html').as_uri()); await pg.wait_for_timeout(800)
            # links in the PDF must point to the public site, not to local files
            await pg.evaluate('''(base) => document.querySelectorAll('a[href]').forEach(a => {
                const h = a.getAttribute('href');
                if (!/^(https?:|mailto:|#)/.test(h)) a.setAttribute('href', base + h);
            })''', PUBLIC)
            await pg.emulate_media(media='print')
            await pg.pdf(path=str(SITE/'pdf'/pdf), format='A4', margin={'top':'18mm','bottom':'18mm','left':'16mm','right':'16mm'}, print_background=True,
                display_header_footer=True, header_template='<div></div>',
                footer_template='<div style="font-size:8px;width:100%;text-align:center;color:#666;direction:rtl">טיוטה לדיון · 29.9.2026 · עמוד <span class="pageNumber"></span> מתוך <span class="totalPages"></span></div>')
            await pg.close()
        await b.close()
asyncio.run(main())
