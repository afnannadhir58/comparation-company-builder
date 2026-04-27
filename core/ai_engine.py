import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def analyze_business_dna(summary, model_name="llama-3.3-70b-versatile"):
    """
    Ekstraksi DNA dengan Persona Equity Research Analyst.
    Fokus pada unit ekonomi, tipe pendapatan, dan keunggulan kompetitif.
    """
    system_prompt = "You are a seasoned Equity Research Analyst at a top-tier Investment Bank. Your task is to dissect a company's core business model."
    
    user_prompt = f"""
    Analyze the following company summary and extract its Business Model DNA. 
    Focus strictly on the underlying economic engine, not marketing jargon.
    
    Company Summary: {summary}
    
    Provide a comprehensive breakdown covering these specific categories:
    1. REVENUE MODEL: How do they monetize? (e.g., B2B SaaS, Hardware Sales, Ad-based, Transactional, Razor-and-Blade).
    2. CUSTOMER TYPE: Who actually pays them? (e.g., Enterprise B2B, SMBs, Consumers, Government).
    3. ECONOMIC MOAT: What is their competitive advantage? (e.g., Switching Costs, Network Effects, Intangible Assets, Cost Advantage).
    4. VALUE PROPOSITION: What core problem are they solving for their customers?
    5. GROWTH DRIVERS: What are the primary levers for future revenue growth?
    6. KEY RISKS: What are the main threats to their business model (e.g., Regulatory, Tech Disruption, Competition)?
    
    Format the output with clear headers for each section.
    """
    
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        model=model_name,
        temperature=0.1, # Sangat rendah agar objektif
    )
    return chat_completion.choices[0].message.content


def get_similarity_score(target_dna, candidate_name, candidate_summary, model_name="llama-3.3-70b-versatile"):
    """
    Scoring dengan matriks valuasi yang ketat dan output JSON.
    """
    system_prompt = "You are a Quantitative Equity Research Analyst. You strictly evaluate business model similarity for Valuation Comps (Comparable Company Analysis). You output ONLY valid JSON."
    
    user_prompt = f"""
    Evaluate if '{candidate_name}' is a suitable valuation comparable for the Target company based strictly on their business engines.
    Do NOT just match their industry labels (e.g., ignore if both are just 'Software', look deeper into how they make money).
    
    TARGET DNA:
    {target_dna}
    
    CANDIDATE ({candidate_name}) SUMMARY:
    {candidate_summary}
    
    SCORING CRITERIA (0-100):
    - 90-100: Identical revenue model, same customer base, similar moat. Perfect comp.
    - 70-89: Similar target market but slightly different monetization, OR same monetization but different end-market. Good comp.
    - 40-69: Same broad sector, but fundamentally different unit economics (e.g., target is SaaS, candidate is hardware). Poor comp.
    - 0-39: Completely irrelevant.
    
    INSTRUCTION:
    Provide the similarity score and a detailed analytical rationale (2-3 sentences) comparing their monetization, customers, and risks.
    
    You MUST format your response as a valid JSON object with exact keys "score" (integer) and "rationale" (string).
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            # Menggunakan model yang lebih kencang untuk scoring jika tersedia, atau tetap llama
            model=model_name,
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        raw_content = chat_completion.choices[0].message.content
        # Ekstraksi JSON yang lebih aman menggunakan regex jika AI memberikan teks tambahan
        import re
        json_match = re.search(r'\{.*\}', raw_content, re.DOTALL)
        if json_match:
            result_dict = json.loads(json_match.group())
        else:
            result_dict = json.loads(raw_content)
            
        return result_dict
    except Exception as e:
        print(f"DEBUG: JSON Parse Error: {str(e)} | Content: {raw_content if 'raw_content' in locals() else 'No content'}")
        return {"score": 0, "rationale": "AI Analysis formatting error. Please retry."}