import os
import re
import uuid
import base64
import requests
import json
from datetime import datetime
from flask import Flask, request, jsonify

# ---------- Configuration ----------
ACCESSTOKEN = os.getenv("WA_ACCESS_TOKEN", "EACH...default_token")
PHONENUMBERID = os.getenv("WA_PHONE_ID", "579796315228068")
APIVER = "v18.0"
WAURL = f"https://graph.facebook.com/{APIVER}/{PHONENUMBERID}/messages"
VERIFYTOKEN = os.getenv("WA_VERIFY_TOKEN", "MYUNIQUEVERIFYTOKEN123")

APPSCRIPTURL = os.getenv("APPSCRIPT_URL", "https://script.google.com/macros/s/AKfycbw...")
OPENROUTERKEY = os.getenv("OPENROUTER_KEY", "sk-or-v1-...")
OPENROUTERMODEL = "qwen/qwen3-30b-a3b:free"
OPENROUTERAPI = "https://openrouter.ai/api/v1/chat/completions"

ADMINEMAIL = os.getenv("ADMIN_EMAIL", "solutions@nexabloom.io")
DRIVEFOLDERID = os.getenv("DRIVE_FOLDER_ID", "1qobSLoixuJILlkSP-nIo4qOHzVOLMpWv")
CALENDLYURL = os.getenv("CALENDLY_URL", "")
CALDEFAULTTZ = os.getenv("CAL_TZ", "Europe/London")
MAXMEDIABYTES = int(os.getenv("MAX_MEDIA_BYTES", str(12*1024*1024)))
GRAPHBASE = f"https://graph.facebook.com/{APIVER}"

SHEETID = os.getenv("SHEET_ID", "105mrH6iAIPzUJ035iHymxIjS7FaEnPcPeb3hIdgBr-s")
SHEETTAB = os.getenv("SHEET_TAB", "Cases")

WALIM = {"title": 24, "listdesc": 72, "button": 20, "header": 60, "body": 1024, "rows": 10}

# ---------- SERVICES data structure (simplified for brevity) ----------
SERVICES = {
    "Family Immigration": {
        "subservices": {
            "Spouse/Partner Visa": {
                "questions": ["Is your partner a British citizen or settled in the UK?"],
                "checklist": ["Valid passport", "Marriage/civil partnership certificate"],
                "nextsteps": "Prepare and submit your application.",
                "faqs": [{"q": "Financial requirement?", "a": "The minimum is £18,600 per year."}]
            }
        }
    },
    "Work Immigration": {
        "subservices": {
            "Skilled Worker Visa": {
                "questions": ["Job offer from approved sponsor?"],
                "checklist": ["Certificate of Sponsorship", "English proficiency proof"],
                "nextsteps": "Sponsor issues CoS. Apply online.",
                "faqs": [{"q": "Min salary 2025?", "a": "£41,700 or going rate."}]
            }
        }
    }
}

EMOJI = {
    "Family Immigration": "👨‍👩‍👧‍👦",
    "Work Immigration": "💼"
}

T = {
    "welcome": "Welcome to Premium ImmigrationBot!",
    "selectcategory": "Service Categories",
    "choosecategory": "Select a category below",
    "selectsub": "Sub-Services",
    "choosesub": "Select a service in {cat}",
    "eligintro": "Eligibility Assessment for {srv}",
    "eligprogress": "Question {curr}/{total}",
    "invalid": "Invalid input. Please use the buttons or type correctly.",
    "askname": "Enter your full name",
    "askemail": "Enter your email",
    "bademail": "Invalid email, try again.",
    "askphone": "Enter phone with country code",
    "askurgency": "Urgency level?",
    "doclist": "Personalized Document Checklist for {srv}:\\n{list}",
    "emaildocs": "Please send all listed docs to solicitors@hotmail.co.uk",
    "faqheader": "FAQs for {srv}",
    "faqbody": "Select a question",
    "faqanswer": "Q: {q}\\nA: {a}",
    "anythingelse": "Anything else I can help with, {name}?",
    "thankyou": "Hello {name}, our team will contact you soonest.",
    "startnew": "Start Again",
    "fallback": "Sorry, didn't catch that. Type 'menu' to restart.",
    "llmdisc": "This is AI-generated reference only - verify with a professional lawyer.",
    "askquestion": "What else can I help with regarding the {srv} visa, {name}?"
}

# ---------- WhatsApp helpers ----------
HDRS = {"Authorization": f"Bearer {ACCESSTOKEN}", "Content-Type": "application/json"}

def wspayload(payload):
    try:
        response = requests.post(WAURL, headers=HDRS, json=payload, timeout=10)
        response.raise_for_status()
        print(f"Message sent successfully: {response.json()}")
    except Exception as e:
        print(f"Error sending WhatsApp message: {e}")

def sendtext(to, body):
    ws = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": body[:1024]}}
    wspayload(ws)

def sendbuttons(to, body, opts):
    opts = opts[:3]
    ws = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body[:1024]},
            "action": {
                "buttons": [{"type": "reply", "reply": {"id": i, "title": t[:20]}} for i, t in opts]
            }
        }
    }
    wspayload(ws)

