-- name: CreateOAuthState :exec
INSERT INTO oauth_states (
    state,
    code_verifier,
    expires,
    ip_address
)
VALUES ($1, $2, $3, $4);

-- name: GetOAuthState :one
SELECT
    state,
    code_verifier,
    expires,
    ip_address
FROM oauth_states
WHERE state = $1
  AND expires > NOW();

-- name: DeleteOAuthState :one
DELETE FROM oauth_states
WHERE state = $1
RETURNING *;


-- name: UpsertUser :one
INSERT INTO users (
    google_sub,
    email, 
    name,
    is_admin
)
VALUES ($1, $2, $3, $4)
ON CONFLICT (google_sub)
DO UPDATE SET
    email = EXCLUDED.email,
    last_login = CURRENT_TIMESTAMP,
    is_admin = EXCLUDED.is_admin
RETURNING *;

-- name: GetUserBySessionTokenHash :one
SELECT 
    u.id,
    u.google_sub,
    u.email,
    u.name, 
    u.created,
    u.last_login,
    u.is_admin
FROM users u
INNER JOIN sessions s ON u.id = s.user_id
WHERE s.token_hash = $1 
  AND s.expires > NOW();


-- name: CreateSession :exec
INSERT INTO sessions (
    user_id,
    token_hash,
    expires
)
VALUES ($1, $2, $3);

-- name: DeleteSession :exec
DELETE FROM sessions
WHERE token_hash = $1;

-- name: GetStash :one
SELECT
    s.id,
    s.is_binary,
    s.slug,
    s.added,
    s.added_by_ip,
    s.added_by_user_id,
    r.revoked_at,
    r.revoked_by_user_id,
    e.expires_at,
    CASE WHEN p.password_hash IS NOT NULL THEN true ELSE false END AS is_protected
FROM stashes s
LEFT JOIN stashes_revocations r
    ON r.stash_id = s.id
LEFT JOIN stashes_expiries e
    ON e.stash_id = s.id
LEFT JOIN stashes_password_hashes p
    ON p.stash_id = s.id
WHERE id = $1;


-- name: GetStashBySlug :one
SELECT
    s.id,
    s.is_binary,
    s.slug,
    s.added,
    s.added_by_ip,
    s.added_by_user_id,
    r.revoked_at,
    r.revoked_by_user_id,
    e.expires_at,
    CASE WHEN p.password_hash IS NOT NULL THEN true ELSE false END AS is_protected
FROM stashes s
LEFT JOIN stashes_revocations r
    ON r.stash_id = s.id
LEFT JOIN stashes_expiries e
    ON e.stash_id = s.id
LEFT JOIN stashes_password_hashes p
    ON p.stash_id = s.id
WHERE s.slug = $1;


-- name: ListStashes :many
SELECT
    s.id,
    s.is_binary,
    s.slug,
    s.added,
    s.added_by_ip,
    s.added_by_user_id,
    r.revoked_at,
    r.revoked_by_user_id,
    e.expires_at,
    CASE WHEN p.password_hash IS NOT NULL THEN true ELSE false END AS is_protected
FROM stashes s
LEFT JOIN stashes_revocations r
    ON r.stash_id = s.id
LEFT JOIN stashes_expiries e
    ON e.stash_id = s.id
LEFT JOIN stashes_password_hashes p
    ON p.stash_id = s.id
WHERE
    -- Use sqlc.arg() to explicitly name your variables
    (sqlc.arg(include_revoked)::boolean = true OR r.revoked_at IS NULL)
AND
    (sqlc.arg(include_expired)::boolean = true OR e.expires_at IS NULL OR e.expires_at > NOW())
ORDER BY s.added DESC, s.id DESC
LIMIT sqlc.arg('limit') OFFSET sqlc.arg('offset');



-- name: GetStashTextContent :one
SELECT content
FROM stashes_text_content
WHERE stash_id = $1;


-- name: GetStashBinaryPath :one
SELECT file_path
FROM stashes_binary_paths
WHERE stash_id = $1;


-- name: CreateStash :one
INSERT INTO stashes (
    is_binary,
    slug,
    added_by_ip,
    added_by_user_id
)
VALUES ($1, $2, $3, $4)
RETURNING
    id,
    is_binary,
    slug,
    added,
    added_by_ip,
    added_by_user_id;


