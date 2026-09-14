#!/usr/bin/env python3
"""
xinru lifestyle · 每日趨勢自動刷新腳本 (v2 — GitHub Actions 友善)
- 讀取 xinru_trends_data.json (curated / auto / history 三段)
- 拉取 slayingsocial.com 最新 IG Reels 趨勢 + 範例連結
- 差異更新：保留仍熱門的、加入新出現的、退潮的歸檔到 history
- 重新生成 index.html 的 TRENDS + HISTORY 常數（含 typ / ex 欄位）
- 純 stdlib，無外部依賴；相對路徑，可在 Actions 工作目錄直接跑
用法: python3 refresh_trends.py
環境變數: DATA_JSON / HTML_PATH (預設相對路徑)
"""
import json, re, os, ssl, datetime, urllib.request, html as _html
from collections import OrderedDict

DATA_JSON = os.environ.get("DATA_JSON", "xinru_trends_data.json")
HTML_PATH  = os.environ.get("HTML_PATH", "index.html")
SOURCES = ["https://slayingsocial.com/instagram-reels-trends/"]
HISTORY_CAP = 200
AUTO_CAP = 20

PILLAR_KW = {
    "travel": ["travel","view","nature","place","earth","walk","trip","scenery","europe","mountain","beach","sea","city"],
    "food": ["coffee","matcha","food","cafe","drink","eat","recipe","bake"],
    "wellness": ["self care","self-care","cup","meditat","mental","calm","health","love myself","mean to myself","journal","slow","noise"],
    "thoughts": ["realize","important that you","ashamed","impress","forgot","diary","life","memory","mind","maturing","realiz","feel","think","know","realize"],
}

def frame(title):
    t = title.lower()
    pillar = "all"
    for p, kws in PILLAR_KW.items():
        if any(k in t for k in kws):
            pillar = p; break
    if "important that you" in t or "realize" in t or "impress" in t:
        emp = "成長期的迷茫與自我和解——人人都在經歷"; alt = "給同齡人一句「你會沒事的」的安慰"
    elif "memory" in t or "forgot" in t or "diary" in t:
        emp = "對日常與回憶的感恩，療癒感"; alt = "提醒觀眾什麼才是真正重要的"
    elif "coffee" in t or "matcha" in t or "cafe" in t or "eat" in t:
        emp = "晨間儀式的安定感"; alt = "推薦好去處/好物（利他收藏）"
    elif any(k in t for k in ["view","nature","earth","travel","beach","sea","city"]):
        emp = "自然/旅途之美的敬畏"; alt = "標記地點＋路線（利他攻略）"
    elif any(k in t for k in ["cup","self","calm","slow","journal","noise"]):
        emp = "自我照顧的微小儀式感"; alt = "給觀眾可抄作業的清單"
    else:
        emp = "日常共鳴情緒——讓人覺得「這在說我」"; alt = "可收藏/轉發的價值點"
    return pillar, emp, alt

def norm(t):
    """normalize title for comparison (strip trailing 'Trend', '*', collapse spaces)"""
    t = (t or "").lower().strip().strip('*').strip()
    t = re.sub(r'\s+trend\s*$', '', t)
    t = re.sub(r'\s+', ' ', t).strip().strip('"').strip()
    return t

def fetch(url):
    ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"})
    with urllib.request.urlopen(req, timeout=40, context=ctx) as r:
        return r.read().decode("utf-8", "ignore")

