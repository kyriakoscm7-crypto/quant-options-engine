# QI BEGINNER FINANCIAL LABS V3
"""Interactive, lesson-first Quant Learn financial labs.

Verified Python calculation models live in app.education.financial_models.
The browser-side examples mirror those simple models for responsive controls.
All HTML is application-authored, not user-provided.
"""
from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from app.education.financial_models import compound_growth, credit_card_payoff

STYLE = r'''
<style>
:root{color-scheme:dark}*,*::before,*::after{box-sizing:border-box}
html,body{margin:0;padding:0;background:transparent;color:#eaf0fc;font-family:ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}
.qi-lesson{background:radial-gradient(ellipse at 100% 0%,rgba(255,120,183,.09),transparent 45%),linear-gradient(135deg,#14223c,#0b162c 68%);border:1px solid #364967;border-radius:20px;padding:clamp(18px,3vw,28px);overflow:hidden;--pink:#ff88bf;--blue:#88a1f2;--line:#344662;--muted:#b9c8df}
.qi-lesson button,.qi-lesson input{font:inherit}.qi-lesson button{cursor:pointer}
.qi-lesson button:focus-visible,.qi-lesson input:focus-visible,.qi-lesson summary:focus-visible{outline:2px solid #ffaed5;outline-offset:3px}
.qi-eyebrow{font-size:11px;letter-spacing:.12em;font-weight:800;color:#ff9cca;text-transform:uppercase}
.qi-lesson h2{font-size:clamp(21px,2.8vw,30px);line-height:1.18;letter-spacing:-.028em;margin:9px 0 10px;color:#fff}
.qi-lesson h3{color:#fff;font-size:clamp(16px,2vw,19px);margin:0 0 10px}
.qi-lesson p{color:var(--muted);line-height:1.65;font-size:14px;margin:7px 0 12px}
.qi-lesson strong{color:#f7f9ff}
.qi-steps{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0 5px}
.qi-steps span{font-size:11px;color:#afc1df;background:#132540;padding:7px 11px;border:1px solid #344868;border-radius:50px;font-weight:650}
.qi-block{border-top:1px solid #344865;margin-top:20px;padding-top:20px}
.qi-section-head{display:flex;align-items:center;gap:10px;margin-bottom:7px}
.qi-num{display:grid;place-items:center;flex:0 0 30px;height:30px;border-radius:10px;background:rgba(255,120,183,.14);border:1px solid rgba(255,120,183,.3);color:#ff9ed0;font-size:12px;font-weight:800}
.qi-concepts{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:13px}
.qi-concept{padding:13px 14px;border:1px solid var(--line);border-radius:13px;background:rgba(9,19,37,.58);min-width:0}
.qi-concept strong{display:block;color:#ff9acb;font-size:13px;margin-bottom:7px}
.qi-concept span{display:block;color:#bfcde2;font-size:12px;line-height:1.5}
.qi-example{padding:14px 17px;background:linear-gradient(100deg,rgba(119,146,225,.12),rgba(255,120,183,.06));border:1px solid #405174;border-radius:13px;margin-top:13px}
.qi-example b{font-size:13px;color:#fff}
.qi-example p{margin:5px 0 0;font-size:13px}
.qi-presets{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0 14px}
.qi-preset{background:#152743;border:1px solid #485d7e;color:#dce7f8;border-radius:10px;font-size:12px;font-weight:700;padding:9px 13px;min-height:38px}
.qi-preset:hover,.qi-preset.active{color:#ffe7f2;border-color:#ff8fc5;background:rgba(255,120,183,.13)}
.qi-controls{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:11px;margin:10px 0}
.qi-control{background:#101e36;border:1px solid #364a6b;border-radius:13px;padding:14px;min-width:0}
.qi-control label{display:flex;justify-content:space-between;align-items:baseline;gap:9px;font-size:12px;line-height:1.4;font-weight:750;color:#cbd8ec}
.qi-control output{color:#ff9ccf;font-weight:800;font-variant-numeric:tabular-nums;white-space:nowrap}
.qi-control input[type=range]{width:100%;margin:16px 0 2px;min-height:26px;accent-color:#ff78b7;cursor:pointer;touch-action:pan-y}
.qi-control .qi-small{color:#96a9c8;font-size:11px;margin-top:6px}
.qi-details{border:1px solid #354869;border-radius:12px;margin:9px 0 12px;background:#101e35;padding:0 13px}
.qi-details summary{cursor:pointer;padding:12px 0;font-size:12px;color:#cbd9ef;font-weight:750;list-style-position:inside}
.qi-details .qi-controls{margin:5px 0 12px}
.qi-metrics{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px;margin:13px 0}
.qi-metric{border:1px solid #3b4f70;background:#102039;border-radius:13px;padding:13px;min-width:0}
.qi-metric span{display:block;font-size:11px;line-height:1.4;color:#b4c3db;margin-bottom:7px}
.qi-metric strong{font-size:clamp(17px,2.5vw,24px);font-variant-numeric:tabular-nums;letter-spacing:-.025em;overflow-wrap:anywhere}
.qi-metric strong.pink{color:#ff92c6}
.qi-figure{padding:13px;border-radius:14px;border:1px solid #394e70;background:#0e1b31;margin:12px 0}
.qi-figure-head{display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;font-size:12px;font-weight:750}
.qi-legend{color:#b4c4df;font-weight:450;font-size:11px}
.qi-dot{display:inline-block;width:8px;height:8px;border-radius:3px;margin:0 4px 0 8px}.qi-dot:first-child{margin-left:0}.qi-dot.pink{background:var(--pink)}.qi-dot.blue{background:var(--blue)}
.qi-figure svg{width:100%;height:auto;max-height:220px;display:block;pointer-events:none;margin-top:7px}
.qi-insight{border-left:3px solid #ff80b9;padding:12px 14px;background:rgba(255,120,183,.075);border-radius:0 9px 9px 0;font-size:13px;color:#e2eaf8;line-height:1.55;margin-top:10px}
.qi-insight.warning{border-left-color:#eda970;background:rgba(237,169,112,.09)}
.qi-breakdown{height:19px;display:flex;overflow:hidden;background:#1f304b;border-radius:7px;margin:13px 0 7px}
.qi-part{height:100%;transition:width .1s linear}
.qi-part.pink{background:#ff88bf}.qi-part.blue{background:#88a1f2}
.qi-breakdown-label{font-size:12px;color:#c4d0e4;display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap}
.qi-question{border-radius:14px;border:1px solid #405174;background:rgba(15,29,52,.85);padding:15px;margin-top:12px}
.qi-question p{font-size:13px;margin:0 0 10px;font-weight:650;color:#edf2ff}
.qi-choices{display:grid;gap:8px}
.qi-choice{text-align:left;background:#152745;color:#dce6f7;border:1px solid #465b7b;padding:11px 13px;border-radius:10px;font-size:12px;line-height:1.5;min-height:40px}
.qi-choice:hover{border-color:#ff95c7}.qi-choice.correct{border-color:#77d4ab;background:rgba(103,205,155,.13)}.qi-choice.wrong{border-color:#f2ab7b;background:rgba(242,171,123,.1)}
.qi-feedback{margin-top:10px;min-height:19px;color:#bde8d2;font-size:12px;line-height:1.6}
.qi-feedback.retry{color:#ffd1ad}
.qi-endnote{font-size:11px!important;line-height:1.6!important;color:#99aac7!important;margin:14px 0 0!important}
.qi-njs{padding:12px;background:#392538;color:#ffccdf;border-radius:10px;margin-top:12px}
@media(max-width:610px){.qi-lesson{border-radius:15px;padding:16px}.qi-concepts{grid-template-columns:1fr}.qi-controls{grid-template-columns:1fr}.qi-metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.qi-metrics .qi-metric:last-child{grid-column:span 2}.qi-metric strong{font-size:19px}.qi-figure svg{max-height:185px}}
@media(max-width:370px){.qi-metrics{grid-template-columns:1fr}.qi-metrics .qi-metric:last-child{grid-column:auto}.qi-presets{gap:6px}.qi-preset{font-size:11px;padding:8px 10px}}
@media(prefers-reduced-motion:reduce){.qi-part{transition:none}}
</style>
'''

