# Xinru Lifestyle 工作台

Aesthetic Instagram 內容工作台：選題 → 腳本 → 素材拍攝 → 數據復盤。
每日自動刷新 IG lifestyle 趨勢，附參考爆款連結、storyline 腳本、螢幕文字與表達方式。

## 線上使用
打開 GitHub Pages 連結即可使用（見 repo 設定 → Pages，或 About 區的網址）。

## 每日自動更新
- `Daily Trend Refresh` workflow 每天約 09:00（台北/香港）跑一次：
  抓 slayingsocial 最新趨勢 → 差異更新 → 退潮選題歸檔到歷史區 → commit + push。
- push 自動觸發 `Deploy to GitHub Pages` → 部署到線上連結。
- 也可在 Actions 頁手動點 `Run workflow` 立即刷新。

## 資料與隱私
- 你填的清單 / 表格 / 日曆存在「你自己瀏覽器的 localStorage」，不會上傳伺服器。
- 跨設備搬移：工作台內「資料備份」區的「匯出 / 匯入」按鈕（下載 / 讀回 JSON 檔）。
