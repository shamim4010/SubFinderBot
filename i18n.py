"""
SubFinder i18n — Bangla (bn) + English (en)
Notun bhasha jog korte: LANGS a code dao, tarpor protita key te oi code er text lekho.
Missing hole English fallback hoy.
"""

LANGS = {"bn": "🇧🇩 বাংলা", "en": "🇬🇧 English"}
D = "━━━━━━━━━━━━━━━"

S = {}


def add(key, bn, en):
    S[key] = {"bn": bn, "en": en}


def T(_l, _k, **kw):
    entry = S.get(_k)
    if not entry:
        return _k
    text = entry.get(_l) or entry["en"]
    kw.setdefault("D", D)
    try:
        return text.format(**kw)
    except (KeyError, IndexError):
        return text


# ============================================================ common / menu
add("lang_pick", "🌐 <b>ভাষা বেছে নিন · Choose your language</b>",
    "🌐 <b>Choose your language · ভাষা বেছে নিন</b>")
add("lang_set", "✅ ভাষা সেট হয়েছে: <b>বাংলা</b>", "✅ Language set: <b>English</b>")
add("welcome",
    "✦ <b>স্বাগতম, {name}!</b> ✦\n{D}\n<b>SubFinder</b> — আপনার পার্সোনাল সাবটাইটেল সহকারী।\n\n"
    "🎬 যেকোনো মুভি, অ্যানিমে বা সিরিজের <b>নাম লিখে পাঠান</b>\n"
    "📁 লাইব্রেরি + 🌐 অনলাইন সোর্স — একসাথে সার্চ\n"
    "🇧🇩 বাংলা ও 🇬🇧 English সাবটাইটেল\n"
    "⏱ সিঙ্ক ঠিক করার টুল · 🔄 VTT কনভার্টার\n"
    "🎁 ইনভাইট করুন, বোনাস ডাউনলোড জিতুন\n\n"
    "<i>উদাহরণ:</i> <code>Interstellar</code> · <code>Code Geass S2 E12</code>",
    "✦ <b>Welcome, {name}!</b> ✦\n{D}\n<b>SubFinder</b> — your personal subtitle companion.\n\n"
    "🎬 Just <b>type any movie, anime or series name</b>\n"
    "📁 Library + 🌐 online sources — searched together\n"
    "🇧🇩 Bangla & 🇬🇧 English subtitles\n"
    "⏱ Sync-fix tools · 🔄 VTT converter\n"
    "🎁 Invite friends, earn bonus downloads\n\n"
    "<i>Examples:</i> <code>Interstellar</code> · <code>Code Geass S2 E12</code>")
add("menu_title", "🏠 <b>মেইন মেনু</b>\n{D}\nকী করতে চান?", "🏠 <b>Main Menu</b>\n{D}\nWhat would you like to do?")
add("ask_name",
    "🎬 মুভি/অ্যানিমের <b>নাম লিখে পাঠান</b>\nযেমন: <code>Interstellar</code> বা <code>Geass S2 E12</code>",
    "🎬 <b>Type the name</b> of a movie or anime\ne.g. <code>Interstellar</code> or <code>Geass S2 E12</code>")
add("help",
    "❓ <b>হেল্প সেন্টার</b>\n{D}\n"
    "🔍 শুধু নাম লিখুন — সার্চ হয়ে যাবে (S2 E12, ep 5 — সবই চলে)\n"
    "📚 /list — লাইব্রেরি\n🔥 /trending — সবাই যা খুঁজছে\n❤️ /favorites — সেভ করা টাইটেল\n"
    "🕘 /history — আগের ডাউনলোড\n👤 /profile — লেভেল, XP, স্ট্যাটাস\n🎁 /invite — বন্ধুকে ইনভাইট করে বোনাস\n"
    "🎟 /redeem — কোড রিডিম\n🏆 /top — লিডারবোর্ড\n💬 /feedback — মতামত পাঠান\n"
    "⚙️ /settings — ভাষা ও নোটিফিকেশন\n🆔 /id — আপনার আইডি\n\n"
    "⏱ <b>টুলস:</b> সাবটাইটেল পাওয়ার পর নিচের বাটনে সিঙ্ক ঠিক করুন বা VTT বানান — এগুলো ফ্রি, কোটা কাটে না।",
    "❓ <b>Help Center</b>\n{D}\n"
    "🔍 Just type a name — S2 E12, ep 5 all work\n"
    "📚 /list — library\n🔥 /trending — what everyone searches\n❤️ /favorites — saved titles\n"
    "🕘 /history — past downloads\n👤 /profile — level, XP, status\n🎁 /invite — invite friends for bonus\n"
    "🎟 /redeem — redeem a code\n🏆 /top — leaderboard\n💬 /feedback — send feedback\n"
    "⚙️ /settings — language & notifications\n🆔 /id — your ID\n\n"
    "⏱ <b>Tools:</b> after you get a subtitle, use the buttons to fix sync or convert to VTT — free, no quota used.")
add("banned", "🚫 আপনার অ্যাকাউন্ট ব্লক করা হয়েছে।", "🚫 Your account has been suspended.")
add("maint", "🛠 বট এখন মেইনটেন্যান্সে আছে। একটু পরে আবার চেষ্টা করুন।",
    "🛠 The bot is under maintenance. Please try again shortly.")
