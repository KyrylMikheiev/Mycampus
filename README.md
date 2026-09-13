# MyCampus Grade Watcher

Checks your MyCampus grades on a schedule and pings you on Telegram
when something changes. Runs on your own machine with your own account —
there is no server, no sign-up, and nothing leaves your computer except the
Telegram message you send to yourself.

### Before you start, know this

- It logs in **as you**, with **your** credentials, to read **your own** data.
  Check your institution's terms of use — you are responsible for how you
  use your account.
- Your username and password sit in **plaintext** in a local `.env` file. That
  is normal for a small local tool, but you should know it. Don't put that file
  on a shared machine and don't ever commit it.
- **Be gentle with the server.** A few times a day is plenty. Do not point a
  per-minute cron job at your university's systems.
- No warranty, see [LICENSE](LICENSE). If it breaks something, that's on you.

## Setup

### Install

1. check your python (or if you dont have it - install): python --version (3.9 or newer)
2. python -m venv .venv
3. activate it:
    1. windows: .venv\Scripts\activate
    2. mac/linux: source .venv/bin/activate
4. pip install -r requirements.txt
5. playwright install chromium

PS: the .venv has to be activated every time you open a new terminal gang

PS2: we do this first because you need playwright to fill the env later

### Your Secrets

1. copy and paste ".env.example"
2. rename it to ".env"
3. put your login data

2/5 fields are set, we are moving quickly gang

Lets do USER_AGENT before Telegram bot

1. open browser
2. open dev tools (or click f12)
3. open Network tab
4. click on any request
5. open Headers tab
6. find request headers
7. find a field "User-Agent" (that is your user agent)

PS: You may use any user agent. Sending a realistic one just means the app
sees a normal browser string and behaves the way it does for you anyway.

3/5 LESSS GOO, now we need telegram

1. Open Telegram
2. Click to chat with @BotFather in Telegram (you may find it in search)
3. then you write in the chat:
    a. /start
    b. /newbot
    c. Type any name you want
    d. type a username for your bot
    e. copy the key and paste it in TG_TOKEN

4/5, last step come on g

1. open browser
2. type in: https://api.telegram.org/bot<whole-token-we-got-in-previous-step>/getUpdates (without <> ofc)
3. you will probably see a json like status true, result empty.
4. Thats why you open your telegram bot and type him something
5. now you look up the url again and you will get chat id (find it)
6. that is what you paste in gang

5/5, Well Done!!!

Now i recommend setting this bot to be private

1. Open @BotFather
2. Open app (left from text area button open)
3. Click on your bot
4. Click "Bot Settings"
5. scroll down
6. turn on "Restrict bot usage"

This way you will ensure nobody will get access to him

### Portal

Jk, not done yet gang, 6 more fields. These ones say WHERE to look, thats why nobody
can fill them in for you

MYCAMPUS_BASE and MYCAMPUS_TENANT, 2 for the price of 1

1. open your portal, f12, Network tab
2. log in by hand (yes really, by hand)
3. find the request named "login"
4. take its url, cut the "login" off the end -> MYCAMPUS_BASE
5. open Payload (or Form Data), find "tenant" -> MYCAMPUS_TENANT

PS: keep the "/" at the end of the base gang

2/6, next one is chill

BOOTSTRAP_COOKIES

1. open a private window, go to your portal, DONT log in
2. f12, Application tab (Storage in firefox)
3. click Cookies, click your portal
4. look at the cookies that are already sitting there
5. write them as json: '{"NAME":"value","OTHER":""}'
6. single quotes around the whole thing, dont forget

PS: nothing there? leave it empty, you are fine

3/6 LESSS GOO, now the clicking part

GRADES_TILE

1. run: playwright codegen <your portal url>
2. log in by hand in the window that opens
3. click your way to your grades
4. look at the code it writes for you on the right
5. copy the selector out of the click line
6. paste it in GRADES_TILE (single quotes again)

4/6, we are flying

GRADES_XHR

1. f12, Network tab, click the Fetch/XHR filter
2. click your grades again
3. find the request that actually brings your grades
4. copy a unique piece of its url (a filename works great)
5. that is your GRADES_XHR

PS: you dont need the whole url, just enough to recognize it

5/6, last one and its optional

REJECT_MARKERS

1. sometimes the portal gives you only half a page
2. the script would save that half page as your baseline, bad
3. find a word that shows up ONLY in that broken page
4. put them comma separated: word1,word2
5. or leave it empty, then it just checks the page isnt empty

6/6, Well Done again!!!

### Run it

```bash
python grade_watcher.py
```

PS: the first run only saves a baseline and tells you so. it will NOT message
you, that is normal gang

Want to watch what the browser is doing? Run it with `HEADLESS=0`.

If it tells you the grades tile never appeared, your `GRADES_TILE` selector
doesn't match anything on the page — check `debug.png`, which the script writes
on that failure, to see what the browser actually got.

### If something breaks

Open an issue — but **never paste your `.env`, your bot token, `debug.png`, or
`last_state.json`** into it. The tracker is public; those contain your login
data and your grades.

### Cheat sheet

Same as the walkthrough above, just short — for when you already know your way
around dev tools.

| key | where to find it |
| --- | --- |
| `MYCAMPUS_BASE` | the URL of the login POST, without the trailing `login` |
| `MYCAMPUS_TENANT` | the `tenant` field in that POST's form body |
| `BOOTSTRAP_COOKIES` | JSON object of the cookies the portal sets before login, e.g. `'{"LANG":"en"}'` — leave empty if yours needs none |
| `GRADES_TILE` | CSS selector of the thing you click to open your grades |
| `GRADES_XHR` | a distinctive part of the URL of the request that returns the grades data, visible in Network when you click through |
| `REJECT_MARKERS` | comma-separated strings that appear only in a half-loaded page; if any shows up, the run is discarded instead of saved as your baseline. Optional |

`playwright codegen <your portal URL>` is the easy way to get `GRADES_TILE`: log
in by hand, click through to your grades, and copy the selector it prints for
that click.

### License

MIT — see [LICENSE](LICENSE).
