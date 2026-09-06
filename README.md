# Stash It

This is a way for me to effortlessly share content between my devices.

I'm sure there are alternatives I can deploy with Docker, but I wanted to make my own.

## Quickstart

Firstly, make your configuration:

```sh
cp .example.env .env
# Now edit it however you like
```

I like Mise, so that should be installed and configured on your shell. Then:

```sh
mise trust
mise install
mise use -g watchexec@latest # installs the file watcher (you only need this once)
cd api
uv sync
uv run fastapi dev # See http://localhost:8000/docs
```

And for installing the front-end (SvelteKit app managed with `npm`, installed by Mise):

```sh
cd web # (assuming you are back in the root directory)
npm install
npm run dev -- # See http://localhost:5173
```

The development front-end expects the FastAPI server to be running on `http://localhost:8000`.

## Docker

The application can be run as a production deployment using Docker Compose. The Compose setup runs the FastAPI API and SvelteKit application as separate containers, with Postgres being provided separately.

First, make sure `.env` exists and is configured:

```sh
cp .example.env .env
# Edit .env with the required configuration
```

Then build and start the application:

```sh
docker compose up
```

This starts:

* The FastAPI API on port `8000`
* The SvelteKit application on port `3000`

The API and web application communicate with each other over the Docker Compose network. The SvelteKit server therefore uses `http://api:8000` when running inside Docker, while browser requests use the same-origin `/api/...` paths.

### nginx

The Docker deployment is intended to sit behind nginx. nginx should proxy the two parts of 
the application separately:

```text
https://stash.example.com/       -> http://web:3000
https://stash.example.com/api/   -> http://api:8000
```

For example, the important part of an nginx configuration looks roughly like:

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000;

    # Identity Headers using Cloudflare shortcuts
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $http_cf_connecting_ip;
    proxy_set_header X-Forwarded-For $http_cf_connecting_ip;
    proxy_set_header X-Forwarded-Proto $scheme;

    # Timeouts for API stability
    proxy_connect_timeout 60s;
    proxy_read_timeout 60s;
}

# Frontend Web App (Vite server running on port 3000)
location / {
    proxy_pass http://127.0.0.1:3001;

    # Identity Headers using Cloudflare shortcuts
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $http_cf_connecting_ip;
    proxy_set_header X-Forwarded-For $http_cf_connecting_ip;
    proxy_set_header X-Forwarded-Proto $scheme;

    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_cache_bypass $http_upgrade;
}
```

The exact nginx configuration will depend on where nginx is running. My global nginx config file is in `nginx.conf` in the root of this repo.

The important distinction is that `/api/` must reach FastAPI directly, while all other paths must reach SvelteKit.

The SvelteKit container needs access to `.env` while the image is being built because it generates its TypeScript API client from the FastAPI OpenAPI schema. The Compose configuration supplies this as a build secret.

### Production deployment

To rebuild the application after making changes:

```sh
docker compose up --build
```

To run it in the background:

```sh
docker compose up --build -d
```

To stop it:

```sh
docker compose down
```

Uploaded files are stored in the Docker `uploads` volume, so they persist when the containers are recreated.

## Tooling

While I'm coding I keep 

```sh
mise watch default ::: sqlc ::: web-check ::: web-lint ::: web-gen-types
```

running from the repo root. It will watch for saves on Python and SQL files and run 
commands to format my Python files or generate code from my SQL files accordingly.
The FastAPI server *does* need to be running though if I'm running the `web-gen-types` 
watcher, otherwise it can't access the OpenAPI spec to generate the TypeScript.

## Example

I have a snippet someone sent me on Slack on my work laptop, and I want to use it on my 
personal PC later. I'll simply go to https://stashit.mydomain.com, upload the file (or 
paste its contents) and hit **Stash**. It'll give me a short link and QR code, e.g. 
`stashit.mydomain.com/DonutsTasteBattery`. All I gotta do is hit that up on my PC later to 
grab the snippet, or download it in-browser.

## Short URL generation

We all know the battery horse stable XKCD comic, so I want to use that. But I think it'd 
be fun if I could customise the possible words, and make them flow somewhat similarly to 
English phrases with nouns, verbs, and adjectives. This should give more than enough 
entropy while making it easy to remember and type, or to read out to someone else.

## Future plans

* Allow the option to protect files during generation. Not with a password, but with Google 
  auth. It's only me and maybe a couple friends using this, so I can allow them to view 
  protected files but just not random strangers. I don't want to use Firebase or Supabase 
  or whatever the kids use these days either. Just somehow let this app use Google as an 
  identity provider, but I'm not sure what's involved in that, or if it's even free?
* Revoke files you've stashed so they are impossible to retrieve and gone from the server.
* Larger uploads with something less fragile than the naive upload and download. Some kind 
  of longer-lived connection would be required, needs research.
* Some kind of admin interface where I can have a little look at files and their metadata, 
  and revoke stuff etc.
* Auto-expiring stashes, or one-time stashes, that are revoked after a certain period of 
  time, or after it's been accessed once.

## Concerns

To be useful, I'd want to have this service available to the outside world, as I can't 
guarantee I'd be on my home Wi-Fi. I think this is a requirement for Google integration 
too.

This makes me slightly nervous about abuse, so:
1. It'll need to sit behind Cloudflare so nobody can trace it back to my home IP.
2. It'll probably need to be protected with Cloudflare Turnstile to prevent bots.
3. I'll need to keep a record of the IP addresses and any other relevant information about 
   people using the service.
4. I'll need to ensure search engines don't index this with a good robots.txt etc. (to 
   avoid people finding it in the first place).
5. Honestly, the upload endpoint needs to be protected behind Google auth... Then only the 
   people I trust are allowed to upload binary files. Though I'm alright with text/snippet 
   stashing to be completely public, I can always revoke anything that is suspicious.
6. I should hook it up to some notification system (potentially my ntfy server, plus email 
   to alert me when someone publicly stashes something) so I can vet it out and decide if 
   I want to revoke it or not. Probably not needed unless the text contains something that 
   looks like an external link or an obvious encoded blob (base64, base85, etc.).

## Technology

I'll stick with that I know, which is Python and SQL.

* The backend API will be `fastapi` + `uvicorn` - something battle tested and I don't need to 
  think about it.
* The database layer will be Postgres, and I have a server running it already and I'll write 
  my queries by hand with SQL. `sqlc-gen-better-python` will compile my queries to type-safe 
  Python code, and I can have it run on a watch task with Mise.
* The front-end will be compiled with Svelte, so I can easily interface with the API without 
  thinking too hard about specific JavaScript frameworks just to make it work and look nice. 
  The Svelte templates will be as simple and semantic as I can get them because that should play 
  nice with Pico CSS, which I'll use as my opinionated small CSS library.