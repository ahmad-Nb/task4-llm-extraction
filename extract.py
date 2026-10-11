import json
import time
import os
from dotenv import load_dotenv
from groq import Groq
load_dotenv()
SYSTEM_PROMPT = """
You are an expert customer support data extraction AI.
Extract information into the EXACT JSON format below. Return ONLY raw JSON. Do not add markdown blocks.

EXPECTED SCHEMA:
{
  "message_id": "string",
  "customer_name": "string" or null,
  "order_ids": ["string"],
  "product": "string" or null,
  "issue_type": "damaged_item" | "defective" | "wrong_item" | "late_delivery" | "refund_request" | "cancellation" | "billing" | "other",
  "wants_refund": true or false,
  "urgency": "low" | "medium" | "high",
  "language": "en" | "ar" | "mixed"
}

CRITICAL RULES:
1. Null Values: If a name or product is missing, use standard JSON `null`.
2. Order IDs: Format as a list of strings prefixed with NT-. Example: "order 10579" -> ["NT-10579"]. If none, return [].
3. Product Names: Extract the FULL product name, including the brand and model (e.g., "Lenovo Ideapad charger", "Xiaomi 55 inch TV", "Dell XPS 13"). Do NOT just write generic nouns like "charger" or "TV".
4. Issue Type: MUST be exactly one of the allowed literal values. 
   - "defective": The item is malfunctioning, sparking, or broken internally.
   - "damaged_item": The item arrived physically shattered or damaged in shipping.
5. Wants Refund: `true` if they explicitly ask for a refund, money back, OR if it is a billing dispute/cancellation where a refund is strongly implied. Otherwise `false`.
6. Urgency:
   - "high": Safety hazards, legal threats, explicit "urgent" keywords.
   - "low": General questions, feedback, account deletion.
   - "medium": Standard support issues without extreme threats.
7. Translation: All JSON values must be in English. Translate Arabic names/products.
8. Language Field: MUST be exactly "en", "ar", or "mixed".
"""

def extract_data():
    # PUT YOUR GROQ API KEY HERE
    api_key = os.getenv("API_KEY")
    client = Groq(api_key=api_key)
    
    input_file = "support_messages.jsonl"
    output_file = "predictions.jsonl"
    
    open(output_file, 'w').close()

    print(f"Starting extraction using Groq (openai/gpt-oss-120b)...")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
                
            message_data = json.loads(line)
            message_id = message_data["message_id"]
            text = message_data["text"]
            
            print(f"Processing {message_id}...")
            
            try:
                # Call Groq API and enforce JSON output
                response = client.chat.completions.create(
                    model='openai/gpt-oss-120b',
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Message ID: {message_id}\n\nMessage Text: {text}"}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.0
                )
                
                prediction = json.loads(response.choices[0].message.content)
                
                with open(output_file, 'a', encoding='utf-8') as out_f:
                    json.dump(prediction, out_f, ensure_ascii=False)
                    out_f.write('\n')
                        
            except Exception as e:
                print(f"Error processing {message_id}: {e}")
            
            # Groq is very fast, but a 1-second pause prevents hitting free tier rate limits
            time.sleep(1)

    print(f"Done! Predictions saved to {output_file}")

if __name__ == "__main__":
    extract_data()