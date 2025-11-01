// static/js/budget_chart.js
document.addEventListener("DOMContentLoaded", function () {
  const ctx = document.getElementById("budgetChart");
  if (!ctx) return;

  // 🔹 Flaskから渡されたデータをHTML属性から取得
  const labels = JSON.parse(ctx.dataset.chartLabels || "[]");
  const amounts = JSON.parse(ctx.dataset.chartAmounts || "[]");

  // 🔹 色を自動生成（項目数に応じて）
  const baseColors = ["#2DD4BF", "#FACC15", "#60A5FA", "#F472B6", "#A3E635", "#C084FC", "#FB7185"];
  const colors = labels.map((_, i) => baseColors[i % baseColors.length]);

  const data = {
    labels: labels,
    datasets: [
      {
        label: "旅行予算内訳",
        data: amounts,
        backgroundColor: colors,
        borderColor: "#fff",
        borderWidth: 2,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "bottom",
        labels: {
          color: "#fff",
          font: { family: "Noto Sans JP", size: 13 },
        },
      },
      title: {
        display: true,
        text: "旅行費用の内訳（円）",
        color: "#fff",
        font: { family: "Noto Serif JP", size: 18, weight: "bold" },
      },
    },
  };

  // グラフ描画
  new Chart(ctx, { type: "pie", data, options });

  // 🔹 内訳リストを自動生成（右側）
  const listContainer = document.getElementById("budgetList");
  if (listContainer) {
    listContainer.innerHTML = labels
      .map(
        (label, i) => `
        <li class="flex justify-between items-center border-b border-white/10 pb-1">
          <span class="flex items-center gap-2">
            <span class="w-3 h-3 inline-block rounded-full" style="background:${colors[i]}"></span>
            ${label}
          </span>
          <span class="font-semibold text-teal-300">¥${amounts[i].toLocaleString()}</span>
        </li>
      `
      )
      .join("");
  }
});
