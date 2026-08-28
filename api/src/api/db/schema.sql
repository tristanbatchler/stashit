CREATE TABLE IF NOT EXISTS users
(
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    google_sub  TEXT NOT NULL UNIQUE,
    email       TEXT NOT NULL,
    created     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions
(
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id    BIGINT NOT NULL
               REFERENCES users (id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    created    TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires    TIMESTAMPTZ NOT NULL,
    last_used  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_sessions_expiry
        CHECK (expires > created)
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id
    ON sessions (user_id);

CREATE INDEX IF NOT EXISTS idx_sessions_expires
    ON sessions (expires);

CREATE TABLE IF NOT EXISTS oauth_states
(
    state         TEXT PRIMARY KEY,
    code_verifier TEXT NOT NULL,
    created       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires       TIMESTAMPTZ NOT NULL,
    ip_address    INET NOT NULL,

    CONSTRAINT chk_oauth_states_expiry
        CHECK (expires > created)
);

CREATE INDEX IF NOT EXISTS idx_oauth_states_expires
    ON oauth_states (expires);

CREATE TABLE IF NOT EXISTS stashes
(
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    is_binary        BOOLEAN NOT NULL,
    slug             TEXT NOT NULL,
    added            TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    added_by_ip      INET NOT NULL,
    added_by_user_id BIGINT
                     REFERENCES users (id) ON DELETE SET NULL,
    
    CONSTRAINT uq_stashes_slug UNIQUE (slug)
);

CREATE INDEX IF NOT EXISTS idx_stashes_added
    ON stashes (added);


CREATE TABLE IF NOT EXISTS stashes_text_content
(
    stash_id BIGINT PRIMARY KEY
             REFERENCES stashes (id) ON DELETE CASCADE,
    content  TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS stashes_binary_paths
(
    stash_id BIGINT PRIMARY KEY
             REFERENCES stashes (id) ON DELETE CASCADE,
    file_path TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS stashes_expiries
(
    stash_id   BIGINT PRIMARY KEY
               REFERENCES stashes (id) ON DELETE CASCADE,
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_stashes_expiries_expires_at
    ON stashes_expiries (expires_at);


CREATE TABLE IF NOT EXISTS stashes_one_time_views
(
    stash_id BIGINT PRIMARY KEY
             REFERENCES stashes (id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS stashes_password_hashes
(
    stash_id     BIGINT PRIMARY KEY
                 REFERENCES stashes (id) ON DELETE CASCADE,
    password_hash TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS stashes_revocations
(
    stash_id     BIGINT PRIMARY KEY
                 REFERENCES stashes (id) ON DELETE CASCADE,
    revoked_at   TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revoked_by_ip INET NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_stashes_revocations_revoked_at
    ON stashes_revocations (revoked_at);


CREATE TABLE IF NOT EXISTS stash_views
(
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    stash_id    BIGINT NOT NULL
                REFERENCES stashes (id) ON DELETE CASCADE,
    ip_address  INET NOT NULL,
    viewed_at   TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stash_views_stash_id
    ON stash_views (stash_id);

CREATE INDEX IF NOT EXISTS idx_stash_views_stash_date
    ON stash_views (stash_id, viewed_at DESC);

CREATE INDEX IF NOT EXISTS idx_stash_views_ip
    ON stash_views (ip_address);

CREATE INDEX IF NOT EXISTS idx_stash_views_date
    ON stash_views (viewed_at DESC);


CREATE TABLE IF NOT EXISTS stash_password_attempts
(
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    stash_id     BIGINT NOT NULL
                 REFERENCES stashes (id) ON DELETE CASCADE,
    ip_address   INET NOT NULL,
    successful   BOOLEAN NOT NULL,
    attempted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stash_password_attempts_stash
    ON stash_password_attempts (stash_id);

CREATE INDEX IF NOT EXISTS idx_stash_password_attempts_stash_date
    ON stash_password_attempts (stash_id, attempted_at DESC);

CREATE INDEX IF NOT EXISTS idx_stash_password_attempts_ip
    ON stash_password_attempts (ip_address);

CREATE INDEX IF NOT EXISTS idx_stash_password_attempts_failed
    ON stash_password_attempts (stash_id, attempted_at DESC)
    WHERE successful = FALSE;


CREATE TABLE IF NOT EXISTS stash_lockouts
(
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    stash_id   BIGINT NOT NULL
               REFERENCES stashes (id) ON DELETE CASCADE,
    ip_address INET NOT NULL,
    added      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires    TIMESTAMPTZ NOT NULL,

    CONSTRAINT chk_stash_lockouts_expiry
        CHECK (expires > added)
);

CREATE INDEX IF NOT EXISTS idx_stash_lockouts_stash_ip_expiry
    ON stash_lockouts (stash_id, ip_address, expires DESC);

CREATE INDEX IF NOT EXISTS idx_stash_lockouts_ip
    ON stash_lockouts (ip_address);

CREATE INDEX IF NOT EXISTS idx_stash_lockouts_expires
    ON stash_lockouts (expires);
