# SubFinder 2050 (v7) — Bangla + English Subtitle Bot

Telegram bot: movie/anime er nam likhle library + online (OpenSubtitles, SubDL) theke subtitle khuje pathay.

## Notun ki ki (v7)
- 💾 **MongoDB persistence** — `MONGODB_URI` dile users, premium, settings, codes, stats, requests, ar admin er add kora subtitle file Render restart/redeploy-e r muchbe na (Atlas free cluster-i jothesto). Na dile age-r moto local file.
- ⭐ **Premium card upgrade** — Free vs Premium compare, plans list, days-left, "Get Premium" contact button, Daily bonus/Invite shortcut
- 🎁 `/daily` (roj bonus download, 7-din streak e +3) · 📥 `/quota` (aj-ker limit bar) · `/search naruto` (direct) · `/request`
- ⏳ Premium sesh hobar 3 din age auto reminder + sesh hole notice
- 🛠 **Admin notun command**: `/revoke` `/addbonus` `/msg` `/find` `/premiumlist` `/expiring` `/codes` `/delcode` `/plans` `/addplan Name | DAYS | Price` `/delplan` `/setcontact @user` `/setdaily N` `/gencode DAYS COUNT USES` `/adminhelp`
- 🧹 **Clean tool** — HTML tag, [sound effect], ♪ music, ad/credit line muche renumber kore.

## v6 feature gula
**User**
- 🌐 Bhasha system: বাংলা / English (/lang, /start a choose, menu-o bodlano jay)
- 🔎 Smart search: typo-tolerant ("code gaess" → Code Geass), S2E12 / ep 5 / Bangla alias
- ❤️ Favorites, 🕘 Download history (abar pao), 🔥 Trending, 🏆 Leaderboard
- 👤 Profile: XP, level, rank, daily streak
- 📥 Daily quota (free) + 🎁 Invite & Earn (bonus download) + 🎟 Redeem code + ⭐ Premium (unlimited)
- ⏱ Subtitle tools (free): sync -5s/-1s/-0.5s/+0.5s/+1s/+5s, 🔄 SRT → VTT, encoding auto-fix
- 📩 Request system — subtitle add hole user ke auto notification
- 💬 /feedback, ⚙️ Settings (language, notification, history clear)

**Admin (/admin — Control Center)**
- Live dashboard, 7-day analytics, top searches/downloads
- 👥 User manager: find, ban/unban, premium +7/30/90 din, bonus credit, direct message, CSV export
- 📣 Broadcast: any media (text/photo/video), audience filter (all / premium / free / bn / en), preview + confirm
- 🎟 Code generator (premium din ba bonus download)
- 📚 Library manager (add, delete, cache clear), 📩 Request manager
- 🔌 API sources, 📢 Join-gate channels (validate kore), ⚙️ Settings (daily limit, referral bonus, maintenance, online premium-only, gate)
- 🛡 Multi-admin (owner add/remove), 💾 Backup zip

Commands: /admin /user ID /ban ID /unban ID /grant ID DAYS /gencode DAYS COUNT /maintenance on|off /broadcast /addsub /done /backup

## Setup (Termux ba VPS)
```
pkg install -y python unzip      # Termux
pip install -r requirements.txt
printf '%s' 'BOT_TOKEN' > token.txt
cp config.example.json config.json   # admin_id boshao (bot a /id likhe pabe)
python bot.py        # ba:  bash run.sh  (crash hole auto restart)
```
`config.json`:  `{"admin_id": 123456789}`   (opensubtitles key optional — admin panel theke-o add kora jay)

## Notun anime add
Admin: `/addsub` → title (`Naruto | 2002`) → .srt / .zip pathao → `/done`.
Ba kono .srt/.zip er caption a title likhe pathao.
`catalog.json` a aliases dile search aro bhalo hoy (example deya ache).

## Files
`bot.py` (main) · `i18n.py` (Bangla/English text — notun language ekhane jog hoy) · `subtools.py` · `opensubs.py` · `subdl.py`
Auto-create: `users.json settings.json stats.json requests.json cache/`

⚠️ `token.txt`, `config.json`, `settings.json` (API key thake) karo sathe share koro na.
⚠️ Join gate: bot ke channel e **admin** banate hobe.
v5 theke upgrade: purono `users.json`/`settings.json` rakhle sob kaj korbe. Purono user ra prothom /start a language choose korbe.
