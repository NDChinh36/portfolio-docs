"""
Fix MDX issues across practice case files:
- AccordionGroup/Accordion → H3 sections
- CardGroup/Card → bullets or sections
- iframes → remove
"""
import re
import glob
import textwrap


def clean_body(text):
    """Strip common leading indentation and extra blank lines."""
    return textwrap.dedent(text).strip()


def convert_card(m):
    attrs = m.group(1)
    body = m.group(2)

    title_m = re.search(r'title="([^"]+)"', attrs)
    href_m = re.search(r'href="([^"]+)"', attrs)
    title = title_m.group(1) if title_m else 'Item'
    href = href_m.group(1) if href_m else None

    body_clean = clean_body(body) if body else ''

    if href and body_clean:
        return f'### [{title}]({href})\n\n{body_clean}\n\n'
    elif href:
        return f'- [{title}]({href})\n'
    elif body_clean:
        nonempty = [l for l in body_clean.splitlines() if l.strip()]
        if len(nonempty) == 1 and len(body_clean) < 120:
            return f'- **{title}** — {body_clean}\n'
        else:
            return f'### {title}\n\n{body_clean}\n\n'
    else:
        return f'- **{title}**\n'


def convert_self_card(m):
    attrs = m.group(1)
    title_m = re.search(r'title="([^"]+)"', attrs)
    href_m = re.search(r'href="([^"]+)"', attrs)
    title = title_m.group(1) if title_m else 'Item'
    href = href_m.group(1) if href_m else None
    if href:
        return f'- [{title}]({href})\n'
    return f'- **{title}**\n'


def convert_accordion(m):
    attrs = m.group(1)
    body = m.group(2)
    title_m = re.search(r'title="([^"]+)"', attrs)
    title = title_m.group(1) if title_m else 'Section'
    body_clean = clean_body(body) if body else ''
    if body_clean:
        return f'### {title}\n\n{body_clean}\n\n'
    return f'### {title}\n\n'


def fix_mdx(text):
    # 1. Remove iframes (self-closing and paired)
    text = re.sub(r'[ \t]*<iframe\b[^>]*/>\s*\n?', '', text)
    text = re.sub(r'[ \t]*<iframe\b[^>]*>.*?</iframe>[ \t]*\n?', '', text, flags=re.DOTALL)

    # 2. CardGroup wrappers → remove
    text = re.sub(r'[ \t]*<CardGroup\b[^>]*>[ \t]*\n', '', text)
    text = re.sub(r'[ \t]*</CardGroup>[ \t]*\n?', '\n', text)

    # 3. Cards with body
    text = re.sub(
        r'[ \t]*<Card\b([^>]*)>[ \t]*\n?(.*?)[ \t]*</Card>[ \t]*\n?',
        convert_card,
        text,
        flags=re.DOTALL,
    )
    # Self-closing cards
    text = re.sub(r'[ \t]*<Card\b([^>]*)/>', convert_self_card, text)
    # Orphaned tags
    text = re.sub(r'[ \t]*<Card\b[^>]*>[ \t]*\n?', '', text)
    text = re.sub(r'[ \t]*</Card>[ \t]*\n?', '', text)

    # 4. AccordionGroup wrappers → remove
    text = re.sub(r'[ \t]*<AccordionGroup>[ \t]*\n', '', text)
    text = re.sub(r'[ \t]*</AccordionGroup>[ \t]*\n?', '\n', text)

    # 5. Accordion → H3 section
    text = re.sub(
        r'[ \t]*<Accordion\b([^>]*)>[ \t]*\n?(.*?)[ \t]*</Accordion>[ \t]*\n?',
        convert_accordion,
        text,
        flags=re.DOTALL,
    )
    # Orphaned accordion tags
    text = re.sub(r'[ \t]*<Accordion\b[^>]*>[ \t]*\n?', '', text)
    text = re.sub(r'[ \t]*</Accordion>[ \t]*\n?', '\n', text)

    # 6. Collapse excess blank lines (max 2 consecutive newlines)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text


files = sorted(
    glob.glob('projects/ewallet/*.mdx')
    + glob.glob('projects/healthcare-appointment/*.mdx')
    + glob.glob('projects/logistics-oms-wms/*.mdx')
    + glob.glob('projects/momo-transfer/*.mdx')
)

changed = []
for path in files:
    with open(path, encoding='utf-8') as f:
        original = f.read()
    fixed = fix_mdx(original)
    if fixed != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(fixed)
        changed.append(path)

print(f'Changed: {len(changed)} files')
for p in changed:
    print(f'  {p}')
