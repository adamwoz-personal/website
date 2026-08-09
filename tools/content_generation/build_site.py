#!/usr/bin/env python3
"""Render static HTML pages for the /adam section from classified data.

Produces:
  adam/index.html                     - landing hub
  adam/pr/index.html                  - curated cybersecurity PR portfolio
  adam/mentions-all/index.html        - unabridged verified mentions
  adam/patents/index.html             - patents index

All pages are pure static HTML with a shared stylesheet. No JS is required to
render, minimizing attack surface.
"""

from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path


HEADER = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="referrer" content="no-referrer-when-downgrade">
  <title>{title}</title>
  <meta name="description" content="{description}">
  <link rel="stylesheet" href="/adam/assets/styles.css">
  <link rel="icon" type="image/png" sizes="32x32" href="/adam/assets/favicon.png">
  <link rel="apple-touch-icon" sizes="180x180" href="/adam/assets/apple-touch-icon.png">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:image" content="https://wosotowsky.org/adam/assets/og-card.png">
  <meta property="og:url" content="https://wosotowsky.org{path}">
  <meta name="twitter:card" content="summary_large_image">
</head>
<body>
  <header class="site-header">
    <div class="wrap header-inner">
      <a class="brand" href="/adam/">Adam&nbsp;Wosotowsky</a>
      <nav class="nav">
        <a href="/adam/about/">About</a>
        <a href="/adam/work/">Work</a>
        <a href="/adam/philosophy/">Philosophy</a>
        <a href="/adam/speaking/">Speaking</a>
        <a href="/adam/pr/">Public relations</a>
        <a href="/adam/patents/">Patents</a>
        <a href="/adam/chat/">Ask</a>
        <a href="/adam/contact/">Contact</a>
      </nav>
    </div>
  </header>
  <main class="wrap">
"""

FOOTER = """  </main>
  <footer class="site-footer">
    <div class="wrap">
      <p>Generated {generated} &middot; Static HTML only.</p>
    </div>
  </footer>
</body>
</html>
"""


def page(title: str, body: str, description: str = "", path: str = "/adam/") -> str:
    default_desc = (
        "Adam Wosotowsky: threat researcher, engineering leader, inventor. "
        "Two decades of cybersecurity work in malware, botnets, and threat intelligence."
    )
    return (
        HEADER.format(
            title=html.escape(title),
            description=html.escape(description or default_desc),
            path=html.escape(path),
        )
        + body
        + FOOTER.format(generated=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    )


def esc(text: str) -> str:
    return html.escape(text or "")


def mention_card(item: dict) -> str:
    outlet = esc(item.get("outlet") or item.get("domain", ""))
    title = esc(item.get("title") or item.get("url", ""))
    description = esc(item.get("description", ""))
    url = esc(item.get("url", "#"))
    domain = esc(item.get("domain", ""))
    desc_html = f'<p class="desc">{description}</p>' if description else ""
    return f"""
    <article class="card mention">
      <div class="outlet">{outlet}</div>
      <h3><a href="{url}" rel="noopener noreferrer">{title}</a></h3>
      {desc_html}
      <p class="src"><a href="{url}" rel="noopener noreferrer">{domain}</a></p>
    </article>
"""


def patent_card(p: dict) -> str:
    title = esc(p.get("title", ""))
    pub = esc(p.get("publication_number", ""))
    assignee = esc(p.get("assignee", ""))
    grant = esc(p.get("grant_date", "") or p.get("filing_date", ""))
    snippet = esc(p.get("snippet", ""))
    long_desc = p.get("long_description", "")  # may contain safe inline entities
    url = esc(p.get("url", "#"))
    long_html = f'<p class="long-desc">{long_desc}</p>' if long_desc else ""
    return f"""
    <article class="card patent" id="{pub}">
      <div class="pub">{pub}</div>
      <h3><a href="{url}" rel="noopener noreferrer">{title}</a></h3>
      <p class="desc">{snippet}</p>
      {long_html}
      <p class="meta"><span>Assignee: {assignee}</span> &middot; <span>Grant/Filing: {grant}</span></p>
    </article>
