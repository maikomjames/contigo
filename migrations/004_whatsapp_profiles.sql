CREATE TABLE IF NOT EXISTS whatsapp_profiles (
  phone TEXT PRIMARY KEY,
  child_name TEXT,
  child_age INTEGER,
  themes TEXT[],
  onboarding_step TEXT DEFAULT 'waiting_name',
  is_premium BOOLEAN DEFAULT FALSE,
  premium_expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS whatsapp_story_logs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  phone TEXT NOT NULL,
  prompt TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
