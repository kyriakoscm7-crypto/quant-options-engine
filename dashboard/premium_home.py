"""Premium, touch-safe landing experience for Quant Intelligence.

The landing page uses a decorative, non-interactive SVG instead of a Plotly
options-pricing chart. The actual options research tools remain available.
"""

import re as _qi_re
from base64 import b64encode

import streamlit as st

_HOMEPAGE_CSS = """
<style>
.qi-home-hero {
    position: relative;
    isolation: isolate;
    display: grid;
    grid-template-columns: minmax(0, 1.07fr) minmax(260px, .93fr);
    align-items: center;
    gap: clamp(18px, 3vw, 36px);
    padding: clamp(26px, 4.5vw, 64px);
    background: radial-gradient(ellipse at 88% 23%, rgba(255, 120, 183, .16), transparent 42%),
                radial-gradient(ellipse at 65% 105%, rgba(87, 116, 230, .13), transparent 48%),
                linear-gradient(125deg, #13213b 0%, #0a1227 55%, #0a1022 100%);
    border: 1px solid #32405d;
    border-radius: 26px;
    box-shadow: 0 24px 65px rgba(0, 0, 0, .19);
    overflow: hidden;
}
.qi-home-hero::before {
    content: "";
    position: absolute;
    inset: 0;
    z-index: -1;
    background: linear-gradient(115deg, rgba(255,255,255,.028), transparent 38%);
    pointer-events: none;
}
.qi-home-eyebrow {
    color: #ff91c6;
    font-size: .69rem;
    font-weight: 800;
    letter-spacing: .19em;
    text-transform: uppercase;
    margin-bottom: 22px;
}
.qi-home-title {
    font-size: clamp(2.4rem, 4.6vw, 4.8rem);
    line-height: 1.07;
    font-weight: 830;
    color: #fff;
    letter-spacing: -.053em;
    margin: 0;
}
.qi-home-title span { color: #ff84be; }
.qi-home-subtitle {
    color: #c0cde2;
    font-size: clamp(.98rem, 1.25vw, 1.16rem);
    line-height: 1.72;
    max-width: 560px;
    margin: 22px 0 0;
}
.qi-home-kicker {
    margin-top: 26px;
    display: flex;
    flex-wrap: wrap;
    gap: 9px;
}
.qi-home-chip {
    display: inline-flex;
    align-items: center;
    border: 1px solid #3a4a67;
    border-radius: 99px;
    padding: 6px 11px;
    color: #b9c8e0;
    background: rgba(15, 24, 45, .6);
    font-size: .7rem;
    font-weight: 650;
    letter-spacing: .025em;
}
.qi-home-visual {
    position: relative;
    min-height: 335px;
    border-radius: 22px;
    background: radial-gradient(circle at 53% 47%, rgba(255, 120, 183, .10), transparent 50%),
                radial-gradient(circle at 51% 48%, rgba(79, 108, 205, .1), transparent 67%);
    overflow: hidden;
    user-select: none;
    touch-action: pan-y;
    pointer-events: none;
}
.qi-home-visual svg { display:block; width:100%; height:330px; overflow: visible; }
.qi-home-visual .qi-orbit {
    fill: none;
    stroke: #4b6289;
    stroke-width: 1;
    opacity: .32;
}
.qi-home-visual .qi-orbit-dashed {
    stroke-dasharray: 3 9;
    animation: qi-home-dash 40s linear infinite;
}
.qi-home-visual .qi-beam {
    fill: none;
    stroke: url(#qiBeamGradient);
    stroke-width: 2.8;
    stroke-linecap: round;
    filter: url(#qi-soft-glow);
    stroke-dasharray: 11 9;
    animation: qi-home-dash 14s linear infinite;
}
.qi-home-visual .qi-pulse { transform-origin: center; animation: qi-home-pulse 3.4s ease-in-out infinite; }
.qi-home-visual .qi-pulse-delay { animation-delay: -1.5s; }
.qi-home-visual .qi-label {
    font-family: ui-sans-serif, system-ui, sans-serif;
    fill: #c5d1e6;
    font-size: 10px;
    font-weight: 690;
    letter-spacing: 1.3px;
}
.qi-home-visual-foot {
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    bottom: 14px;
    white-space: nowrap;
    color: #93a6c8;
    font-size: .63rem;
    letter-spacing: .14em;
    text-align: center;
}
@keyframes qi-home-dash { to { stroke-dashoffset: -180; } }
@keyframes qi-home-pulse { 0%, 100% { opacity: .4; } 50% { opacity: 1; } }
.qi-home-actions { margin-top: 16px; }
.st-key-qi_home_primary_actions button {
    border-radius: 12px !important;
    min-height: 52px !important;
    font-size: .93rem !important;
    font-weight: 700 !important;
}
.qi-home-section-head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 12px;
    margin: 37px 0 18px;
}
.qi-home-section-head h2 {
    font-size: clamp(1.45rem, 2.4vw, 2rem) !important;
    font-weight: 750 !important;
    color: #f7f9ff !important;
    margin: 0 !important;
}
.qi-home-section-head span { color: #95a7c6; font-size: .84rem; }
.qi-home-card {
    background: linear-gradient(146deg, #1b2a46, #101a30);
    border: 1px solid #324360;
    border-radius: 19px;
    padding: 24px;
    min-height: 187px;
    transition: border-color .2s, transform .2s;
}
.qi-home-card:hover { border-color: #d273a9; transform: translateY(-2px); }
.qi-home-card-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 42px;
    height: 42px;
    background: rgba(255, 120, 183, .11);
    border: 1px solid rgba(255, 120, 183, .22);
    border-radius: 12px;
    color: #ff90c7;
    margin-bottom: 16px;
}
.qi-home-card-icon svg {width: 24px; height: 24px; display: block;}
.qi-home-card h3 {
    margin: 0 0 9px !important;
    color: #fff;
    font-size: 1.19rem;
    font-weight: 750;
    letter-spacing: -.025em;
}
.qi-home-card p { margin: 0; color: #b9c7de; font-size: .87rem; line-height: 1.62; }
[class*="st-key-qi_home_card_actions_"] button { min-height: 43px !important; margin-top: 3px; }
.qi-home-learn-spotlight {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: center;
    gap: 16px;
    border: 1px solid #4c3d69;
    border-radius: 20px;
    padding: 24px 27px;
    background: radial-gradient(ellipse at 100% 50%, rgba(255, 120, 183, .11), transparent 50%),
                linear-gradient(120deg, #17233e, #141a34);
}
.qi-home-learn-spotlight .qi-eyebrow { color: #ff91c6; font-size: .68rem; font-weight:800; letter-spacing: .13em; }
.qi-home-learn-spotlight h3 { color: #fff; margin: 9px 0 7px !important; font-size: clamp(1.13rem, 2.2vw, 1.45rem); }
.qi-home-learn-spotlight p { color: #bccae1; font-size: .88rem; margin:0; line-height:1.6; }
.qi-home-learn-spotlight .qi-lesson-icon { color: #ff90c7; display: inline-flex; align-items: center; }
.qi-home-footer { color: #91a2bf; font-size: .75rem; padding-top: 23px; margin-top: 24px; border-top: 1px solid #2d3a55; }
@media (max-width: 960px) {
    .qi-home-hero { grid-template-columns: 1fr; }
    .qi-home-visual { min-height: 260px; }
    .qi-home-visual svg { height: 250px; }
}
@media (max-width: 640px) {
    .qi-home-hero { padding: 24px 21px; border-radius: 19px; }
    .qi-home-title { font-size: clamp(2.3rem, 10vw, 3.45rem); }
    .qi-home-eyebrow { margin-bottom: 16px; }
    .qi-home-subtitle { font-size: 1rem; margin-top: 16px; }
    .qi-home-visual { min-height: 203px; }
    .qi-home-visual svg { height: 198px; }
    .qi-home-visual-foot { font-size: .51rem; bottom: 0; }
    .qi-home-section-head { display: block; }
    .qi-home-section-head span { display: block; margin-top: 6px; }
    .qi-home-card { min-height: auto; }
    .qi-home-learn-spotlight { padding: 20px; }
    .qi-home-learn-spotlight .qi-lesson-icon { display: none; }
}
@media (prefers-reduced-motion: reduce) {
    .qi-home-visual *, .qi-home-card { animation: none !important; transition: none !important; }
}

/* Signature Intelligence Network: passive illustration, never captures scroll. */
.qi-home-hero {
    grid-template-columns: minmax(0, 1.15fr) minmax(0, .85fr);
}
.qi-home-title {
    font-size: clamp(2.45rem, 3.65vw, 4.0rem);
    line-height: 1.075;
}
.qi-home-visual {
    min-height: 0;
    background: radial-gradient(circle at center, rgba(255,120,183,.065), transparent 65%);
    overflow: hidden;
    pointer-events: none;
    touch-action: pan-y;
}
.qi-home-visual .qi-network-illustration {
    display: block;
    width: 100%;
    height: auto;
    object-fit: contain;
    pointer-events: none;
    user-select: none;
    -webkit-user-drag: none;
}
@media (max-width: 900px) {
    .qi-home-hero {
        grid-template-columns: minmax(0, 1fr);
        padding: clamp(22px, 5vw, 35px);
        gap: 4px;
    }
    .qi-home-title { font-size: clamp(2.15rem, 7vw, 3.75rem); }
    .qi-home-visual { max-width: 450px; width: 100%; margin: 0 auto; }
}
@media (max-width: 520px) {
    .qi-home-title { font-size: clamp(2rem, 9vw, 3.15rem); }
    .qi-home-visual { max-width: 365px; }
    .qi-home-kicker { margin-top: 18px; }
}



/* QI NETWORK V5 — Professional endpoint navigation */

.qi-home-visual {
    position: relative;
    width: 100%;
    min-width: 0;
    container-type: inline-size;
    overflow: hidden;
    touch-action: pan-y;
    background:
        radial-gradient(circle at 50% 48%,
            rgba(255,120,183,.055), transparent 61%);
}

.qi-home-visual .qi-network-illustration {
    display: block;
    width: 100%;
    height: auto;
    aspect-ratio: 4 / 3;
    object-fit: contain;
    pointer-events: none;
    user-select: none;
    -webkit-user-drag: none;
}

.qi-network-nav {
    position: absolute;
    inset: 0;
    z-index: 4;
    pointer-events: none;
}

.qi-network-endpoint {
    position: absolute;
    display: inline-flex;
    align-items: center;
    gap: 7px;
    transform: translate(-22px, -50%);
    pointer-events: auto;
    text-decoration: none !important;
    color: #eaf0fc !important;
    cursor: pointer;
    touch-action: manipulation;
    -webkit-tap-highlight-color: transparent;
    border-radius: 12px;
}

.qi-network-endpoint.qi-node-right {
    flex-direction: row-reverse;
    transform: translate(calc(-100% + 22px), -50%);
}

.qi-network-touch {
    display: block;
    width: 44px;
    height: 44px;
    flex: 0 0 44px;
    border: 1px solid transparent;
    border-radius: 50%;
    box-sizing: border-box;
    transition: border-color .2s, box-shadow .2s;
}

.qi-network-name {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 35px;
    box-sizing: border-box;
    padding: 7px 12px;
    border-radius: 10px;
    border: 1px solid rgba(116,141,185,.42);
    background: rgba(16,27,49,.96);
    box-shadow: 0 5px 18px rgba(0,0,0,.13);
    font-size: .66rem;
    font-weight: 750;
    letter-spacing: .085em;
    line-height: 1.1;
    white-space: nowrap;
    transition:
        border-color .2s,
        background-color .2s,
        transform .2s;
}

.qi-network-endpoint:hover .qi-network-name,
.qi-network-endpoint:focus-visible .qi-network-name {
    border-color: #ff8ec2;
    background: #263653;
    transform: translateY(-1px);
}

.qi-network-endpoint:hover .qi-network-touch,
.qi-network-endpoint:focus-visible .qi-network-touch {
    border-color: rgba(255,120,183,.5);
    box-shadow: 0 0 18px rgba(255,120,183,.19);
}

.qi-network-endpoint:focus-visible {
    outline: 2px solid #ffb4d8;
    outline-offset: 4px;
}

/* Match the four endpoints in the 480 x 360 artwork. */

.qi-node-discover { left: 21.25%; top: 23.6%; }
.qi-node-research { left: 78.33%; top: 25.3%; }
.qi-node-learn    { left: 24.6%;  top: 76.7%; }
.qi-node-analyze  { left: 75.2%;  top: 76.95%; }

/* Compact endpoint labels when the actual graphic is narrow. */

@container (max-width: 560px) {
    .qi-network-endpoint,
    .qi-network-endpoint.qi-node-right {
        flex-direction: column;
        gap: 1px;
        transform: translate(-50%, -22px);
    }

    .qi-network-name {
        font-size: .59rem;
        min-height: 29px;
        padding: 6px 9px;
        letter-spacing: .035em;
    }
}

@container (max-width: 340px) {
    .qi-network-name {
        font-size: .54rem;
        padding: 5px 7px;
        letter-spacing: .01em;
    }

    .qi-network-touch {
        width: 42px;
        height: 42px;
        flex-basis: 42px;
    }
}

@media (prefers-reduced-motion: reduce) {
    .qi-network-name,
    .qi-network-touch {
        transition: none !important;
    }
}


/* QI FINAL RESPONSIVE HERO FIX V6 */

/* Automatically stack when the available content area is narrow,
   including when the Streamlit sidebar is expanded. */
.qi-home-hero {
    grid-template-columns:
        repeat(auto-fit, minmax(min(100%, 390px), 1fr)) !important;
    align-items: center;
}

.qi-home-hero > div {
    min-width: 0;
}

/* Preserve a substantial, centered network in stacked layouts. */
.qi-home-hero .qi-home-visual {
    width: 100%;
    max-width: 480px;
    margin-inline: auto;
}

/* Keep section headings and descriptions from crowding each other. */
.qi-home-section-head {
    flex-wrap: wrap;
    align-items: flex-start;
}

.qi-home-section-head h2 {
    flex: 1 1 370px;
    min-width: 0;
}

.qi-home-section-head > span {
    flex: 1 1 240px;
    min-width: 0;
}

/* Prevent homepage button labels from getting cut off. */
.st-key-qi_home_primary_actions button {
    white-space: normal !important;
    overflow-wrap: normal;
    line-height: 1.35 !important;
}


/* Single clickable destination cards */
a.qi-home-card-link {
    display: block;
    position: relative;
    color: inherit !important;
    text-decoration: none !important;
    cursor: pointer;
    transition: transform .2s ease, border-color .2s ease,
                box-shadow .2s ease;
}
a.qi-home-card-link:hover {
    transform: translateY(-2px);
    border-color: rgba(255, 120, 183, .65) !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, .15);
}
a.qi-home-card-link:focus-visible {
    outline: 3px solid #FF78B7;
    outline-offset: 3px;
}
.qi-home-card-arrow {
    position: absolute;
    right: 18px;
    bottom: 14px;
    color: #FF78B7;
    font-size: 1.25rem;
}
@media (prefers-reduced-motion: reduce) {
    a.qi-home-card-link {
        transition: none;
    }
    a.qi-home-card-link:hover {
        transform: none;
    }
}


/* Clean interactive network */
.qi-home-visual {
    pointer-events: auto !important;
    overflow: visible !important;
}
.qi-network-nav {
    pointer-events: none;
}
.qi-network-endpoint {
    pointer-events: auto !important;
    z-index: 6;
}
.qi-home-visual::after {
    content: "";
    position: absolute;
    left: 50%;
    top: 50%;
    width: 54%;
    aspect-ratio: 1;
    border: 1px dashed rgba(139, 169, 255, .27);
    border-top: 2px solid rgba(255, 120, 183, .75);
    border-radius: 50%;
    transform: translate(-50%, -50%) rotate(0deg);
    animation: qi-hero-orbit 120s linear infinite;
    pointer-events: none;
    z-index: 2;
}
@keyframes qi-hero-orbit {
    to {
        transform: translate(-50%, -50%) rotate(360deg);
    }
}
@media (prefers-reduced-motion: reduce) {
    .qi-home-visual::after {
        animation: none !important;
    }
}


/* One synchronized animation for the entire QI network. */
.qi-home-visual {
    padding: 22px 12px !important;
    overflow: visible !important;
}

.qi-home-visual::after {
    content: none !important;
    display: none !important;
}

.qi-home-visual .qi-network-rotator {
    position: relative;
    width: 100%;
    aspect-ratio: 4 / 3;
    transform-origin: 50% 50%;
    animation: qi-full-network-orbit 210s linear infinite;
}

@keyframes qi-full-network-orbit {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

/* Keep destination labels readable during the rotation. */
.qi-home-visual .qi-network-name {
    transform-origin: center;
    animation: qi-upright-label 210s linear infinite;
}

@keyframes qi-upright-label {
    from { rotate: 0deg; }
    to { rotate: -360deg; }
}

/* Clickable elements rotate with their associated SVG nodes. */
.qi-home-visual .qi-network-nav {
    position: absolute;
    inset: 0;
    pointer-events: none;
}

.qi-home-visual .qi-network-endpoint {
    pointer-events: auto !important;
}

@media (prefers-reduced-motion: reduce) {
    .qi-home-visual .qi-network-rotator,
    .qi-home-visual .qi-network-name {
        animation: none !important;
    }
}

</style>
"""


