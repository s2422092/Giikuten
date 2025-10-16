(() => {
  const regionSel = document.getElementById("region-select");
  const prefSel   = document.getElementById("prefecture-select");
  const citySel   = document.getElementById("city-select");

  // フォールバックの静的地域（DB/APIが空でも壊れない）
  const FALLBACK_REGIONS = ["北海道","東北","関東","中部","近畿","中国","四国","九州・沖縄"];

  let prefReqId = 0;
  let cityReqId = 0;

  const sleep = (ms) => new Promise(r => setTimeout(r, ms));
  async function fetchJSON(url, retries = 2) {
    for (let i=0; i<=retries; i++) {
      try {
        const res = await fetch(url, { credentials: "same-origin" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
      } catch (e) {
        if (i === retries) throw e;
        await sleep(200 * (i+1));
      }
    }
  }

  function resetSelect(sel, placeholder, disable=true) {
    sel.innerHTML = "";
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = placeholder;
    sel.appendChild(opt);
    sel.disabled = disable;
  }

  function fillOptions(sel, items, includeEmptyLabel) {
    sel.innerHTML = "";
    if (includeEmptyLabel) {
      const empty = document.createElement("option");
      empty.value = "";
      empty.textContent = includeEmptyLabel;
      sel.appendChild(empty);
    }
    for (const v of items) {
      const o = document.createElement("option");
      o.value = v;
      o.textContent = v;
      sel.appendChild(o);
    }
    sel.disabled = false;
  }

  // 地域の初期ロード
  async function loadRegions() {
    resetSelect(regionSel, "読込中...", true);
    try {
      const data = await fetchJSON("/plan/api/region");
      if (data.ok && data.items.length) {
        fillOptions(regionSel, data.items, "選択してください");
      } else {
        fillOptions(regionSel, FALLBACK_REGIONS, "選択してください");
      }
    } catch {
      fillOptions(regionSel, FALLBACK_REGIONS, "選択してください");
    }
    resetSelect(prefSel, "自動提案に任せる", false);
    resetSelect(citySel, "自動提案に任せる", false);
  }

  // 地域変更時：都道府県ロード
  async function onRegionChange() {
    const region = regionSel.value;
    resetSelect(prefSel, "自動提案に任せる", false);
    resetSelect(citySel, "自動提案に任せる", false);
    if (!region) return;

    const myReq = ++prefReqId;
    prefSel.disabled = true;
    prefSel.options[0].textContent = "読込中...";

    try {
      const data = await fetchJSON(`/plan/api/prefecture?region=${encodeURIComponent(region)}`);
      if (myReq !== prefReqId) return;
      if (data.ok && data.items.length) {
        fillOptions(prefSel, data.items, "自動提案に任せる");
      } else {
        resetSelect(prefSel, "自動提案に任せる", false);
      }
    } catch {
      resetSelect(prefSel, "自動提案に任せる", false);
    }
  }

  // 都道府県変更時：市区町村ロード
  async function onPrefChange() {
    const pref = prefSel.value;
    resetSelect(citySel, "自動提案に任せる", false);
    if (!pref) return;

    const myReq = ++cityReqId;
    citySel.disabled = true;
    citySel.options[0].textContent = "読込中...";

    try {
      const data = await fetchJSON(`/plan/api/area?prefecture=${encodeURIComponent(pref)}`);
      if (myReq !== cityReqId) return;
      if (data.ok && data.items.length) {
        fillOptions(citySel, data.items, "自動提案に任せる");
      } else {
        resetSelect(citySel, "自動提案に任せる", false);
      }
    } catch {
      resetSelect(citySel, "自動提案に任せる", false);
    }
  }

  regionSel.addEventListener("change", onRegionChange);
  prefSel.addEventListener("change", onPrefChange);

  // 初期実行
  loadRegions();
})();