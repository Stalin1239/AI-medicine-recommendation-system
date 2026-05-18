import os
from groq import Groq

async def get_ai_recommendation(symptoms, age, weight):
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    if not GROQ_API_KEY:
        print("⚠️ Groq API key is not configured. Returning safe fallback response.")
        return "AI Assistant Insights\nA supportive overview, not clinical advice.\n\nAI Insight: Currently unavailable. Use the verified local guidance below for immediate support."

    client = Groq(api_key=GROQ_API_KEY)

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a medical assistant for the FedMedFlow project. Based on the patient's symptoms, provide a concise response in the following format:\n\n- **Disease Name:** [Inferred disease]\n- **Medicine:** [Actual medicine name and dosage]\n- **Diet:** What to eat and what to avoid\n- **Safety Tip:** [One key safety tip]\n- **Myths:** [Common myth to debunk]\n- **Description:** [Small description of the disease]\n- **Severity Score:** [Score from 1-10 if severe, otherwise N/A]\n\nAlways end with: 'Doctor consultation is recommended.'\n\nThis is not a substitute for professional medical advice.",
                },
                {
                    "role": "user",
                    "content": f"Patient details: {age} years old, {weight} kg. Symptoms: {symptoms}",
                },
            ],
        )
        return completion.choices[0].message.content

    except Exception as e:
        print(f"🤖 Groq API Error: {e}")
        return "AI Assistant Insights\nA supportive overview, not clinical advice.\n\nAI Insight: Currently unavailable. Use the verified local guidance below for immediate support."
