from flask import Flask, request, jsonify
import requests
import json
import hmac
import hashlib
import time

app = Flask(__name__)

# ================ التكوينات ================
# GREEN-API
GREEN_INSTANCE = "7103526784"
GREEN_TOKEN = "ed20681800954c8bb3983ad224ab7a945555cc8390154153a0"
GREEN_API_URL = "https://7103.api.greenapi.com"

# تيليغرام
TELEGRAM_BOT_TOKEN = "8791948930:AAGoy-Q_eyJEKqrt-vup2V6wk574M6O45nY"
TELEGRAM_CHAT_ID = "6310927437"

# API الخاص بموقعك (غيّره إلى رابط موقعك الفعلي)
YOUR_SITE_API = "https://yoursite.com/api/receive-code"
# ===========================================

def send_to_telegram(message):
    """إرسال إشعار إلى تيليغرام"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        requests.post(url, json=data, timeout=5)
    except Exception as e:
        print(f"خطأ في إرسال تيليغرام: {e}")

def send_to_your_site(phone, code, timestamp):
    """إرسال الكود إلى موقعك"""
    try:
        data = {
            "phone": phone,
            "code": code,
            "timestamp": timestamp,
            "source": "whatsapp_bot"
        }
        headers = {"Content-Type": "application/json"}
        response = requests.post(YOUR_SITE_API, json=data, headers=headers, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"خطأ في إرسال إلى الموقع: {e}")
        return False

@app.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """استقبال رسائل واتساب من GREEN-API"""
    try:
        data = request.json
        print(f"استقبال بيانات: {json.dumps(data, indent=2)}")
        
        # التحقق من وجود رسالة نصية
        if 'body' in data.get('messageData', {}):
            message_data = data['messageData']
            sender_data = data.get('senderData', {})
            
            # استخراج رقم المرسل
            sender = sender_data.get('sender', '')
            # تنظيف الرقم (إزالة @c.us إذا وجد)
            if '@c.us' in sender:
                sender = sender.replace('@c.us', '')
            
            # استخراج الكود إذا كانت الرسالة نصية
            if message_data['type'] == 'textMessage':
                code = message_data['textMessageData']['textMessage']
                timestamp = str(int(time.time()))
                
                # إرسال إلى تيليغرام
                telegram_msg = f"🔔 <b>كود واتساب جديد</b>\n\n📱 من: {sender}\n🔑 الكود: {code}\n⏱ الوقت: {timestamp}"
                send_to_telegram(telegram_msg)
                
                # إرسال إلى موقعك
                sent_to_site = send_to_your_site(sender, code, timestamp)
                
                return jsonify({
                    "status": "success",
                    "message": "تم استلام الكود",
                    "sent_to_site": sent_to_site
                }), 200
        
        return jsonify({"status": "ignored", "message": "ليست رسالة نصية"}), 200
        
    except Exception as e:
        print(f"خطأ في المعالجة: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/test', methods=['GET'])
def test():
    """صفحة اختبار للتأكد من أن البوت يعمل"""
    return jsonify({
        "status": "active",
        "message": "بوت واتساب يعمل بنجاح",
        "green_instance": GREEN_INSTANCE,
        "telegram_configured": bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
    })

@app.route('/send-test', methods=['GET'])
def send_test():
    """إرسال رسالة اختبار إلى تيليغرام"""
    send_to_telegram("✅ بوت واتساب يعمل بنجاح وجاهز لاستقبال الأكواد")
    return jsonify({"status": "sent", "message": "تم إرسال رسالة اختبار إلى تيليغرام"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
