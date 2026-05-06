import os
import asyncio
import aiohttp
import json
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

# ─── CONFIG ───────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
GEMINI_KEY     = os.environ.get("GEMINI_KEY", "")
KIE_KEY        = os.environ.get("KIE_KEY", "")

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
KIE_CREATE = "https://api.kie.ai/api/v1/jobs/createTask"
KIE_QUERY  = "https://api.kie.ai/api/v1/jobs/queryTask"

# ─── BEFORE/AFTER IDEAS ───────────────────────────────────
BEFORE_AFTER_IDEAS = [
    ("Tired face with dark circles and dull skin", "Glowing face with perfect skin and radiant eyes"),
    ("Messy bedroom with clothes everywhere", "Luxury minimalist bedroom, clean and elegant"),
    ("Damaged dry lifeless hair", "Shiny thick perfect hairstyle"),
    ("Disorganized desk with papers everywhere", "Modern clean productive workspace setup"),
    ("Basic outfit neglected look", "Stylish elegant full fashion transformation"),
    ("Skin with acne and scars", "Smooth flawless perfect skin"),
    ("Yellow misaligned teeth", "Perfect white bright smile"),
    ("Before gym body transformation", "Athletic fit body after 90 days"),
    ("Empty sad apartment", "Decorated cozy modern apartment"),
    ("Blurry badly lit portrait", "Professional studio light perfect portrait"),
    ("Old dark kitchen", "Modern white bright kitchen"),
    ("Abandoned garden with weeds", "Perfect garden with flowers green lawn"),
    ("Tired face without makeup", "Professional glam makeup total transformation"),
    ("Dirty damaged car", "Clean detailed like new car"),
    ("Curved posture overweight body", "Straight posture confident fit body"),
]

# ─── GEMINI CONTENT ───────────────────────────────────────
async def generate_content(before: str, after: str) -> dict:
    prompt = f"""You are a TikTok viral expert for Before/After AI transformation niche.

TRANSFORMATION: "{before}" → "{after}"

Generate complete TikTok content as strict JSON only:

{{
  "hook": "ultra-viral hook 0-3s (max 15 words, emotional shock, in French)",
  "video_prompt": "detailed cinematic English prompt for AI video: describe the visual transformation, cinematic style, lighting, colors, camera movement, 9:16 vertical TikTok format. Max 150 words.",
  "description": "complete TikTok caption in French with emojis (100-150 words), emotional storytelling, strong call to action",
  "hashtags": "#beforeafter #transformation #IA #viral #fyp #tiktok #beforeandafter #glow #amazing #ai #artificialintelligence #incredible #change #lifestyle #wow #beauty #glowup #makeover #stunning #mindblowing",
  "audio_tip": "trending sound recommendation",
  "best_time": "best posting time today",
  "viral_score": "8"
}}

Respond ONLY with the JSON, nothing else."""

    async with aiohttp.ClientSession() as session:
        async with session.post(GEMINI_URL, json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.9, "maxOutputTokens": 1000}
        }) as r:
            data = await r.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            text = text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)

