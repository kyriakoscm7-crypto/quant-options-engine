"""Instant-response, client-side simulations for Quant Learn.

All numbers are illustrative, calculated in the browser with no network calls.
The fallback for older Streamlit versions renders the same lab in an iframe.
"""
from __future__ import annotations

import inspect

import streamlit as st

COMMON_STYLE = r'''
<style>
.qi-live-shell {font-family:inherit;color:#edf2ff;background:linear-gradient(135deg,#131f38 0%,#0b152b 58%,#17172f 100%);border:1px solid #37496a;border-radius:22px;padding:clamp(16px,3vw,28px);box-shadow:0 15px 45px rgba(0,0,0,.16);margin:14px 0 24px}
.qi-live-shell * {box-sizing:border-box}
.qi-live-shell .eyebrow{font-size:11px;letter-spacing:.12em;color:#ff99c9;font-weight:800;text-transform:uppercase}
.qi-live-shell h3{font-size:clamp(1.25rem,2.2vw,1.7rem);line-height:1.26;margin:9px 0 6px;color:#fff}
.qi-live-shell p{font-size:14px;line-height:1.6;color:#bdcae1;margin:6px 0 16px}
.qi-live-shell .slab{background:rgba(8,15,33,.65);border:1px solid #2b3d5d;border-radius:16px;padding:17px;min-width:0}
.qi-live-shell .twocol{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin:14px 0}
.qi-live-shell .threecol{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:14px 0}
.qi-live-shell .metric-label{font-size:12px;color:#aebdda;font-weight:600;margin-bottom:8px}
.qi-live-shell .metric-value{font-size:clamp(1.15rem,2.8vw,1.85rem);font-weight:800;color:#fff;letter-spacing:-.03em;overflow-wrap:anywhere}
.qi-live-shell .metric-value.pink{color:#ff86bf}
.qi-live-shell .metric-value.mint{color:#83e6bd}
.qi-live-shell label{display:block;font-size:13px;font-weight:700;color:#dfe7f5;margin-bottom:10px}
.qi-live-shell .value-pill{float:right;font-weight:800;color:#ff91c5;font-variant-numeric:tabular-nums}
.qi-live-shell input[type=range]{display:block;width:100%;accent-color:#ff78b7;cursor:pointer;min-height:28px;margin:4px 0 8px}
.qi-live-shell select,.qi-live-shell input[type=number]{width:100%;background:#101f38;color:#f7faff;border:1px solid #405477;border-radius:10px;font:inherit;padding:10px 12px;max-width:100%}
.qi-live-shell .tiny{font-size:11px;color:#97a9ca}
.qi-live-shell .bar-wrap{background:#202c48;height:22px;border-radius:8px;overflow:hidden;display:flex;width:100%;margin:10px 0 7px}
.qi-live-shell .bar{height:100%;transition:width 90ms linear}
.qi-live-shell .bar.blue{background:#7997f1}.qi-live-shell .bar.pink{background:#ff78b7}
.qi-live-shell .legend{display:flex;gap:15px;flex-wrap:wrap;font-size:11px;color:#b8c8e2}
.qi-live-shell .dot{display:inline-block;width:9px;height:9px;border-radius:3px;margin-right:6px}.qi-live-shell .dot.blue{background:#7997f1}.qi-live-shell .dot.pink{background:#ff78b7}
.qi-live-shell .hint{margin-top:14px;padding:13px 15px;border-left:3px solid #ff78b7;background:rgba(255,120,183,.075);color:#e1e9f8;font-size:13px;line-height:1.5;border-radius:0 10px 10px 0}
.qi-live-shell .warning{border-color:#e9ab71;background:rgba(233,171,113,.07)}
.qi-live-shell .timeline{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:20px 0}
.qi-live-shell .stage{padding:14px 10px;background:#111e38;border:1px solid #37496a;border-radius:14px;min-width:0}
.qi-live-shell .stage .point{display:inline-grid;place-items:center;width:22px;height:22px;border-radius:50%;background:#ff78b7;color:#101b30;font-weight:800;font-size:11px;margin-bottom:9px}
.qi-live-shell .stage .stage-label{font-size:11px;line-height:1.4;color:#aebbd6;min-height:30px}
.qi-live-shell .stage .stage-value{font-weight:800;font-size:clamp(1rem,2vw,1.3rem);margin-top:8px;overflow-wrap:anywhere}
.qi-live-shell .scenario{display:flex;align-items:flex-start;gap:10px;margin:15px 0;background:#0e1b33;border-radius:12px;padding:14px}
.qi-live-shell .scenario input{margin:3px 0 0;accent-color:#ff78b7;width:18px;height:18px}
.qi-live-shell .scenario label{margin:0;font-weight:500;line-height:1.5;cursor:pointer}
@media(max-width:600px){.qi-live-shell{padding:16px;border-radius:16px}.qi-live-shell .twocol{grid-template-columns:1fr}.qi-live-shell .threecol{grid-template-columns:repeat(2,minmax(0,1fr))}.qi-live-shell .threecol .slab:last-child{grid-column:span 2}.qi-live-shell .timeline{gap:5px}.qi-live-shell .stage{padding:9px 7px}}
@media(prefers-reduced-motion:reduce){.qi-live-shell .bar{transition:none}}

/* QI BEGINNER SCENARIOS V5 */
.qi-live-shell .qi-presets {
  display:flex;
  flex-wrap:wrap;
  gap:9px;
  margin:12px 0;
}
.qi-live-shell .qi-preset-choice {
  padding:11px 14px;
  min-height:44px;
  border:1px solid #536584;
  border-radius:11px;
  background:#192b47;
  color:#f0f3ff;
  font:inherit;
  font-size:12px;
  font-weight:700;
  cursor:pointer;
}
.qi-live-shell .qi-preset-choice:hover,
.qi-live-shell .qi-preset-choice.active {
  border-color:#ff91c5;
  background:#38334f;
}
.qi-live-shell .qi-preset-choice:focus-visible {
  outline:2px solid #ffb5d8;
  outline-offset:3px;
}

</style>
'''

