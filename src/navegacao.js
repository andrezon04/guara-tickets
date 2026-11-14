// Menu do celular e botão fixo do WhatsApp.
(() => {
  const menu = document.querySelector('.mobile-menu');
  if (menu) {
    const close = () => { menu.open = false; };
    menu.querySelectorAll('a').forEach(a => a.addEventListener('click', close));
    document.addEventListener('click', e => { if (menu.open && !menu.contains(e.target)) close(); });
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && menu.open) { close(); menu.querySelector('summary').focus(); }
    });
  }

  // O botão fixo fica escondido enquanto o topo da página está visível, para não cobrir o conteúdo.
  const bar = document.querySelector('.mobile-contact');
  const top = document.querySelector('.hero, .page-hero');
  if (bar && top && 'IntersectionObserver' in window) {
    new IntersectionObserver(([entry]) => bar.classList.toggle('is-hidden', entry.isIntersecting)).observe(top);
  }
})();
