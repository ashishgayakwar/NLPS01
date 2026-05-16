"""
FastAPI app exposing the semantic search via a Pristyn Care-themed web UI.
Run: python app.py
Then open: http://localhost:8000
"""

from dataclasses import asdict

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
from intent_router import route_patient_intent
from search import SemanticSearch

app = FastAPI(title="Pristyn Care - Smart Search Demo")

print("Initializing search engine (this happens once at startup)...")
engine = SemanticSearch()
print("Ready! Open http://localhost:8000")


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pristyn Care - Smart Search</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root {
    --navy: #173a7e;
    --navy-dark: #0f2a5e;
    --navy-light: #2e4fa0;
    --orange: #f97316;
    --orange-light: #ff8a2b;
    --orange-soft: #fff4ec;
    --bg: #f7f8fc;
    --card: #ffffff;
    --border: #e8eaf2;
    --text: #1a2542;
    --text-muted: #6b7388;
    --text-light: #9aa0b4;
    --blue-soft: #eef2fc;
    --shadow-sm: 0 2px 8px rgba(23, 58, 126, 0.04);
    --shadow-md: 0 4px 16px rgba(23, 58, 126, 0.08);
    --shadow-lg: 0 8px 32px rgba(23, 58, 126, 0.12);
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
    min-height: 100vh;
  }

  .header {
    background: var(--card);
    border-bottom: 1px solid var(--border);
    padding: 16px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 100;
  }
  .logo {
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 800;
    font-size: 22px;
    color: var(--navy);
  }
  .logo-mark {
    width: 32px;
    height: 32px;
    background: linear-gradient(135deg, var(--navy) 0%, var(--orange) 100%);
    border-radius: 14px;
    display: grid;
    place-items: center;
    color: white;
    font-size: 16px;
    font-weight: 800;
  }
  .header-cta {
    background: var(--orange);
    color: white;
    padding: 10px 20px;
    border-radius: 14px;
    font-weight: 600;
    font-size: 14px;
    border: none;
    cursor: pointer;
    transition: background 0.2s;
    font-family: inherit;
  }
  .header-cta:hover { background: var(--orange-light); }

  .hero {
    background: linear-gradient(135deg, var(--navy) 0%, var(--navy-light) 100%);
    padding: 56px 32px 88px;
    position: relative;
    overflow: hidden;
  }
  .hero::before {
    content: '';
    position: absolute;
    top: -100px;
    right: -100px;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(249, 115, 22, 0.15) 0%, transparent 70%);
    border-radius: 50%;
  }
  .hero-content {
    max-width: 880px;
    margin: 0 auto;
    position: relative;
    z-index: 1;
  }
  .hero-tagline {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(255, 255, 255, 0.1);
    color: white;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 500;
    margin-bottom: 20px;
    border: 1px solid rgba(255, 255, 255, 0.15);
  }
  .hero-tagline-icon { color: var(--orange-light); font-weight: 700; }
  .hero h1 {
    color: white;
    font-size: 42px;
    font-weight: 800;
    line-height: 1.15;
    margin-bottom: 12px;
    letter-spacing: -0.02em;
  }
  .hero h1 .accent { color: var(--orange-light); }
  .hero-subtitle {
    color: rgba(255, 255, 255, 0.75);
    font-size: 17px;
    margin-bottom: 32px;
    max-width: 600px;
  }

  .search-wrapper {
    background: white;
    border-radius: 28px;
    padding: 6px;
    box-shadow: var(--shadow-lg);
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .search-icon {
    color: var(--text-light);
    padding-left: 16px;
    flex-shrink: 0;
  }
  .search-box {
    flex: 1;
    padding: 16px 8px;
    font-size: 16px;
    font-family: inherit;
    border: none;
    outline: none;
    background: transparent;
    color: var(--text);
  }
  .search-box::placeholder { color: var(--text-light); }
  .search-btn {
    background: var(--orange);
    color: white;
    border: none;
    padding: 14px 24px;
    border-radius: 14px;
    font-weight: 600;
    font-size: 15px;
    cursor: pointer;
    font-family: inherit;
    transition: background 0.2s;
  }
  .search-btn:hover { background: var(--orange-light); }

  .chips-label {
    color: rgba(255, 255, 255, 0.6);
    font-size: 13px;
    margin: 20px 0 10px;
  }
  .chips { display: flex; flex-wrap: wrap; gap: 12px; }
  .chip {
    background: rgba(255, 255, 255, 0.08);
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.18);
    padding: 7px 14px;
    border-radius: 14px;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.15s;
    font-family: inherit;
  }
  .chip:hover { background: var(--orange); border-color: var(--orange); }

  .main {
    max-width: 880px;
    margin: -24px auto 0;
    padding: 0 32px 64px;
    position: relative;
    z-index: 2;
  }

  .results-header {
    background: white;
    border: 1px solid var(--border);
    border-radius: 24px;
    box-shadow: var(--shadow-sm);
    margin-bottom: 16px;
    padding: 22px 24px;
  }
  .results-title { color: var(--navy); font-weight: 800; font-size: 20px; margin-bottom: 6px; }
  .results-message { color: var(--text-muted); font-size: 14px; line-height: 1.55; max-width: 680px; }
  .results-count { color: var(--text-muted); font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.4px; margin-top: 14px; }
  .clarifier-question { color: var(--text); font-size: 14px; font-weight: 700; margin-top: 18px; }
  .clarifier-chips { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 12px; }
  .clarifier-chip {
    display: inline-flex;
    align-items: center;
    background: var(--blue-soft);
    color: var(--navy);
    border: 1px solid var(--border);
    padding: 8px 14px;
    border-radius: 14px;
    font-size: 13px;
    font-weight: 700;
    text-decoration: none;
    transition: background 0.15s, border-color 0.15s, color 0.15s;
  }
  .clarifier-chip:hover {
    background: var(--orange-soft);
    border-color: var(--orange);
    color: var(--orange);
  }

  .empty-state {
    background: #fafbff;
    border-radius: 24px;
    padding: 64px 24px;
    text-align: center;
    color: var(--text-muted);
  }
  .empty-state-icon {
    width: 48px;
    height: 48px;
    margin: 0 auto 16px;
    color: var(--navy);
    font-size: 0;
  }
  .empty-state-icon svg {
    width: 48px;
    height: 48px;
    display: block;
  }
  .empty-state-icon:not(:has(svg))::before {
    content: "";
    display: block;
    width: 48px;
    height: 48px;
    background: currentColor;
    -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='11' cy='11' r='8'/%3E%3Cpath d='m21 21-4.35-4.35'/%3E%3C/svg%3E") center / contain no-repeat;
    mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='11' cy='11' r='8'/%3E%3Cpath d='m21 21-4.35-4.35'/%3E%3C/svg%3E") center / contain no-repeat;
  }
  .empty-state-text { font-size: 15px; margin-bottom: 4px; color: var(--text); font-weight: 600; }
  .empty-state-sub { font-size: 13px; }

  .result-card {
    background: white;
    padding: 22px 24px;
    border-radius: 24px;
    margin-bottom: 12px;
    border: 1px solid var(--border);
    transition: transform 0.15s, box-shadow 0.15s, border-color 0.15s;
    display: flex;
    gap: 16px;
    align-items: flex-start;
  }
  .result-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
    border-color: var(--navy-light);
  }
  .result-card.top-result {
    border-color: var(--orange);
    border-width: 2px;
    background: linear-gradient(to right, var(--orange-soft) 0%, white 30%);
  }
  .result-icon {
    width: 48px;
    height: 48px;
    background: var(--blue-soft);
    border-radius: 14px;
    display: grid;
    place-items: center;
    color: var(--navy);
    font-size: 0;
    flex-shrink: 0;
    position: relative;
  }
  .result-icon::before {
    content: "";
    width: 22px;
    height: 22px;
    background: currentColor;
    -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='22' height='22' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12.586 2.586A2 2 0 0 0 11.172 2H4a2 2 0 0 0-2 2v7.172a2 2 0 0 0 .586 1.414l8.704 8.704a2.426 2.426 0 0 0 3.42 0l6.58-6.58a2.426 2.426 0 0 0 0-3.42z'/%3E%3Ccircle cx='7.5' cy='7.5' r='.5' fill='black'/%3E%3C/svg%3E") center / contain no-repeat;
    mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='22' height='22' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12.586 2.586A2 2 0 0 0 11.172 2H4a2 2 0 0 0-2 2v7.172a2 2 0 0 0 .586 1.414l8.704 8.704a2.426 2.426 0 0 0 3.42 0l6.58-6.58a2.426 2.426 0 0 0 0-3.42z'/%3E%3Ccircle cx='7.5' cy='7.5' r='.5' fill='black'/%3E%3C/svg%3E") center / contain no-repeat;
  }
  .top-result .result-icon { background: var(--orange); color: white; }
  .result-body { flex: 1; min-width: 0; }
  .result-name { font-size: 16px; font-weight: 700; color: var(--navy); margin-bottom: 2px; }
  .result-hindi { font-size: 14px; color: var(--text-muted); margin-bottom: 8px; }
  .result-desc { font-size: 13.5px; color: var(--text); line-height: 1.55; margin-bottom: 12px; }
  .meta-row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
  .category-pill {
    background: var(--blue-soft);
    color: var(--navy);
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
  }
  .top-badge {
    background: var(--orange);
    color: white;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
  }
  .score-bar,
  .score-text {
    display: none !important;
  }

  .primary-match-card {
    background: white;
    border: 2px solid var(--orange);
    border-radius: 24px;
    padding: 26px;
    box-shadow: var(--shadow-md);
    margin-bottom: 18px;
  }
  .primary-match-top {
    display: flex;
    justify-content: space-between;
    gap: 14px;
    align-items: flex-start;
    margin-bottom: 14px;
  }
  .primary-match-title {
    color: var(--navy);
    font-size: 22px;
    font-weight: 800;
    line-height: 1.25;
  }
  .specialist-line {
    color: var(--text-muted);
    font-size: 13px;
    font-weight: 700;
    margin-top: 6px;
  }
  .primary-match-desc {
    color: var(--text);
    font-size: 14px;
    line-height: 1.6;
    max-width: 720px;
    margin-bottom: 18px;
  }
  .primary-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
  }
  .primary-action {
    border-radius: 14px;
    padding: 11px 16px;
    font-size: 14px;
    font-weight: 800;
    text-decoration: none;
    border: 1px solid var(--orange);
  }
  .primary-action.primary { background: var(--orange); color: white; }
  .primary-action.secondary { background: white; color: var(--orange); }
  .primary-action.link { border-color: var(--border); color: var(--navy); background: var(--blue-soft); }
  .alternatives-title {
    color: var(--text-muted);
    font-size: 12px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    margin: 18px 0 10px;
  }
  .alternative-card {
    background: white;
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 16px 18px;
    margin-bottom: 10px;
    display: flex;
    justify-content: space-between;
    gap: 14px;
    align-items: center;
  }
  .alternative-title {
    color: var(--navy);
    font-size: 15px;
    font-weight: 800;
    margin-bottom: 4px;
  }
  .alternative-meta {
    color: var(--text-muted);
    font-size: 12px;
    font-weight: 700;
  }
  .alternative-actions {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-shrink: 0;
  }
  .read-more-link {
    color: var(--orange);
    font-size: 13px;
    font-weight: 800;
    text-decoration: none;
    white-space: nowrap;
  }

  .consult-card {
    background: white;
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 24px;
    box-shadow: var(--shadow-sm);
  }
  .consult-title {
    color: var(--navy);
    font-size: 18px;
    font-weight: 800;
    margin-bottom: 8px;
  }
  .consult-copy {
    color: var(--text);
    font-size: 14px;
    line-height: 1.6;
    max-width: 680px;
  }
  .consult-secondary {
    color: var(--text-muted);
    margin-top: 8px;
  }
  .consult-safety {
    background: var(--orange-soft);
    color: var(--navy);
    border-left: 3px solid var(--orange);
    border-radius: 14px;
    padding: 10px 12px;
    margin-top: 16px;
    font-size: 13px;
    line-height: 1.5;
  }
  .consult-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-top: 18px;
  }
  .consult-btn {
    border-radius: 14px;
    padding: 11px 16px;
    font-size: 14px;
    font-weight: 700;
    text-decoration: none;
    border: 1px solid var(--orange);
  }
  .consult-btn.primary { background: var(--orange); color: white; }
  .consult-btn.secondary { background: white; color: var(--orange); }

  .loading { text-align: center; color: var(--navy); padding: 32px 20px; font-size: 14px; }
  .loading-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    background: var(--orange);
    border-radius: 50%;
    margin: 0 2px;
    animation: bounce 1.4s infinite ease-in-out both;
  }
  .loading-dot:nth-child(1) { animation-delay: -0.32s; }
  .loading-dot:nth-child(2) { animation-delay: -0.16s; }
  @keyframes bounce {
    0%, 80%, 100% { transform: scale(0); }
    40% { transform: scale(1); }
  }

  .footer-note { text-align: center; color: var(--text-light); font-size: 12px; padding: 32px 16px; }

  @media (max-width: 720px) {
    .hero { padding: 40px 20px 72px; }
    .hero h1 { font-size: 30px; }
    .main { padding: 0 16px 48px; }
    .main { margin-top: -16px; }
    .search-btn { padding: 12px 16px; font-size: 14px; }
    .result-card { padding: 18px 18px; }
    .primary-match-top,
    .alternative-card {
      display: block;
    }
    .top-badge,
    .alternative-actions {
      margin-top: 10px;
    }
  }
