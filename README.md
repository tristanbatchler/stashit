# Stash It

This is a way for me to effortlessly share content between my devices.

I'm sure there are alternatives I can deploy with Docker, but I wanted to make my own.

## Quickstart

I like Mise, so that should be installed and configured on your shell. Then:

```
mise install
mise use -g watchexec@latest # installs the file watcher (you only need this once)
cd api
uv sync
uv run fastapi dev
```

While I'm coding I keep `mise watch default ::: sqlc` running from the repo root.
It will watch for saves on Python and SQL files and run commands to format my Python files
or generate code from my SQL files accordingly.

## Frontend

The frontend is a SvelteKit app in `web/`. Dependencies are installed with `npm`
(Mise puts `npm` on my PATH):

```
cd web
npm install
npm run dev -- --open
```

That starts Vite on http://localhost:5173/.

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