"""


def build_landing(patents: list[dict], curated_count: int, unabridged_count: int) -> str:
    patent_summary = "".join(
        f"""      <li><a href="/adam/patents/#{esc(p['publication_number'])}">
        <strong>{esc(p['publication_number'])}</strong> &mdash; {esc(p['title'])}
      </a></li>
"""
        for p in patents
    )
    return page(
        "Adam Wosotowsky",
        f"""
    <section class="hero">
      <h1>Adam Wosotowsky</h1>
      <p class="lead">Threat researcher &middot; engineering leader &middot; inventor.</p>
      <p class="lead-sub">Two decades of malware, botnet, and threat-intelligence work quoted across hundreds of press interviews and features. The pages below highlight a curated selection.</p>
      <p class="hero-links"><a href="/adam/about/">Read a short bio &rarr;</a> &middot; <a href="/adam/work/">What I work on &rarr;</a> &middot; <a href="/adam/philosophy/">Philosophy &rarr;</a> &middot; <a href="/adam/chat/">Ask the site &rarr;</a> &middot; <a href="/adam/contact/">Contact &rarr;</a> &middot; <a href="/adam/resume.pdf">Resume (PDF) &darr;</a></p>
      <div class="hero-tiles">
        <a class="tile tile-pr" href="/adam/pr/">
          <span class="tile-label">Public relations</span>
          <span class="tile-count">{curated_count}+</span>
          <span class="tile-sub">selected US interviews &amp; features</span>
        </a>
        <a class="tile tile-patents" href="/adam/patents/">
          <span class="tile-label">Patents</span>
          <span class="tile-count">{len(patents)}</span>
          <span class="tile-sub">granted U.S. patents</span>
        </a>
        <a class="tile tile-all" href="/adam/mentions-all/">
          <span class="tile-label">More mentions</span>
          <span class="tile-count">{unabridged_count}+</span>
          <span class="tile-sub">a broader sample worldwide</span>
        </a>
      </div>
    </section>

    <section class="card patents-preview">
      <h2>Patents at a glance</h2>
      <ul class="patent-list">
{patent_summary}      </ul>
      <p><a class="more" href="/adam/patents/">See all patents &rarr;</a></p>
    </section>
""",
    )


def build_pr(curated: list[dict]) -> str:
    if not curated:
        cards = '<p class="empty">No curated interviews are currently listed. Seeds live in <code>data/mentions/seeds.json</code>.</p>'
    else:
        cards = "\n".join(mention_card(m) for m in curated)
    return page(
        "Cybersecurity public relations",
        f"""
    <section class="page-head">
      <h1>Cybersecurity public relations</h1>
      <p class="lead">A curated selection from hundreds of interviews, quotes, and features across two decades of cybersecurity press &mdash; focused here on popular US technology and security outlets. See the <a href="/adam/mentions-all/">broader sample</a> for additional references worldwide.</p>
    </section>
    <section class="grid">
      {cards}
    </section>
""",
    )


def build_all(mentions: list[dict]) -> str:
    if not mentions:
        cards = '<p class="empty">No verified mentions yet.</p>'
    else:
        cards = "\n".join(mention_card(m) for m in mentions)
    return page(
        "More verified mentions",
        f"""
    <section class="page-head">
      <h1>More verified mentions</h1>
      <p class="lead">A broader sample of press mentions across languages and regions. This is a working subset of an archive spanning hundreds of interviews, quotes, and citations &mdash; not a comprehensive list.</p>
    </section>
    <section class="grid">
      {cards}
    </section>
""",
    )


def build_patents(patents: list[dict]) -> str:
    if not patents:
        cards = '<p class="empty">No patents listed.</p>'
    else:
        cards = "\n".join(
            f'<div id="{esc(p["publication_number"])}">{patent_card(p)}</div>' for p in patents
        )
    return page(
        "Patents",
        f"""
    <section class="page-head">
      <h1>Patents</h1>
      <p class="lead">United States patents where Adam Wosotowsky is listed as an inventor. Data pulled directly from Google Patents.</p>
    </section>
    <section class="grid">
      {cards}
    </section>