add("slow", "⏳ একটু ধীরে! খুব দ্রুত মেসেজ পাঠাচ্ছেন।", "⏳ Slow down a little — too many messages.")
add("cancelled", "❌ বাতিল করা হয়েছে।", "❌ Cancelled.")
add("unknown_cb", "এই বাটনটি আর কাজ করছে না, আবার সার্চ করুন।", "This button has expired — please search again.")

# reply keyboard + menu buttons
add("btn_search", "🔍 সার্চ", "🔍 Search")
add("btn_library", "📚 লাইব্রেরি", "📚 Library")
add("btn_trending", "🔥 ট্রেন্ডিং", "🔥 Trending")
add("btn_favs", "❤️ ফেভারিট", "❤️ Favorites")
add("btn_profile", "👤 প্রোফাইল", "👤 Profile")
add("btn_premium", "⭐ প্রিমিয়াম", "⭐ Premium")
add("btn_request", "📩 রিকুয়েস্ট", "📩 Request")
add("btn_settings", "⚙️ সেটিংস", "⚙️ Settings")
add("btn_history", "🕘 হিস্ট্রি", "🕘 History")
add("btn_invite", "🎁 ইনভাইট", "🎁 Invite")
add("btn_help", "❓ হেল্প", "❓ Help")
add("btn_home", "⬅️ মেইন মেনু", "⬅️ Main Menu")

# ============================================================ search / library
add("lib_empty", "📭 এখনো কোনো সাবটাইটেল যোগ হয়নি।", "📭 No subtitles in the library yet.")
add("lib_title", "📚 <b>আমাদের লাইব্রেরি</b>\n{D}\nযেটি লাগবে চাপ দিন 👇", "📚 <b>Our Library</b>\n{D}\nTap what you need 👇")
add("lib_row", "🎬 {title} ({n} ep)", "🎬 {title} ({n} ep)")
add("anime_card",
    "🎬 <b>{title}</b>{yr}\n{D}\n📦 মোট <b>{n}</b>টি এপিসোড{rng} · 🇧🇩 বাংলা সাবটাইটেল{note}\n\nএপিসোড বেছে নিন 👇",
    "🎬 <b>{title}</b>{yr}\n{D}\n📦 <b>{n}</b> episodes{rng} · 🇧🇩 Bangla subtitles{note}\n\nPick an episode 👇")
add("zip_btn", "📦 ফুল সিজন ZIP ⭐", "📦 Full Season ZIP ⭐")
add("fav_add_btn", "🤍 ফেভারিটে রাখুন", "🤍 Add to favorites")
add("fav_del_btn", "❤️ ফেভারিট থেকে সরান", "❤️ Remove from favorites")
add("fav_added", "❤️ ফেভারিটে যোগ হয়েছে", "❤️ Added to favorites")
add("fav_removed", "💔 ফেভারিট থেকে সরানো হয়েছে", "💔 Removed from favorites")
add("fav_title", "❤️ <b>আপনার ফেভারিট</b>\n{D}\nখুলতে চাপ দিন 👇", "❤️ <b>Your Favorites</b>\n{D}\nTap to open 👇")
add("fav_empty", "💔 কোনো ফেভারিট নেই। টাইটেল কার্ডে 🤍 চাপ দিন।", "💔 No favorites yet. Tap 🤍 on a title card.")
add("not_found", "📁 লাইব্রেরিতে পাইনি। অনলাইনে খুঁজে দেখব?", "📁 Not in the library. Search online?")
add("did_you_mean", "🤔 <b>আপনি কি এগুলো খুঁজছিলেন?</b>", "🤔 <b>Did you mean one of these?</b>")
add("online_offer", "🌐 অনলাইন থেকেও খুঁজে দেখব? ⭐", "🌐 Search online too? ⭐")
add("online_btn", "🌐 অনলাইনে খুঁজুন ⭐", "🌐 Search online ⭐")
add("req_btn", "📩 রিকুয়েস্ট করুন", "📩 Request it")
add("online_none", "🌐 অনলাইন সোর্স এখন চালু নেই।", "🌐 No online source is enabled right now.")
add("need_query", "আগে একটা মুভি/অ্যানিমের নাম লিখুন, তারপর অনলাইনে খুঁজব।", "Type a title first, then I'll search online.")
add("searching_online", "🌐 অনলাইনে খুঁজছি...", "🌐 Searching online...")
add("pick_title", "🌐 <b>কোনটি খুঁজছেন?</b>\nসঠিক টাইটেল বেছে নিন 👇", "🌐 <b>Which one?</b>\nPick the right title 👇")
add("subs_header",
    "🌐 <b>{title}</b>\n{D}\n📄 মোট {n}টি সাবটাইটেল · পাতা {p}/{pp}\nযেটি লাগবে চাপ দিন 👇",
    "🌐 <b>{title}</b>\n{D}\n📄 {n} subtitles · page {p}/{pp}\nTap the one you need 👇")
add("subs_empty", "এই ফিল্টারে কিছু নেই 😔 অন্য ভাষা দেখুন, অথবা রিকুয়েস্ট করুন:",
    "Nothing under this filter 😔 Try another language or request it:")
