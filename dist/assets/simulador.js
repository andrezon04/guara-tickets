const amount=document.getElementById('amount'),category=document.getElementById('category');
const money=n=>n.toLocaleString('pt-BR',{style:'currency',currency:'BRL'});
function parseAmount(s){let v=s.trim().replace(/R\$\s*/g,'').replace(/\s/g,'');if(v.includes(','))v=v.replace(/\./g,'').replace(',','.');else if(/^\d{1,3}(\.\d{3})+$/.test(v))v=v.replace(/\./g,'');if(!/^\d+(\.\d{0,2})?$/.test(v))return NaN;return Number(v)}
function rateFor(cents,type){return type==='other'?15:cents<=100000?17:cents<=200000?16:15;}
function quote(cents,type){const rate=rateFor(cents,type),fee=Math.round(cents*rate/100);return {gross:cents,fee,net:cents-fee,rate};}
function calculate(){
 const value=parseAmount(amount.value),valid=Number.isFinite(value)&&value>=0.01&&value<=10000000;
 amount.setAttribute('aria-invalid',String(!valid));
 const link=document.getElementById('sim-link');
 if(!valid){document.getElementById('net').textContent='—';document.getElementById('rate').textContent='';document.getElementById('fee').textContent='Informe um valor válido, maior que zero.';link.href='https://wa.me/5511940240988';return;}
 const q=quote(Math.round(value*100),category.value);
 document.getElementById('net').textContent=money(q.net/100);
 document.getElementById('rate').textContent='Taxa de '+q.rate+'%';
 document.getElementById('fee').textContent='Taxa estimada: '+money(q.fee/100)+' sobre '+money(q.gross/100)+'.';
 const type=category.value==='other'?'outros benefícios':'alimentação/refeição';
 link.href='https://wa.me/5511940240988?text='+encodeURIComponent('Olá! Simulei o valor total de '+money(q.gross/100)+' em cartões de '+type+', com taxa estimada de '+q.rate+'% e recebimento de '+money(q.net/100)+'. Gostaria de confirmar as condições e agendar.');
}
amount.addEventListener('input',calculate);category.addEventListener('change',calculate);amount.addEventListener('blur',()=>{const v=parseAmount(amount.value);if(Number.isFinite(v)&&v>0)amount.value=v.toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2});calculate()});calculate();
