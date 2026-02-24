# Deploy Dagban Kurli to GitHub Pages

Follow these steps to put your dictionary online so others can preview it.

## 1. Create a new repository on GitHub

1. Go to [github.com](https://github.com) and sign in.
2. Click the **+** (top right) → **New repository**.
3. Name it (e.g. `dagban-kurli`).
4. Leave it **Public**, do **not** add a README.
5. Click **Create repository**.

## 2. Push your project from your computer

Open **Terminal** or **PowerShell** in your project folder and run:

```bash
cd "C:\Users\maman\OneDrive\Desktop\Dagban Kurli"

# Initialize git
git init

# Add all files
git add .
git status   # Optional: check what will be added

# First commit
git commit -m "Initial commit: Dagban Kurli dictionary"

# Add your GitHub repo (replace YOUR_USERNAME and REPO_NAME with yours)
git remote add origin https://github.com/YOUR_USERNAME/dagban-kurli.git

# Push to GitHub
git branch -M main
git push -u origin main
```

When prompted for credentials, use your GitHub username and a [Personal Access Token](https://github.com/settings/tokens) (not your password).

## 3. Turn on GitHub Pages

1. On your repo page, go to **Settings** → **Pages**.
2. Under **Source**, choose **Deploy from a branch**.
3. Branch: **main**, Folder: **/ (root)**.
4. Click **Save**.

## 4. Your site URL

After a minute or two, your site will be live at:

```
https://YOUR_USERNAME.github.io/dagban-kurli/
```

Replace `YOUR_USERNAME` and `dagban-kurli` with your actual GitHub username and repo name.

---

## Files needed for the site to work

Make sure these are included (they should be by default):

- `index.html` – main app
- `dictionary_import.json` – dictionary content (auto-loads on first visit)
- `images/` folder – king photos, boy/girl images, etc.

## Optional: Supabase auth (cloud sign-in)

For real user accounts (sign up, sign in, roles), see **SUPABASE_SETUP.md**. Add your Supabase URL and anon key to `index.html`. Without them, the app uses localStorage (works offline, no cloud).

## Updating the live site

After making changes locally:

```bash
git add .
git commit -m "Describe your changes"
git push
```

GitHub Pages will redeploy automatically (usually within 1–2 minutes).
