CREATE TABLE IF NOT EXISTS stashes
(
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    is_binary       BOOLEAN NOT NULL,
    slug            TEXT NOT NULL,
    added           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    added_by_ip     INET NOT NULL,
    expires_at      TIMESTAMPTZ,
    one_time_view   BOOLEAN NOT NULL DEFAULT FALSE,
    password_hash   TEXT,
    revoked_at      TIMESTAMPTZ,
    revoked_by_ip   INET,
    
    CONSTRAINT uq_stashes_slug UNIQUE (slug)
);

CREATE INDEX IF NOT EXISTS idx_stashes_added ON stashes (added);

CREATE INDEX IF NOT EXISTS idx_stashes_expires_at ON stashes (expires_at) 
WHERE expires_at IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_stashes_revoked_at ON stashes (revoked_at) 
WHERE revoked_at IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_stashes_active ON stashes (id) 
WHERE revoked_at IS NULL;

CREATE TABLE IF NOT EXISTS stashes_text_content
(
    stash_id  BIGINT PRIMARY KEY
              REFERENCES stashes (id) ON DELETE CASCADE,
    content   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS stashes_binary_paths
(
    stash_id  BIGINT PRIMARY KEY
              REFERENCES stashes (id) ON DELETE CASCADE,
    file_path TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS stash_views
(
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    stash_id    BIGINT NOT NULL
                REFERENCES stashes (id) ON DELETE CASCADE,
    ip_address  INET NOT NULL,
    viewed_at   TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stash_views_stash_id ON stash_views (stash_id);

CREATE INDEX IF NOT EXISTS idx_stash_views_stash_date ON stash_views (stash_id, viewed_at DESC);

CREATE INDEX IF NOT EXISTS idx_stash_views_ip ON stash_views (ip_address);

CREATE INDEX IF NOT EXISTS idx_stash_views_date ON stash_views (viewed_at DESC);

CREATE TABLE IF NOT EXISTS stash_password_attempts
(
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    stash_id    BIGINT NOT NULL
                REFERENCES stashes (id) ON DELETE CASCADE,
    ip_address  INET NOT NULL,
    successful  BOOLEAN NOT NULL,
    attempted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stash_password_attempts_stash ON stash_password_attempts (stash_id);

CREATE INDEX IF NOT EXISTS idx_stash_password_attempts_stash_date ON stash_password_attempts (stash_id, attempted_at DESC);

CREATE INDEX IF NOT EXISTS idx_stash_password_attempts_ip ON stash_password_attempts (ip_address);

CREATE INDEX IF NOT EXISTS idx_stash_password_attempts_failed ON stash_password_attempts (stash_id, attempted_at DESC)
WHERE successful = FALSE;


CREATE TABLE IF NOT EXISTS stash_lockouts
(
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    stash_id    BIGINT NOT NULL
                REFERENCES stashes (id) ON DELETE CASCADE,
    ip_address  INET NOT NULL,
    added       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires     TIMESTAMPTZ NOT NULL,

    CONSTRAINT chk_stash_lockouts_expiry CHECK (expires > added)
);

CREATE INDEX IF NOT EXISTS idx_stash_lockouts_stash_ip_expiry ON stash_lockouts (stash_id, ip_address, expires DESC);

CREATE INDEX IF NOT EXISTS idx_stash_lockouts_ip ON stash_lockouts (ip_address);

CREATE INDEX IF NOT EXISTS idx_stash_lockouts_expires ON stash_lockouts (expires);