""",
    )


def build_about(bio: dict) -> str:
    about = bio.get("about", {})
    intro_html = "".join(f"      <p>{esc(p)}</p>\n" for p in about.get("intro", []))
    highlights_html = "".join(f"        <li>{esc(h)}</li>\n" for h in about.get("highlights", []))
    roles = about.get("roles_summary", "")
    tagline = esc(about.get("tagline", ""))
    looking_html = build_looking_for_card(bio)
    return page(
        about.get("title", "About Adam"),
        f"""
    <section class="page-head">
      <h1>About Adam</h1>
      <p class="lead">{tagline}</p>
    </section>
    <section class="card bio-intro">
{intro_html}    </section>
    <section class="card bio-highlights">
      <h2>Highlights</h2>
      <ul class="bullet-list">
{highlights_html}      </ul>
    </section>
    <section class="card bio-roles">
      <h2>Roles at a glance</h2>
      <p>{roles}</p>
      <p><a class="more" href="/adam/work/">See what I work on &rarr;</a> &middot; <a class="more" href="/adam/resume.pdf">Download resume (PDF) &darr;</a></p>
    </section>
{looking_html}    <section class="card see-also">
      <h2>Related reading</h2>
      <p><a href="/adam/philosophy/#agentic-ai">How I think about agentic AI in engineering &rarr;</a></p>
      <p><a href="/adam/philosophy/#management">How I manage &rarr;</a></p>
    </section>
    <script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "Adam Wosotowsky",
  "url": "https://wosotowsky.org/",
  "jobTitle": "Cybersecurity research and engineering leader",
  "description": "Threat researcher, engineering leader, and inventor with two decades of work in malware, botnets, and threat intelligence.",
  "sameAs": [
    "https://www.linkedin.com/in/adamwosotowsky",
    "https://github.com/adamwoz-personal"
  ],
  "address": {{
    "@type": "PostalAddress",
    "addressLocality": "Lilburn",
    "addressRegion": "GA",
    "addressCountry": "US"
  }},
  "knowsAbout": [
    "Threat intelligence",
    "Malware analysis",
    "Botnet takedowns",
    "IP and domain reputation",
    "Machine learning for security",
    "Mobile threat intelligence",
    "Messaging abuse and email fraud"
  ]
}}
    </script>
""",
        description=tagline,
        path="/adam/about/",
    )


def build_looking_for_card(bio: dict) -> str:
    lf = bio.get("looking_for") or {}
    if not lf:
        return ""
    body_html = "".join(f"      <p>{p}</p>\n" for p in lf.get("body", []))
    return f"""    <section class="card bio-looking">
      <h2>{esc(lf.get('title', "What I'm looking for"))}</h2>
{body_html}      <p><a class="more" href="/adam/contact/">Get in touch &rarr;</a></p>
    </section>
