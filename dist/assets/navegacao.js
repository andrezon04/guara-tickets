document.querySelectorAll('.mobile-menu a').forEach(a=>a.addEventListener('click',()=>{a.closest('details').open=false}));
