import os
import sys
import time
import traceback
from flask import Flask, request, jsonify

# បង្ខំ Server ឱ្យដើរម៉ោងនៅស្រុកខ្មែរ ១០០%
os.environ['TZ'] = 'Asia/Phnom_Penh'
if hasattr(time, 'tzset'):
    time.tzset()

from bakong_khqr import KHQR

app = Flask(__name__)
app.config["DEBUG"] = True

# 🔴 ប្រើ RBK Token ថ្មីរបស់មេ ដើម្បីទម្លាយប្លុក IP ក្រៅប្រទេស
MY_TOKEN = "rbk6oWzLWXhkVzI8XRiFClRlwPSHOzTwa0v-agsm4D6CkU"
khqr = KHQR(MY_TOKEN)

@app.route('/')
def index():
    return "<h1>✅ DramaFlix Movie API is Running!</h1>"

@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    try:
        data = request.json or {}
        
        # ១. ទាញយក UID ភ្ញៀវ
        raw_uid = data.get('uid', 'UNKNOWN')
        short_uid = raw_uid[:8] if len(raw_uid) > 8 else raw_uid
        bill_num = f"MV{short_uid}" 

        # ២. 🔴 ចំណុចថ្មី៖ ទាញយកតម្លៃលុយដែលផ្ញើមកពី Flutter
        # បើ Flutter មិនបានផ្ញើតម្លៃមកទេ វានឹងដាក់តម្លៃដើម 1.0 ដុល្លារ
        try:
            price_amount = float(data.get('amount', 1.0))
        except:
            price_amount = 1.0

        # ៣. បង្កើត QR តាមស្តង់ដារបាកង
        qr_string = khqr.create_qr(
            bank_account="thong_sovannda@bkrt",      # Bakong ID របស់មេ
            merchant_name="KOLAB KHMER",         # ឈ្មោះក្នុងកុង (អក្សរធំ)
            merchant_city="PHNOM PENH",      
            amount=price_amount,              # 💵 ប្រើតម្លៃដែលបានមកពី Flutter
            currency="USD",                   
            store_label="KOLABKHMER",         
            phone_number="85512345678",       
            bill_number=bill_num,            
            terminal_label="APP",            
            static=False,
            expiration=10                     # QR មានសុពលភាព ១០ នាទី
        )
        
        # ៤. បង្កើត MD5 សម្រាប់ទុកឆែកស្ថានភាពបង់ប្រាក់
        md5_hash = khqr.generate_md5(qr_string)
        
        return jsonify({
            "status": "success", 
            "qr_string": qr_string, 
            "md5": md5_hash,
            "amount": price_amount
        })
        
    except Exception as e:
        error_msg = traceback.format_exc()
        print(f"QR Error: {error_msg}") 
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/check_status', methods=['POST'])
def check_status():
    try:
        data = request.json or {}
        md5 = data.get('md5')
        
        if not md5: 
            return jsonify({"status": "error", "message": "បាត់លេខ MD5"}), 400
        
        # ឆែកស្ថានភាពលុយពីធនាគារជាតិបាកង
        status = khqr.check_payment(md5) 
        
        # បោះលទ្ធផលទៅឱ្យ Flutter វិញ (PAID ឬ UNPAID)
        return jsonify({"status": status})
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# មុខងារសម្រាប់តេស្តសាកល្បងលើ Browser
@app.route('/test_connection')
def test_connection():
    try:
        # តេស្តឆែកលុយដោយប្រើ MD5 ក្លែងក្លាយ ដើម្បីដឹងថា Server ដើរឬអត់
        status = khqr.check_payment("1234567890abcdef")
        return f"<h1>✅ ជោគជ័យ! Server អាចភ្ជាប់ទៅបាកងបាន (Status: {status})</h1>"
    except Exception as e:
        return f"<h1>❌ បរាជ័យ៖ {e}</h1>"

if __name__ == '__main__':
    # Render តម្រូវឱ្យប្រើ Port ដែលវាផ្ដល់ឱ្យ
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