def _clean(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    s = _html.unescape(s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

def clean_url(u):
    u = u.replace('&amp;', '&')
    u = re.sub(r'[?&]igsh=[^&\s]*', '', u)
    u = u.rstrip('?&')
    return u

def extract_trends(html_text):
    """從 slayingsocial 提取 [{title, ex}]：每個 trend 在 <strong>NAME | <a href=URL> Example</a>:</strong>"""
    cur = re.split(r'Past Instagram', html_text, maxsplit=1)[0]
    blocks = re.findall(r'<strong[^>]*>(.*?)</strong>', cur, re.DOTALL)
    out = []
    for b in blocks:
        m_ex = re.search(r'<a[^>]*href="([^"]+)"[^>]*>\s*[\&\xa0]*\s*[Ee]xample', b)
        if not m_ex: continue
        ex = clean_url(m_ex.group(1).strip())
        if 'instagram.com' not in ex: continue
        name_part = re.split(r'\|', b, maxsplit=1)[0]
        name = _clean(re.sub(r'<[^>]+>', '', name_part))
        if len(name) < 3 or name.lower() in ('current', 'past') or 'Trend Alerts' in name: continue
        out.append({"title": name, "ex": ex})
    seen = set(); res = []
    for x in out:
        k = norm(x["title"])
        if k and k not in seen:
            seen.add(k); res.append(x)
    return res

def js_str(s):
    """HTML-escape (anti-XSS) then JS-escape, then prevent </script> breakout."""
    s = s or ""
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    s = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", " ")
    s = s.replace("</", "<\\/")
    return s

def entry(t):
    cur = "true" if t.get("cur") else "false"
    return ('{cur:' + cur +
            ',t:"' + js_str(t.get('t', '')) +
            '",f:"' + js_str(t.get('f', 'rise')) +
            '",p:"' + js_str(t.get('p', 'all')) +
            '",typ:"' + js_str(t.get('typ', 'reel')) +
            '",fmt:"' + js_str(t.get('fmt', 'Reel')) +
            '",emp:"' + js_str(t.get('emp', '')) +
            '",alt:"' + js_str(t.get('alt', '')) +
            '",hook:"' + js_str(t.get('hook', '')) +
            '",why:"' + js_str(t.get('why', '')) +
            '",ex:"' + js_str(t.get('ex', '')) + '"}')

def trends_block(trends):
    if not trends: return "const TRENDS = [];"
    return "const TRENDS = [\n  " + ",\n  ".join(entry(t) for t in trends) + "\n];"

def history_block(history):
    if not history: return "var HISTORY=[];"
    parts = []
    for g in history:
        items = ", ".join(entry(t) for t in g.get("items", []))
        parts.append('{d:"' + js_str(g.get("d", "")) + '", items:[' + items + ']}')
    return "var HISTORY=[\n  " + ",\n  ".join(parts) + "\n];"

def main():
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    today = datetime.date.today().isoformat()
    print(f"[{now_str}] xinru 趨勢刷新 v2 開始")

    try:
        with open(DATA_JSON, encoding="utf-8") as f: data = json.load(f)
    except Exception as e:
        print("✗ 讀取 JSON 失敗:", e); data = {}
    curated = data.get("curated", [])
    auto = data.get("auto", [])
    history = data.get("history", [])

    fetched = []
    for url in SOURCES:
        try:
            h = fetch(url)
            fetched = extract_trends(h)
            print(f"  ✓ 抓取 {url} -> {len(fetched)} 條")
        except Exception as e:
            print(f"  ✗ 抓取失敗 {url}: {e}")
    if not fetched:
        print("未抓到趨勢，保留現有資料不動。"); return

    fetched_norms = {norm(x["title"]) for x in fetched}
    # 退潮：現有 auto 不在 fetched 的
    retired = [t for t in auto if norm(t.get("t", "")) not in fetched_norms]
    keep    = [t for t in auto if norm(t.get("t", "")) in fetched_norms]
    # 新出現：fetched 不在 curated 也不在 auto 的
    known_norms = {norm(t.get("t", "")) for t in curated + auto}
    new_adds = []
    for x in fetched:
        k = norm(x["title"])
        if k in known_norms: continue
        pillar, emp, alt = frame(x["title"])
        new_adds.append({
            "cur": False, "t": x["title"], "f": "rise", "p": pillar, "typ": "reel",
            "fmt": "Reel (新發現)", "emp": emp, "alt": alt, "hook": x["title"],
            "why": "trending now", "ex": x["ex"]
        })
        known_norms.add(k)
    new_auto = keep + new_adds
    new_auto = new_auto[-AUTO_CAP:]
    print(f"  保留 {len(keep)} · 新增 {len(new_adds)} · 退潮歸檔 {len(retired)}")

    # 歸檔退潮到 history（今日群組）
    if retired:
        grp = None
        for g in history:
            if g.get("d") == today: grp = g; break
        if not grp:
            grp = {"d": today, "items": []}; history.append(grp)
        grp["items"].extend(retired)
    # trim history to last HISTORY_CAP items
    flat = []
    for g in history:
        for it in g.get("items", []): flat.append((g.get("d", ""), it))
    if len(flat) > HISTORY_CAP:
        flat = flat[-HISTORY_CAP:]
        gg = OrderedDict()
        for d, it in flat: gg.setdefault(d, []).append(it)
        history = [{"d": d, "items": its} for d, its in gg.items()]

    trends = curated + new_auto
    data2 = {
        "last_refreshed": now_str, "account": "@xinruzz_",
        "positioning": "共情 + 利他 + aesthetic lifestyle",
        "pillars": ["travel", "thoughts", "food", "wellness"],
        "curated": curated, "auto": new_auto, "history": history
    }
    with open(DATA_JSON, "w", encoding="utf-8") as f:
        json.dump(data2, f, ensure_ascii=False, indent=2)
    print(f"  ✓ 寫入 {DATA_JSON} (精選 {len(curated)} + 自動 {len(new_auto)} + 歷史 {sum(len(g.get('items',[])) for g in history)})")

    # 重新生成 HTML TRENDS + HISTORY
    try:
        with open(HTML_PATH, encoding="utf-8") as f: h = f.read()
        tb = trends_block(trends); hb = history_block(history)
        h2 = re.sub(r'const TRENDS\s*=\s*\[[\s\S]*?\];', lambda m: tb, h, count=1)
        h2 = re.sub(r'var HISTORY\s*=\s*\[[\s\S]*?\];', lambda m: hb, h2, count=1)
        m = re.search(r'<span id="lastUpd">[^<]*</span>', h2)
        if m: h2 = re.sub(r'<span id="lastUpd">[^<]*</span>', '<span id="lastUpd">' + now_str + '</span>', h2)
        with open(HTML_PATH, "w", encoding="utf-8") as f: f.write(h2)
        print(f"  ✓ 更新 {HTML_PATH} (TRENDS={len(trends)}, HISTORY groups={len(history)})")
    except Exception as e:
        print(f"  ✗ 更新 HTML 失敗: {e}")
    print("刷新完成。")

if __name__ == "__main__":
    main()
