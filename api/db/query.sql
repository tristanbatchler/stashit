-- name: GetStash :one
SELECT
    is_binary,
    slug,
    added,
    added_by_ip,
    expires_at,
    one_time_view,
    password_hash,
    revoked_at,
    revoked_by_ip
FROM stashes
WHERE id = $1;

-- name: GetStashBySlug :one
SELECT
    id,
    is_binary,
    added,
    added_by_ip,
    expires_at,
    one_time_view,
    password_hash,
    revoked_at,
    revoked_by_ip
FROM stashes
WHERE slug = $1;

-- name: ListStashes :many
SELECT * 
FROM stashes
ORDER BY added DESC, id DESC
LIMIT $1 OFFSET $2;

-- name: GetStashTextContent :one
SELECT content
FROM stashes_text_content
WHERE stash_id = $1;

-- name: GetStashBinaryPath :one
SELECT file_path
FROM stashes_binary_paths
WHERE stash_id = $1;

-- name: CreateStash :one
INSERT INTO stashes (is_binary, slug, added_by_ip)
VALUES ($1, $2, $3)
RETURNING *;

-- name: CreateStashTextContent :exec
INSERT INTO stashes_text_content (stash_id, content)
VALUES ($1, $2);

-- name: CreateStashBinaryPath :exec
INSERT INTO stashes_binary_paths (stash_id, file_path)
VALUES ($1, $2);

-- name: CheckSlugExists :one
SELECT EXISTS (
    SELECT 1
    FROM stashes
    WHERE slug = $1
);

-- name: CreateStashView :exec
INSERT INTO stash_views (stash_id, ip_address)
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
JOIN stashes ON stashes.id = stash_views.stash_id
WHERE stashes.slug = $1;

-- name: GetStashUniqueViewsBySlug :one
SELECT COUNT(DISTINCT stash_views.ip_address)
FROM stash_views
JOIN stashes ON stashes.id = stash_views.stash_id
WHERE stashes.slug = $1;