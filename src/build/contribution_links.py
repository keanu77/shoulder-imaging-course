"""Add contribution links to public pages only; context survives without JavaScript."""
import re
from html import escape
from urllib.parse import quote


def add_contribution_links(dist, base):
    for page in dist.rglob("*.html"):
        text = page.read_text()
        if 'class="HubReturn"' not in text or 'class="ContributionLink"' in text:
            continue
        path = page.relative_to(dist).as_posix()
        if path == "index.html":
            path = ""
        context = base + path
        href = "https://injury.sportsmedicine.tw/contribute/?context=" + quote(context, safe="")
        link = f'<a class="ContributionLink" href="{escape(href, quote=True)}" target="_blank" rel="noopener noreferrer" aria-label="推薦影片、參考文獻或資料修正（新分頁）">推薦影片／文獻 ↗</a>'
        text = re.sub(r'(<a class="HubReturn".*?</a>)', lambda m, link=link: '<nav class="ContributionNav" aria-label="學習站與資料回饋">' + m[1] + link + '</nav>', text, count=1, flags=re.S)
        page.write_text(text)
