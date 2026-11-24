/**
 * 確認シートに、サイトからの質問を毎日追加する Google Apps Script。
 * 使い方: スプレッドシートの「拡張機能 → Apps Script」に貼り付け、SITE_URL を自分のサイトに変更し、
 * 「トリガー」で addReviewRows を「日付ベース・毎日 午前6〜7時」に設定します。
 */
const SITE_URL = "https://fuyumi.pages.dev"; // ← 自分のサイトのURL

function addReviewRows() {
  const sheet = SpreadsheetApp.getActive().getSheetByName("確認");
  const res = UrlFetchApp.fetch(SITE_URL + "/data/review.json", { muteHttpExceptions: true });
  if (res.getResponseCode() !== 200) return;
  const items = JSON.parse(res.getContentText());
  const existing = new Set(sheet.getDataRange().getValues().slice(1).map((r) => r[0] + "|" + r[1]));
  const rows = items.filter((i) => !existing.has(i["種類"] + "|" + i["対象"]))
                    .map((i) => [i["種類"], i["対象"], i["内容"], ""]);
  if (rows.length) sheet.getRange(sheet.getLastRow() + 1, 1, rows.length, 4).setValues(rows);
}
