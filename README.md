# 🤖 TikTok Before/After AI Bot

Bot Telegram qui génère automatiquement tes vidéos TikTok virales.

---

## 🚀 INSTALLATION EN 4 ÉTAPES

### ÉTAPE 1 — Créer le Bot Telegram (2 min)

1. Ouvre Telegram → cherche **@BotFather**
2. Tape `/newbot`
3. Donne un nom: `TikTok Before After AI`
4. Donne un username: `tiktok_beforeafter_bot` (ou autre)
5. **Copie le TOKEN** (ex: `7234567890:AAFxxxxxx`)

---

### ÉTAPE 2 — Obtenir les clés API

**Gemini (gratuit):**
- Va sur https://aistudio.google.com/app/apikey
- Crée une clé → copie `AIzaSy...`

**Kie.ai (pour les vidéos):**
- Va sur https://kie.ai
- Crée un compte → Dashboard → API Keys
- Copie ta clé
- Recharge 10€ de crédits (~60-80 vidéos)

---

### ÉTAPE 3 — Déployer sur Railway (gratuit)

1. Va sur https://railway.app
2. Crée un compte avec GitHub
3. Clique **"New Project"** → **"Deploy from GitHub"**
4. Upload ce dossier sur GitHub d'abord, ou utilise **"Empty Project"**
5. Dans Railway → **Variables** → Ajoute:
   ```
   TELEGRAM_TOKEN = ton_token_botfather
   GEMINI_KEY = ta_clé_gemini
   KIE_KEY = ta_clé_kie
   ```
6. Deploy → Le bot démarre automatiquement ✅

---

### ÉTAPE 4 — Utiliser le Bot

Ouvre Telegram → cherche ton bot → `/start`

**Commandes:**
- `/start` — Menu principal avec boutons
- `/video` — Générer 1 vidéo
- `/pack` — Pack 2 vidéos du jour
- `/more 5` — Générer 5 vidéos
- `/stats` — Tes statistiques

---

## 💰 Coût Réel

| Action | Coût |
|--------|------|
| 1 vidéo 5s (Kling 2.1) | ~0.13$ |
| Pack 2 vidéos/jour | ~0.26$/jour |
| 1 mois (2 vidéos/jour) | ~8$/mois |
| Budget 10€/mois | ~60 vidéos ✅ |

---

## 📱 Workflow Quotidien

**Matin (5 min):**
1. Ouvre Telegram
2. `/video` → attends 2-3 min
3. Télécharge la vidéo
4. Poste sur TikTok avec la description générée

**Soir (5 min):**
1. `/video` → attends 2-3 min
2. Télécharge → Poste

**Si tu veux plus:**
- `/more 3` → génère 3 vidéos supplémentaires