QI_NETWORK_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 360" role="img" aria-label="Quant Intelligence connected research network">\n  <defs>\n    <radialGradient id="qiAura"><stop offset="0" stop-color="#FF78B7" stop-opacity=".22"/><stop offset=".48" stop-color="#6884F2" stop-opacity=".07"/><stop offset="1" stop-color="#10182F" stop-opacity="0"/></radialGradient>\n    <linearGradient id="qiEdge" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#6B8BDB"/><stop offset=".53" stop-color="#FF78B7"/><stop offset="1" stop-color="#8BA9FF"/></linearGradient>\n    <linearGradient id="qiCore" x1="0" x2="1" y1="0" y2="1"><stop stop-color="#273657"/><stop offset="1" stop-color="#151F39"/></linearGradient>\n    <filter id="qiHalo" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="6"/></filter>\n  </defs>\n  <style>\n    .quiet { fill:none; stroke:#6C83AF; stroke-width:1; opacity:.35; }\n    .spin { transform-origin:240px 176px; animation:qiOrbit 85s linear infinite; }\n    \n    .spinBack { transform-origin:240px 176px; animation:qiOrbitBack 110s linear infinite; }\n    .edge { fill:none; stroke:url(#qiEdge); stroke-width:1.25; stroke-dasharray:3 9; opacity:.60; animation:qiFlow 18s linear infinite; }\n    .nodeOuter { fill:#192641; stroke:#536A95; stroke-width:1.1; }\n    .nodeInner { fill:#FF96C9; }\n    .nodeRing { fill:none; stroke:#FF78B7; stroke-width:1.15; opacity:.26; animation:qiBreath 4.3s ease-in-out infinite; }\n    .label { font-family:Arial,Helvetica,sans-serif; font-size:10px; font-weight:700; letter-spacing:1.65px; fill:#C4D1E8; }\n    .spark { fill:#FFD6EB; opacity:.93; }\n    .pulse1 { animation:qiSignalA 6s ease-in-out infinite; }\n    .pulse2 { animation:qiSignalB 7.5s ease-in-out infinite -2.2s; }\n    .pulse3 { animation:qiSignalC 8.5s ease-in-out infinite -4s; }\n    .pulse4 { animation:qiSignalD 7.1s ease-in-out infinite -1s; }\n    .coreGlow { animation:qiBreath 5s ease-in-out infinite; }\n    .qi-core-upright, .qi-icon-upright { transform-box:view-box; animation:qiCounterOrbit 210s linear infinite; }\n    .qi-core-upright {transform-origin:240px 176px;}\n    .qi-icon-discover {transform-origin:102px 85px;}\n    .qi-icon-research {transform-origin:376px 91px;}\n    .qi-icon-learn {transform-origin:118px 276px;}\n    .qi-icon-analyze {transform-origin:361px 277px;}\n    @keyframes qiCounterOrbit { to {transform:rotate(-360deg);} }\n    @keyframes qiOrbit { to { transform:rotate(360deg); } }\n    @keyframes qiOrbitBack { to { transform:rotate(-360deg); } }\n    @keyframes qiFlow { to {stroke-dashoffset:-144;} }\n    @keyframes qiBreath { 0%,100% {opacity:.24;} 50% {opacity:.72;} }\n    @keyframes qiSignalA {0% {transform:translate(240px,176px);opacity:0;} 14% {opacity:1;} 84% {opacity:1;} 100% {transform:translate(102px,85px);opacity:0;}}\n    @keyframes qiSignalB {0% {transform:translate(240px,176px);opacity:0;} 14% {opacity:1;} 84% {opacity:1;} 100% {transform:translate(376px,91px);opacity:0;}}\n    @keyframes qiSignalC {0% {transform:translate(240px,176px);opacity:0;} 14% {opacity:1;} 84% {opacity:1;} 100% {transform:translate(118px,276px);opacity:0;}}\n    @keyframes qiSignalD {0% {transform:translate(240px,176px);opacity:0;} 14% {opacity:1;} 84% {opacity:1;} 100% {transform:translate(361px,277px);opacity:0;}}\n    @media (prefers-reduced-motion:reduce) { .qi-core-upright,.qi-icon-upright,.spin,.spinBack,.edge,.nodeRing,.coreGlow,.pulse1,.pulse2,.pulse3,.pulse4 { animation:none!important; } .pulse1,.pulse2,.pulse3,.pulse4 {display:none;} }\n  </style>\n  <circle cx="240" cy="176" r="170" fill="url(#qiAura)"/>\n  <g class="spin"><circle class="quiet" cx="240" cy="176" r="122" stroke-dasharray="5 13"/><path class="quiet" stroke="#FF78B7" stroke-width="1.6" d="M240 54 A122 122 0 0 1 323 87"/></g>\n  <g class="spinBack"><circle class="quiet" cx="240" cy="176" r="89" stroke-dasharray="1.5 9"/><circle class="quiet" cx="240" cy="176" r="148" stroke-dasharray="1 17"/></g>\n  <ellipse class="quiet" cx="240" cy="176" rx="195" ry="74" transform="rotate(-26 240 176)"/>\n  <ellipse class="quiet" cx="240" cy="176" rx="195" ry="74" transform="rotate(30 240 176)" opacity=".65"/>\n  <g><path class="edge" d="M240 176 L102 85"/><path class="edge" d="M240 176 L376 91"/><path class="edge" d="M240 176 L118 276"/><path class="edge" d="M240 176 L361 277"/></g>\n  <circle class="spark pulse1" r="3.2" cx="0" cy="0"/><circle class="spark pulse2" r="3" cx="0" cy="0"/><circle class="spark pulse3" r="3.3" cx="0" cy="0"/><circle class="spark pulse4" r="3" cx="0" cy="0"/>\n  <g class="qi-core-upright"><circle cx="240" cy="176" r="64" fill="#FF78B7" fill-opacity=".10" class="coreGlow"/>\n  <circle cx="240" cy="176" r="45" fill="#FF78B7" fill-opacity=".13" filter="url(#qiHalo)"/>\n  <circle cx="240" cy="176" r="39" fill="url(#qiCore)" stroke="#FF91C4" stroke-width="1.7"/>\n  <circle cx="240" cy="176" r="33" fill="none" stroke="#FF78B7" stroke-opacity=".23"/>\n  <text x="240" y="182" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="23" font-weight="800" letter-spacing="-1.5" fill="#FFE4F0">QI</text></g>\n  <g class="qi-icon-upright qi-icon-discover"><circle class="nodeRing" cx="102" cy="85" r="27"/><circle class="nodeOuter" cx="102" cy="85" r="17"/><circle class="nodeInner" cx="102" cy="85" r="4.5"/><circle cx="102" cy="85" r="10" fill="none" stroke="#FF78B7" stroke-opacity=".34"/><text class="label" x="102" y="51" text-anchor="middle">DISCOVER</text></g>\n  <g class="qi-icon-upright qi-icon-research"><circle class="nodeRing" cx="376" cy="91" r="27"/><circle class="nodeOuter" cx="376" cy="91" r="17"/><path d="M369 96 L375 90 L380 92 L384 85" fill="none" stroke="#FF96C9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><text class="label" x="376" y="57" text-anchor="middle">RESEARCH</text></g>\n  <g class="qi-icon-upright qi-icon-learn"><circle class="nodeRing" cx="118" cy="276" r="27"/><circle class="nodeOuter" cx="118" cy="276" r="17"/><path d="M109 272 Q114 270 118 273 Q122 270 127 272 L127 282 Q122 280 118 283 Q114 280 109 282 Z" fill="none" stroke="#FF96C9" stroke-width="1.8" stroke-linejoin="round"/><path d="M118 273 V282" stroke="#FF96C9" stroke-width="1.4"/><text class="label" x="118" y="313" text-anchor="middle">LEARN</text></g>\n  <g class="qi-icon-upright qi-icon-analyze"><circle class="nodeRing" cx="361" cy="277" r="27"/><circle class="nodeOuter" cx="361" cy="277" r="17"/><path d="M353 282 V275 M359 282 V269 M365 282 V272 M371 282 V266" stroke="#FF96C9" stroke-width="2.3" stroke-linecap="round"/><text class="label" x="361" y="314" text-anchor="middle">ANALYZE</text></g>\n  <g fill="#8DA8FF" opacity=".7"><circle cx="179" cy="54" r="2"/><circle cx="310" cy="304" r="2.2"/><circle cx="55" cy="183" r="1.8"/><circle cx="425" cy="193" r="2"/></g>\n</svg>'