GROWTH = r'''
<main class="qi-lesson" id="qi-growth-v2">
  <div class="qi-eyebrow">Quant Learn / 5-minute guided lesson</div>
  <h2>Make time work for your savings</h2>
  <p>Saving and investing are related, but different. First understand the moving parts. Then try a scenario and answer one question.</p>
  <div class="qi-steps"><span>01 Learn</span><span>02 See an example</span><span>03 Experiment</span><span>04 Check yourself</span></div>
  <section class="qi-block">
    <div class="qi-section-head"><span class="qi-num">01</span><h3>Three things build your balance</h3></div>
    <div class="qi-concepts">
      <div class="qi-concept"><strong>Your starting savings</strong><span>The amount already put aside. Even without growth, it remains part of the total.</span></div>
      <div class="qi-concept"><strong>New contributions</strong><span>Money you keep adding. Regular saving increases your balance even with a 0% return.</span></div>
      <div class="qi-concept"><strong>Compounding</strong><span>When previous growth stays invested, future growth can build on it. Losses can compound too.</span></div>
    </div>
  </section>
  <section class="qi-block">
    <div class="qi-section-head"><span class="qi-num">02</span><h3>A simple example</h3></div>
    <div class="qi-example"><b>Start with $1,000. Save $100 each month for one year. Assume 0% growth.</b>
      <p>You finish with <strong>$2,200</strong> ($1,000 + 12 × $100). Every dollar came from you. A positive hypothetical return could add growth, but it would not be guaranteed.</p></div>
  </section>
  <section class="qi-block">
    <div class="qi-section-head"><span class="qi-num">03</span><h3>Try changing the story</h3></div>
    <p>Start with a familiar saving habit. We choose example numbers for you. Then explore how the amount saved, time, and uncertain investment returns change the outcome.</p>
    <div class="qi-presets" role="group" aria-label="Savings scenarios">
      <button type="button" class="qi-preset active" data-scenario="steady">Save about $25 per week</button>
      <button type="button" class="qi-preset" data-scenario="zero">What if savings earn 0%?</button>
      <button type="button" class="qi-preset" data-scenario="long">Keep saving for 30 years</button>
<button type="button" class="qi-preset" data-scenario="down">What if returns are negative?</button>
    </div>
    <div class="qi-controls">
      <div class="qi-control"><label for="g-month">Monthly savings <output id="g-month-v">$250</output></label><input id="g-month" type="range" min="0" max="3000" step="25" value="250"><div class="qi-small">Money you add at the end of each month</div></div>
      <div class="qi-control"><label for="g-years">Years of saving <output id="g-years-v">20 years</output></label><input id="g-years" type="range" min="1" max="45" step="1" value="20"><div class="qi-small">Longer periods also mean more contributions</div></div>
    </div>
    <details class="qi-details"><summary>Adjust starting amount and return assumptions</summary>
      <div class="qi-controls"><div class="qi-control"><label for="g-start">Starting savings <output id="g-start-v">$5,000</output></label><input id="g-start" type="range" min="0" max="100000" step="500" value="5000"></div>
      <div class="qi-control"><label for="g-rate">Illustrative nominal annual return <output id="g-rate-v">5.0%</output></label><input id="g-rate" type="range" min="-10" max="15" step="0.5" value="5"></div></div>
    </details>
    <div class="qi-metrics">
      <div class="qi-metric"><span>Example ending balance</span><strong id="g-end" class="pink">Calculating…</strong></div>
      <div class="qi-metric"><span>Money you contributed</span><strong id="g-paid">Calculating…</strong></div>
      <div class="qi-metric"><span>Illustrative growth or loss</span><strong id="g-gain">Calculating…</strong></div>
    </div>
    <div class="qi-figure"><div class="qi-figure-head"><strong>Follow the money across the years</strong><span class="qi-legend"><i class="qi-dot pink"></i>Total balance <i class="qi-dot blue"></i>Your deposits</span></div>
      <svg viewBox="0 0 700 235" role="img" aria-label="Chart of modeled total balance and cumulative deposits across the selected years"><g id="g-grid"></g><path id="g-area" fill="#ff78b7" fill-opacity=".08"></path><path id="g-saved" fill="none" stroke="#88a1f2" stroke-width="3" stroke-linecap="round"></path><path id="g-balance" fill="none" stroke="#ff92c5" stroke-width="3.5" stroke-linecap="round"></path><text x="16" y="224" font-size="12" fill="#afbfda">Year 0</text><text id="g-endyear" x="680" y="224" font-size="12" fill="#afbfda" text-anchor="end">Year 20</text><text id="g-axis" x="16" y="16" font-size="12" fill="#afbfda"></text></svg></div>
    <div class="qi-insight" id="g-insight" aria-live="polite">Calculating the example…</div>
  </section>
  <section class="qi-block">
    <div class="qi-section-head"><span class="qi-num">04</span><h3>Check your understanding</h3></div>
    <div class="qi-question"><p>If your savings earn a 0% return, what can still make the balance increase?</p>
      <div class="qi-choices" role="group" aria-label="Savings knowledge check"><button class="qi-choice" data-answer="wrong" type="button">Nothing. The balance must stay unchanged.</button><button class="qi-choice" data-answer="correct" type="button">Adding more of your own money.</button><button class="qi-choice" data-answer="wrong" type="button">A guaranteed stock-market profit.</button></div>
      <div class="qi-feedback" id="g-feedback" aria-live="polite">Choose an answer to test what you learned.</div>
    </div>
    <p><strong>Remember:</strong> a projection is not a promise. Financial markets fluctuate, and inflation, fees and taxes can affect the outcome.</p>
  </section>
  <p class="qi-endnote">Educational scenario: a constant nominal annual return divided into monthly rates, monthly compounding, and month-end deposits. No fees, inflation, taxes, or random market movements. This is not a forecast or personal financial advice.</p>
  <noscript><div class="qi-njs">This interactive lesson requires JavaScript. Enable it to see live results and complete the practice check.</div></noscript>
<!-- QI EXTENDED FINANCIAL EDUCATION V3 -->

<section class="qi-block" aria-label="Deeper learning about saving and investing">
  <div class="qi-section-head"><span class="qi-num">05</span><h3>Go deeper: what actually makes money grow?</h3></div>
  <p>There are three different ways your balance can increase: money you deposit, returns earned on that money, and returns earned on earlier returns. Understanding the difference helps you interpret any savings projection.</p>
  <div class="qi-concepts">
    <div class="qi-concept"><strong>Simple interest</strong><span>Interest is calculated on the original amount. For example, $1,000 earning 5% simple interest produces $50 each year.</span></div>
    <div class="qi-concept"><strong>Compound growth</strong><span>Earlier earnings can earn more earnings. At a hypothetical 5% compounded annually, $1,000 becomes $1,050 after year one and $1,102.50 after year two.</span></div>
    <div class="qi-concept"><strong>Regular contributions</strong><span>Adding money consistently increases the amount working for you. In a projection, deposits and investment returns must be shown separately.</span></div>
  </div>
  <div class="qi-example">
    <b>Why does starting early matter?</b>
    <p>Consider two people who each deposit $100 per month at a hypothetical 5% annual return, compounded monthly. After 20 years, the projected balance is about $41,100. After 30 years, it is about $83,200. The extra decade adds $12,000 in contributions but produces a much larger increase in the projected balance because returns have more time to compound.</p>
    <p>These are illustrations, not guaranteed outcomes. Actual investments can lose value.</p>
  </div>
</section>
<section class="qi-block" aria-label="What savings projections can leave out">
  <div class="qi-section-head"><span class="qi-num">06</span><h3>What a growth calculator doesn't tell you</h3></div>
  <div class="qi-concepts">
    <div class="qi-concept"><strong>Inflation</strong><span>A larger future balance may buy less than the same amount today. A 3% annual inflation assumption means prices approximately double over 24 years.</span></div>
    <div class="qi-concept"><strong>Fees and taxes</strong><span>Management fees reduce the return you keep. Taxes depend on the account and investment; Canadian TFSAs and RRSPs have different rules.</span></div>
    <div class="qi-concept"><strong>Investment risk</strong><span>Market returns are not steady. A constant-return simulation smooths away the gains and losses investors actually experience.</span></div>
  </div>
  <div class="qi-example"><b>A practical takeaway</b><p>When comparing savings plans, examine how much you contribute, how long you save, the uncertainty of returns, fees, inflation, and when you might need the money. Higher projected returns should never be treated as certain.</p></div>
</section>
<section class="qi-block" aria-label="Savings knowledge checks">
  <div class="qi-section-head"><span class="qi-num">07</span><h3>Can you explain it?</h3></div>
  <details class="qi-details"><summary>Question 1: If your investment doubles, is all that money investment growth?</summary><p>Not necessarily. Your final balance contains your original deposits and any gains or losses. To calculate investment growth, subtract all your contributions from the ending balance.</p></details>
  <details class="qi-details"><summary>Question 2: Can an investment have positive returns but lose purchasing power?</summary><p>Yes. If your investment earns 2% while prices rise 4%, you have more dollars but, approximately, less purchasing power after inflation.</p></details>
</section>

</main>
<script>
(()=>{'use strict';
  const root=document.getElementById('qi-growth-v2');if(!root||root.dataset.ready==='yes')return;root.dataset.ready='yes';
  const $=id=>root.querySelector('#'+id),cash=n=>(n<0?'−':'')+'$'+Math.round(Math.abs(n)).toLocaleString('en-CA');
  const controls=['g-month','g-years','g-start','g-rate'];
  const scenarios={steady:[0,100,5,20],long:[0,100,5,30],zero:[0,100,0,20],down:[0,100,-5,20]};
  function point(values,maxVal){const left=16,right=682,top=23,bottom=195,maxY=Math.max(1,maxVal);return values.map((n,i)=>[left+(right-left)*i/(values.length-1),bottom-(bottom-top)*n/maxY].map(v=>v.toFixed(2)).join(',')).join(' L');}
  function draw(){
    const start=+$('g-start').value,month=+$('g-month').value,rate=+$('g-rate').value,years=+$('g-years').value;
    $('g-start-v').textContent=cash(start);$('g-month-v').textContent=cash(month);$('g-rate-v').textContent=rate.toFixed(1)+'%';$('g-years-v').textContent=years+' '+(years===1?'year':'years');
    let balance=start,contributed=start;const balances=[balance],paid=[contributed];
    for(let y=1;y<=years;y++){for(let m=0;m<12;m++){balance=balance*(1+rate/1200)+month;contributed+=month;}balances.push(balance);paid.push(contributed);}
    const difference=balance-contributed;
    $('g-end').textContent=cash(balance);$('g-paid').textContent=cash(contributed);$('g-gain').textContent=cash(difference);
    const max=Math.max(1,...balances,...paid),b='M'+point(balances,max),c='M'+point(paid,max);
    $('g-balance').setAttribute('d',b);$('g-saved').setAttribute('d',c);$('g-area').setAttribute('d',b+' L682,195 L16,195 Z');
    $('g-grid').innerHTML=[0,.5,1].map(t=>'<line x1="16" x2="682" y1="'+(195-172*t)+'" y2="'+(195-172*t)+'" stroke="#445572" stroke-dasharray="4 7" opacity=".55"/>').join('');
    $('g-axis').textContent='Up to '+cash(max);$('g-endyear').textContent='Year '+years;
    $('g-insight').textContent=difference>1?'Your modeled balance includes '+cash(contributed)+' you deposited and '+cash(difference)+' in hypothetical growth. Try 0% to isolate the impact of saving.':difference< -1?'The assumed return caused a modeled loss of '+cash(-difference)+'. Even with regular deposits, an investment can finish below what you put in.':'Here, your modeled balance comes entirely from deposits. The 0% return adds no growth. Saving itself still moves the total upward.';

    // Explain when a payment equals the original balance but
    // does not cover the interest accrued in the modeled month.
    const onePaymentAmount=bal+first;
    if(pay>=bal && pay<onePaymentAmount-0.005){
      hint.className='qi-insight warning';
      hint.textContent='Why does '+cash(pay)+' not clear a '+cash(bal)+
        ' balance? This example adds '+cash(first)+
        ' in first-month interest before your payment. The modeled '+
        'amount needed to clear the balance in that first payment is '+
        cash(onePaymentAmount)+'. Paying '+cash(pay)+
        ' leaves approximately '+cash(onePaymentAmount-pay)+
        ' outstanding. This is different from paying an eligible '+
        'statement balance in full within a grace period.';
    }else if(pay>=onePaymentAmount-0.005){
      hint.className='qi-insight';
      hint.textContent='Your payment is enough to clear this modeled '+
        'balance in one month. Of the approximately '+
        cash(onePaymentAmount)+' due, '+cash(first)+
        ' is first-month interest and '+cash(bal)+
        ' pays down the original balance. An unused portion of your '+
        'chosen payment is not charged.';
    }
    root.dataset.calculated='yes';
  }
  controls.forEach(id=>$(id).addEventListener('input',()=>{root.querySelectorAll('.qi-preset').forEach(b=>b.classList.remove('active'));draw();}));
  root.querySelectorAll('.qi-preset').forEach(b=>b.addEventListener('click',()=>{const vals=scenarios[b.dataset.scenario];['g-start','g-month','g-rate','g-years'].forEach((id,i)=>{$(id).value=vals[i];});root.querySelectorAll('.qi-preset').forEach(x=>x.classList.toggle('active',x===b));draw();}));
  root.querySelectorAll('.qi-choice').forEach(b=>b.addEventListener('click',()=>{root.querySelectorAll('.qi-choice').forEach(x=>x.classList.remove('correct','wrong'));const yes=b.dataset.answer==='correct';b.classList.add(yes?'correct':'wrong');const f=$('g-feedback');f.className='qi-feedback'+(yes?'':' retry');f.textContent=yes?'Correct! Your deposits increase your savings even if no investment return is earned.':'Not quite. Think about the $1,000 + $100 per month example, then try again.';}));
  draw();
})();
</script>
'''