</style>
</head>
<body>

<header class="header">
  <div class="logo">
    <div class="logo-mark">P</div>
    Pristyn Care
  </div>
  <button class="header-cta">Book Free Consultation</button>
</header>

<section class="hero">
  <div class="hero-content">
    <div class="hero-tagline"><span class="hero-tagline-icon">\u2726</span> AI-Powered Smart Search</div>
    <h1>Find the right treatment<br>in your <span class="accent">own words</span></h1>
    <p class="hero-subtitle">Type in English, Hindi, or Hinglish - our AI understands what you mean, not just what you type.</p>

    <div class="search-wrapper">
      <svg class="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="11" cy="11" r="8"></circle>
        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
      </svg>
      <input id="q" class="search-box" placeholder="Try: bawasir ka ilaj, ghutne mein dard, chashma hatana..." autofocus />
      <button class="search-btn" onclick="doSearch()">Search</button>
    </div>

    <div class="chips-label">Popular searches</div>
    <div class="chips">
      <button class="chip" onclick="setQ(this)">bawasir ka ilaj</button>
      <button class="chip" onclick="setQ(this)">ghutne mein dard</button>
      <button class="chip" onclick="setQ(this)">pet ki pathri</button>
      <button class="chip" onclick="setQ(this)">chashma hatana</button>
      <button class="chip" onclick="setQ(this)">bacha nahi ho raha</button>
      <button class="chip" onclick="setQ(this)">kharrate</button>
      <button class="chip" onclick="setQ(this)">wazan kam karna</button>
      <button class="chip" onclick="setQ(this)">khatti dakar</button>
    </div>
  </div>