add("lang_bn", "🇧🇩 বাংলা", "🇧🇩 Bangla")
add("lang_en", "🇬🇧 English", "🇬🇧 English")
add("lang_all", "🌐 সব", "🌐 All")
add("prev", "⬅️ আগে", "⬅️ Prev")
add("next", "পরে ➡️", "Next ➡️")
add("online_fail", "অনলাইন সার্চ হয়নি 😔 {err}", "Online search failed 😔 {err}")
add("dl_fail", "ডাউনলোড হয়নি 😔 {err}", "Download failed 😔 {err}")
add("src_off", "সোর্সটি এখন বন্ধ আছে।", "That source is currently off.")
add("old_result", "এই রেজাল্ট পুরনো, আবার সার্চ করুন।", "This result is stale — please search again.")
add("sending", "📤 পাঠাচ্ছি...", "📤 Sending...")
add("caption_local", "🎬 {title}\n🇧🇩 বাংলা সাবটাইটেল · SubFinder", "🎬 {title}\n🇧🇩 Bangla subtitle · SubFinder")
add("caption_online", "🎬 {title}\n{lang} সাবটাইটেল · {src} · SubFinder", "🎬 {title}\n{lang} subtitle · {src} · SubFinder")
add("caption_zip", "📦 {title} — ফুল সিজন প্যাক ⭐\nSubFinder", "📦 {title} — Full Season Pack ⭐\nSubFinder")
add("caption_tool", "🎬 {title}\n🛠 {label} · SubFinder", "🎬 {title}\n🛠 {label} · SubFinder")
add("tool_expired", "টুল সেশন শেষ হয়ে গেছে — সাবটাইটেলটি আবার নিন।", "Tool session expired — fetch the subtitle again.")
add("tool_vtt", "🔄 VTT বানান", "🔄 Make VTT")
add("tool_hint", "⏱ সিঙ্ক ঠিক করুন (ফ্রি)", "⏱ Fix sync (free)")

# ============================================================ quota / gate / premium
add("quota_hit",
    "⛔ <b>আজকের ডাউনলোড লিমিট শেষ</b> ({used}/{limit})\n{D}\n"
    "🎁 বন্ধুকে ইনভাইট করে বোনাস নিন\n🎟 রিডিম কোড ব্যবহার করুন\n⭐ প্রিমিয়ামে আনলিমিটেড\n\n"
    "🔄 লিমিট আগামীকাল রিসেট হবে।",
    "⛔ <b>Daily download limit reached</b> ({used}/{limit})\n{D}\n"
    "🎁 Invite friends for bonus downloads\n🎟 Redeem a code\n⭐ Premium is unlimited\n\n"
    "🔄 Your limit resets tomorrow.")
add("gate_prompt", "⭐ এটি <b>প্রিমিয়াম ফিচার</b>! ব্যবহার করতে নিচের চ্যানেলগুলোতে জয়েন করুন 👇",
    "⭐ This is a <b>premium feature</b>! Join the channels below to unlock it 👇")
add("join_check", "✅ জয়েন করেছি, চেক করুন", "✅ I've joined — check")
add("join_ok", "✅ জয়েন কনফার্মড! এখন ব্যবহার করতে পারবেন।", "✅ Join confirmed! You're in.")
add("join_no", "এখনো সব চ্যানেলে জয়েন হয়নি", "You haven't joined all channels yet")
add("premium_locked", "🔒 অনলাইন সার্চ এখন শুধু <b>প্রিমিয়াম</b> ইউজারদের জন্য।\n🎟 কোড থাকলে /redeem করুন।",
    "🔒 Online search is <b>Premium-only</b> right now.\n🎟 Have a code? Use /redeem.")
add("premium_card",
    "⭐ <b>SubFinder প্রিমিয়াম</b>\n{D}\n🌐 অনলাইন সার্চ — যেকোনো মুভি/অ্যানিমে (বাংলা + English)\n"
    "📦 ফুল সিজন ZIP — এক ক্লিকে\n♾ আনলিমিটেড ডাউনলোড\n⚡ ক্যাশ থেকে ইনস্ট্যান্ট ডেলিভারি\n{D}\n{status}",
    "⭐ <b>SubFinder Premium</b>\n{D}\n🌐 Online search — any movie/anime (Bangla + English)\n"
    "📦 Full Season ZIP — one tap\n♾ Unlimited downloads\n⚡ Instant delivery from cache\n{D}\n{status}")
add("prem_active", "✅ আপনার প্রিমিয়াম চালু আছে — মেয়াদ: <b>{until}</b>", "✅ Premium active — valid until <b>{until}</b>")
add("prem_gate_open", "✅ চ্যানেল জয়েন করা আছে — প্রিমিয়াম ফিচার খোলা!", "✅ Channels joined — premium features unlocked!")
add("prem_gate_lock", "🔒 আনলক করতে নিচের চ্যানেলগুলোতে জয়েন করুন 👇\n🎟 অথবা কোড থাকলে /redeem",
    "🔒 Join the channels below to unlock 👇\n🎟 Or use /redeem if you have a code")
add("prem_none", "💡 কোড থাকলে /redeem — অথবা বন্ধুদের ইনভাইট করুন", "💡 Have a code? /redeem — or invite friends")
add("unlimited", "♾ আনলিমিটেড", "♾ Unlimited")

# ============================================================ profile / levels
add("profile",
    "👤 <b>{name}</b>\n{D}\n🏅 লেভেল <b>{lvl}</b> · {rank}\n{bar} {xp}/{nxt} XP\n"
    "🔥 স্ট্রিক: <b>{streak}</b> দিন\n{D}\n🔎 সার্চ: <b>{searches}</b> · 📥 ডাউনলোড: <b>{downloads}</b>\n"
    "🎁 রেফারেল: <b>{refs}</b> · 💎 বোনাস: <b>{bonus}</b>\n⭐ স্ট্যাটাস: {status}\n📥 আজকের ডাউনলোড: {quota}\n🗓 জয়েন: {since}",
    "👤 <b>{name}</b>\n{D}\n🏅 Level <b>{lvl}</b> · {rank}\n{bar} {xp}/{nxt} XP\n"
    "🔥 Streak: <b>{streak}</b> days\n{D}\n🔎 Searches: <b>{searches}</b> · 📥 Downloads: <b>{downloads}</b>\n"
    "🎁 Referrals: <b>{refs}</b> · 💎 Bonus: <b>{bonus}</b>\n⭐ Status: {status}\n📥 Today's downloads: {quota}\n🗓 Joined: {since}")