for _qi_static_node_label in ("DISCOVER", "RESEARCH", "LEARN", "ANALYZE"):
    QI_NETWORK_SVG = _qi_re.sub(
        rf"<text\b[^>]*>\s*{_qi_static_node_label}\s*</text>",
        "", QI_NETWORK_SVG, flags=_qi_re.IGNORECASE | _qi_re.DOTALL,
    )

QI_NETWORK_DATA_URL = "data:image/svg+xml;base64," + b64encode(QI_NETWORK_SVG.encode("utf-8")).decode("ascii")


_HERO = """
<div class="qi-home-hero">
  <div>
    <div class="qi-home-eyebrow">QUANT INTELLIGENCE &nbsp; / &nbsp; RESEARCH + LEARN</div>
    <h1 class="qi-home-title">Make sense of<br><span>every market move.</span></h1>
    <p class="qi-home-subtitle">
      Explore real-stock charts, experiment with quantitative simulations, and
      learn the financial ideas behind the models.
    </p>
    <div class="qi-home-kicker">
      <span class="qi-home-chip">MARKET RESEARCH</span>
      <span class="qi-home-chip">INTERACTIVE LEARNING</span>
      <span class="qi-home-chip">RISK INTELLIGENCE</span>
    </div>
  </div>
  <div class="qi-home-visual" role="group" aria-label="Animated network connecting Quant Intelligence research, discovery, learning and analysis. Decorative illustration, not market data.">
    <div class="qi-network-rotator">
    <img class="qi-network-illustration" src="__QI_NETWORK_IMAGE__" alt="" aria-hidden="true" draggable="false">
    <nav class="qi-network-nav" aria-label="Quant Intelligence navigation">
  <a class="qi-network-endpoint qi-node-discover"
     href="?qi_go=discover" aria-label="Open Quant Discovery">
    <span class="qi-network-touch" aria-hidden="true"></span>
    <span class="qi-network-name">DISCOVER</span>
  </a>
  <a class="qi-network-endpoint qi-node-right qi-node-research"
     href="?qi_go=research" aria-label="Open Stock Explorer">
    <span class="qi-network-touch" aria-hidden="true"></span>
    <span class="qi-network-name">RESEARCH</span>
  </a>
  <a class="qi-network-endpoint qi-node-learn"
     href="?qi_go=learn" aria-label="Open Quant Learn">
    <span class="qi-network-touch" aria-hidden="true"></span>
    <span class="qi-network-name">LEARN</span>
  </a>
  <a class="qi-network-endpoint qi-node-right qi-node-analyze"
     href="?qi_go=analyze" aria-label="Open Options Lab">
    <span class="qi-network-touch" aria-hidden="true"></span>
    <span class="qi-network-name">ANALYZE</span>
  </a>
</nav>
    </div>
  </div>
</div>
"""


