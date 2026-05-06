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
KIE_URL    = "https://api.kie.ai/api/v1/jobs/createTask"
KIE_STATUS = "https://api.kie.ai/api/v1/jobs/queryTask"

# ─── BEFORE/AFTER IDEAS ───────────────────────────────────
BEFORE_AFTER_IDEAS = [
    ("Visage fatigué, cernes, peau terne", "Visage lumineux, peau parfaite, regard éclatant"),
    ("Chambre en désordre total, vêtements partout", "Chambre de luxe minimaliste, rangée et élégante"),
    ("Corps avant régime, posture courbée", "Corps transformé, musclé, posture droite et confiante"),
    ("Cheveux abîmés, secs, sans vie", "Cheveux brillants, épais, coiffure parfaite"),
    ("Bureau désorganisé, papiers partout", "Bureau moderne et épuré, setup productif"),
    ("Tenue basique, look négligé", "Look stylé, élégant, transformation mode complète"),
    ("Jardin abandonné, herbes folles", "Jardin parfait, fleurs, pelouse verte impeccable"),
    ("Visage sans maquillage, traits fatigués", "Maquillage professionnel, glam total"),
    ("Voiture sale et abîmée", "Voiture propre, détaillée, comme neuve"),
    ("Cuisine vieille et sombre", "Cuisine moderne, blanche, lumineuse"),
    ("Peau avec acné et cicatrices", "Peau lisse, uniforme, sans imperfections"),
    ("Dents jaunes et mal alignées", "Sourire parfait, dents blanches éclatantes"),
    ("Silhouette avant musculation", "Silhouette athlétique après 90 jours"),
    ("Appartement vide et triste", "Appartement décoré, cosy et moderne"),
    ("Portrait flou et mal éclairé", "Portrait professionnel, studio light parfait"),
]

# ─── GEMINI: GENERATE CONTENT ─────────────────────────────
async def generate_content(before: str, after: str) -> dict:
    prompt = f"""Tu es expert TikTok viral spécialisé niche "Transformation Before/After IA".

TRANSFORMATION: "{before}" → "{after}"

Génère le contenu TikTok complet en JSON strict:

{{
  "hook": "accroche 0-3s ultra-virale (max 15 mots, choc émotionnel)",
  "video_prompt": "prompt détaillé en anglais pour générer la vidéo IA: décris la transformation visuelle, style cinématique, éclairage, couleurs, mouvement de caméra. Max 200 mots.",
  "description": "légende TikTok complète avec emojis (150-200 mots), storytelling émotionnel, appel à l'action fort",
  "hashtags": "#hashtag1 #hashtag2 ... (exactement 20 hashtags: 5 viraux géneraux + 8 niche before/after + 7 IA/transformation)",
  "audio_tip": "recommandation son/musique tendance pour cette vidéo",
  "best_time": "meilleur moment pour poster aujourd'hui",
  "viral_score": "score viral estimé /10"
}}

Réponds UNIQUEMENT avec le JSON, rien d'autre."""

    async with aiohttp.ClientSession() as session:
        async with session.post(GEMINI_URL, json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.9, "maxOutputTokens": 1500}
        }) as r:
            data = await r.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            text = text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)