add("status_premium", "💎 প্রিমিয়াম ({until} পর্যন্ত)", "💎 Premium (until {until})")
add("status_free", "🆓 ফ্রি", "🆓 Free")
ADD_RANKS = [
    ("Rookie", "নবীন"), ("Seeker", "অন্বেষী"), ("Hunter", "শিকারি"),
    ("Navigator", "নেভিগেটর"), ("Cyber Sage", "সাইবার সেজ"), ("Quantum Lord", "কোয়ান্টাম লর্ড"),
]
add("top_title", "🏆 <b>লিডারবোর্ড</b> (XP)\n{D}\n{rows}", "🏆 <b>Leaderboard</b> (XP)\n{D}\n{rows}")
add("trend_title", "🔥 <b>ট্রেন্ডিং এখন</b>\n{D}\n{rows}\n\nনাম লিখলেই আপনিও পাবেন!", "🔥 <b>Trending now</b>\n{D}\n{rows}\n\nType a name and get yours too!")
add("trend_empty", "এখনো কেউ সার্চ করেনি।", "Nobody has searched yet.")
add("hist_title", "🕘 <b>আপনার ডাউনলোড হিস্ট্রি</b>\n{D}\nআবার পেতে চাপ দিন 👇", "🕘 <b>Your Download History</b>\n{D}\nTap to get it again 👇")
add("hist_empty", "🕘 এখনো কিছু ডাউনলোড করেননি।", "🕘 No downloads yet.")
add("hist_gone", "ফাইলটি আর নেই — আবার সার্চ করুন।", "That file is gone — search again.")

# ============================================================ invite / redeem / feedback / request
add("invite",
    "🎁 <b>ইনভাইট ও আয় করুন</b>\n{D}\nআপনার লিংক:\n<code>{link}</code>\n\n"
    "বন্ধু জয়েন করলে দুজনেই পাবেন <b>+{bonus}</b> বোনাস ডাউনলোড + XP!\n👥 এ পর্যন্ত ইনভাইট: <b>{refs}</b>",
    "🎁 <b>Invite & Earn</b>\n{D}\nYour link:\n<code>{link}</code>\n\n"
    "When a friend joins, you both get <b>+{bonus}</b> bonus downloads + XP!\n👥 Invited so far: <b>{refs}</b>")
add("ref_joined", "🎉 আপনার ইনভাইটে <b>{name}</b> জয়েন করেছেন! +{bonus} বোনাস ডাউনলোড পেলেন।",
    "🎉 <b>{name}</b> joined via your invite! You got +{bonus} bonus downloads.")
add("ref_welcome", "🎁 ইনভাইট বোনাস: +{bonus} ডাউনলোড যোগ হয়েছে!", "🎁 Invite bonus: +{bonus} downloads added!")
add("redeem_ask", "🎟 আপনার কোডটি পাঠান (বাতিল: /cancel)", "🎟 Send your code (cancel: /cancel)")
add("redeem_ok_premium", "🎉 কোড সফল! <b>{days} দিন</b> প্রিমিয়াম যোগ হলো — মেয়াদ: <b>{until}</b>",
    "🎉 Code accepted! <b>{days} days</b> of Premium added — valid until <b>{until}</b>")
add("redeem_ok_credits", "🎉 কোড সফল! <b>+{n}</b> বোনাস ডাউনলোড যোগ হলো।", "🎉 Code accepted! <b>+{n}</b> bonus downloads added.")
add("redeem_bad", "❌ কোডটি ভুল বা ব্যবহার হয়ে গেছে।", "❌ Invalid or already used code.")
add("feedback_ask", "💬 আপনার মতামত/সমস্যা লিখে পাঠান (বাতিল: /cancel)", "💬 Send your feedback or issue (cancel: /cancel)")
add("feedback_ok", "💙 ধন্যবাদ! অ্যাডমিন দেখবেন।", "💙 Thank you! The admin will see it.")
add("feedback_wait", "⏳ একটু পরে আবার ফিডব্যাক পাঠান।", "⏳ Please wait a bit before sending more feedback.")
add("req_ok", "📩 রিকুয়েস্ট জমা হয়েছে! সাবটাইটেল যোগ হলেই আপনাকে জানাব 🙏", "📩 Request saved! I'll notify you when it's added 🙏")
add("req_dup", "📩 এই রিকুয়েস্ট আগেই জমা আছে — যোগ হলে জানাব।", "📩 You've already requested this — I'll notify you.")
add("req_need", "আগে যে সাবটাইটেল চান তার <b>নাম লিখুন</b>, তারপর রিকুয়েস্ট বাটন কাজ করবে।",
    "First <b>type the title</b> you want, then the request button will work.")
add("req_done", "✅ সুখবর! আপনার রিকুয়েস্ট করা <b>{q}</b> এখন লাইব্রেরিতে আছে — নাম লিখে সার্চ করুন।",
    "✅ Good news! Your requested <b>{q}</b> is now in the library — just search for it.")
