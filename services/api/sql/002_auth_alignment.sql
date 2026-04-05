-- Phase 5 auth alignment:
-- - link app users to Supabase auth users
-- - track workspace owner explicitly

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS auth_user_id UUID;

-- Backfill existing rows where id already mirrored auth uid.
UPDATE users
SET auth_user_id = id
WHERE auth_user_id IS NULL;

ALTER TABLE users
    ALTER COLUMN auth_user_id SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'users_auth_user_id_key'
    ) THEN
        ALTER TABLE users
            ADD CONSTRAINT users_auth_user_id_key UNIQUE (auth_user_id);
    END IF;
END$$;

ALTER TABLE workspaces
    ADD COLUMN IF NOT EXISTS owner_user_id UUID REFERENCES users(id) ON DELETE SET NULL;

-- Backfill owner from first owner membership (if available).
UPDATE workspaces w
SET owner_user_id = wm.user_id
FROM (
    SELECT DISTINCT ON (workspace_id) workspace_id, user_id
    FROM workspace_members
    WHERE role = 'owner'
    ORDER BY workspace_id, created_at ASC
) wm
WHERE w.id = wm.workspace_id
  AND w.owner_user_id IS NULL;