</section>

<main class="main">
  <div id="results-section">
    <div class="empty-state">
      <div class="empty-state-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <circle cx="11" cy="11" r="8"></circle>
          <path d="m21 21-4.35-4.35"></path>
        </svg>
      </div>
      <div class="empty-state-text">Start typing to find a treatment</div>
      <div class="empty-state-sub">Try one of the popular searches above</div>
    </div>
  </div>
</main>

<div class="footer-note">
  Powered by OpenAI embeddings - Demo prototype - Not affiliated with Pristyn Care
</div>

<script>
  const q = document.getElementById("q");
  const resultsSection = document.getElementById("results-section");

  const categoryIcon = {
    "Proctology": "\U0001FA7A",
    "General Surgery": "\U0001F52C",
    "Urology": "\U0001F4A7",
    "Gynecology": "\U0001F338",
    "Ophthalmology": "\U0001F441\uFE0F",
    "Orthopedics": "\U0001F9B4",
    "Vascular": "\u2764\uFE0F",
    "ENT": "\U0001F442",
    "Cosmetic": "\u2728",
    "Endocrine Surgery": "\U0001F98B",
    "Gastroenterology": "\U0001F37D\uFE0F",
    "Bariatric": "\u2696\uFE0F",
    "Dental": "\U0001F9B7"
  };

  function setQ(el) {
    q.value = el.innerText;
    doSearch();
  }

  window.addEventListener("DOMContentLoaded", () => {
    const params = new URLSearchParams(window.location.search);
    const initialQuery = params.get("q");
    if (initialQuery) {
      q.value = initialQuery;
      doSearch();
    }
  });

  let debounceTimer;
  q.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(doSearch, 300);
  });
  q.addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); doSearch(); }
  });

  async function doSearch() {
    const query = q.value.trim();
    if (!query) {
      renderEmpty();
      return;
    }
    resultsSection.innerHTML = '<div class="loading"><span class="loading-dot"></span><span class="loading-dot"></span><span class="loading-dot"></span><div style="margin-top:8px">Finding the best treatments for you</div></div>';
    try {
      const res = await fetch("/search?q=" + encodeURIComponent(query));
      const data = await res.json();
      render(data.results, query, data.decision);
    } catch (e) {
      resultsSection.innerHTML = '<div class="empty-state"><div class="empty-state-icon">\u26A0\uFE0F</div><div class="empty-state-text">Something went wrong</div><div class="empty-state-sub">' + escapeHtml(e.message) + '</div></div>';
    }
  }

  function renderEmpty() {
    resultsSection.innerHTML = '<div class="empty-state"><div class="empty-state-icon">\U0001F50D</div><div class="empty-state-text">Start typing to find a treatment</div><div class="empty-state-sub">Try one of the popular searches above</div></div>';
  }

  function render(items, query, decision) {
    items = items || [];

    const title = decision && decision.title ? decision.title : 'Results for "' + query + '"';
    const message = decision && decision.message ? decision.message : items.length + ' matches';
    const state = decision && decision.state ? decision.state : '';
    let sectionLabel = items.length + ' matches';
    if (state === 'needs_clarification') {
      sectionLabel = 'Likely starting point';
    } else if (state === 'direct_match') {
      sectionLabel = 'Best match found';
    } else if (state === 'needs_confirmation') {
      sectionLabel = 'Please confirm the closest match';
    }

    if (state === 'doctor_fallback') {
      const safetyNote = decision && decision.safety_note
        ? '<div class="consult-safety">' + escapeHtml(decision.safety_note) + '</div>'
        : '';
      resultsSection.innerHTML =
        '<div class="consult-card">' +
          '<div class="consult-title">Talk to a doctor</div>' +
          '<div class="consult-copy">This may need clinical context before choosing a treatment path.</div>' +
          '<div class="consult-copy consult-secondary">We could not confidently map this to one treatment. A Pristyn care coordinator can help route you to the right specialist.</div>' +
          safetyNote +
          '<div class="consult-actions">' +
            '<a class="consult-btn primary" href="#">Book Free Consultation</a>' +
            '<a class="consult-btn secondary" href="tel:">Call Now</a>' +
          '</div>' +
        '</div>';
      return;
    }

    const clarifierQuestion = decision && decision.clarifier_question ? '<div class="clarifier-question">' + escapeHtml(decision.clarifier_question) + '</div>' : '';
    const clarifierChips = decision && decision.clarifier_chips && decision.clarifier_chips.length
      ? '<div class="clarifier-chips">' + decision.clarifier_chips.map(chip =>
          '<a class="clarifier-chip" href="/?q=' + encodeURIComponent(query + ' ' + chip) + '">' + escapeHtml(chip) + '</a>'
        ).join("") + '</div>'
      : '';
    const header = '<div class="results-header">' +
      '<div class="results-title">' + escapeHtml(title) + '</div>' +
      '<div class="results-message">' + escapeHtml(message) + '</div>' +
      clarifierQuestion +
      clarifierChips +
      '<div class="results-count">' + escapeHtml(sectionLabel) + '</div>' +
    '</div>';

    if (items.length === 0) {
      resultsSection.innerHTML = header + '<div class="empty-state"><div class="empty-state-icon">\U0001F914</div><div class="empty-state-text">No matches found</div><div class="empty-state-sub">Try a different phrasing</div></div>';
      return;
    }

    if (state === 'direct_match') {
      const primary = decision && decision.primary_result ? decision.primary_result : items[0];
      const primaryKey = resultKey(primary);
      const sourceAlternatives = decision && decision.alternatives && decision.alternatives.length
        ? decision.alternatives
        : items.slice(1);
      const alternatives = sourceAlternatives
        .filter(it => resultKey(it) !== primaryKey)
        .slice(0, 3);

      const primaryUrl = primary.url || '#';
      const primaryCard =
        '<div class="primary-match-card">' +
          '<div class="primary-match-top">' +
            '<div>' +
              '<div class="primary-match-title">' + escapeHtml(primary.name) + '</div>' +
              '<div class="specialist-line">' + escapeHtml(getSpecialist(primary)) + '</div>' +
            '</div>' +
            '<span class="top-badge">Best Match</span>' +
          '</div>' +
          '<div class="primary-match-desc">' + escapeHtml(shortDescription(primary.description)) + '</div>' +
          '<div class="primary-actions">' +
            '<!-- TODO: Replace placeholder consultation and call links with real Pristyn lead/call links. -->' +
            '<a class="primary-action primary" href="#">Book Free Consultation</a>' +
            '<a class="primary-action secondary" href="tel:+910000000000">Call Now</a>' +
            '<a class="primary-action link" href="' + escapeAttr(primaryUrl) + '" target="_blank" rel="noopener">Read more on Pristyn \u2192</a>' +
          '</div>' +
        '</div>';

      const alternativeCards = alternatives.length
        ? '<div class="alternatives-title">Other possible matches</div>' + alternatives.map(it =>
            '<div class="alternative-card">' +
              '<div>' +
                '<div class="alternative-title">' + escapeHtml(it.name) + '</div>' +
                '<div class="alternative-meta">' + escapeHtml(getSpecialist(it)) + '</div>' +
              '</div>' +
              '<div class="alternative-actions">' +
                '<span class="top-badge">Also possible</span>' +
                '<a class="read-more-link" href="' + escapeAttr(it.url || '#') + '" target="_blank" rel="noopener">Read more</a>' +
              '</div>' +
            '</div>'
          ).join("")
        : '';

      resultsSection.innerHTML = header + primaryCard + alternativeCards;
      return;
    }

    const cards = items.map((it, idx) => {
      const isTop = idx === 0;
      const icon = categoryIcon[it.category] || "\U0001F3E5";
      let badge = '';
      if (state === 'needs_clarification' && isTop) {
        badge = 'Starting Point';
      } else if (state === 'needs_confirmation') {
        badge = isTop ? 'Likely Match' : 'Also Possible';
      } else if (state === 'direct_match' && isTop) {
        badge = 'Best Match';
      } else if (isTop) {
        badge = 'Likely Match';
      }
      return '<div class="result-card ' + (isTop ? 'top-result' : '') + '">' +
        '<div class="result-icon">' + icon + '</div>' +
        '<div class="result-body">' +
          '<div class="result-name">' + escapeHtml(it.name) + '</div>' +
          '<div class="result-hindi">' + escapeHtml(it.hindi_name) + '</div>' +
          '<div class="result-desc">' + escapeHtml(it.description) + '</div>' +
          '<div class="meta-row">' +
            (badge ? '<span class="top-badge">' + escapeHtml(badge) + '</span>' : '') +
            '<span class="category-pill">' + escapeHtml(it.category) + '</span>' +
          '</div>' +
        '</div>' +
      '</div>';
    }).join("");

    resultsSection.innerHTML = header + cards;
  }

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.innerText = s == null ? "" : s;
    return d.innerHTML;
  }

  function escapeAttr(s) {
    return escapeHtml(s).replace(/"/g, "&quot;");
  }

  function resultKey(it) {
    if (!it) return "";
    return it.slug || it.url || it.name || "";
  }

  function shortDescription(text) {
    const clean = (text || "A Pristyn care coordinator can help you understand the right treatment path.").replace(/\\s+/g, " ").trim();
    if (clean.length <= 180) return clean;
    const clipped = clean.slice(0, 180);
    const lastSpace = clipped.lastIndexOf(" ");
    return (lastSpace > 120 ? clipped.slice(0, lastSpace) : clipped).trim() + "...";
  }

  function getSpecialist(it) {
    const haystack = [it && it.slug, it && it.name, it && it.category, it && it.description]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    if (/piles|fissure|fistula/.test(haystack)) return "Proctologist";
    if (/kidney stone|urinary|circumcision|phimosis/.test(haystack)) return "Urologist";
    if (/hernia|appendix|gallstone/.test(haystack)) return "General Surgeon";
    if (/cataract|lasik/.test(haystack)) return "Ophthalmologist";
    if (/tinnitus|ear|snoring/.test(haystack)) return "ENT Specialist";
    if (/varicose/.test(haystack)) return "Vascular Specialist";
    if (/infertility/.test(haystack)) return "Fertility Specialist";
    if (/knee/.test(haystack)) return "Orthopedic Doctor";
    return "Specialist Doctor";
  }
</script>

</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def home():
    return HTML_PAGE


@app.get("/search")
def search(q: str = Query(..., min_length=1), top_k: int = 5):
    results = engine.search(q, top_k=top_k)
    decision = route_patient_intent(q, results)
    print(f"[intent] query={q!r}")
    print(f"[intent] state={decision.state}")
    print(f"[intent] title={decision.title}")
    print(f"[intent] alternatives={len(decision.alternatives)}")
    if decision.clarifier_question:
        print(f"[intent] clarifier_question={decision.clarifier_question}")
    if decision.clarifier_chips:
        print(f"[intent] clarifier_chips={decision.clarifier_chips}")
    return JSONResponse({"query": q, "results": results, "decision": asdict(decision)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