def sendlistsafe(to, header, body, btn, rows, fallbacktag=None):
    if not rows:
        sendtext(to, "No options available right now. Please try again later.")
        return False
    
    header = header or WALIM["header"]
    body = body or WALIM["body"]
    btn = btn or "Select"[:WALIM["button"]]
    rows = rows[:WALIM["rows"]]
    
    normrows = []
    for i, t, d in rows:
        normrows.append({
            "id": i,
            "title": t[:WALIM["title"]],
            "description": d[:WALIM["listdesc"]]
        })
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": header},
            "body": {"text": body},
            "action": {
                "button": btn,
                "sections": [{"title": "Options", "rows": normrows}]
            }
        }
    }
    
    try:
        r = requests.post(WAURL, headers={"Authorization": f"Bearer {ACCESSTOKEN}"}, json=payload, timeout=15)
        if r.status_code == 200:
            sessions.setdefault(to, {}).setdefault("fallback", {})[fallbacktag or "mode"] = {
                "mode": "list",
                "rows": [(i, t, d) for i, t, d in rows]
            }
            return True
        else:
            print("WA list error:", r.text)
    except Exception as e:
        print("WA list exception:", e)
    
    numbered = "\\n".join([f"{idx}. {t}" for idx, (_, t, _) in enumerate(rows, start=1)])
    sendtext(to, f"{header}\\n{body}\\n{numbered}\\nReply with the number or the name.")
    sessions.setdefault(to, {}).setdefault("fallback", {})[fallbacktag or "mode"] = {
        "mode": "numbered",
        "rows": [(i, t, d) for i, t, d in rows]
    }
    return False

def askllm(q, ctx):
    try:
        resp = requests.post(
            OPENROUTERAPI,
            headers={"Authorization": f"Bearer {OPENROUTERKEY}"},
            json={
                "model": OPENROUTERMODEL,
                "messages": [
                    {"role": "system", "content": "You are a UK immigration solicitor. Provide accurate, professional advice based on 2025 rules."},
                    {"role": "user", "content": f"Context: {ctx}\\n{q}"}
                ]
            },
            timeout=15
        )
        if resp.status_code == 200:
            ans = resp.json()["choices"][0]["message"]["content"].strip()
            return ans + " " + T["llmdisc"]
    except:
        pass
    return "Sorry, couldn't fetch info. " + T["llmdisc"]

sessions = {}

def resetuid(uid):
    sessions[uid] = {
        "state": "",
        "cat": None,
        "sub": None,
        "qidx": 0,
        "ans": {},
        "info": {},
        "case": str(uuid.uuid4()),
        "complex": False,
        "score": 0,
        "registered": False
    }

app = Flask(__name__)

@app.route("/", methods=["GET"])
def health():
    return "OK", 200

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFYTOKEN:
            return request.args.get("hub.challenge"), 200
        return "Forbidden", 403
    
    data = request.get_json(force=True)
    print(f"Incoming webhook: {data}")
    
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for msg in value.get("messages", []):
                uid = msg.get("from")
                
                if uid not in sessions:
                    resetuid(uid)
                
                s = sessions[uid]
                text = msg.get("text", {}).get("body") if "text" in msg else None
                
                itype = iid = ititle = None
                if "interactive" in msg:
                    inter = msg["interactive"]
                    if "button_reply" in inter:
                        itype, iid, ititle = "btn", inter["button_reply"]["id"], inter["button_reply"]["title"]
                    elif "list_reply" in inter:
                        itype, iid, ititle = "list", inter["list_reply"]["id"], inter["list_reply"]["title"]
                
                handle(uid, text, itype, iid, ititle)
    
    return jsonify({"status": "ok"}), 200

def handle(uid, text, itype, iid, ititle):
    if uid not in sessions:
        resetuid(uid)
    
    s = sessions[uid]
    
    if text and text.lower() in ["hi", "menu", "restart", "start"]:
        resetuid(uid)
        s["state"] = ""
    
    state = s["state"]
    
    if state == "":
        cats = list(SERVICES.keys())
        rows = [(f"cat_{i}", EMOJI.get(c, "") + " " + c, "Select for details") for i, c in enumerate(cats)]
        sendlistsafe(uid, T["selectcategory"], T["choosecategory"], "Select", rows, fallbacktag="cat")
        s["state"] = "cat"
        return
    
    if state == "cat":
        if itype == "list" and iid.startswith("cat_"):
            idx = int(iid.split("_")[1])
            cats = list(SERVICES.keys())
            s["cat"] = cats[idx]
            subs = list(SERVICES[s["cat"]]["subservices"].keys())
            rows = [(f"sub_{i}", sub, "Select for details") for i, sub in enumerate(subs)]
            sendlistsafe(uid, T["selectsub"], T["choosesub"].format(cat=s["cat"]), "Select", rows, fallbacktag="sub")
            s["state"] = "sub"
            return
    
    if state == "sub":
        if itype == "list" and iid.startswith("sub_"):
            idx = int(iid.split("_")[1])
            subs = list(SERVICES[s["cat"]]["subservices"].keys())
            s["sub"] = subs[idx]
            s["state"] = "elig"
            s["qidx"] = 0
            ask_next_question(uid, s)
            return
    
    if state == "elig":
        if text:
            questions = SERVICES[s["cat"]]["subservices"][s["sub"]]["questions"]
            s["ans"][questions[s["qidx"]]] = text
            s["qidx"] += 1
            ask_next_question(uid, s)
            return
    
    sendtext(uid, T["fallback"])

def ask_next_question(uid, s):
    questions = SERVICES[s["cat"]]["subservices"][s["sub"]]["questions"]
    if s["qidx"] < len(questions):
        sendtext(uid, f"{T['eligprogress'].format(curr=s['qidx']+1, total=len(questions))}\\n{questions[s['qidx']]}")
    else:
        sendtext(uid, f"Thank you! Your case ID is {s['case']}.")
        checklist = SERVICES[s["cat"]]["subservices"][s["sub"]]["checklist"]
        sendtext(uid, T["doclist"].format(srv=s["sub"], list="\\n".join([f"• {item}" for item in checklist])))
        s["state"] = ""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
