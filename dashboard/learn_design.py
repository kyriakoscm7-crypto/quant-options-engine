"""Reusable, accessible visual language for Quant Intelligence Learn.

No network, scripts, external font downloads, or injected learner content.
All dynamic text is escaped and the accent palette matches Quant Intelligence.
"""
from __future__ import annotations

from html import escape

import streamlit as st

from dashboard.visual_icons import icon_svg

LEARN_CSS = """
<style>
.qi-lesson-v2,.qi-learn-hero-v2 {
  color:#edf2ff; font-family:inherit; min-width:0;
}
.qi-lesson-v2 *,.qi-learn-hero-v2 *{box-sizing:border-box}
.qi-learn-hero-v2{
  border:1px solid #34415e; border-radius:22px;
  background:linear-gradient(125deg,#101b32 0%,#131c35 55%,#301c36 100%);
  padding:clamp(20px,4vw,38px); margin:12px 0 25px;
  box-shadow:0 18px 35px rgba(0,0,0,.18);
}
.qi-learn-hero-v2 .eyebrow,.qi-lesson-v2 .eyebrow {
  font-size:11px;letter-spacing:.15em;text-transform:uppercase;
  font-weight:800;color:#ff95c6;line-height:1.5;
}
.qi-learn-hero-v2 h1{
  font-size:clamp(1.75rem,4vw,3.1rem)!important;letter-spacing:-.042em;
  line-height:1.1;color:#fff;margin:9px 0 12px;
  font-weight:830;max-width:850px;
}
.qi-learn-hero-v2 p{color:#c2cee2;line-height:1.65;max-width:820px;font-size:clamp(.95rem,1.5vw,1.08rem)}
.qi-lesson-v2 h2{
  font-size:clamp(1.5rem,2.8vw,2.3rem)!important;
  letter-spacing:-.034em;line-height:1.21;margin:6px 0 9px!important;color:#fff;
}
.qi-lesson-v2 .chapter-top{display:flex;gap:12px;align-items:center;margin:16px 0 5px}
.qi-lesson-v2 .icon-well,.qi-learn-hero-v2 .icon-well{
  display:inline-flex;align-items:center;justify-content:center;
  width:43px;height:43px;min-width:43px;border-radius:13px;
  background:rgba(255,120,183,.11);border:1px solid rgba(255,120,183,.23);
}
.qi-lesson-v2 .subtitle{font-size:clamp(.93rem,1.4vw,1.07rem);line-height:1.65;color:#c8d2e2;max-width:810px}
.qi-lesson-v2 .progress-track{
  display:flex;gap:5px;margin:17px 0 6px;max-width:760px;
}
.qi-lesson-v2 .progress-track>span{
  flex:1;height:6px;border-radius:10px;background:#38445f;
}
.qi-lesson-v2 .progress-track>span.passed{background:#ff78b7}
.qi-lesson-v2 .chapter-caption{font-size:12px;color:#aab9d2;letter-spacing:.02em}
.qi-lesson-v2 .pair-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:13px;margin:14px 0 18px}
.qi-lesson-v2 .concept{
  border-radius:18px;padding:clamp(16px,2.5vw,22px);
  min-width:0;border:1px solid transparent;
}
.qi-lesson-v2 .concept.pink{background:#25151f;border-color:#42303b}
.qi-lesson-v2 .concept.blue{background:#101b2c;border-color:#2a3855}
.qi-lesson-v2 .concept-head{display:flex;align-items:center;gap:12px;margin-bottom:11px}
.qi-lesson-v2 .concept-head strong{font-size:clamp(1.03rem,1.7vw,1.22rem);line-height:1.3;color:#fff}
.qi-lesson-v2 .concept p{color:#e1e7f3;font-size:clamp(.92rem,1.5vw,1.04rem);line-height:1.58;margin:0 0 12px}
.qi-lesson-v2 .concept .foot{font-size:.88rem;font-weight:700;color:#ff8bc0}
.qi-lesson-v2 .concept.blue .foot{color:#83adff}
.qi-lesson-v2 .large-example{
  border:1px solid #33425a;border-radius:19px;padding:clamp(17px,2.7vw,25px);
  background:#0c1425;margin:15px 0 18px;
}
.qi-lesson-v2 .example-label{color:#9daecb;font-size:13px;font-weight:650;margin-bottom:5px}
.qi-lesson-v2 .example-value{color:#fff;font-size:clamp(2rem,5vw,3.1rem);font-weight:800;letter-spacing:-.045em;font-variant-numeric:tabular-nums;line-height:1.1}
.qi-lesson-v2 .example-row{display:flex;align-items:end;justify-content:space-between;gap:12px;flex-wrap:wrap}
.qi-lesson-v2 .segbar{display:flex;width:100%;height:clamp(20px,3vw,30px);overflow:hidden;border-radius:11px;margin:20px 0 13px;background:#293754}
.qi-lesson-v2 .segbar .pink{background:#ff78b7}
.qi-lesson-v2 .segbar .blue{background:#80a8f5}
.qi-lesson-v2 .legend{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
.qi-lesson-v2 .legend-item{display:flex;gap:8px;align-items:center;color:#fff;font-weight:730;font-size:clamp(.92rem,1.4vw,1.03rem)}
.qi-lesson-v2 .legend-dot{height:12px;width:12px;min-width:12px;border-radius:50%}
.qi-lesson-v2 .legend-note{color:#aebbd2;font-size:.83rem;margin-top:3px}
.qi-lesson-v2 .force{
  display:flex;align-items:flex-start;gap:17px;padding:19px 4px;
  border-bottom:1px solid #2d3850;
}
.qi-lesson-v2 .force:last-child{border-bottom:0}
.qi-lesson-v2 .force-icon{width:45px;min-width:45px;padding:9px 0;display:flex;justify-content:center}
.qi-lesson-v2 .force-body{min-width:0}
.qi-lesson-v2 .force h3{font-size:clamp(1.1rem,1.6vw,1.35rem)!important;margin:0 0 9px;color:#fff}
.qi-lesson-v2 .force p{font-size:clamp(.95rem,1.6vw,1.09rem);line-height:1.68;margin:0 0 9px;color:#ecf0f7}
.qi-lesson-v2 .force .example{font-size:.91rem;color:#acbad3;line-height:1.58}
.qi-lesson-v2 .insight{
  display:flex;gap:13px;align-items:flex-start;
  background:#1a243b;border-left:3px solid #ff78b7;
  border-radius:0 13px 13px 0;padding:16px 17px;margin:16px 0;
}
.qi-lesson-v2 .insight strong{color:#fff}
.qi-lesson-v2 .insight p{margin:0;color:#dfe6f3;line-height:1.62;font-size:.95rem}
.qi-lesson-v2 .eyebrow.blue{color:#90b8ff}
.qi-lesson-v2 .small-note{font-size:.78rem;color:#a9bad6;line-height:1.6}
.qi-lesson-v2 .timeline{display:flex;gap:10px;align-items:center;justify-content:space-around;padding:17px 5px;flex-wrap:wrap}
.qi-lesson-v2 .timeline .node{background:#18243b;border:1px solid #35435e;border-radius:12px;padding:14px;flex:1;min-width:110px;text-align:center}
.qi-lesson-v2 .timeline strong{color:#fff;display:block;margin-bottom:6px}
.qi-lesson-v2 .timeline span{color:#a9bcda;font-size:.82rem}
.qi-lesson-v2 .timeline .arrow{color:#ff88bd;font-weight:900}
.qi-learn-v2-feature{background:linear-gradient(120deg,#14233e,#271e38);border:1px solid #4c3755;border-top:2px solid #ff78b7;border-radius:20px;padding:clamp(17px,2.7vw,26px);margin:12px 0 18px}
.qi-learn-v2-feature .top{display:flex;align-items:center;gap:12px;margin-bottom:9px}
.qi-learn-v2-feature .kicker{font-size:11px;letter-spacing:.13em;color:#ff9acc;font-weight:790}
.qi-learn-v2-feature h2{font-size:clamp(1.38rem,2.8vw,2.05rem)!important;line-height:1.23;margin:4px 0 8px;color:#fff}
.qi-learn-v2-feature p{font-size:.98rem;line-height:1.6;color:#d6e0ee;margin:0}
.qi-learn-v2-feature .capsules{display:flex;gap:7px;flex-wrap:wrap;margin:13px 0}
.qi-learn-v2-feature .capsules span{padding:6px 10px;border-radius:20px;color:#b9c8ea;background:#152441;font-size:.77rem;border:1px solid #33415b}
.st-key-qi_learn_existing_lesson [data-testid="stMarkdownContainer"] h3{
  border-bottom:1px solid #34415f;padding-bottom:.58rem;margin-top:1.45rem;color:#fff
}
.st-key-qi_learn_existing_lesson [data-testid="stMarkdownContainer"] h4{
  color:#ffaad1;margin-top:1.2rem
}
@media(max-width:680px){
  .qi-lesson-v2 .pair-grid{grid-template-columns:1fr}
  .qi-lesson-v2 .force{gap:10px}
  .qi-lesson-v2 .force-icon{min-width:34px;width:34px}
  .qi-lesson-v2 .timeline .arrow{display:none}
  .qi-lesson-v2 .timeline .node{min-width:calc(50% - 8px)}
}
@media(prefers-reduced-motion:reduce){.qi-lesson-v2 *{scroll-behavior:auto!important}}
</style>
"""