add("no_file_upload", "ফাইলের জন্য ধন্যবাদ, কিন্তু সাবটাইটেল শুধু অ্যাডমিন যোগ করতে পারেন। নাম লিখে সার্চ করুন!",
    "Thanks for the file, but only admins can add subtitles. Just type a name to search!")

# ============================================================ settings
add("settings",
    "⚙️ <b>সেটিংস</b>\n{D}\n🌐 ভাষা: <b>{lang}</b>\n🔔 নোটিফিকেশন: <b>{notif}</b>",
    "⚙️ <b>Settings</b>\n{D}\n🌐 Language: <b>{lang}</b>\n🔔 Notifications: <b>{notif}</b>")
add("on", "চালু", "ON")
add("off", "বন্ধ", "OFF")
add("set_lang", "🌐 ভাষা বদলান", "🌐 Change language")
add("set_notif", "🔔 নোটিফিকেশন: {state}", "🔔 Notifications: {state}")
add("set_clear_hist", "🗑 হিস্ট্রি মুছুন", "🗑 Clear history")
add("hist_cleared", "🗑 হিস্ট্রি মুছে ফেলা হয়েছে।", "🗑 History cleared.")

# ============================================================ admin panel
add("a_denied", "এটি শুধু অ্যাডমিনের জন্য", "Admins only")
add("a_owner", "এটি শুধু ওনারের জন্য", "Owner only")
add("a_dash",
    "🛰 <b>SUBFINDER · CONTROL CENTER</b>\n{D}\n"
    "👥 ইউজার <b>{users}</b> (আজ +{new}) · 🟢 আজ অ্যাকটিভ <b>{active}</b>\n"
    "🔎 আজকের সার্চ <b>{s}</b> · 📥 ডাউনলোড <b>{d}</b>\n"
    "⭐ প্রিমিয়াম <b>{prem}</b> · 🚫 ব্যান <b>{ban}</b>\n"
    "📩 পেন্ডিং রিকুয়েস্ট <b>{pr}</b> · 📚 লাইব্রেরি <b>{titles}</b> টাইটেল / <b>{eps}</b> ep\n"
    "🔌 সোর্স <b>{src}</b> · 🚪 গেট <b>{gate}</b> · 🛠 মেইনটেন্যান্স <b>{maint}</b>\n"
    "⏱ আপটাইম <b>{up}</b>",
    "🛰 <b>SUBFINDER · CONTROL CENTER</b>\n{D}\n"
    "👥 Users <b>{users}</b> (+{new} today) · 🟢 Active today <b>{active}</b>\n"
    "🔎 Searches today <b>{s}</b> · 📥 Downloads <b>{d}</b>\n"
    "⭐ Premium <b>{prem}</b> · 🚫 Banned <b>{ban}</b>\n"
    "📩 Pending requests <b>{pr}</b> · 📚 Library <b>{titles}</b> titles / <b>{eps}</b> ep\n"
    "🔌 Sources <b>{src}</b> · 🚪 Gate <b>{gate}</b> · 🛠 Maintenance <b>{maint}</b>\n"
    "⏱ Uptime <b>{up}</b>")
add("a_b_stats", "📈 অ্যানালিটিক্স", "📈 Analytics")
add("a_b_users", "👥 ইউজার", "👥 Users")
add("a_b_bc", "📣 ব্রডকাস্ট", "📣 Broadcast")
add("a_b_codes", "🎟 কোড", "🎟 Codes")
add("a_b_lib", "📚 লাইব্রেরি", "📚 Library")
add("a_b_reqs", "📩 রিকুয়েস্ট", "📩 Requests")
add("a_b_src", "🔌 API সোর্স", "🔌 API Sources")
add("a_b_ch", "📢 চ্যানেল", "📢 Channels")
add("a_b_cfg", "⚙️ সেটিংস", "⚙️ Settings")
add("a_b_admins", "🛡 অ্যাডমিন", "🛡 Admins")
add("a_b_backup", "💾 ব্যাকআপ", "💾 Backup")
add("a_b_refresh", "🔄 রিফ্রেশ", "🔄 Refresh")
add("a_b_back", "⬅️ প্যানেল", "⬅️ Panel")
add("a_analytics", "📈 <b>অ্যানালিটিক্স</b> (শেষ ৭ দিন)\n{D}\n{rows}\n\n🔥 <b>টপ সার্চ</b>\n{top}\n\n📥 <b>টপ ডাউনলোড</b>\n{dl}",
    "📈 <b>Analytics</b> (last 7 days)\n{D}\n{rows}\n\n🔥 <b>Top searches</b>\n{top}\n\n📥 <b>Top downloads</b>\n{dl}")
