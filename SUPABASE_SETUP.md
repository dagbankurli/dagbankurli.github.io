# Supabase Setup for Dagban Kurli

Follow these steps to connect your app to Supabase (free tier).

## 1. Create a Supabase project

1. Go to [supabase.com](https://supabase.com) and sign up (free).
2. Click **New Project**.
3. Name it (e.g. `dagban-kurli`), set a database password, choose a region.
4. Wait for the project to be created.

## 2. Get your API keys

1. In the Supabase dashboard, go to **Project Settings** (gear icon) → **API**.
2. Copy:
   - **Project URL** (e.g. `https://xxxxx.supabase.co`)
   - **anon public** key (under "Project API keys")

## 3. Add keys to your app

**Local development:** Copy `config.example.js` to `config.js` and add your keys. `config.js` is gitignored.

**Deployment (GitHub Pages):** Add these as GitHub Secrets so keys stay out of the repo:

1. Go to your repo on GitHub → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add:
   - Name: `SUPABASE_URL` → Value: `https://your-project.supabase.co`
   - Name: `SUPABASE_ANON_KEY` → Value: your anon key

4. In **Settings** → **Pages**, set **Source** to **GitHub Actions** (not "Deploy from a branch")

## 4. Create the database tables

In Supabase, go to **SQL Editor** and run this SQL:

```sql
-- Profiles table (extends Supabase Auth users with app-specific fields)
CREATE TABLE profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  username TEXT UNIQUE NOT NULL,
  role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('visitor', 'user', 'contributor', 'admin')),
  attribution_name TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security (RLS)
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Users can read their own profile
CREATE POLICY "Users can read own profile" ON profiles
  FOR SELECT USING (auth.uid() = id);

-- Users can insert their own profile (on signup)
CREATE POLICY "Users can insert own profile" ON profiles
  FOR INSERT WITH CHECK (auth.uid() = id);

-- Users can update their own profile (except role - admins do that)
CREATE POLICY "Users can update own profile" ON profiles
  FOR UPDATE USING (auth.uid() = id);

-- Anyone can read profiles (for displaying usernames)
CREATE POLICY "Public profiles readable" ON profiles
  FOR SELECT USING (true);

-- Auto-create profile on signup (handles email confirmation flow)
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, username, role, attribution_name)
  VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'username', split_part(NEW.email, '@', 1)),
    COALESCE(NEW.raw_user_meta_data->>'role', 'user'),
    NEW.raw_user_meta_data->>'attribution_name'
  )
  ON CONFLICT (id) DO UPDATE SET
    username = COALESCE(EXCLUDED.username, profiles.username),
    role = COALESCE(EXCLUDED.role, profiles.role),
    attribution_name = COALESCE(EXCLUDED.attribution_name, profiles.attribution_name),
    updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
```

The trigger creates the profile when a user signs up (including when email confirmation is required).

### Activity log (for admins)

```sql
CREATE TABLE activity_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  type TEXT NOT NULL CHECK (type IN ('approved', 'rejected')),
  kind TEXT NOT NULL CHECK (kind IN ('word', 'phrase', 'idiom')),
  item_id TEXT,
  dagbani TEXT,
  by_username TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE activity_log ENABLE ROW LEVEL SECURITY;

-- Admins can read activity log
CREATE POLICY "Admins can read activity_log" ON activity_log
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin')
  );

-- Admins can insert activity log
CREATE POLICY "Admins can insert activity_log" ON activity_log
  FOR INSERT WITH CHECK (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin')
  );
```

### Allow admins to update user roles (for User Management)

```sql
CREATE POLICY "Admins can update other profiles" ON profiles
  FOR UPDATE USING (
    EXISTS (SELECT 1 FROM profiles p WHERE p.id = auth.uid() AND p.role = 'admin')
  );
```

## 5. Promote your first admin

After creating an account and signing in, run this in the SQL Editor (replace `your@email.com` with your email):

```sql
UPDATE profiles SET role = 'admin' WHERE id = (
  SELECT id FROM auth.users WHERE email = 'your@email.com'
);
```

Or promote by username:

```sql
UPDATE profiles SET role = 'admin' WHERE username = 'your_username';
```

## 6. Configure Auth (optional)

In Supabase: **Authentication** → **Providers** → **Email**:
- Enable "Confirm email" if you want users to verify their email (or disable for simpler flow).
- For a free community app, you may disable confirmation so signup works immediately.

## 7. Run the new tables (User Management + Activity Log)

If you already set up Supabase before, run this **additional SQL** in the SQL Editor:

```sql
-- Activity log table
CREATE TABLE IF NOT EXISTS activity_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  type TEXT NOT NULL CHECK (type IN ('approved', 'rejected')),
  kind TEXT NOT NULL CHECK (kind IN ('word', 'phrase', 'idiom')),
  item_id TEXT,
  dagbani TEXT,
  by_username TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE activity_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Admins can read activity_log" ON activity_log
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin')
  );

CREATE POLICY "Admins can insert activity_log" ON activity_log
  FOR INSERT WITH CHECK (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin')
  );

-- Allow admins to update user roles (User Management)
CREATE POLICY "Admins can update other profiles" ON profiles
  FOR UPDATE USING (
    EXISTS (SELECT 1 FROM profiles p WHERE p.id = auth.uid() AND p.role = 'admin')
  );
```

## 8. Pending submissions (cross-device sync)

Run this SQL so contributor submissions sync to Supabase and admins see them on any device:

```sql
CREATE TABLE IF NOT EXISTS pending_submissions (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('word', 'phrase', 'idiom')),
  user_id UUID REFERENCES auth.users(id),
  content JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE pending_submissions ENABLE ROW LEVEL SECURITY;

-- Contributors can insert their own submissions
CREATE POLICY "Contributors can insert own pending" ON pending_submissions
  FOR INSERT WITH CHECK (
    auth.uid() = user_id AND
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('contributor', 'admin'))
  );

-- Admins can read all pending submissions
CREATE POLICY "Admins can read all pending" ON pending_submissions
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin')
  );

-- Admins can delete (when approving/rejecting)
CREATE POLICY "Admins can delete pending" ON pending_submissions
  FOR DELETE USING (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin')
  );

-- Contributors can read their own (for My Contributions)
CREATE POLICY "Users can read own pending" ON pending_submissions
  FOR SELECT USING (auth.uid() = user_id);
```

**Note:** Large audio/image data URLs may hit row size limits. If inserts fail, the app falls back to localStorage and the contributor can use Export for admin.

## 9. Deploy

Push your changes. The app will use Supabase when `SUPABASE_URL` and `SUPABASE_ANON_KEY` are set. If they are empty, it falls back to localStorage (offline mode).