def enable_learn_style() -> None:
    st.html(LEARN_CSS)


def _safe(value: object) -> str:
    return escape(str(value), quote=True)


def hero(kicker: str, title: str, subtitle: str, *, icon: str = "book-open") -> None:
    st.html(
        '<section class="qi-learn-hero-v2">'
        f'<div class="eyebrow">{icon_svg(icon, 24)}&nbsp; {_safe(kicker)}</div>'
        f'<h1>{_safe(title)}</h1><p>{_safe(subtitle)}</p>'
        '</section>'
    )


def chapter(number: int, total: int, level: str, title: str,
            subtitle: str, *, icon: str = "book-open") -> None:
    if not 1 <= number <= total <= 12:
        raise ValueError("Invalid Learn chapter progress")
    progress = "".join(
        '<span class="passed"></span>' if i <= number else "<span></span>"
        for i in range(1, total + 1)
    )
    st.html(
        '<section class="qi-lesson-v2">'
        f'<div class="chapter-top"><span class="icon-well">{icon_svg(icon, 26)}</span>'
        f'<div class="eyebrow">CHAPTER {number:02d} · {_safe(level)}</div></div>'
        f'<h2>{_safe(title)}</h2><p class="subtitle">{_safe(subtitle)}</p>'
        f'<div class="progress-track" aria-label="Chapter {number} of {total}">{progress}</div>'
        f'<div class="chapter-caption">{number} of {total} chapters</div></section>'
    )