-- name: CreateStashTextContent :exec
INSERT INTO stashes_text_content (
    stash_id,
    content
)
VALUES ($1, $2);


-- name: CreateStashBinaryPath :exec
INSERT INTO stashes_binary_paths (
    stash_id,
    file_path
)
VALUES ($1, $2);


-- name: CheckSlugExists :one
SELECT EXISTS (
    SELECT 1
    FROM stashes
    WHERE slug = $1
);


-- name: CreateStashView :exec
INSERT INTO stash_views (
    stash_id,
    ip_address
)
VALUES ($1, $2);


-- name: CreateStashPasswordAttempt :exec
INSERT INTO stash_password_attempts (
    stash_id,
    ip_address,
    successful
)
VALUES ($1, $2, $3);


-- name: CreateStashLockout :exec
INSERT INTO stash_lockouts (
    stash_id,
    ip_address,
    expires
)
VALUES ($1, $2, $3);


-- name: GetActiveStashLockout :one
SELECT
    id,
    added,
    expires
FROM stash_lockouts
WHERE stash_id = $1
  AND ip_address = $2
  AND expires > CURRENT_TIMESTAMP
ORDER BY expires DESC
LIMIT 1;


-- name: GetStashViews :one
SELECT COUNT(*)
FROM stash_views
WHERE stash_id = $1;


-- name: GetStashUniqueViews :one
SELECT COUNT(DISTINCT ip_address)
FROM stash_views
WHERE stash_id = $1;


-- name: GetStashViewsBySlug :one
SELECT COUNT(*)
FROM stash_views
JOIN stashes
    ON stashes.id = stash_views.stash_id
WHERE stashes.slug = $1;


-- name: GetStashUniqueViewsBySlug :one
SELECT COUNT(DISTINCT stash_views.ip_address)
FROM stash_views
JOIN stashes
    ON stashes.id = stash_views.stash_id
WHERE stashes.slug = $1;


-- name: GetStashExpiry :one
SELECT expires_at
FROM stashes_expiries
WHERE stash_id = $1;


-- name: CreateStashExpiry :exec
INSERT INTO stashes_expiries (
    stash_id,
    expires_at
)
VALUES ($1, $2);


-- name: GetStashOneTimeView :one
SELECT stash_id
FROM stashes_one_time_views
WHERE stash_id = $1;


-- name: CreateStashOneTimeView :exec
INSERT INTO stashes_one_time_views (
    stash_id
)
VALUES ($1);


-- name: GetStashPasswordHash :one
SELECT password_hash
FROM stashes_password_hashes
WHERE stash_id = $1;


-- name: CreateStashPasswordHash :exec
INSERT INTO stashes_password_hashes (
    stash_id,
    password_hash
)
VALUES ($1, $2);


-- name: GetStashRevocation :one
SELECT
    revoked_at,
    revoked_by_user_id
FROM stashes_revocations
WHERE stash_id = $1;


-- name: CreateStashRevocation :one
WITH revoked AS (
    INSERT INTO stashes_revocations (
        stash_id,
        revoked_by_user_id
    )
    SELECT s.id, $2
    FROM stashes AS s
    WHERE s.slug = $1
    ON CONFLICT (stash_id) DO NOTHING
    RETURNING stash_id
)
SELECT
    s.id,
    s.is_binary,
    s.slug,
    s.added,
    s.added_by_ip,
    s.added_by_user_id
FROM stashes AS s
JOIN revoked AS r
    ON r.stash_id = s.id;


-- name: DeleteStashTextContent :exec
DELETE FROM stashes_text_content
WHERE stash_id = $1;

-- name: DeleteStashBinaryPath :one
DELETE FROM stashes_binary_paths
WHERE stash_id = $1
RETURNING file_path;

-- name: GetRecentFailedStashPasswordAttempts :one
SELECT COUNT(*)
FROM stash_password_attempts
WHERE stash_id = @stash_id
  AND ip_address = @ip_address
  AND successful = FALSE
  AND attempted_at > @attempted_since;