TAX_HTML = COMMON_STYLE + r'''
<div class="qi-live-shell" id="qi-tax-lab-v3">
<!-- QI BEGINNER SCENARIOS V5 -->
<div class="slab">
  <strong>Choose an everyday situation</strong>
  <p>Pick an example and we'll set the numbers for you.</p>
  <div class="qi-presets">
    <button type="button" class="qi-preset-choice" data-income="45000" data-raise="5000">I got a raise</button>
    <button type="button" class="qi-preset-choice" data-income="48000" data-raise="10000">I received a bonus</button>
    <button type="button" class="qi-preset-choice" data-income="95000" data-raise="20000">My income increased a lot</button>
  </div>
  <p class="tiny">Fictional tax brackets, not actual Canadian tax rates.</p>
</div>

<div class="eyebrow">Interactive experiment · responds instantly</div>
<h3>What happens when you get a raise?</h3>
<p>Move the sliders. Watch how the <strong style="color:#fff">same dollars stay in their original tax bracket</strong> even when your income grows.</p>
<div class="twocol">
  <div class="slab"><label for="qi-tax-income">Annual taxable income <span id="qi-tax-income-val" class="value-pill">$45,000</span></label>
    <select id="qi-tax-range" aria-label="Income range"><option value="250000">Everyday incomes · $0–$250k</option><option value="3000000">Explore up to $3 million</option></select>
    <input id="qi-tax-income" type="range" min="0" max="250000" step="1000" value="45000" aria-label="Starting annual taxable income">
    <span class="tiny">Adjust the income range above to investigate larger salaries.</span>
  </div>
  <div class="slab"><label for="qi-tax-raise">Your hypothetical raise <span id="qi-tax-raise-val" class="value-pill">$15,000</span></label>
    <input id="qi-tax-raise" type="range" min="0" max="500000" step="1000" value="15000" aria-label="Amount of raise">
    <span class="tiny">Try a small raise or a much larger increase.</span>
  </div>
</div>
<div class="slab">
  <div class="metric-label">Before the raise</div>
  <div class="bar-wrap" aria-label="Income portions before raise"><div class="bar blue" id="qi-tax-before-low"></div><div class="bar pink" id="qi-tax-before-high"></div></div>
  <div style="display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap"><span class="tiny" id="qi-tax-before-caption"></span><span class="tiny" id="qi-tax-before-net"></span></div>
  <div class="metric-label" style="margin-top:18px">After the raise</div>
  <div class="bar-wrap" aria-label="Income portions after raise"><div class="bar blue" id="qi-tax-after-low"></div><div class="bar pink" id="qi-tax-after-high"></div></div>
  <div style="display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap"><span class="tiny" id="qi-tax-after-caption"></span><span class="tiny" id="qi-tax-after-net"></span></div>
  <div class="legend" style="margin-top:13px"><span><span class="dot blue"></span>First $50,000 · 10% rate</span><span><span class="dot pink"></span>Above $50,000 · 20% rate</span></div>
</div>
<div class="threecol">
  <div class="slab"><div class="metric-label">Example tax on the raise</div><div class="metric-value" id="qi-tax-extra-tax"></div></div>
  <div class="slab"><div class="metric-label">Raise you keep after example tax</div><div class="metric-value mint" id="qi-tax-keep"></div></div>
  <div class="slab"><div class="metric-label">Example effective tax rate after raise</div><div class="metric-value pink" id="qi-tax-effective"></div></div>
</div>
<div class="hint" id="qi-tax-explanation" aria-live="polite"></div>
<p class="tiny" style="margin-top:14px">Simplified fictional two-rate example only, not current Canadian tax brackets or a tax estimate. Real taxes include federal and provincial rules, deductions, credits and other factors.</p>
</div>
<script>
(() => {
 const root=document.getElementById('qi-tax-lab-v3');if(!root||root.dataset.ready==='yes')return;root.dataset.ready='yes';
 const $=id=>root.querySelector('#'+id), money=n=>'$'+Math.round(n).toLocaleString('en-CA');
 const income=$('qi-tax-income'), raise=$('qi-tax-raise'), band=$('qi-tax-range');
 const tax=n=>Math.min(n,50000)*.1+Math.max(0,n-50000)*.2;
 const fmtPct=n=>(n*100).toFixed(1)+'%';
 function render(){
   const before=Number(income.value),r=Number(raise.value),after=before+r;
   $('qi-tax-income-val').textContent=money(before);$('qi-tax-raise-val').textContent=money(r);
   const scale=Math.max(after,50000);const low=n=>Math.min(n,50000),high=n=>Math.max(0,n-50000);
   [['before',before],['after',after]].forEach(([prefix,n])=>{
     $("qi-tax-"+prefix+"-low").style.width=(low(n)/scale*100)+'%';
     $("qi-tax-"+prefix+"-high").style.width=(high(n)/scale*100)+'%';
     $("qi-tax-"+prefix+"-caption").textContent=money(n)+' taxable income';
     $("qi-tax-"+prefix+"-net").textContent=money(n-tax(n))+' after illustrative tax';
   });
   const extra=tax(after)-tax(before), kept=r-extra;
   $('qi-tax-extra-tax').textContent=money(extra);$('qi-tax-keep').textContent=money(kept);
   $('qi-tax-effective').textContent=fmtPct(after?tax(after)/after:0);
   const atLower=Math.max(0,Math.min(after,50000)-Math.min(before,50000));
   const atHigher=r-atLower;
   $('qi-tax-explanation').textContent='Of your '+money(r)+' raise, '+money(atLower)+' falls in the 10% bracket and '+money(atHigher)+' falls in the 20% bracket. In this simplified model, taking a raise never causes an outright drop in your after-tax income.';
 }
 [income,raise].forEach(el=>el.addEventListener('input',render));
 band.addEventListener('change',()=>{const prev=Number(income.value);const max=Number(band.value);income.max=max;income.step=max>250000?10000:1000;income.value=Math.min(prev,max);render();});
 render();

  root.querySelectorAll('.qi-preset-choice').forEach(button=>{
    button.addEventListener('click',()=>{
      income.value=button.dataset.income;
      raise.value=button.dataset.raise;
      root.querySelectorAll('.qi-preset-choice').forEach(
        other=>other.classList.toggle('active',other===button)
      );
      render();
    });
  });
})();
</script>
'''