# ─── KIE.AI VIDEO ─────────────────────────────────────────
async def create_video_task(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {KIE_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "kling-2.1/text-to-video",
        "input": {
            "prompt": prompt,
            "negative_prompt": "blurry, low quality, distorted",
            "duration": "5",
            "aspect_ratio": "9:16"
        }
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(KIE_CREATE, headers=headers, json=payload) as r:
            text = await r.text()
            print(f"KIE CREATE STATUS: {r.status}")
            print(f"KIE CREATE BODY: {text[:500]}")
            data = json.loads(text)
            if data.get("code") == 200:
                task_id = data["data"]["task_id"]
                print(f"KIE TASK ID: {task_id}")
                return task_id
            raise Exception(f"Kie error {data.get('code')}: {data.get('message', text[:200])}")

async def get_video_url(task_id: str) -> str:
    headers = {"Authorization": f"Bearer {KIE_KEY}"}
    for attempt in range(60):
        await asyncio.sleep(5)
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{KIE_QUERY}?task_id={task_id}", headers=headers) as r:
                data = await r.json()
                task_data = data.get("data", {})
                status = task_data.get("task_status", "unknown")
                print(f"KIE STATUS [{attempt}]: {status}")
                if status == "succeed":
                    works = task_data.get("works", [])
                    if works:
                        url = works[0].get("resource", {}).get("resource", "")
                        print(f"KIE VIDEO URL: {url}")
                        return url
                    raise Exception("No video URL in response")
                elif status == "failed":
                    raise Exception(f"Generation failed: {task_data}")
    raise Exception("Timeout after 5 minutes")

# ─── FORMAT ───────────────────────────────────────────────
def format_message(content: dict, before: str, after: str, idx: int) -> str:
    now = datetime.now().strftime("%H:%M")
    return f"""🎬 *VIDÉO #{idx} — BEFORE/AFTER IA*
━━━━━━━━━━━━━━━━━━━━━━

🔄 *Transformation:*
❌ Avant: {before}
✅ Après: {after}

⚡ *HOOK (0\-3s):*
_{content.get('hook', 'Cette transformation va te choquer 😱')}_

📝 *DESCRIPTION:*
{content.get('description', '')}

{content.get('hashtags', '#beforeafter #transformation #IA #viral #fyp')}

🎵 *Son:* {content.get('audio_tip', 'Son dramatique tendance')}
⏰ *Poster à:* {content.get('best_time', '18h-21h')}
🔥 *Score viral:* {content.get('viral_score', '8')}/10

━━━━━━━━━━━━━━━━━━━━━━
_Généré à {now}_"""

# ─── HANDLERS ─────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎬 Générer 1 Vidéo", callback_data="gen_1")],
        [InlineKeyboardButton("🚀 Pack 2 Vidéos du Jour", callback_data="gen_2")],
        [InlineKeyboardButton("💥 Pack 5 Vidéos", callback_data="gen_5")],
        [InlineKeyboardButton("ℹ️ Comment ça marche", callback_data="help")],
    ]
    await update.message.reply_text(
        """🎯 *TikTok Before/After AI Bot*
━━━━━━━━━━━━━━━━━━━━━━

Bienvenue\! Je génère automatiquement tes vidéos TikTok virales\.

*Ta niche:* 🔄 Transformation Before/After IA

*Ce que je fais:*
✅ Trouve l'idée virale du jour
✅ Génère la vidéo IA \(Kling 2\.1\)
✅ Description \+ 20 hashtags viraux
✅ Meilleur moment pour poster

*Coût:* \~0\.13$ par vidéo 5s

━━━━━━━━━━━━━━━━━━━━━━
Choisis une option 👇""",
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def generate_videos(update: Update, context: ContextTypes.DEFAULT_TYPE, count: int = 1):
    msg = update.message or update.callback_query.message
    status_msg = await msg.reply_text(
        f"⚙️ Génération de {count} vidéo(s) en cours...\n⏳ ~2-3 minutes par vidéo"
    )
    ideas = random.sample(BEFORE_AFTER_IDEAS, min(count, len(BEFORE_AFTER_IDEAS)))

    for i, (before, after) in enumerate(ideas, 1):
        try:
            await status_msg.edit_text(f"🤖 Vidéo {i}/{count}: Gemini génère le script...")
            content = await generate_content(before, after)

            await status_msg.edit_text(f"🎬 Vidéo {i}/{count}: Kie.ai génère la vidéo...\n⏳ 2-3 minutes...")
            task_id = await create_video_task(content.get("video_prompt", f"Cinematic before and after transformation: {before} transforms into {after}. Dramatic reveal, smooth transition, vertical 9:16 TikTok format."))
            video_url = await get_video_url(task_id)

            caption = format_message(content, before, after, i)
            keyboard = [[
                InlineKeyboardButton("⬇️ Télécharger", url=video_url),
                InlineKeyboardButton("🔄 Nouvelle vidéo", callback_data="gen_1")
            ]]
            await msg.reply_video(
                video=video_url,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as e:
            print(f"ERROR video {i}: {e}")
            content = content if 'content' in locals() else {}
            await msg.reply_text(
                f"⚠️ *Vidéo {i} — Erreur:* `{str(e)[:100]}`\n\n"
                f"📝 Contenu généré:\n"
                f"❌ Avant: {before}\n✅ Après: {after}\n\n"
                f"⚡ Hook: {content.get('hook', 'Cette transformation va te choquer!')}\n\n"
                f"{content.get('hashtags', '#beforeafter #transformation #viral')}",
                parse_mode=ParseMode.MARKDOWN
            )

    await status_msg.edit_text(
        f"✅ {count} vidéo(s) traitée(s)!\n📲 Télécharge et poste sur TikTok!"
    )

async def video_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await generate_videos(update, context, 1)

async def pack_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await generate_videos(update, context, 2)

async def more_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    count = min(int(args[0]) if args and args[0].isdigit() else 1, 10)
    await generate_videos(update, context, count)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "gen_1":
        await generate_videos(update, context, 1)
    elif query.data == "gen_2":
        await generate_videos(update, context, 2)
    elif query.data == "gen_5":
        await generate_videos(update, context, 5)
    elif query.data == "help":
        await query.message.reply_text(
            "ℹ️ *Commandes:*\n/video — 1 vidéo\n/pack — 2 vidéos\n/more 5 — 5 vidéos\n\n"
            "*Workflow:*\n🌅 Matin → /video → Poste\n🌆 Soir → /video → Poste",
            parse_mode=ParseMode.MARKDOWN
        )

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("video", video_command))
    app.add_handler(CommandHandler("pack", pack_command))
    app.add_handler(CommandHandler("more", more_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("🤖 Bot démarré!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
