import os
import asyncio
import aiohttp
import json
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
GEMINI_KEY     = os.environ.get("GEMINI_KEY", "")
KIE_KEY        = os.environ.get("KIE_KEY", "")

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
KIE_CREATE = "https://api.kie.ai/api/v1/jobs/createTask"
KIE_QUERY  = "https://api.kie.ai/api/v1/jobs/queryTask"

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

async def generate_content(before: str, after: str) -> dict:
    prompt = f"""TikTok viral expert. TRANSFORMATION: "{before}" to "{after}".
Generate JSON only, no markdown:
{{"hook":"ultra-viral French hook max 15 words","video_prompt":"cinematic English AI video prompt 100 words vertical 9:16 TikTok before after transformation dramatic reveal","description":"French TikTok caption 100 words emojis storytelling CTA","hashtags":"#beforeafter #transformation #IA #viral #fyp #tiktok #beforeandafter #glow #amazing #ai #incredible #change #lifestyle #wow #beauty #glowup #makeover #stunning #mindblowing #aiart","audio_tip":"trending sound type","best_time":"18h-21h","viral_score":"8"}}"""
    async with aiohttp.ClientSession() as session:
        async with session.post(GEMINI_URL, json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.9, "maxOutputTokens": 800}
        }) as r:
            data = await r.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            text = text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)

async def create_video(prompt: str) -> str:
    headers = {"Authorization": f"Bearer {KIE_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "kling-2.1/text-to-video",
        "input": {
            "prompt": prompt,
            "negative_prompt": "blurry, low quality, distorted",
            "cfg_scale": 0.5,
            "mode": "std",
            "duration": "5",
            "aspect_ratio": "9:16"
        }
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(KIE_CREATE, headers=headers, json=payload) as r:
            text = await r.text()
            print(f"KIE CREATE [{r.status}]: {text[:300]}")
            data = json.loads(text)
            if data.get("code") == 200:
                return data["data"]["task_id"]
            raise Exception(f"KIE ERROR {data.get('code')}: {data.get('message','')}")

async def get_video(task_id: str) -> str:
    headers = {"Authorization": f"Bearer {KIE_KEY}"}
    for i in range(60):
        await asyncio.sleep(5)
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{KIE_QUERY}?task_id={task_id}", headers=headers) as r:
                data = await r.json()
                task = data.get("data", {})
                status = task.get("task_status", "")
                print(f"KIE STATUS [{i}]: {status}")
                if status == "succeed":
                    works = task.get("works", [])
                    if works:
                        return works[0].get("resource", {}).get("resource", "")
                    raise Exception("No URL in response")
                elif status == "failed":
                    raise Exception(f"Failed: {task}")
    raise Exception("Timeout 5min")

def fmt(content: dict, before: str, after: str, idx: int) -> str:
    now = datetime.now().strftime("%H:%M")
    h = content.get('hook','Cette transformation va te choquer!').replace('*','').replace('_','').replace('`','')
    desc = content.get('description','').replace('*','').replace('_','').replace('`','')
    tags = content.get('hashtags','#beforeafter #transformation #viral #fyp')
    audio = content.get('audio_tip','Son dramatique tendance')
    time = content.get('best_time','18h-21h')
    score = content.get('viral_score','8')
    return f"""🎬 VIDÉO #{idx} — BEFORE/AFTER IA
━━━━━━━━━━━━━━━━━━━━━━

🔄 Transformation:
❌ Avant: {before}
✅ Après: {after}

⚡ HOOK: {h}

📝 DESCRIPTION:
{desc}

{tags}

🎵 Son: {audio}
⏰ Poster à: {time}
🔥 Score viral: {score}/10

━━━━━━━━━━━━━━━━━━━━━━
Généré à {now}"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("🎬 Générer 1 Vidéo", callback_data="gen_1")],
        [InlineKeyboardButton("🚀 Pack 2 Vidéos du Jour", callback_data="gen_2")],
        [InlineKeyboardButton("💥 Pack 5 Vidéos", callback_data="gen_5")],
    ]
    await update.message.reply_text(
        "🎯 TikTok Before/After AI Bot\n\n✅ Trouve idée virale\n✅ Génère vidéo IA\n✅ Description + hashtags\n\nChoisis une option 👇",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def run(update: Update, context: ContextTypes.DEFAULT_TYPE, count: int):
    msg = update.message or update.callback_query.message
    sm = await msg.reply_text(f"⚙️ Génération {count} vidéo(s)... ~2-3 min chacune")
    ideas = random.sample(BEFORE_AFTER_IDEAS, min(count, len(BEFORE_AFTER_IDEAS)))
    content = {}
    for i, (before, after) in enumerate(ideas, 1):
        try:
            await sm.edit_text(f"🤖 Vidéo {i}/{count}: Gemini crée le script...")
            content = await generate_content(before, after)
            vp = content.get("video_prompt", f"Cinematic before after transformation: {before} transforms into {after}. Dramatic slow reveal, smooth transition, vertical 9:16 TikTok format, high quality.")
            await sm.edit_text(f"🎬 Vidéo {i}/{count}: Kie.ai génère la vidéo... ⏳")
            task_id = await create_video(vp)
            await sm.edit_text(f"⏳ Vidéo {i}/{count}: Rendu en cours (~2 min)...")
            video_url = await get_video(task_id)
            caption = fmt(content, before, after, i)
            kb = [[InlineKeyboardButton("⬇️ Télécharger", url=video_url), InlineKeyboardButton("🔄 Autre", callback_data="gen_1")]]
            await msg.reply_video(video=video_url, caption=caption, reply_markup=InlineKeyboardMarkup(kb))
        except Exception as e:
            print(f"ERR {i}: {e}")
            caption = fmt(content, before, after, i)
            await msg.reply_text(f"⚠️ Erreur vidéo: {str(e)[:150]}\n\n{caption}")
    await sm.edit_text(f"✅ {count} vidéo(s) traitée(s)! 📲 Poste sur TikTok!")

async def video_cmd(u, c): await run(u, c, 1)
async def pack_cmd(u, c): await run(u, c, 2)
async def more_cmd(u, c):
    count = min(int(c.args[0]) if c.args and c.args[0].isdigit() else 1, 10)
    await run(u, c, count)

async def btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    counts = {"gen_1":1,"gen_2":2,"gen_5":5}
    if q.data in counts:
        await run(update, context, counts[q.data])

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("video", video_cmd))
    app.add_handler(CommandHandler("pack", pack_cmd))
    app.add_handler(CommandHandler("more", more_cmd))
    app.add_handler(CallbackQueryHandler(btn))
    print("🤖 Bot started!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
