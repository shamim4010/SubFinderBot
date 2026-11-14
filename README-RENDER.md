# SubFinder Bot — Render a Tolar Step (Free 24/7)

Ei file gula GitHub er ekta repo te tulle, sekhan theke Render free te bot cholbe.
⚠️ Token / password kokhono GitHub a tulba na — segula sudhu Render er Environment box a jabe.

## Step 1: GitHub repo ✅ HOYE GECE
Repo: **github.com/shamim4010/SubFinderBot** — sob file (bot.py + data/ folder a 23 ta subtitle) GF tule diyeche.
Season pack (full-pack.zip) repo te rakha hoy nai — bot start holei episode file diye nije baniye nebe.

## Step 2: Render service
1. **render.com** a jao → **Get Started / Sign In** → GitHub diye login koro
2. **New +** → **Web Service** → **Public Git Repository** beche nao
3. Tomar repo er link bosao: `https://github.com/shamim4010/SubFinderBot` → Continue
4. Settings:
   - Name: `subfinder-bot`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python3 bot.py`
   - Instance Type: **Free**
5. **Environment Variables** a ei gula nije bosao (Add Environment Variable):
   - `BOT_TOKEN` = BotFather theke neya notun token
   - `ADMIN_ID` = `7051812427`
   - `OS_API_KEY` = OpenSubtitles er API key
   - `OS_USERNAME` = OpenSubtitles username
   - `OS_PASSWORD` = OpenSubtitles password
   - `GATE_CHANNELS` = `@animesub_bd` (join gate er channel; ekadhik hole comma diye)
   - `JOIN_GATE` = `1` (join gate permanently ON rakhte)
   - `GATE_ALL` = `1` (gate sudhu premium na, SOB feature/library download eo lagbe)
   - `SUBDL_API_KEY` = SubDL API key (optional — thakle SubDL source o auto add hobe)
   ⚠️ GATE_CHANNELS ar JOIN_GATE diye rakhle bot er vitor theke set kora gate ar kokhono redeploy a muchbe na.
6. **Create Web Service** → deploy hote 2-5 min lagte pare
7. Deploy sesh hole upore tomar bot er URL dekhba, jemon: `https://subfinder-bot.onrender.com`

## Step 3: Ghum theke jagiye rakha (UptimeRobot)
Render free service 15 min kew na dakle ghumiye jay. Jagiye rakhte:
1. **uptimerobot.com** a free account kholo
2. **Add New Monitor** → Type: **HTTP(s)** → URL: tomar Render URL ta → Interval: **5 minutes** → Create
3. Bas! Proti 5 min a ekta ping jabe, bot jege thakbe

## Step 4: Test
Telegram a @AnySubFinderBot a giye /start dao. Prothom bar ghum theke uthle uttor aste ~1 min lagte pare, tarpor normal.

## Mone rakho
- Bot restart/redeploy hole bot er **user list, cache, ar bot er vitore add kora notun subtitle** muche jabe (Render free te file system permanent na). Bosano library (Code Geass R2) ar online search sob somoy thik thakbe.
- Bot er vitore /addsub diye notun subtitle add korle seta restart porjonto thakbe; permanent korte hole file ta GF ke dile library.zip a dhukiye neya jabe.