add("a_none", "—", "—")
add("a_users_menu", "👥 <b>ইউজার ম্যানেজমেন্ট</b>\n{D}\nমোট: <b>{n}</b>", "👥 <b>User Management</b>\n{D}\nTotal: <b>{n}</b>")
add("a_u_find", "🔎 আইডি দিয়ে খুঁজুন", "🔎 Find by ID")
add("a_u_recent", "🆕 নতুন ইউজার", "🆕 Newest users")
add("a_u_prem", "⭐ প্রিমিয়াম ইউজার", "⭐ Premium users")
add("a_u_ban", "🚫 ব্যান লিস্ট", "🚫 Banned list")
add("a_u_top", "🏆 টপ XP", "🏆 Top XP")
add("a_u_ask", "🆔 ইউজারের Telegram ID পাঠান (বাতিল: /cancel)", "🆔 Send the user's Telegram ID (cancel: /cancel)")
add("a_u_none", "ইউজার পাওয়া যায়নি।", "User not found.")
add("a_u_empty", "লিস্ট খালি।", "List is empty.")
add("a_ucard",
    "👤 <b>{name}</b> {uname}\n🆔 <code>{uid}</code> · 🌐 {lang}\n{D}\n"
    "🏅 Lv {lvl} · {xp} XP · 🔎 {searches} · 📥 {downloads}\n"
    "⭐ {status}\n💎 বোনাস: {bonus} · 🎁 রেফারেল: {refs}\n🚫 ব্যান: {banned}\n🗓 জয়েন {since} · শেষ দেখা {last}",
    "👤 <b>{name}</b> {uname}\n🆔 <code>{uid}</code> · 🌐 {lang}\n{D}\n"
    "🏅 Lv {lvl} · {xp} XP · 🔎 {searches} · 📥 {downloads}\n"
    "⭐ {status}\n💎 Bonus: {bonus} · 🎁 Referrals: {refs}\n🚫 Banned: {banned}\n🗓 Joined {since} · Last seen {last}")
add("a_ban", "🚫 ব্যান", "🚫 Ban")
add("a_unban", "✅ আনব্যান", "✅ Unban")
add("a_revoke", "❌ প্রিমিয়াম বাতিল", "❌ Revoke Premium")
add("a_credits", "💎 বোনাস দিন", "💎 Give credits")
add("a_dm", "✉️ মেসেজ", "✉️ Message")
add("a_done", "হয়ে গেছে ✅", "Done ✅")
add("a_ask_credits", "💎 কতগুলো বোনাস ডাউনলোড দেবেন? (সংখ্যা পাঠান)", "💎 How many bonus downloads? (send a number)")
add("a_ask_dm", "✉️ ইউজারকে যা পাঠাতে চান লিখুন:", "✉️ Type the message to send to the user:")
add("a_dm_sent", "✉️ পাঠানো হয়েছে।", "✉️ Sent.")
add("a_dm_fail", "পাঠানো যায়নি (ইউজার বট ব্লক করেছে?)", "Couldn't send (user blocked the bot?)")
add("a_user_prem_msg", "🎉 অ্যাডমিন আপনাকে <b>{days} দিন</b> প্রিমিয়াম দিয়েছেন! মেয়াদ: <b>{until}</b>",
    "🎉 The admin gifted you <b>{days} days</b> of Premium! Valid until <b>{until}</b>")
add("a_user_credit_msg", "🎁 অ্যাডমিন আপনাকে <b>+{n}</b> বোনাস ডাউনলোড দিয়েছেন!", "🎁 The admin gave you <b>+{n}</b> bonus downloads!")
add("a_bc_menu", "📣 <b>ব্রডকাস্ট</b>\n{D}\nকাদের পাঠাবেন?", "📣 <b>Broadcast</b>\n{D}\nWho should receive it?")
add("a_bc_all", "👥 সবাই ({n})", "👥 Everyone ({n})")
add("a_bc_prem", "⭐ প্রিমিয়াম ({n})", "⭐ Premium ({n})")
add("a_bc_free", "🆓 ফ্রি ({n})", "🆓 Free ({n})")
add("a_bc_bn", "🇧🇩 বাংলা ইউজার ({n})", "🇧🇩 Bangla users ({n})")
add("a_bc_en", "🇬🇧 English ইউজার ({n})", "🇬🇧 English users ({n})")
add("a_bc_ask", "📝 যে মেসেজটি পাঠাতে চান সেটি এখানে পাঠান (টেক্সট/ছবি/ভিডিও — যেকোনো কিছু)।\nবাতিল: /cancel",
    "📝 Send the message you want to broadcast (text/photo/video — anything).\nCancel: /cancel")