-- name: CreateIPBan :one
INSERT INTO ip_bans (
    ip_address,
    expires,
    reason,
    added_by_user_id
)
VALUES ($1, $2, $3, $4)
RETURNING *;


-- name: GetIPBan :one
SELECT
    id,
    ip_address,
    added,
    expires,
    reason,
    added_by_user_id,
    revoked_at,
    revoked_by_user_id,
    revocation_reason
FROM ip_bans
WHERE id = $1;


-- name: GetActiveIPBan :one
SELECT
    id,
    ip_address,
    added,
    expires,
    reason,
    added_by_user_id,
    revoked_at,
    revoked_by_user_id,
    revocation_reason
FROM ip_bans
WHERE ip_address = $1
  AND revoked_at IS NULL
  AND (expires IS NULL OR expires > CURRENT_TIMESTAMP)
ORDER BY expires DESC NULLS FIRST
LIMIT 1;


-- name: ListIPBans :many
SELECT
    id,
    ip_address,
    added,
    expires,
    reason,
    added_by_user_id,
    revoked_at,
    revoked_by_user_id,
    revocation_reason
FROM ip_bans
WHERE ip_address = $1
ORDER BY added DESC, id DESC;


-- name: ListActiveIPBans :many
SELECT
    id,
    ip_address,
    added,
    expires,
    reason,
    added_by_user_id,
    revoked_at,
    revoked_by_user_id,
    revocation_reason
FROM ip_bans
WHERE revoked_at IS NULL
  AND (expires IS NULL OR expires > CURRENT_TIMESTAMP)
ORDER BY added DESC, id DESC;


-- name: RevokeIPBan :one
UPDATE ip_bans
SET
    revoked_at = CURRENT_TIMESTAMP,
    revoked_by_user_id = $2,
    revocation_reason = $3
WHERE id = $1
    AND revoked_at IS NULL
RETURNING ip_address;


-- name: ListIPActivity :many
SELECT
    event_at,
    event_type,
    stash_id,
    slug,
    details
FROM (
    SELECT
        s.added AS event_at,
        'stash_created'::TEXT AS event_type,
        s.id AS stash_id,
        s.slug,
        NULL::TEXT AS details
    FROM stashes s
    WHERE s.added_by_ip = @ip_address

    UNION ALL

    SELECT
        v.viewed_at AS event_at,
        CASE
            WHEN s.is_binary THEN 'stash_downloaded'
            ELSE 'stash_viewed'
        END AS event_type,
        s.id AS stash_id,
        s.slug,
        NULL::TEXT AS details
    FROM stash_views v
    INNER JOIN stashes s
        ON s.id = v.stash_id
    WHERE v.ip_address = @ip_address

    UNION ALL

    SELECT
        p.attempted_at AS event_at,
        CASE
            WHEN p.successful THEN 'password_success'
            ELSE 'password_failure'
        END AS event_type,
        s.id AS stash_id,
        s.slug,
        NULL::TEXT AS details
    FROM stash_password_attempts p
    INNER JOIN stashes s
        ON s.id = p.stash_id
    WHERE p.ip_address = @ip_address

    UNION ALL

    SELECT
        b.added AS event_at,
        'ip_banned'::TEXT AS event_type,
        NULL::BIGINT AS stash_id,
        NULL::TEXT AS slug,
        b.reason AS details
    FROM ip_bans b
    WHERE b.ip_address = @ip_address

    UNION ALL

    SELECT
        b.revoked_at AS event_at,
        'ip_ban_revoked'::TEXT AS event_type,
        NULL::BIGINT AS stash_id,
        NULL::TEXT AS slug,
        b.revokation_reason AS details
    FROM ip_bans b
    WHERE b.ip_address = @ip_address
      AND b.revoked_at IS NOT NULL

    UNION ALL

    SELECT
        r.revoked_at AS event_at,
        'stash_revoked'::TEXT AS event_type,
        s.id AS stash_id,
        s.slug,
        NULL::TEXT AS details
    FROM stashes_revocations r
    INNER JOIN stashes s
        ON s.id = r.stash_id
    WHERE s.added_by_ip = @ip_address
) events
ORDER BY event_at DESC
LIMIT sqlc.arg('limit')::int
OFFSET sqlc.arg('offset')::int;
