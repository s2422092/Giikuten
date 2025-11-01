document.addEventListener('DOMContentLoaded', () => {
  // 現在ページタブはリンクを無効化
  document.querySelectorAll('.tab-link.active').forEach(tab => {
    tab.addEventListener('click', e => {
      e.preventDefault();  // クリックによるページ遷移を阻止
    });
    tab.style.cursor = 'default';  // カーソルも変える
  });
});