add("a_bc_preview", "👆 প্রিভিউ — <b>{n}</b> জনকে পাঠানো হবে। নিশ্চিত?", "👆 Preview — will be sent to <b>{n}</b> users. Confirm?")
add("a_bc_go", "🚀 পাঠান", "🚀 Send")
add("a_bc_no", "❌ বাতিল", "❌ Cancel")
add("a_bc_run", "🚀 ব্রডকাস্ট শুরু হলো...", "🚀 Broadcast started...")
add("a_bc_done", "📣 <b>ব্রডকাস্ট শেষ</b>\n✅ সফল: {ok}\n⚠️ ব্যর্থ: {fail}", "📣 <b>Broadcast finished</b>\n✅ Delivered: {ok}\n⚠️ Failed: {fail}")
add("a_codes_menu", "🎟 <b>রিডিম কোড</b>\n{D}\nবাকি (অব্যবহৃত) কোড: <b>{n}</b>", "🎟 <b>Redeem Codes</b>\n{D}\nUnused codes: <b>{n}</b>")
add("a_code_new", "➕ নতুন কোড বানান", "➕ Generate codes")
add("a_code_list", "📋 অব্যবহৃত কোড", "📋 Unused codes")
add("a_code_kind", "কোডে কী থাকবে?", "What should the codes give?")
add("a_code_k_prem", "⭐ প্রিমিয়াম দিন", "⭐ Premium days")
add("a_code_k_cred", "💎 বোনাস ডাউনলোড", "💎 Bonus downloads")
add("a_code_val", "কত {unit}? (সংখ্যা পাঠান)", "How many {unit}? (send a number)")
add("a_code_cnt", "কতগুলো কোড বানাবেন? (১–৫০, সংখ্যা পাঠান)", "How many codes? (1–50, send a number)")
add("a_code_made", "✅ {n}টি কোড তৈরি ({what}):\n\n{codes}", "✅ {n} codes created ({what}):\n\n{codes}")
add("a_code_unused", "📋 <b>অব্যবহৃত কোড</b>\n\n{codes}", "📋 <b>Unused codes</b>\n\n{codes}")
add("a_num_bad", "⚠️ শুধু সংখ্যা পাঠান।", "⚠️ Please send a number.")
add("a_lib", "📚 <b>লাইব্রেরি ম্যানেজার</b>\n{D}\n{n} টাইটেল · {eps} ep · ক্যাশ {cache} ফাইল", "📚 <b>Library Manager</b>\n{D}\n{n} titles · {eps} ep · cache {cache} files")
add("a_lib_add", "➕ সাবটাইটেল যোগ", "➕ Add subtitles")
add("a_lib_cache", "🧹 ক্যাশ পরিষ্কার", "🧹 Clear cache")
add("a_lib_cleared", "🧹 ক্যাশ পরিষ্কার হয়েছে ({n} ফাইল)", "🧹 Cache cleared ({n} files)")
add("a_lib_del_ask", "🗑 <b>{title}</b> মুছে ফেলবেন?", "🗑 Delete <b>{title}</b>?")
add("a_lib_deleted", "🗑 <b>{title}</b> মুছে ফেলা হয়েছে।", "🗑 <b>{title}</b> deleted.")
add("a_yes", "✅ হ্যাঁ", "✅ Yes")
add("a_no", "❌ না", "❌ No")
add("a_add_title", "📥 মুভি/অ্যানিমের <b>টাইটেল</b> লিখুন (বছর সহ: <code>Title | 2024</code>)।\nবাতিল: /cancel",
    "📥 Type the <b>title</b> (with year: <code>Title | 2024</code>).\nCancel: /cancel")
add("a_add_files", "টাইটেল: <b>{title}</b>\nএখন .srt ফাইলগুলো পাঠান (একটা একটা করে, অথবা zip)। শেষ হলে /done",
    "Title: <b>{title}</b>\nNow send the .srt files (one by one, or a zip). Send /done when finished.")
add("a_add_ok", "✅ <b>{title}</b> এ {n}টি সাবটাইটেল যোগ হলো। আরও পাঠান, নাহলে /done",
    "✅ Added {n} subtitle(s) to <b>{title}</b>. Send more, or /done")
add("a_add_done", "✅ সম্পন্ন! মোট {n}টি সাবটাইটেল যোগ হলো। 📩 রিকুয়েস্ট মিলেছে: {m}", "✅ Done! {n} subtitle(s) added. 📩 Requests fulfilled: {m}")
add("a_add_notitle", "ফাইল পেলাম কিন্তু টাইটেল বুঝিনি। /addsub দিয়ে শুরু করুন, অথবা ক্যাপশনে টাইটেল দিন।",
    "Got the file but no title. Start with /addsub or put the title in the caption.")
add("a_add_dlfail", "ফাইল ডাউনলোড করা যায়নি 😔", "Couldn't download the file 😔")
add("a_add_zipfail", "Zip খোলা যায়নি 😔 ({e})", "Couldn't open the zip 😔 ({e})")
add("a_reqs", "📩 <b>পেন্ডিং রিকুয়েস্ট</b> ({n})\n{D}\nখুলতে চাপ দিন 👇", "📩 <b>Pending requests</b> ({n})\n{D}\nTap to open 👇")
add("a_reqs_none", "📩 কোনো পেন্ডিং রিকুয়েস্ট নেই 🎉", "📩 No pending requests 🎉")
add("a_req_card", "📩 <b>রিকুয়েস্ট #{id}</b>\n{D}\n🎬 <b>{q}</b>\n👤 {name} (<code>{uid}</code>)\n🕒 {ts}",
    "📩 <b>Request #{id}</b>\n{D}\n🎬 <b>{q}</b>\n👤 {name} (<code>{uid}</code>)\n🕒 {ts}")
add("a_req_done_btn", "✅ হয়েছে + ইউজারকে জানান", "✅ Done + notify user")
add("a_req_del_btn", "🗑 মুছুন", "🗑 Delete")
add("a_req_new", "📩 <b>নতুন রিকুয়েস্ট</b>: {q}\n👤 {name} (<code>{uid}</code>)", "📩 <b>New request</b>: {q}\n👤 {name} (<code>{uid}</code>)")
add("a_src", "🔌 <b>API সোর্স</b>\n{D}\n{rows}", "🔌 <b>API Sources</b>\n{D}\n{rows}")
add("a_src_none", "কোনো সোর্স নেই — নিচ থেকে যোগ করুন।", "No sources yet — add one below.")
add("a_src_add", "➕ সোর্স যোগ", "➕ Add source")
add("a_src_pick", "🔌 কোন সাইটের API যোগ করবেন?", "🔌 Which API do you want to add?")
add("a_src_name", "🔌 {t} সোর্স। একটি <b>নাম</b> দিন (যেমন: main, backup):", "🔌 {t} source. Give it a <b>name</b> (e.g. main, backup):")
add("a_src_key", "API key পাঠান:", "Send the API key:")
add("a_src_user", "OpenSubtitles username পাঠান:", "Send the OpenSubtitles username:")
add("a_src_pass", "OpenSubtitles password পাঠান:", "Send the OpenSubtitles password:")
add("a_src_ok", "✅ সোর্স যোগ হলো: <b>{name}</b> ({t})", "✅ Source added: <b>{name}</b> ({t})")
add("a_ch", "📢 <b>গেট চ্যানেল</b>\n{D}\n{rows}", "📢 <b>Gate Channels</b>\n{D}\n{rows}")
add("a_ch_none", "কোনো চ্যানেল নেই।", "No channels.")
add("a_ch_add", "➕ চ্যানেল যোগ", "➕ Add channel")
add("a_ch_ask", "📢 চ্যানেলের @username বা t.me লিংক পাঠান:", "📢 Send the channel @username or t.me link:")
add("a_ch_ok", "✅ চ্যানেল যোগ হলো: {ch}", "✅ Channel added: {ch}")
add("a_ch_warn", "⚠️ বটকে এই চ্যানেলে <b>অ্যাডমিন</b> বানাতে হবে, নাহলে জয়েন চেক কাজ করবে না।",
    "⚠️ Make the bot an <b>admin</b> of this channel, otherwise join-checks won't work.")