DEBT = r'''
<main class="qi-lesson" id="qi-debt-v2">
  <div class="qi-eyebrow">Quant Learn / 5-minute guided lesson</div>
  <h2>Understand what credit-card interest costs</h2>
  <p>Credit is not free money. Learn why a debt can shrink slowly, then see how changing the payment alters the example.</p>
  <div class="qi-steps"><span>01 Learn</span><span>02 See an example</span><span>03 Experiment</span><span>04 Check yourself</span></div>
  <section class="qi-block">
    <div class="qi-section-head"><span class="qi-num">01</span><h3>Your payment does two jobs</h3></div>
    <div class="qi-concepts">
      <div class="qi-concept"><strong>APR</strong><span>The annual percentage rate used to calculate interest. Real cards often calculate interest daily.</span></div>
      <div class="qi-concept"><strong>Interest</strong><span>The cost of carrying a balance. Part of your payment covers this cost first.</span></div>
      <div class="qi-concept"><strong>Principal</strong><span>The amount you still owe. Only the part of a payment beyond interest reduces it.</span></div>
    </div>
  </section>
  <section class="qi-block">
    <div class="qi-section-head"><span class="qi-num">02</span><h3>A $1,000 example</h3></div>
    <div class="qi-example"><b>Suppose you owe $1,000 at 24% APR and pay $30 this month.</b><p>In this simplified monthly model, first-month interest is roughly <strong>$20</strong> ($1,000 × 24% ÷ 12). Only about <strong>$10</strong> of that $30 reduces your debt. You still owe roughly <strong>$990</strong>.</p></div>
  </section>
  <section class="qi-block">
    <div class="qi-section-head"><span class="qi-num">03</span><h3>See why payments matter</h3></div>
    <p>Start with the same fictional $1,000 debt in each situation. This calculator assumes the balance is already accruing interest and adds one month's interest before each payment. Choose a monthly payment to explore how repayment changes.

<!-- QI CREDIT CARD CLARITY V4 -->
<div class="qi-example">
  <b>Two situations that work differently</b>
  <p><strong>Paying a statement in full:</strong> If you pay the full
  statement balance by the due date and meet your card's grace-period
  conditions, eligible purchases generally do not incur purchase
  interest.</p>
  <p><strong>Repaying existing interest-bearing debt:</strong> The
  calculator below models a balance that accrues interest each month.
  At 24% APR, a $1,000 balance incurs about $20 of interest in its
  first modeled month, making the amount to clear it approximately
  <strong>$1,020</strong> at that payment point.</p>
  <p class="qi-small">Real credit cards often calculate interest daily.
  Exact payoff amounts depend on dates, transaction types, fees and
  issuer rules. This is an educational example, not a payoff quote.</p>
</div>
</p>
    <div class="qi-presets" role="group" aria-label="Credit-card scenarios"><button class="qi-preset active" data-scenario="everyday" type="button">Pay $30 each month</button><button class="qi-preset" data-scenario="larger" type="button">Pay $150 each month</button><button class="qi-preset" data-scenario="trap" type="button">Pay only the first month's interest</button></div>
    <div class="qi-controls">
      <div class="qi-control"><label for="d-pay">Monthly payment <output id="d-pay-v">$100</output></label><input id="d-pay" type="range" min="10" max="1500" step="10" value="100"><div class="qi-small">Amount you pay each month, assuming no new spending</div></div>
      <div class="qi-control"><label for="d-extra">What if you pay extra? <output id="d-extra-v">+$50</output></label><input id="d-extra" type="range" min="0" max="500" step="10" value="50"><div class="qi-small">Compare with this additional payment each month</div></div>
    </div>
    <details class="qi-details"><summary>Adjust balance and annual interest rate</summary><div class="qi-controls">
      <div class="qi-control"><label for="d-balance">Balance owed <output id="d-balance-v">$1,000</output></label><input id="d-balance" type="range" min="100" max="20000" step="100" value="1000"></div>
      <div class="qi-control"><label for="d-apr">APR <output id="d-apr-v">24.0%</output></label><input id="d-apr" type="range" min="0" max="35" step="0.5" value="24"></div>
    </div></details>
    <div class="qi-metrics"><div class="qi-metric"><span>Months to pay off</span><strong id="d-months" class="pink">Calculating…</strong></div><div class="qi-metric"><span>Interest over repayment</span><strong id="d-interest">Calculating…</strong></div><div class="qi-metric"><span>Possible interest saved by paying extra</span><strong id="d-saved">Calculating…</strong></div></div>
    <div class="qi-figure"><div class="qi-figure-head"><strong>Where your first payment goes</strong><span class="qi-legend"><i class="qi-dot pink"></i>Interest <i class="qi-dot blue"></i>Principal</span></div>
      <div class="qi-breakdown" role="img" aria-label="First payment split between interest and principal"><div class="qi-part pink" id="d-interest-bar" style="width:0%"></div><div class="qi-part blue" id="d-principal-bar" style="width:0%"></div></div>
      <div class="qi-breakdown-label"><span id="d-firstinterest">Calculating interest…</span><span id="d-firstprincipal">Calculating principal…</span></div></div>
    <div class="qi-figure"><div class="qi-figure-head"><strong>How the amount owed changes</strong><span class="qi-legend"><i class="qi-dot pink"></i>Current payment <i class="qi-dot blue"></i>With extra</span></div>
      <svg viewBox="0 0 700 230" role="img" aria-label="Remaining credit card balance with and without the additional monthly payment"><g id="d-grid"></g><path id="d-standard" fill="none" stroke="#ff92c5" stroke-width="3.5" stroke-linecap="round"></path><path id="d-fast" fill="none" stroke="#88a1f2" stroke-width="3" stroke-linecap="round"></path><text x="16" y="220" fill="#afbfda" font-size="12">Now</text><text x="682" y="220" fill="#afbfda" font-size="12" text-anchor="end">Months →</text></svg></div>
    <div class="qi-insight" id="d-insight" aria-live="polite">Calculating your repayment example…</div>
  </section>
  <section class="qi-block"><div class="qi-section-head"><span class="qi-num">04</span><h3>Check your understanding</h3></div>
    <div class="qi-question"><p>What happens if the payment is smaller than the interest charged that month and there are no other adjustments?</p>
      <div class="qi-choices" role="group" aria-label="Debt knowledge check"><button type="button" class="qi-choice" data-answer="correct">The balance can increase even though you paid.</button><button type="button" class="qi-choice" data-answer="wrong">The balance always goes down when you pay anything.</button><button type="button" class="qi-choice" data-answer="wrong">The interest rate automatically falls to zero.</button></div><div class="qi-feedback" id="d-feedback" aria-live="polite">Choose an answer to test what you learned.</div></div>
    <p><strong>Remember:</strong> a bigger payment generally helps you reduce principal sooner, but actual minimum-payment rules, fees, grace periods, and daily interest vary by card. Paying the full statement balance by the due date can avoid purchase interest when the grace-period conditions are met.</p>
  </section>
  <p class="qi-endnote">Illustrative monthly-interest model: APR divided by 12, interest charged before each payment, no new purchases, no fees, and a 600-month limit. This is not a real credit-card statement or personalized advice.</p>
  <noscript><div class="qi-njs">JavaScript is required to interact with the live example and knowledge check.</div></noscript>
<!-- QI EXTENDED FINANCIAL EDUCATION V3 -->

<section class="qi-block" aria-label="Deeper learning about credit cards">
  <div class="qi-section-head"><span class="qi-num">05</span><h3>Understand the credit card statement</h3></div>
  <p>Before thinking about repayment, understand which balance you are looking at and when interest may be charged.</p>
  <div class="qi-concepts">
    <div class="qi-concept"><strong>Statement balance</strong><span>The amount shown when your billing period closes. Paying this in full by the due date generally helps preserve the interest-free grace period on eligible purchases.</span></div>
    <div class="qi-concept"><strong>Current balance</strong><span>The amount currently owed, potentially including purchases made after the statement date. It can differ from your last statement balance.</span></div>
    <div class="qi-concept"><strong>Minimum payment</strong><span>The smallest payment required by the issuer. Paying it may keep the account current, but it can leave substantial debt collecting interest.</span></div>
  </div>
  <div class="qi-example"><b>Example: the statement closes at $600</b><p>If you make a new $100 purchase after the statement date, your current balance may become $700, while your last statement balance remains $600. The payment needed to retain the purchase grace period depends on your card agreement and whether you already carry a balance.</p></div>
</section>
<section class="qi-block" aria-label="Credit card interest and safer repayment">
  <div class="qi-section-head"><span class="qi-num">06</span><h3>Why credit card debt can become expensive</h3></div>
  <div class="qi-concepts">
    <div class="qi-concept"><strong>Interest often accrues daily</strong><span>Real credit cards may use daily balance methods. The lesson's APR ÷ 12 calculation is a simplified teaching model, not a substitute for your card agreement.</span></div>
    <div class="qi-concept"><strong>Grace periods have conditions</strong><span>Eligible purchases may avoid interest when the required statement balance is paid on time. Cash advances generally work differently and can accrue interest immediately.</span></div>
    <div class="qi-concept"><strong>Small payments create a long tail</strong><span>If most of each payment goes toward interest, little principal disappears. Paying more than the required minimum can reduce total interest and repayment time.</span></div>
  </div>
  <div class="qi-example"><b>Four practical habits</b><p>Review your statement, track the due date, avoid spending beyond what you can repay, and prioritize high-interest balances when making a repayment plan. If repayment becomes difficult, consider contacting the lender or a reputable nonprofit credit counsellor.</p></div>
</section>
<section class="qi-block" aria-label="Credit card knowledge checks">
  <div class="qi-section-head"><span class="qi-num">07</span><h3>Can you explain it?</h3></div>
  <details class="qi-details"><summary>Question 1: Does paying the minimum mean you avoid interest?</summary><p>No. The minimum payment is not usually the same as paying the statement balance in full. Remaining eligible purchase balances may accrue interest, subject to the card's terms and grace-period rules.</p></details>
  <details class="qi-details"><summary>Question 2: Why does increasing the monthly payment help?</summary><p>More of your money can reduce principal sooner. A smaller principal generally means less interest accrues in later periods, assuming the interest rate and other conditions remain unchanged.</p></details>
</section>

</main>
<script>
(()=>{'use strict';
 const root=document.getElementById('qi-debt-v2');if(!root||root.dataset.ready==='yes')return;root.dataset.ready='yes';
 const $=id=>root.querySelector('#'+id),cash=n=>'$'+Math.round(Math.max(0,n)).toLocaleString('en-CA');
 const scenarios={everyday:[1000,24,30,50],larger:[1000,24,150,50],trap:[1000,24,20,50]};
 const controls=['d-pay','d-extra','d-balance','d-apr'];
 function simulate(start,rate,payment){const r=rate/1200;if(payment<=start*r+1e-9)return null;let balance=start,interest=0,total=0;const values=[balance];for(let m=1;m<=600;m++){const i=balance*r,p=Math.min(payment,balance+i);balance=Math.max(0,balance+i-p);interest+=i;total+=p;values.push(balance);if(balance<.005)return{months:m,interest,total,values};}return null;}
 function months(n){if(n==null)return 'Not repaid';const y=Math.floor(n/12),m=n%12;return y?y+' yr '+m+' mo':m+' months';}
 function draw(){
   const bal=+$('d-balance').value,apr=+$('d-apr').value,pay=+$('d-pay').value,extra=+$('d-extra').value;
   $('d-balance-v').textContent=cash(bal);$('d-apr-v').textContent=apr.toFixed(1)+'%';$('d-pay-v').textContent=cash(pay);$('d-extra-v').textContent='+'+cash(extra);
   const standard=simulate(bal,apr,pay),fast=simulate(bal,apr,pay+extra),first=bal*apr/1200,applied=Math.min(pay,bal+first),principal=Math.max(0,applied-first);
   $('d-months').textContent=months(standard?.months);$('d-interest').textContent=standard?cash(standard.interest):'Not repaid';
   $('d-saved').textContent=standard&&fast?cash(Math.max(0,standard.interest-fast.interest)):'Not comparable';
   $('d-interest-bar').style.width=(applied?Math.min(100,first/applied*100):0)+'%';$('d-principal-bar').style.width=(applied?Math.min(100,principal/applied*100):0)+'%';
   $('d-firstinterest').textContent=cash(first)+' first-month interest';$('d-firstprincipal').textContent=cash(principal)+' toward principal';
   const horizon=Math.max(1,standard?.months||0,fast?.months||0),end=682,top=22,bottom=195;
   function line(values){if(!values)return'';return 'M'+values.map((v,i)=>(16+(end-16)*i/horizon).toFixed(2)+','+(top+(bottom-top)*(1-Math.min(1,v/bal))).toFixed(2)).join(' L');}
   $('d-standard').setAttribute('d',line(standard?.values));$('d-fast').setAttribute('d',line(fast?.values));
   $('d-grid').innerHTML=[0,.5,1].map(t=>'<line x1="16" x2="682" y1="'+(top+(bottom-top)*t)+'" y2="'+(top+(bottom-top)*t)+'" stroke="#445572" stroke-dasharray="4 7" opacity=".55"/>').join('');
   const hint=$('d-insight');
   if(!standard){hint.className='qi-insight warning';hint.textContent=pay<=first?'The first month costs '+cash(first)+' in interest, more than or equal to the '+cash(pay)+' payment. The balance will not go down at this payment. Try paying more.':'The balance is not fully repaid within this model’s 50-year limit. Try increasing the payment.';}
   else if(extra>0&&fast){hint.className='qi-insight';hint.textContent='Increasing the payment from '+cash(pay)+' to '+cash(pay+extra)+' could shorten repayment by '+(standard.months-fast.months)+' months and reduce modeled interest by '+cash(Math.max(0,standard.interest-fast.interest))+'.';}
   else{hint.className='qi-insight';hint.textContent='At '+cash(pay)+' per month, the modeled balance can be paid off in '+months(standard.months)+'. Try adding a little more each month to compare.';}
   root.dataset.calculated='yes';
 }
 controls.forEach(id=>$(id).addEventListener('input',()=>{root.querySelectorAll('.qi-preset').forEach(b=>b.classList.remove('active'));draw();}));
 root.querySelectorAll('.qi-preset').forEach(b=>b.addEventListener('click',()=>{const v=scenarios[b.dataset.scenario];['d-balance','d-apr','d-pay','d-extra'].forEach((id,i)=>{$(id).value=v[i];});root.querySelectorAll('.qi-preset').forEach(x=>x.classList.toggle('active',x===b));draw();}));
 root.querySelectorAll('.qi-choice').forEach(b=>b.addEventListener('click',()=>{root.querySelectorAll('.qi-choice').forEach(x=>x.classList.remove('correct','wrong'));const yes=b.dataset.answer==='correct';b.classList.add(yes?'correct':'wrong');const f=$('d-feedback');f.className='qi-feedback'+(yes?'':' retry');f.textContent=yes?'Correct! A payment below the interest charged can allow the balance to grow.':'Try again. Your payment first has to cover the interest; only what remains can reduce principal.';}));
 draw();
})();
</script>
'''


