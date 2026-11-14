// Simulador do tíquete: única fonte das faixas de taxa usadas no site.
(() => {
  const WA = 'https://wa.me/5511940240988';
  const $ = id => document.getElementById(id);
  const amount = $('amount');
  if (!amount) return;

  const radios = [...document.querySelectorAll('input[name="category"]')];
  const tiers = $('tiers');
  // Faixas de alimentação/refeição: limite superior em centavos (inclusive) e taxa em %.
  const TIERS = [{ max: 100000, rate: 17 }, { max: 200000, rate: 16 }, { max: Infinity, rate: 15 }];
  const OTHER_RATE = 15;

  const money = cents => (cents / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  const category = () => radios.find(r => r.checked).value;

  // Aceita "2500", "2.500", "2.500,00", "2500,5" e "R$ 2.500,00".
  function parseAmount(text) {
    let v = text.trim().replace(/R\$\s*/g, '').replace(/\s/g, '');
    if (v.includes(',')) v = v.replace(/\./g, '').replace(',', '.');
    else if (/^\d{1,3}(\.\d{3})+$/.test(v)) v = v.replace(/\./g, '');
    return /^\d+(\.\d{0,2})?$/.test(v) ? Number(v) : NaN;
  }

  const tierIndex = cents => TIERS.findIndex(t => cents <= t.max);
  const rateFor = (cents, type) => (type === 'other' ? OTHER_RATE : TIERS[tierIndex(cents)].rate);

  function quote(cents, type) {
    const rate = rateFor(cents, type), fee = Math.round(cents * rate / 100);
    return { gross: cents, fee, net: cents - fee, rate };
  }

  // Mostra quanto falta para a próxima faixa: é a promessa "junto rende mais" em números.
  function hintFor(cents, type) {
    if (type === 'other') return '';
    const i = tierIndex(cents);
    if (i === TIERS.length - 1) return 'Você já está na menor taxa.';
    return 'Com mais ' + money(TIERS[i].max + 1 - cents) + ' nos cartões, a taxa cai para ' + TIERS[i + 1].rate + '%.';
  }

  function markTier(rate) {
    tiers.querySelectorAll('li').forEach(li => {
      const on = Number(li.dataset.tier) === rate;
      li.classList.toggle('is-on', on);
      if (on) li.setAttribute('aria-current', 'true'); else li.removeAttribute('aria-current');
    });
  }

  function calculate() {
    const type = category(), value = parseAmount(amount.value);
    const valid = Number.isFinite(value) && value >= 0.01 && value <= 10000000;
    amount.setAttribute('aria-invalid', String(!valid));
    tiers.hidden = type === 'other';
    if (!valid) {
      $('net').textContent = '—';
      $('fee').textContent = 'Informe um valor maior que zero, por exemplo 1.500,00.';
      $('hint').textContent = '';
      markTier(0);
      $('sim-link').href = WA;
      return;
    }
    const q = quote(Math.round(value * 100), type);
    $('net').textContent = money(q.net);
    $('fee').textContent = 'Taxa de ' + q.rate + '%: ' + money(q.fee) + ' sobre ' + money(q.gross) + '.';
    $('hint').textContent = hintFor(q.gross, type);
    markTier(type === 'other' ? 0 : q.rate);
    const label = type === 'other' ? 'outros benefícios' : 'alimentação/refeição';
    $('sim-link').href = WA + '?text=' + encodeURIComponent('Olá! Simulei o valor total de ' + money(q.gross) + ' em cartões de ' + label + ', com taxa estimada de ' + q.rate + '% e recebimento de ' + money(q.net) + '. Gostaria de confirmar as condições e agendar.');
  }

  amount.addEventListener('input', calculate);
  radios.forEach(r => r.addEventListener('change', calculate));
  amount.addEventListener('blur', () => {
    const v = parseAmount(amount.value);
    if (Number.isFinite(v) && v > 0) amount.value = v.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    calculate();
  });
  calculate();
})();