"""


def build_philosophy(bio: dict) -> str:
    ph = bio.get("philosophy") or {}
    lead = esc(ph.get("lead", ""))
    essays = ph.get("essays", [])
    parts = []
    for e in essays:
        eid = esc(e.get("id", ""))
        heading = esc(e.get("heading", ""))
        body_html = "".join(f"      <p>{p}</p>\n" for p in e.get("body", []))
        parts.append(
            f"""    <section class="card essay" id="{eid}">
      <h2>{heading}</h2>
{body_html}    </section>
"""
        )
    essays_html = "\n".join(parts)
    return page(
        ph.get("title", "Philosophy"),
        f"""
    <section class="page-head">
      <h1>Philosophy</h1>
      <p class="lead">{lead}</p>
      <p class="see-also-inline"><a href="/adam/about/">About Adam</a> &middot; <a href="/adam/work/">What I work on</a></p>
    </section>
{essays_html}""",
        description=ph.get("lead", ""),
        path="/adam/philosophy/",
    )


def build_chat() -> str:
    body = """
    <section class="page-head">
      <h1>Ask about Adam</h1>
      <p class="lead">A small assistant grounded in this site's own content. Try it on questions about work history, patents, or philosophy. Off-topic questions get redirected \u2014 for anything else you'd want a general chatbot.</p>
    </section>
    <section class="card chat-card">
      <div id="chat-messages" class="chat-messages" aria-live="polite" aria-label="Conversation"></div>
      <form id="chat-form" class="chat-form" autocomplete="off">
        <label for="chat-input" class="visually-hidden">Your question</label>
        <textarea id="chat-input" name="message" rows="2" maxlength="2000" placeholder="Ask about Adam's work, patents, philosophy..." required></textarea>
        <div class="chat-controls">
          <div id="chat-status" class="chat-status" aria-live="polite"></div>
          <button id="chat-submit" type="submit" class="chat-submit">Ask</button>
        </div>
      </form>
      <div class="chat-suggestions">
        <span class="chip" data-suggest="What has Adam worked on in botnets?">botnets</span>
        <span class="chip" data-suggest="What are Adam's patents actually about?">patents</span>
        <span class="chip" data-suggest="How does Adam think about agentic AI in engineering?">agentic AI</span>
        <span class="chip" data-suggest="What kind of role is Adam looking for?">what he's looking for</span>
        <span class="chip" data-suggest="Where has Adam spoken publicly?">speaking</span>
      </div>
      <p class="chat-footnote">Runs on AWS Bedrock via a small self-hosted service. Rate limits and a daily token budget keep costs bounded. Nothing sensitive is stored; message bodies are truncated to 64 characters in an audit log for abuse triage. See <a href="/adam/philosophy/#agentic-ai">the philosophy essay</a> for the design thinking.</p>
    </section>
    <script src="/adam/chat/chat.js" defer></script>
"""
    return page(
        "Ask about Adam \u2014 wosotowsky.org",
        body,
        description="A small RAG assistant grounded in Adam Wosotowsky's site content.",
        path="/adam/chat/",
    )


def build_speaking(bio: dict) -> str:
    sp = bio.get("speaking") or {}
    lead = esc(sp.get("lead", ""))
    closing = esc(sp.get("closing", ""))
    sections = sp.get("sections", [])
    parts = []
    for s in sections:
        heading = esc(s.get("heading", ""))
        body_html = "".join(f"      <p>{p}</p>\n" for p in s.get("body", []))
        parts.append(
            f"""    <section class="card speaking-section">
      <h2>{heading}</h2>
{body_html}    </section>
"""
        )
    sections_html = "\n".join(parts)
    closing_html = f'    <p class="closing-note">{closing}</p>\n' if closing else ""
    return page(
        sp.get("title", "Speaking"),
        f"""
    <section class="page-head">
      <h1>Speaking, teaching, and community</h1>
      <p class="lead">{lead}</p>
    </section>
{sections_html}{closing_html}""",
        description=sp.get("lead", ""),
        path="/adam/speaking/",
    )


def build_contact(bio: dict) -> str:
    c = bio.get("contact") or {}
    lead = esc(c.get("lead", ""))
    rows = []
    for ch in c.get("channels", []):
        label = esc(ch.get("label", ""))
        value = esc(ch.get("value", ""))
        href = ch.get("href")
        if href:
            row_val = f'<a href="{esc(href)}"' + (' rel="noopener noreferrer"' if href.startswith("http") else "") + f'>{value}</a>'
        else:
            row_val = value
        rows.append(f'      <li><span class="ch-label">{label}</span><span class="ch-value">{row_val}</span></li>')
    channels_html = "\n".join(rows)
    notes_html = "".join(f'      <p class="note">{esc(n)}</p>\n' for n in c.get("notes", []))
    return page(
        c.get("title", "Contact"),
        f"""
    <section class="page-head">
      <h1>Contact</h1>
      <p class="lead">{lead}</p>
    </section>
    <section class="card contact-card">
      <ul class="contact-list">
{channels_html}
      </ul>
{notes_html}    </section>
""",
        description=c.get("lead", ""),
        path="/adam/contact/",
    )


def build_work(bio: dict) -> str:
    work = bio.get("work", {})
    lead = esc(work.get("lead", ""))
    sections = work.get("sections", [])
    section_html_parts = []
    for s in sections:
        sid = esc(s.get("id", ""))
        heading = esc(s.get("heading", ""))
        body_html = "".join(f"      <p>{p}</p>\n" for p in s.get("body", []))
        refs = s.get("patent_refs") or []
        refs_html = ""
        if refs:
            links = " &middot; ".join(
                f'<a href="/adam/patents/#{esc(r)}">{esc(r)}</a>' for r in refs
            )
            refs_html = f'      <p class="meta">Related patents: {links}</p>\n'
        section_html_parts.append(
            f"""    <section class="card work-section" id="{sid}">
      <h2>{heading}</h2>
{body_html}{refs_html}    </section>
"""
        )
    sections_html = "\n".join(section_html_parts)
    return page(
        work.get("title", "What I work on"),
        f"""
    <section class="page-head">
      <h1>What I work on</h1>
      <p class="lead">{lead}</p>
    </section>
{sections_html}
    <section class="card see-also">
      <h2>Related reading</h2>
      <p><a href="/adam/philosophy/#agentic-ai">How I think about agentic AI in engineering &rarr;</a></p>
      <p><a href="/adam/philosophy/#management">How I manage &rarr;</a></p>
      <p><a href="/adam/patents/">Patents that came out of this work &rarr;</a></p>
    </section>