def _show_lesson(html: str, *, legacy_height: int = 1640) -> None:
    """Run trusted application-authored JS in a frame, not an inline st.html node.

    Streamlit's st.iframe sizes content automatically on newer versions.
    The older components API still executes JavaScript but needs a fixed height.
    """
    document = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head><body>' + STYLE + html + '</body></html>'
    if hasattr(st, "iframe"):
        st.iframe(document, width="stretch", height="content", alt="Interactive financial education lesson")
    else:
        components.html(document, height=legacy_height, scrolling=True)


def render_compound_growth() -> None:
    """Teach and demonstrate growth using the canonical tested backend model."""
    compound_growth(5000, 250, 5, 20)
    _show_lesson(GROWTH)


# QI SIMPLE CREDIT CARD LESSON V5
def render_credit_card() -> None:
    """A beginner-first credit-card lesson with optional advanced tools."""

    st.markdown("### What happens if you don't pay your credit card?")
    st.write(
        "Imagine you spent **CAD 1,000** using your credit card. "
        "Your statement arrives. What do you do next?"
    )

    st.markdown("#### Choose what you would pay")

    situation = st.radio(
        "Your decision",
        [
            "I pay the full $1,000 statement balance on time",
            "I only pay $500",
            "I only pay $30",
        ],
        key="qi_simple_credit_situation_v5",
    )

    with st.container(border=True):
        if situation.startswith("I pay the full"):
            st.metric("Unpaid portion of the original balance", "CAD 0")
            st.success(
                "You paid the full statement balance! Eligible purchases "
                "generally avoid interest when you pay in full by the due "
                "date and meet your card's grace-period conditions."
            )
        elif situation == "I only pay $500":
            st.metric(
                "Unpaid portion of the original balance", "CAD 500"
            )
            st.write(
                "You paid half of what you owed. The other CAD 500 is "
                "still unpaid, and interest may apply. The exact amount "
                "you owe depends on your card's rules and dates."
            )
        else:
            st.metric(
                "Unpaid portion of the original balance", "CAD 970"
            )
            st.write(
                "You only paid a small amount. Most of the original "
                "balance remains unpaid. Interest may apply, making "
                "the debt more expensive over time."
            )

    st.caption(
        "This shows only the unpaid portion of the original purchase, "
        "not an exact credit-card payoff amount. Interest and fees, "
        "if applicable, are not included."
    )

    st.markdown("#### Check what you learned")
    answer = st.radio(
        "What's generally the best way to avoid purchase interest "
        "on a credit card?",
        [
            "Pay only the minimum payment",
            "Pay the full statement balance on time, "
            "while meeting grace-period conditions",
            "Wait until interest appears",
        ],
        index=None,
        key="qi_simple_credit_question_v5",
    )

    if answer:
        if answer.startswith("Pay the full statement"):
            st.success(
                "Correct! Paying the full statement balance by the "
                "due date, when the grace period applies, generally "
                "avoids interest on eligible purchases."
            )
        else:
            st.info(
                "Try again. Paying only part of your balance generally "
                "does not preserve the purchase-interest grace period."
            )

    with st.expander(
        "Advanced: Explore credit-card interest and repayment",
        expanded=False,
    ):
        st.write(
            "This detailed calculator explores an existing balance "
            "that is already accumulating interest. It is separate "
            "from the statement-payment example above."
        )
        """Teach and demonstrate repayment using the canonical tested backend model."""
        credit_card_payoff(1000, 24, 100)
        _show_lesson(DEBT)
