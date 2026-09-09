(() => {
  'use strict';
  const scriptURL = document.currentScript.src;
  const questionURL = new URL(document.currentScript.dataset.questions || 'questions.json', scriptURL);
  const prefix = `advanced-review:${document.body.dataset.package}:`;
  const status = document.getElementById('storage-status');
  const forms = [...document.querySelectorAll('[data-question]')];
  let questions = null;
  const storage = (fn) => {
    try { return fn(localStorage); }
    catch { status.textContent = '此瀏覽器無法儲存筆記；目前仍可閱讀與作答，重新整理前請自行保存。'; return null; }
  };
  function showUnit() {
    const units = [...document.querySelectorAll('.unit')];
    const active = units.find(unit => `#${unit.id}` === location.hash) || units[0];
    units.forEach(unit => { unit.hidden = unit !== active; });
    document.querySelectorAll('.unit-link').forEach(link => link.setAttribute('aria-current', String(link.hash === `#${active.id}`)));
    if (location.hash === `#${active.id}`) requestAnimationFrame(() => { active.scrollIntoView({ block: 'start' }); active.focus({ preventScroll: true }); });
  }
  addEventListener('hashchange', showUnit);
  showUnit();
  document.querySelectorAll('[data-case]').forEach(input => {
    input.value = storage(store => store.getItem(prefix + input.id)) || '';
    input.addEventListener('input', () => {
      const saved = storage(store => { store.setItem(prefix + input.id, input.value); return true; });
      input.nextElementSibling.textContent = saved ? '已儲存在此瀏覽器。' : '尚未儲存；請自行保存。';
    });
  });
  function feedback(form, selected) {
    const question = questions[form.dataset.question];
    const result = form.querySelector('.feedback');
    result.replaceChildren();
    const headline = document.createElement('strong');
    headline.textContent = question.options[selected].correct ? '本題答對。請核對其他選項的限制。' : '本題需再核對。比較下列解析後可重新作答。';
    result.append(headline);
    question.options.forEach((option, index) => {
      const text = document.createElement('p');
      text.textContent = `${index + 1}. ${option.correct ? '✓ 正確' : '不適當'}：${option.text} — ${option.rationale}`;
      result.append(text);
    });
  }
  forms.forEach(form => form.addEventListener('submit', event => {
    event.preventDefault();
    const chosen = form.querySelector('input:checked');
    if (!chosen) return;
    if (!questions) { form.querySelector('.feedback').textContent = '解析暫時無法載入，請重新整理再試。'; return; }
    const selected = Number(chosen.value);
    feedback(form, selected);
    storage(store => store.setItem(prefix + form.dataset.question, String(selected)));
  }));
  fetch(questionURL).then(response => {
    if (!response.ok) throw new Error('questions unavailable');
    return response.json();
  }).then(data => {
    questions = data;
    forms.forEach(form => {
      const saved = storage(store => store.getItem(prefix + form.dataset.question));
      if (saved === null || !/^[0-2]$/.test(saved)) return;
      const input = form.querySelector(`input[value="${saved}"]`);
      if (input) { input.checked = true; feedback(form, Number(saved)); }
    });
  }).catch(() => { status.textContent = '知識題解析暫時無法載入；請重新整理再試，教材與報告練習仍可閱讀。'; });
  document.getElementById('reset').addEventListener('click', () => {
    const cleared = storage(store => {
      Object.keys(store).filter(key => key.startsWith(prefix)).forEach(key => store.removeItem(key));
      return true;
    });
    forms.forEach(form => { form.reset(); form.querySelector('.feedback').replaceChildren(); });
    document.querySelectorAll('[data-case]').forEach(input => { input.value = ''; input.nextElementSibling.textContent = ''; });
    status.textContent = cleared ? '已清除此版工作坊的作答；其他課程進度保留。' : '畫面已清空；瀏覽器儲存無法存取，請自行檢查儲存設定。';
  });
  document.getElementById('print').addEventListener('click', () => {
    const details = [...document.querySelectorAll('details')];
    const openState = details.map(item => item.open);
    details.forEach(item => { item.open = true; });
    const restore = () => details.forEach((item, index) => { item.open = openState[index]; });
    addEventListener('afterprint', restore, { once: true });
    window.print();
  });
})();