""",
        description=work.get("lead", ""),
        path="/adam/work/",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build /adam site pages.")
    parser.add_argument("--mentions", default="data/mentions/processed/classified.json")
    parser.add_argument("--patents", default="data/patents/patents.json")
    parser.add_argument("--bio", default="data/bio/bio.json")
    parser.add_argument("--adam-dir", default="adam")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    mentions_path = Path(args.mentions)
    patents_path = Path(args.patents)
    bio_path = Path(args.bio)
    mentions = json.loads(mentions_path.read_text(encoding="utf-8")) if mentions_path.exists() else {}
    patents_payload = json.loads(patents_path.read_text(encoding="utf-8")) if patents_path.exists() else {}
    bio = json.loads(bio_path.read_text(encoding="utf-8")) if bio_path.exists() else {}

    curated = mentions.get("curated", [])
    unabridged = mentions.get("unabridged", [])
    patents = patents_payload.get("patents", [])

    adam_dir = Path(args.adam_dir)
    for sub in ("about", "work", "philosophy", "speaking", "contact", "chat", "pr", "mentions-all", "patents"):
        (adam_dir / sub).mkdir(parents=True, exist_ok=True)

    (adam_dir / "index.html").write_text(
        build_landing(patents, len(curated), len(unabridged)), encoding="utf-8"
    )
    (adam_dir / "about" / "index.html").write_text(build_about(bio), encoding="utf-8")
    (adam_dir / "work" / "index.html").write_text(build_work(bio), encoding="utf-8")
    (adam_dir / "philosophy" / "index.html").write_text(build_philosophy(bio), encoding="utf-8")
    (adam_dir / "speaking" / "index.html").write_text(build_speaking(bio), encoding="utf-8")
    (adam_dir / "contact" / "index.html").write_text(build_contact(bio), encoding="utf-8")
    (adam_dir / "chat" / "index.html").write_text(build_chat(), encoding="utf-8")
    (adam_dir / "pr" / "index.html").write_text(build_pr(curated), encoding="utf-8")
    (adam_dir / "mentions-all" / "index.html").write_text(build_all(unabridged), encoding="utf-8")
    (adam_dir / "patents" / "index.html").write_text(build_patents(patents), encoding="utf-8")

    print(
        f"Built pages in {adam_dir}/ (curated={len(curated)}, all={len(unabridged)}, "
        f"patents={len(patents)}, bio={'yes' if bio else 'no'})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
