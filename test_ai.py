async def get_ai_recommendation(symptoms, age, weight):
    try:
        client = genai.Client(api_key="AIzaSyDf36Ad963W85V4KIfZm7V8MZEEpFvGaT8")
        
        # CHANGED: Using 1.5-flash as it has a higher free limit
        response = client.models.generate_content(
            model='gemini-1.5-flash', 
            contents=f"Patient {age}yr, {weight}kg. Symptoms: {symptoms}. Give 3 health tips."
        )
        return response.text
    except Exception as e:
        print(f"--- AI ERROR: {e} ---")
        return "AI Insight is refreshing..."