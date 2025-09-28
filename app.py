import os
from flask import Flask, request, jsonify
import requests

# --- Flask App ---
app = Flask(__name__)

# --- Configuration ---
# WARNING: Apni API Key ko direct code mein daalna aam taur par aacha nahi maana jaata.
# Lekin shuruaat ke liye, aap ise yahaan daal sakte hain.
SHOPIFY_ACCESS_TOKEN = "YAHAN_APNA_SHOPIFY_ACCESS_TOKEN_DAALEIN"

# --- API Route ---
@app.route('/index.php', methods=['GET'])
def handle_request():
    # URL se 'site' aur 'cc' parameters nikalein
    site = request.args.get('site')
    cc = request.args.get('cc')

    # 1. Check karein ki parameters maujood hain ya nahi
    if not site or not cc:
        return jsonify({"error": "'site' aur 'cc' parameters zaroori hain."}), 400

    # 2. 'cc' parameter ko parse karein
    try:
        card_parts = cc.split('|')
        card_number = card_parts[0]
        expiry_month = card_parts[1]
        expiry_year = card_parts[2]
        cvv = card_parts[3]
    except IndexError:
        # Agar 'cc' ka format galat hai to error bhejें
        return jsonify({"error": "'cc' parameter ka format galat hai. Sahi format: 'number|month|year|cvv'"}), 400

    # 3. Shopify API ko call karne ki koshish karein
    try:
        # Aapko is URL ko apne asli Shopify endpoint se badalna hoga
        # Hum yahaan ek naya order banane ka endpoint istemaal kar rahe hain
        shopify_api_url = f"{site.rstrip('/')}/admin/api/2023-10/orders.json"

        # 4. Shopify ke liye Payload Banayein
        # Yeh ek example payload hai. Aapko ise apni zaroorat ke hisaab se badalna hoga.
        payload = {
          "order": {
            "line_items": [
              {
                "variant_id": 447654528,  # <<-- APNE PRODUCT KI ASLI VARIANT ID YAHAN DAALEIN
                "quantity": 1
              }
            ],
            "customer": {
              "first_name": "John",
              "last_name": "Doe",
              "email": "john.doe@example.com" # <<-- Customer ka email
            },
            "financial_status": "pending", # Order ko pending status mein banayein
            
            # WARNING: Credit card details ko is tarah save karna unsafe hai.
            # Yeh sirf example ke liye hai.
            "note_attributes": [
                {
                    "name": "PaymentInfo_CardNum (Unsafe)",
                    "value": f"Starts with {card_number[:4]}"
                },
                {
                    "name": "PaymentInfo_Expiry (Unsafe)",
                    "value": f"{expiry_month}/{expiry_year}"
                }
            ]
          }
        }
        
        # Request ke liye Headers
        headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN
        }

        # 5. Shopify API ko request bhejein
        api_response = requests.post(shopify_api_url, json=payload, headers=headers, timeout=15)
        
        # Agar Shopify se koi error (jaise 401, 404, 500) aata hai to use handle karein
        api_response.raise_for_status()

        # Shopify se mile response ko wapas bhej dein
        return jsonify(api_response.json())

    except requests.exceptions.Timeout:
        # Agar request time out ho jaati hai
        return jsonify({"error": "Shopify API se connect karne mein time out ho gaya"}), 504

    except requests.exceptions.HTTPError as err:
        # Agar Shopify se 4xx ya 5xx error aata hai
        return jsonify({
            "error": "Shopify API se ek HTTP error aaya",
            "status_code": err.response.status_code,
            "details": err.response.json() # Error details ko JSON mein dikhayein
        }), err.response.status_code

    except requests.exceptions.RequestException as e:
        # Network ya dusre connection errors ke liye
        return jsonify({"error": f"API call karte samay ek error aaya: {e}"}), 500

# --- Server Start ---
if __name__ == "__main__":
    # Render is port ka istemaal karega
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
