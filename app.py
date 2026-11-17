import os
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)


def get_all_bot_tokens():
  """Environment variables se saare bot tokens dynamically fetch karega."""
  tokens = []
  # Pehle BOT_TOKEN check karo
  t1 = os.environ.get("BOT_TOKEN")
  if t1:
    tokens.append(t1)

  # Baaki BOT_TOKEN2, BOT_TOKEN3, ... check karo
  i = 2
  while True:
    t = os.environ.get(f"BOT_TOKEN{i}")
    if not t:
      break
    tokens.append(t)
    i += 1
  return tokens


@app.route("/sent", methods=["GET"])
def send_otp():
  number = request.args.get("number")
  otp = request.args.get("otp")
  key = request.args.get("key")
  app_key = os.environ.get("KEY_SENT")

  # API Key Verification
  if not app_key or key != app_key:
    return jsonify({"status": "error", "message": "Invalid or missing key"}), 403

  if not number or not otp:
    return (
        jsonify(
            {"status": "error", "message": "Number and OTP are required"}
        ),
        400,
    )

  bot_tokens = get_all_bot_tokens()
  if not bot_tokens:
    return (
        jsonify({"status": "error", "message": "No bot tokens configured"}),
        500,
    )

  # Message format customize kar sakte ho
  message = f"🔐 *Your OTP Code*\n\nNumber: `{number}`\nOTP: `{otp}`"

  # Fallback mechanism: Ek bot fail ho toh agle par try karega
  for index, token in enumerate(bot_tokens, start=1):
    # Yahan hum assume karte hain ki number actually ek Telegram Chat ID hai
    # (Telegram API direct phone number par message nahi bhej sakta, chat ID chahiye hoti hai)
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": number, "text": message, "parse_mode": "Markdown"}

    try:
      response = requests.post(url, json=payload, timeout=5)
      data = response.json()

      if data.get("ok"):
        return jsonify({
            "status": "success",
            "message": "OTP sent successfully",
            "bot_used": f"BOT_TOKEN{index if index > 1 else ''}",
        })
      else:
        # Agar current bot block ya fail hua toh loop agle bot par chala jayega
        continue
    except Exception:
      # Network error ya timeout hone par next bot try karo
      continue

  return (
      jsonify({
          "status": "error",
          "message": "All bots failed to send OTP or limit reached",
      }),
      500,
  )


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