TFSA_HTML = COMMON_STYLE + r'''
<div class="qi-live-shell" id="qi-tfsa-lab-v3">
<!-- QI BEGINNER SCENARIOS V5 -->
<div class="slab">
  <strong>Choose an everyday situation</strong>
  <p>See how putting money into or taking money out of a TFSA changes your available contribution room.</p>
  <div class="qi-presets">
    <button type="button" class="qi-preset-choice" data-deposit="2000" data-withdraw="0" data-replace="0">I'm saving money</button>
    <button type="button" class="qi-preset-choice" data-deposit="4000" data-withdraw="3000" data-replace="0">I withdrew for a purchase</button>
    <button type="button" class="qi-preset-choice" data-deposit="8000" data-withdraw="6000" data-replace="1">I put money back too soon</button>
  </div>
  <p class="tiny">Example starts with CAD 10,000 of unused room. Actual room varies.</p>
</div>

<div class="eyebrow">Interactive timeline · responds instantly</div>
<h3>Follow your TFSA room through time</h3>
<p>A TFSA is a <strong style="color:#fff">type of account</strong>, not a specific investment. Experiment with a deposit and a withdrawal to see when contribution room returns.</p>
<div class="twocol">
  <div class="slab"><label for="qi-tfsa-deposit">Contribute in 2026 <span class="value-pill" id="qi-tfsa-deposit-val"></span></label><input id="qi-tfsa-deposit" type="range" min="0" max="10000" step="500" value="6000" aria-label="Deposit during the year"></div>
  <div class="slab"><label for="qi-tfsa-withdraw">Withdraw in 2026 <span class="value-pill" id="qi-tfsa-withdraw-val"></span></label><input id="qi-tfsa-withdraw" type="range" min="0" max="6000" step="500" value="2000" aria-label="Withdrawal during the year"></div>
</div>
<div class="timeline">
  <div class="stage"><span class="point">1</span><div class="stage-label">Start of 2026</div><div class="stage-value" id="qi-tfsa-start">$10,000</div></div>
  <div class="stage"><span class="point">2</span><div class="stage-label">After deposit and withdrawal in 2026</div><div class="stage-value" id="qi-tfsa-now"></div></div>
  <div class="stage"><span class="point">3</span><div class="stage-label">Jan 1, 2027 · excluding new annual room</div><div class="stage-value" id="qi-tfsa-next"></div></div>
</div>
<div class="slab">
  <div class="metric-label">Available contribution room during 2026</div>
  <div class="bar-wrap"><div id="qi-tfsa-now-bar" class="bar blue"></div></div>
  <div class="metric-label" style="margin-top:17px">Restored withdrawal room on Jan 1, 2027</div>
  <div class="bar-wrap"><div id="qi-tfsa-next-bar" class="bar pink"></div></div>
  <div class="legend"><span><span class="dot blue"></span>Unused room after contribution</span><span><span class="dot pink"></span>Room restored next January</span></div>
</div>
<div class="scenario"><input type="checkbox" id="qi-tfsa-replace"><label for="qi-tfsa-replace">What if I put all the withdrawn money back during 2026?</label></div>
<div class="hint" id="qi-tfsa-explanation" aria-live="polite"></div>
<p class="tiny" style="margin-top:14px">Illustration assumes $10,000 of unused contribution room at the start of 2026, no other TFSA activity, no overcontributions already, and no new 2027 annual entitlement. It does not determine anyone's actual eligibility or available room.</p>
</div>
<script>
(() => {
 const root=document.getElementById('qi-tfsa-lab-v3');if(!root||root.dataset.ready==='yes')return;root.dataset.ready='yes';
 const $=id=>root.querySelector('#'+id),money=n=>'$'+Math.round(n).toLocaleString('en-CA');
 const deposit=$('qi-tfsa-deposit'), withdraw=$('qi-tfsa-withdraw'),replace=$('qi-tfsa-replace');
 function render(){
  const d=Number(deposit.value);withdraw.max=d;if(Number(withdraw.value)>d)withdraw.value=d;
  const w=Number(withdraw.value),now=10000-d,next=now+w;
  $('qi-tfsa-deposit-val').textContent=money(d);$('qi-tfsa-withdraw-val').textContent=money(w);
  $('qi-tfsa-now').textContent=money(now);$('qi-tfsa-next').textContent=money(next);
  $('qi-tfsa-now-bar').style.width=now/10000*100+'%';$('qi-tfsa-next-bar').style.width=w/10000*100+'%';
  const info=$('qi-tfsa-explanation');info.classList.toggle('warning',false);
  if(replace.checked && w>now){
    const over=w-now;info.classList.add('warning');
    info.textContent='Potential excess contribution: '+money(over)+'. Your withdrawal did not immediately restore room; replacing '+money(w)+' would exceed the remaining '+money(now)+' of unused room in this simplified scenario.';
  } else if(replace.checked) {
    info.textContent=w===0?'There is no withdrawal to replace.':'Putting back '+money(w)+' would use part of your existing '+money(now)+' of unused room. The withdrawal itself adds no new room during 2026.';
  } else {
    info.textContent='You have '+money(now)+' of unused room during 2026. The '+money(w)+' withdrawal generally becomes additional contribution room on January 1, 2027, not right away.';
  }
 }
 [deposit,withdraw].forEach(el=>el.addEventListener('input',render));replace.addEventListener('change',render);render();

  root.querySelectorAll('.qi-preset-choice').forEach(button=>{
    button.addEventListener('click',()=>{
      deposit.value=button.dataset.deposit;
      withdraw.max=deposit.value;
      withdraw.value=button.dataset.withdraw;
      replace.checked=button.dataset.replace==='1';
      root.querySelectorAll('.qi-preset-choice').forEach(
        other=>other.classList.toggle('active',other===button)
      );
      render();
    });
  });
})();
</script>
'''


def _render(html: str, *, fallback_height: int) -> None:
    """Use inline JavaScript when available; fall back to an isolated iframe."""
    if "unsafe_allow_javascript" in inspect.signature(st.html).parameters:
        st.html(html, unsafe_allow_javascript=True)
    else:
        import streamlit.components.v1 as components
        components.html(html, height=fallback_height, scrolling=True)


def render_tax_lab() -> None:
    _render(TAX_HTML, fallback_height=860)


def render_tfsa_lab() -> None:
    _render(TFSA_HTML, fallback_height=860)