add("a_ch_bad", "চ্যানেলটি পাওয়া যায়নি। @username ঠিক আছে?", "Channel not found. Is the @username correct?")
add("a_ch_invite",
    "❌ <b>Invite link</b> দিয়ে হবে না — জয়েন চেকের জন্য চ্যানেলের <b>@username</b> লাগে।\n"
    "চ্যানেলের Settings থেকে public username সেট করে সেই @username টা এখানে পাঠাও।\n"
    "আর বটকে চ্যানেলে <b>অ্যাডমিন</b> বানিয়ে দিও।",
    "❌ An <b>invite link</b> won't work — the join check needs the channel's <b>@username</b>.\n"
    "Set a public username in the channel's settings and send that @username here.\n"
    "Also make the bot an <b>admin</b> in the channel.")
add("search_hint",
    "🔍 Search করতে নিচের <b>🔍 Search</b> button চাপ দিয়ে movie/anime এর নাম লিখো",
    "🔍 To search, tap the <b>🔍 Search</b> button below and type the movie/anime name")
add("a_cfg",
    "⚙️ <b>বট সেটিংস</b>\n{D}\n📥 ফ্রি ডেইলি লিমিট: <b>{limit}</b>\n🎁 রেফারেল বোনাস: <b>{ref}</b>\n"
    "🛠 মেইনটেন্যান্স: <b>{maint}</b>\n🔒 অনলাইন শুধু প্রিমিয়াম: <b>{onl}</b>\n"
    "🚪 জয়েন গেট: <b>{gate}</b>\n🔐 গেট লেভেল: <b>{glevel}</b>",
    "⚙️ <b>Bot Settings</b>\n{D}\n📥 Free daily limit: <b>{limit}</b>\n🎁 Referral bonus: <b>{ref}</b>\n"
    "🛠 Maintenance: <b>{maint}</b>\n🔒 Online = Premium only: <b>{onl}</b>\n"
    "🚪 Join gate: <b>{gate}</b>\n🔐 Gate level: <b>{glevel}</b>")
add("a_cfg_limit", "📥 ডেইলি লিমিট বদলান", "📥 Set daily limit")
add("a_cfg_ref", "🎁 রেফারেল বোনাস বদলান", "🎁 Set referral bonus")
add("a_cfg_maint", "🛠 মেইনটেন্যান্স টগল", "🛠 Toggle maintenance")
add("a_cfg_onl", "🔒 অনলাইন প্রিমিয়াম-অনলি টগল", "🔒 Toggle online premium-only")
add("a_cfg_gate", "🚪 জয়েন গেট টগল", "🚪 Toggle join gate")
add("a_cfg_glevel", "🔐 গেট লেভেল টগল", "🔐 Toggle gate level")
add("a_cfg_num", "নতুন মান পাঠান (সংখ্যা, 0 = আনলিমিটেড/নেই):", "Send the new value (number, 0 = unlimited/none):")
add("a_gl_all", "সব ডাউনলোড", "All downloads")
add("a_gl_prem", "শুধু প্রিমিয়াম ফিচার", "Premium features only")
add("a_admins", "🛡 <b>অ্যাডমিন লিস্ট</b>\n{D}\n👑 ওনার: <code>{owner}</code>\n{rows}", "🛡 <b>Admins</b>\n{D}\n👑 Owner: <code>{owner}</code>\n{rows}")
add("a_adm_add", "➕ অ্যাডমিন যোগ", "➕ Add admin")
add("a_adm_ask", "🆔 নতুন অ্যাডমিনের Telegram ID পাঠান:", "🆔 Send the new admin's Telegram ID:")
add("a_adm_ok", "✅ অ্যাডমিন যোগ হলো: {uid}", "✅ Admin added: {uid}")
add("a_backup_cap", "💾 SubFinder ব্যাকআপ · {ts}", "💾 SubFinder backup · {ts}")
add("a_users_csv", "📄 ইউজার এক্সপোর্ট", "📄 Users export")
add("a_feedback", "💬 <b>ফিডব্যাক</b> — {name} (<code>{uid}</code>)\n{D}\n{text}", "💬 <b>Feedback</b> — {name} (<code>{uid}</code>)\n{D}\n{text}")
add("a_not_set", "⚠️ <b>admin_id সেট করা নেই।</b> config.json এ আপনার ID বসান (বটে /id লিখে পাবেন)।",
    "⚠️ <b>admin_id is not set.</b> Put your ID in config.json (send /id to the bot).")
