-- =============================================================================
-- Dagban Kurli – Supabase schema (run once in SQL Editor)
-- =============================================================================

-- 1. Profiles table
CREATE TABLE IF NOT EXISTS profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  username TEXT UNIQUE NOT NULL,
  role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('visitor', 'user', 'contributor', 'admin')),
  attribution_name TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can read own profile" ON profiles;
CREATE POLICY "Users can read own profile" ON profiles
  FOR SELECT USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can insert own profile" ON profiles;
CREATE POLICY "Users can insert own profile" ON profiles
  FOR INSERT WITH CHECK (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own profile" ON profiles;
CREATE POLICY "Users can update own profile" ON profiles
  FOR UPDATE USING (auth.uid() = id);

DROP POLICY IF EXISTS "Public profiles readable" ON profiles;
CREATE POLICY "Public profiles readable" ON profiles
  FOR SELECT USING (true);

DROP POLICY IF EXISTS "Admins can update other profiles" ON profiles;
CREATE POLICY "Admins can update other profiles" ON profiles
  FOR UPDATE USING (
    EXISTS (SELECT 1 FROM profiles p WHERE p.id = auth.uid() AND p.role = 'admin')
  );

-- Auto-create profile on signup
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

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 2. Activity log
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

DROP POLICY IF EXISTS "Admins can read activity_log" ON activity_log;
CREATE POLICY "Admins can read activity_log" ON activity_log
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin')
  );

DROP POLICY IF EXISTS "Admins can insert activity_log" ON activity_log;
CREATE POLICY "Admins can insert activity_log" ON activity_log
  FOR INSERT WITH CHECK (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin')
  );

-- 3. Pending submissions (cross-device sync)
CREATE TABLE IF NOT EXISTS pending_submissions (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('word', 'phrase', 'idiom')),
  user_id UUID REFERENCES auth.users(id),
  content JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE pending_submissions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Contributors can insert own pending" ON pending_submissions;
CREATE POLICY "Contributors can insert own pending" ON pending_submissions
  FOR INSERT WITH CHECK (
    auth.uid() = user_id AND
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('contributor', 'admin'))
  );

DROP POLICY IF EXISTS "Admins can read all pending" ON pending_submissions;
CREATE POLICY "Admins can read all pending" ON pending_submissions
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin')
  );

DROP POLICY IF EXISTS "Admins can delete pending" ON pending_submissions;
CREATE POLICY "Admins can delete pending" ON pending_submissions
  FOR DELETE USING (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin')
  );

DROP POLICY IF EXISTS "Users can read own pending" ON pending_submissions;
CREATE POLICY "Users can read own pending" ON pending_submissions
  FOR SELECT USING (auth.uid() = user_id);

-- 4. Dictionary (words, phrases, idioms) – single source of truth, synced on git push or JSON import
CREATE TABLE IF NOT EXISTS dictionary (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  kind TEXT NOT NULL CHECK (kind IN ('word', 'phrase', 'idiom')),
  item_id TEXT NOT NULL,
  content JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(kind, item_id)
);

ALTER TABLE dictionary ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Anyone can read dictionary" ON dictionary;
CREATE POLICY "Anyone can read dictionary" ON dictionary
  FOR SELECT USING (true);

DROP POLICY IF EXISTS "Admins can insert dictionary" ON dictionary;
CREATE POLICY "Admins can insert dictionary" ON dictionary
  FOR INSERT WITH CHECK (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin')
  );

DROP POLICY IF EXISTS "Admins can update dictionary" ON dictionary;
CREATE POLICY "Admins can update dictionary" ON dictionary
  FOR UPDATE USING (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin')
  );

DROP POLICY IF EXISTS "Admins can delete dictionary" ON dictionary;
CREATE POLICY "Admins can delete dictionary" ON dictionary
  FOR DELETE USING (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin')
  );

-- Service role (CI) bypasses RLS; no policy needed for that.

-- =============================================================================
-- AFTER signing up in the app, promote your first admin (run separately):
-- UPDATE profiles SET role = 'admin' WHERE username = 'your_username';
-- Or by email: UPDATE profiles SET role = 'admin' WHERE id = (SELECT id FROM auth.users WHERE email = 'your@email.com');
-- =============================================================================