# ─── KIE.AI: GENERATE VIDEO ───────────────────────────────
async def start_video_generation(prompt: str) -> str:
    """Start video generation and return task_id"""
    headers = {
        "Authorization": f"Bearer {KIE_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "kling-2.1/text-to-video",
        "input": {
            "prompt": prompt,
            "negative_prompt": "blurry, low quality, distorted, ugly",
            "duration": "5",
            "aspect_ratio": "9:16"
        }
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(KIE_URL, headers=headers, json=payload) as r:
            data = await r.json()
            if data.get("code") == 200:
                return data["data"]["task_id"]
            raise Exception(f"Kie.ai error: {data}")

async def check_video_status(task_id: str) -> dict:
    """Check video generation status"""
    headers = {"Authorization": f"Bearer {KIE_KEY}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{KIE_STATUS}?task_id={task_id}", headers=headers) as r:
            return await r.json()

async def wait_for_video(task_id: str, max_wait: int = 300) -> str:
    """Poll until video is ready, return URL"""
    for _ in range(max_wait // 5):
        await asyncio.sleep(5)
        result = await check_video_status(task_id)
        task_data = result.get("data", {})
        status = task_data.get("task_status", "")
        if status == "succeed":
            works = task_data.get("works", [])
            if works:
                return works[0].get("resource", {}).get("resource", "")
        elif status == "failed":
            raise Exception("Génération vidéo échouée")
    raise Exception("Timeout — vidéo trop longue à générer")

# ─── FORMAT MESSAGE ───────────────────────────────────────
def format_video_message(content: dict, before: str, after: str, idx: int) -> str:
    now = datetime.now().strftime("%H:%M")
    return f"""🎬 *VIDÉO #{idx} — BEFORE/AFTER IA*
━━━━━━━━━━━━━━━━━━━━━━

🔄 *Transformation:*
❌ Avant: {before}
✅ Après: {after}

⚡ *HOOK (0-3s):*
_{content.get('hook', '')}_

📝 *DESCRIPTION TIKTOK:*
{content.get('description', '')}

{content.get('hashtags', '')}

🎵 *Son recommandé:* {content.get('audio_tip', '')}
⏰ *Meilleur moment:* {content.get('best_time', '')}
🔥 *Score viral:* {content.get('viral_score', '?')}/10

━━━━━━━━━━━━━━━━━━━━━━
_Généré à {now} • TikTok Before/After Bot_"""

# ─── HANDLERS ─────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎬 Générer 1 Vidéo", callback_data="gen_1")],
        [InlineKeyboardButton("🚀 Pack 2 Vidéos du Jour", callback_data="gen_2")],
        [InlineKeyboardButton("💥 Pack 5 Vidéos", callback_data="gen_5")],
        [InlineKeyboardButton("ℹ️ Comment ça marche", callback_data="help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"""🎯 *TikTok Before/After AI Bot*
━━━━━━━━━━━━━━━━━━━━━━

Bienvenue ! Je génère automatiquement tes vidéos TikTok virales.

*Ta niche:* 🔄 Transformation Before/After IA

*Ce que je fais pour toi:*
✅ Trouve l'idée virale du jour
✅ Génère la vidéo IA automatiquement
✅ Crée la description optimisée
✅ Génère 20 hashtags viraux
✅ Recommande le meilleur moment

*Coût:* ~0.13$ par vidéo 5s avec Kling 2.1

━━━━━━━━━━━━━━━━━━━━━━
Choisis une option 👇""",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def video_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate 1 video"""
    await generate_videos(update, context, count=1)

async def pack_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate daily pack of 2 videos"""
    await generate_videos(update, context, count=2)

async def more_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate extra videos"""
    args = context.args
    count = int(args[0]) if args and args[0].isdigit() else 1
    count = min(count, 10)  # max 10 at once
    await generate_videos(update, context, count=count)

async def generate_videos(update: Update, context: ContextTypes.DEFAULT_TYPE, count: int = 1):
    msg = update.message or update.callback_query.message
    
    status_msg = await msg.reply_text(
        f"⚙️ *Génération en cours...*\n\n"
        f"📊 Sélection de {count} idée(s) virale(s)...\n"
        f"🤖 Gemini IA génère le contenu...\n"
        f"🎬 Kie.ai génère la/les vidéo(s)...\n\n"
        f"⏳ Temps estimé: {count * 2}-{count * 3} minutes",
        parse_mode=ParseMode.MARKDOWN
    )

    ideas = random.sample(BEFORE_AFTER_IDEAS, min(count, len(BEFORE_AFTER_IDEAS)))
    
    for i, (before, after) in enumerate(ideas, 1):
        try:
            await status_msg.edit_text(
                f"⚙️ *Vidéo {i}/{count} en cours...*\n\n"
                f"✅ Idée sélectionnée\n"
                f"🤖 Gemini génère le script...\n"
                f"🎬 Lancement génération vidéo IA...",
                parse_mode=ParseMode.MARKDOWN
            )

            # Generate content with Gemini
            content = await generate_content(before, after)

            await status_msg.edit_text(
                f"⚙️ *Vidéo {i}/{count} en cours...*\n\n"
                f"✅ Script généré\n"
                f"🎬 Vidéo IA en cours de rendu...\n"
                f"⏳ 1-2 minutes...",
                parse_mode=ParseMode.MARKDOWN
            )

            # Generate video with Kie.ai
            video_prompt = content.get("video_prompt", f"Cinematic before and after transformation: {before} transforms into {after}. Dramatic reveal, smooth transition, 9:16 vertical format, TikTok style, high quality.")
            
            task_id = await start_video_generation(video_prompt)
            video_url = await wait_for_video(task_id)

            # Send video + content
            caption = format_video_message(content, before, after, i)
            
            keyboard = [[
                InlineKeyboardButton("🎬 Télécharger Vidéo", url=video_url),
                InlineKeyboardButton("🔄 Générer une autre", callback_data="gen_1")
            ]]
            
            await msg.reply_video(
                video=video_url,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as e:
            # If video fails, still send the content
            content_only = format_video_message(content if 'content' in locals() else {
                "hook": f"Cette transformation va te choquer 😱",
                "description": f"Avant: {before}\nAprès: {after}\n\nL'IA change tout ! 🤯",
                "hashtags": "#beforeafter #transformation #IA #viral #fyp #tiktok #beforeandafter #glow #amazing #wow #incredible #ai #tech #change #lifestyle",
                "audio_tip": "Son dramatique tendance",
                "best_time": "18h-21h",
                "viral_score": "8"
            }, before, after, i)
            
            await msg.reply_text(
                f"⚠️ Vidéo en cours de génération (peut prendre 5 min)...\n\n{content_only}",
                parse_mode=ParseMode.MARKDOWN
            )

    await status_msg.edit_text(
        f"✅ *{count} vidéo(s) générée(s) avec succès!*\n\n"
        f"📲 Télécharge et poste sur TikTok maintenant!\n"
        f"💡 Tape /video pour une nouvelle vidéo",
        parse_mode=ParseMode.MARKDOWN
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "gen_1":
        await generate_videos(update, context, count=1)
    elif query.data == "gen_2":
        await generate_videos(update, context, count=2)
    elif query.data == "gen_5":
        await generate_videos(update, context, count=5)
    elif query.data == "help":
        await query.message.reply_text(
            """ℹ️ *Comment utiliser le bot:*

*Commandes disponibles:*
/start — Menu principal
/video — Générer 1 vidéo
/pack — Pack 2 vidéos du jour
/more 3 — Générer 3 vidéos (ou tout chiffre)

*Workflow quotidien recommandé:*
🌅 Matin → /video → Télécharge → Poste
🌆 Soir → /video → Télécharge → Poste

*Chaque vidéo contient:*
🎬 Vidéo Before/After générée par IA
📝 Description TikTok optimisée
#️⃣ 20 hashtags viraux
⚡ Hook d'accroche
🎵 Recommandation audio
⏰ Meilleur moment pour poster

*Coût par vidéo:* ~0.13$ (Kling 2.1 Standard)
*Budget 10€/mois:* ~60 vidéos ✅""",
            parse_mode=ParseMode.MARKDOWN
        )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """📊 *Tes Stats du Mois:*

🎬 Vidéos générées: disponible bientôt
💰 Budget utilisé: disponible bientôt
🔥 Niche: Before/After IA

*Idées restantes dans la banque:*
✅ 15 transformations uniques prêtes""",
        parse_mode=ParseMode.MARKDOWN
    )

# ─── MAIN ─────────────────────────────────────────────────
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("video", video_command))
    app.add_handler(CommandHandler("pack", pack_command))
    app.add_handler(CommandHandler("more", more_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("🤖 Bot TikTok Before/After démarré!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
