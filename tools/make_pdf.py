import asyncio, pathlib, sys
from playwright.async_api import async_playwright
SITE=pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SITE))
from build import PAGES, TODAY  # one list of pages for the site and the PDFs
PUBLIC='https://yahalevy.github.io/israel-constitution-tikkun-and-tikva-parties/'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(color_scheme='light')
        for page in PAGES:
            slug, pdf = page['slug'], page['pdf']
            pg=await ctx.new_page(); await pg.goto((SITE/f'{slug}.html').as_uri()); await pg.wait_for_timeout(800)
            # links in the PDF must point to the public site, not to local files
            await pg.evaluate('''(base) => document.querySelectorAll('a[href]').forEach(a => {
                const h = a.getAttribute('href');
                if (!/^(https?:|mailto:|#)/.test(h)) a.setAttribute('href', base + h);
            })''', PUBLIC)
            await pg.emulate_media(media='print')
            await pg.pdf(path=str(SITE/'pdf'/pdf), format='A4', margin={'top':'18mm','bottom':'18mm','left':'16mm','right':'16mm'}, print_background=True,
                display_header_footer=True, header_template='<div></div>',
                footer_template='<div style="font-size:8px;width:100%%;text-align:center;color:#666;direction:rtl">טיוטה לדיון · %s · עמוד <span class="pageNumber"></span> מתוך <span class="totalPages"></span></div>' % TODAY)
            await pg.close()
            print('pdf:', pdf)
        await b.close()
asyncio.run(main())