def concept_pair(left: tuple[str, str, str, str],
                 right: tuple[str, str, str, str]) -> None:
    def card(spec: tuple[str, str, str, str], color: str) -> str:
        icon, title, body, foot = spec
        return (
            f'<div class="concept {color}">'
            f'<div class="concept-head">{icon_svg(icon, 27)}<strong>{_safe(title)}</strong></div>'
            f'<p>{_safe(body)}</p><div class="foot">{_safe(foot)}</div></div>'
        )
    st.html(
        '<section class="qi-lesson-v2"><div class="pair-grid">'
        + card(left, "pink") + card(right, "blue") + '</div></section>'
    )


def premium_bar(premium: float, intrinsic: float) -> None:
    if not (0 <= intrinsic <= premium and premium > 0):
        raise ValueError("Breakdown must be nonnegative and sum to the premium")
    fraction = intrinsic / premium * 100
    st.html(
        '<section class="qi-lesson-v2"><div class="large-example">'
        '<div class="example-row"><div><div class="example-label">Total option premium</div>'
        f'<div class="example-value">${premium:,.2f}</div></div>'
        '<div class="small-note">Per underlying share</div></div>'
        '<div class="segbar" aria-label="Intrinsic and time-value breakdown">'
        f'<div class="pink" style="width:{fraction:.3f}%"></div>'
        '<div class="blue" style="flex:1"></div></div>'
        '<div class="legend">'
        f'<div><div class="legend-item"><span class="legend-dot" style="background:#ff78b7"></span>${intrinsic:,.2f} intrinsic</div>'
        '<div class="legend-note">Exercise value right now</div></div>'
        f'<div><div class="legend-item"><span class="legend-dot" style="background:#80a8f5"></span>${premium-intrinsic:,.2f} time value</div>'
        '<div class="legend-note">Premium above intrinsic</div></div>'
        '</div></div></section>'
    )


def forces(items: tuple[tuple[str, str, str, str], ...]) -> None:
    sections = []
    for i, (icon, title, description, example) in enumerate(items, 1):
        sections.append(
            '<div class="force">'
            f'<div class="force-icon">{icon_svg(icon, 29)}</div>'
            '<div class="force-body">'
            f'<h3>{i}. {_safe(title)}</h3>'
            f'<p>{_safe(description)}</p>'
            f'<div class="example">{_safe(example)}</div>'
            '</div></div>'
        )
    st.html('<section class="qi-lesson-v2">' + "".join(sections) + "</section>")


def insight(title: str, body: str) -> None:
    st.html(
        '<aside class="qi-lesson-v2"><div class="insight">'
        f'{icon_svg("lightbulb", 22)}'
        f'<p><strong>{_safe(title)}</strong> {_safe(body)}</p>'
        '</div></aside>'
    )


def featured_lesson() -> None:
    st.html(
        '<section class="qi-learn-v2-feature">'
        f'<div class="top">{icon_svg("gem", 28)}'
        '<span class="kicker">FEATURED · NEW INTERACTIVE COURSE</span></div>'
        '<h2>Why do option premiums change?</h2>'
        '<p>Start with the very basics, then discover intrinsic value, time decay, '
        'volatility, and the Greeks through big visual examples and hands-on models.</p>'
        '<div class="capsules"><span>8 guided chapters</span>'
        '<span>Interactive graphs</span><span>Beginner to advanced</span>'
        '<span>Entirely hypothetical prices</span></div>'
        '</section>'
    )