def _navigate(destination: str) -> None:
    """Use the app's existing navigation-request mechanism."""
    st.session_state["_navigation_request"] = destination
    st.rerun()


def _workspace_card(
    icon: str,
    title: str,
    description: str,
    destination: str,
    key: str,
    cta: str,
) -> None:
    """Render a single accessible navigation card."""
    from html import escape

    with st.container(border=True):
        st.markdown(f"### {escape(title)}")
        st.write(description)
        st.button(cta, key=f"qi_home_card_{key}", on_click=_request_route, args=(destination,), use_container_width=True)


def _request_route(destination):
    st.session_state["_navigation_request"] = destination


def render_premium_home() -> None:
    """Clear, engaging homepage without a gesture-capturing chart."""
    st.html(_HOMEPAGE_CSS)
    st.html(_HERO.replace("__QI_NETWORK_IMAGE__", QI_NETWORK_DATA_URL))
    st.html(
        '<div class="qi-home-section-head"><h2>Where would you like to begin?</h2>'
        '<span>Pick a starting point. Go deeper whenever you want.</span></div>'
    )

    first = st.columns(2, gap="large")
    with first[0]:
        _workspace_card("radar", "Opportunity Discovery", "Screen real companies in provider displays, build your shortlist and compare source-linked research.", "💎 Quant Discovery", "discover", "Open Discovery")
    with first[1]:
        _workspace_card("book-open", "Learn finance, simply", "Explore everyday money, taxes, investing and markets through interactive lessons.", "📚 Learn", "learn", "Explore Quant Learn")

    second = st.columns(2, gap="large")
    with second[0]:
        _workspace_card("chart-line", "Explore research workflows", "Explore real-stock TradingView charts and separate experimental simulation tools.", "🔎 Stock Explorer", "stock", "Open Stock Explorer")
    with second[1]:
        _workspace_card("calculator", "Options & risk analysis", "Explore theoretical option prices, Greeks and scenarios using your own assumptions.", "💰 Options Lab", "analyze", "Open Options Lab")

    st.html(
        '<div class="qi-home-footer">QUANT INTELLIGENCE  /  INDEPENDENT RESEARCH AND EDUCATION. '
        'Information and models are not personalized financial or investment advice.</div>'
    )
