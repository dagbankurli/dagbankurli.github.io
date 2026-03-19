# Step-by-step: Git and GitHub Pages for Dagban Kurli

## 1. Open a terminal in your project folder

- In VS Code/Cursor: **Terminal → New Terminal** (or `` Ctrl+` ``).
- Or open **PowerShell** or **Command Prompt**, then:
  ```bash
  cd "C:\Users\maman\OneDrive\Desktop\Dagban Kurli"
  ```

---

## 2. Check if Git is set up

```bash
git --version
```

If you see a version number, Git is installed. If not, install from: https://git-scm.com/download/win

---

## 3. (First time only) Set your name and email for Git

```bash
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"
```

Use the same email as your GitHub account.

---

## 4. See what Git thinks has changed

```bash
git status
```

You’ll see modified/untracked files (e.g. `index.html`).

---

## 5. Stage all files you want to publish

```bash
git add .
```

Or only specific files:

```bash
git add index.html
git add dictionary_import.json
```

---

## 6. Commit with a short message

```bash
git commit -m "Fix for GitHub Pages and base path"
```

If Git says “nothing to commit”, everything is already committed; you can skip to step 8.

---

## 7. Create a repo on GitHub (if you don’t have one yet)

1. Go to **https://github.com** and sign in.
2. Click the **+** (top right) → **New repository**.
3. **Repository name:** e.g. `dagbankurli.github.io` (for a user site) or `Dagban-Kurli` (for a project site).
4. Choose **Public**.
5. **Do not** add a README, .gitignore, or license (you already have files).
6. Click **Create repository**.

---

## 8. Connect your folder to GitHub (first time only)

GitHub will show a “Quick setup” with a URL. Use your actual repo URL in the commands below.

**If this is the first time in this folder (no remote):**

```bash
git remote add origin https://github.com/dagbankurli/dagbankurli.github.io.git
```

Replace `dagbankurli/dagbankurli.github.io` with your **username/repo-name** if different.

**If you already added `origin` and want to fix it:**

```bash
git remote set-url origin https://github.com/dagbankurli/dagbankurli.github.io.git
```

**Check it:**

```bash
git remote -v
```

You should see `origin` with your GitHub URL.

---

## 9. Push your code to GitHub

**If your branch is `main`:**

```bash
git push -u origin main
```

**If your branch is `master`:**

```bash
git push -u origin master
```

**If Git says the branch doesn’t exist on GitHub yet:**

```bash
git branch -M main
git push -u origin main
```

Enter your GitHub username and password when asked. (Use a **Personal Access Token** instead of password if you have 2FA: GitHub → Settings → Developer settings → Personal access tokens.)

---

## 10. Turn on GitHub Pages

1. On GitHub, open your repo (e.g. `https://github.com/dagbankurli/dagbankurli.github.io`).
2. Click **Settings**.
3. In the left sidebar, click **Pages** (under “Code and automation” or “Build and deployment”).
4. Under **Source**, choose **Deploy from a branch**.
5. Under **Branch**:
   - Branch: **main** (or **master** if that’s what you use).
   - Folder: **/ (root)**.
6. Click **Save**.

---

## 11. Wait and open your site

- GitHub will build the site (usually 1–2 minutes).
- Your site will be at:
  - **User/org site:** `https://dagbankurli.github.io`
  - **Project site:** `https://dagbankurli.github.io/RepoName` (e.g. `https://dagbankurli.github.io/Dagban-Kurli`)

Refresh the page; the app should load with the correct base path.

---

## 12. Later: make changes and update the live site

Whenever you change files and want to update GitHub (and GitHub Pages):

```bash
git add .
git commit -m "Short description of what you changed"
git push
```

No need to change GitHub Pages settings again; the site updates from the latest push.

---

## Checklist

- [ ] Terminal opened in `Dagban Kurli` folder  
- [ ] `git status` shows your files  
- [ ] `git add .` and `git commit -m "..."`  
- [ ] Repo created on GitHub (if new)  
- [ ] `git remote add origin ...` (first time only)  
- [ ] `git push -u origin main`  
- [ ] Settings → Pages → Deploy from branch → main → / (root) → Save  
- [ ] Open `https://yourusername.github.io` or `https://yourusername.github.io/RepoName`

---

## If you use a project repo (e.g. `Dagban-Kurli`)

- Keep `index.html` and `dictionary_import.json` (if you have one) in the **root** of the repo.
- The site URL will be: `https://dagbankurli.github.io/Dagban-Kurli/` (use the exact repo name).
- The app code already uses the correct base path for this.

## Troubleshooting

- **404 or blank page:** Wait 2–3 minutes after enabling Pages; clear cache or try an incognito window.
- **Push rejected:** Run `git pull origin main --rebase`, then `git push` again.
- **Wrong branch:** In Pages settings, pick the branch you actually push to (e.g. `main`).
