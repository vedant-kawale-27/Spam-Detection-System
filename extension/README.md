# Spam Detection Inbox Scanner (Browser Extension)

Chrome/Firefox extension (Manifest V3) that scans visible Gmail and Outlook web
messages and shows an inline spam/smishing/offensive badge, using the existing
Spam Detection System classification API as its backend. Implements issue #187.

## How it works

- Content scripts (`src/content/gmail.js`, `src/content/outlook.js`) find
  message rows in the inbox list, extract the subject + preview text, and ask
  the background service worker to classify it.
- The background service worker (`src/background.js`) holds the API base URL
  and an account token (set via the options page) and calls the existing
  `POST /predict` endpoint on the Node backend.
- Results are cached **in memory only**, per page load, keyed by the
  provider's own message/thread id. Reloading the tab clears the cache.
- Each badge has a rescan (↻) and dismiss (✕) control.

## Install (development / unpacked)

**Chrome / Edge / Brave:**
1. Go to `chrome://extensions`, enable "Developer mode".
2. Click "Load unpacked" and select the `extension/` folder.

**Firefox:**
1. Go to `about:debugging#/runtime/this-firefox`.
2. Click "Load Temporary Add-on…" and select `extension/manifest.json`.
   (Temporary add-ons are removed when Firefox restarts — see
   [web-ext](https://extensionworkshop.com/documentation/develop/web-ext-command-reference/)
   for a persistent dev workflow.)

## Configure

1. Click the extension icon → "Open settings".
2. Set the API base URL (defaults to `http://localhost:3000`, the Node
   gateway used by the rest of this project).
3. Log into the Spam Detection web app. If it's running locally at
   `localhost:5173` (the Vite dev default), a content script
   (`src/content/webapp-bridge.js`) picks up your login token from
   `localStorage` automatically within a few seconds — no manual step needed.
   Otherwise, open devtools on the web app's page, run
   `localStorage.getItem('token')`, and paste the result into "Account token".

If you deploy the frontend or backend somewhere other than `localhost`, add
that origin to `host_permissions`/the relevant `content_scripts.matches`
entry in `manifest.json` before loading the extension (or use
`chrome.permissions.request` — out of scope for this first pass).

## Privacy

- Only the subject + a short preview snippet (truncated to 500 characters) is
  sent to the classification API per message — never the full message body.
- Classification results are kept in memory only, scoped to the current page
  load. Nothing is written to `chrome.storage` or disk except your API base
  URL and account token (used to authenticate to your own backend).
- Dismissing a flag only affects local in-memory state; it does not call the
  backend.

## Known limitations

- Gmail/Outlook DOM selectors (`src/content/gmail.js`, `src/content/outlook.js`)
  are based on current unofficial markup and **will break** if Google/Microsoft
  change their markup. If badges stop appearing, inspect a message row in
  devtools and update the selectors at the top of the relevant file.
- Confirmed loading unpacked in a real Chrome profile with no manifest/
  background errors (service worker starts cleanly). Scanning behavior
  against a live, logged-in Gmail/Outlook inbox still needs end-to-end
  verification by whoever has that session available.

## Publishing (optional follow-up)

This PR ships the extension as source only — it is not published to any
store. Getting a one-click "Add to Chrome"/"Add to Firefox" install requires
the project maintainer to submit it under their own developer account. Draft
listing copy, a privacy policy, permission justifications, and icons are in
`store-listing/` and `icons/` to make that easier later; real screenshots
still need to be captured from a live browser session (see
`store-listing/screenshots/README.md`).

## Tests

Pure logic (caching, text truncation, badge mapping) is covered by
`node --test`:

```sh
cd extension
npm test
```

DOM scanning and the background/options/popup UI require a real browser and
are not covered by automated tests in this PR.
