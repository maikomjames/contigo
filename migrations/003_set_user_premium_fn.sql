CREATE OR REPLACE FUNCTION set_user_premium(p_user_id UUID, p_expires_at TIMESTAMPTZ)
RETURNS void AS $$
BEGIN
  UPDATE profiles
  SET is_premium = TRUE, premium_expires_at = p_expires_at, updated_at = NOW()
  WHERE id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
