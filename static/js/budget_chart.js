// budget_chart.js

document.addEventListener("DOMContentLoaded", function () {
  const ctx = document.getElementById("budgetChart");

  if (!ctx) return; // HTML側にcanvasがない場合は終了

  // データ設定（HTMLの費用表と一致）
  const labels = ["交通費", "宿泊費", "食費", "拝観料", "お土産・雑費"];
  const amounts = [15000, 30000, 12000, 3000, 5000];
  const colors = ["#2DD4BF", "#FACC15", "#60A5FA", "#F472B6", "#A3E635"];

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

  // オプション設定（既存＋サイズ最適化）
  const options = {
    responsive: true,
    maintainAspectRatio: false, // 縦横比を固定しない（サイズ調整可能に）
    plugins: {
      legend: {
        position: "bottom",
        labels: {
          font: {
            family: "Noto Sans JP",
            size: 13,
          },
        },
      },
      title: {
        display: true,
        text: "旅行費用の内訳（円）",
        font: {
          family: "Noto Serif JP",
          size: 18,
          weight: "bold",
        },
      },
    },
  };

  // 円グラフ描画（サイズ半分程度）
  const chart = new Chart(ctx, {
    type: "pie",
    data: data,
    options: options,
  });

  // ---------- 内訳リスト（右側に表示） ----------
  const listContainer = document.getElementById("budgetList");
  if (listContainer) {
    listContainer.innerHTML = labels
      .map(
        (label, i) => `
        <li class="flex justify-between items-center border-b pb-1">
          <span class="flex items-center gap-2">
            <span class="w-3 h-3 inline-block rounded-full" style="background:${colors[i]}"></span>
            ${label}
          </span>
          <span class="font-semibold text-gray-800">¥${amounts[i].toLocaleString()}</span>
        </li>
      `
      )
      .join("");
  }
});
