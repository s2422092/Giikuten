    // 二重送信防止スクリプト
    const form = document.getElementById("registration-form");
    const button = document.getElementById("submit-btn");

    form.addEventListener("submit", () => {
      button.disabled = true;           // ボタンを無効化
      button.textContent = "送信中..."; // ボタンの文字を変更（任意）
    });