# Why dagbankurli.github.io can still look “broken”

## What went wrong before (and what fixed it locally)

If you see **huge blocks of JavaScript as normal text** at the bottom of the page, the HTML on GitHub is **missing** an opening `<script>` tag right after the small Supabase block.

**Correct structure (must look like this in the file GitHub serves):**

```html
    </script>
    <script>
        /**
         * Dagban Kurli - Dagbani-English Community Lexicon
```

If your file has this instead (BAD — browser shows code as text):

```html
    </script>
        /**
         * Dagban Kurli ...
```

Then GitHub Pages is still deploying an **old** `index.html`, or you pushed to a **different repo** than the one Pages uses.

---

## 30-second check (no Git needed)

1. Open your repo on GitHub in the browser (the one used for Pages — usually **`dagbankurli/dagbankurli.github.io`**).
2. Open **`index.html`** → click **Raw**.
3. Press **Ctrl+F** and search for: `Dagban Kurli - Dagbani-English`

You must see **immediately above** that line:

- `</script>`  
- then **`<script>`** on the next line  

If `<script>` is missing → **that** is why the site is “fucked”. Fix = replace `index.html` on GitHub with your fixed local copy and commit.

---

## Common mix-ups

| Problem | What to do |
|--------|------------|
| You push to **`mwumpini/...`** but the site is **`dagbankurli.github.io`** | The org site only updates from the **`dagbankurli`** org repo (e.g. `dagbankurli/dagbankurli.github.io`). Push there or fork/PR into that repo. |
| Pages uses **`gh-pages`** branch but you only pushed **`main`** | GitHub → **Settings → Pages** → see which **branch** is selected. Push your fix to **that** branch. |
| **0 words** after the UI works | Commit **`dictionary_import.json`** to the **same** repo root (or load data from Supabase). Open `https://dagbankurli.github.io/dictionary_import.json` — should not be 404. |

---

## If you want to skip GitHub Pages stress

- **Netlify Drop**: drag your project folder at [app.netlify.com/drop](https://app.netlify.com/drop) — free HTTPS, no branch confusion.
- **Cloudflare Pages** — connect repo or upload.

Your **local** folder on the desktop is the source of truth; the website is only as good as whatever file actually landed on the server.
