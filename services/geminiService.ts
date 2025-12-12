import { GoogleGenAI, Type, Schema } from "@google/genai";
import { AnalyzedBill, NavigationAction } from "../types";

// Initialize Gemini Client
// In a real production app, this key should be proxied through a backend.
const ai = new GoogleGenAI({ apiKey: process.env.API_KEY || '' });

// 1. Bill Analysis Service
export const analyzeMedicalBill = async (base64Image: string): Promise<AnalyzedBill> => {
  const modelId = "gemini-2.5-flash"; // Fast, multimodal model

  const schema: Schema = {
    type: Type.OBJECT,
    properties: {
      providerName: { type: Type.STRING },
      date: { type: Type.STRING },
      totalAmount: { type: Type.NUMBER },
      summary: { type: Type.STRING },
      potentialSavings: { type: Type.NUMBER },
      issues: {
        type: Type.ARRAY,
        items: { type: Type.STRING }
      },
      lineItems: {
        type: Type.ARRAY,
        items: {
          type: Type.OBJECT,
          properties: {
            description: { type: Type.STRING },
            cptCode: { type: Type.STRING },
            charge: { type: Type.NUMBER },
            expectedCost: { type: Type.NUMBER },
            flagged: { type: Type.BOOLEAN },
            issueDescription: { type: Type.STRING }
          }
        }
      }
    },
    required: ["providerName", "totalAmount", "lineItems", "issues"]
  };

  try {
    const response = await ai.models.generateContent({
      model: modelId,
      contents: {
        parts: [
          {
            inlineData: {
              mimeType: "image/jpeg",
              data: base64Image
            }
          },
          {
            text: `Analyze this medical bill image. 
            Extract line items, identify CPT codes if visible. 
            Check for common errors like duplicate charges, upcoding, or unbundling. 
            Estimate typical costs for these services (use general US average knowledge) and flag significant discrepancies.
            Calculate potential savings if errors are corrected.`
          }
        ]
      },
      config: {
        responseMimeType: "application/json",
        responseSchema: schema,
        temperature: 0.1 // Low temperature for factual extraction
      }
    });

    const text = response.text;
    if (!text) throw new Error("No response from Gemini");
    
    const data = JSON.parse(text);
    
    // Enrich with client-side ID and defaults
    return {
      ...data,
      id: crypto.randomUUID(),
      confidenceScore: 0.95,
      status: 'analyzed'
    };

  } catch (error) {
    console.error("Analysis Failed", error);
    throw error;
  }
};

// 2. Navigation Plan Generator
export const generateActionPlan = async (bills: AnalyzedBill[]): Promise<NavigationAction[]> => {
  const modelId = "gemini-2.5-flash";

  if (bills.length === 0) return [];

  const billsContext = JSON.stringify(bills.map(b => ({
    provider: b.providerName,
    amount: b.totalAmount,
    issues: b.issues
  })));

  const schema: Schema = {
    type: Type.ARRAY,
    items: {
      type: Type.OBJECT,
      properties: {
        title: { type: Type.STRING },
        description: { type: Type.STRING },
        priority: { type: Type.STRING, enum: ["high", "medium", "low"] },
        estimatedSavings: { type: Type.NUMBER },
        category: { type: Type.STRING, enum: ["bill_review", "negotiate", "assistance"] }
      }
    }
  };

  try {
    const response = await ai.models.generateContent({
      model: modelId,
      contents: `Based on these medical bill summaries: ${billsContext}. 
      Generate a prioritized checklist of 3-5 financial actions the patient should take to reduce their debt.
      Include specific negotiation tactics or dispute actions if errors were found.`,
      config: {
        responseMimeType: "application/json",
        responseSchema: schema
      }
    });

    const data = JSON.parse(response.text || "[]");
    return data.map((item: any) => ({ ...item, id: crypto.randomUUID(), status: 'pending' }));
  } catch (error) {
    console.error("Plan Generation Failed", error);
    return [];
  }
};

// 3. Chat Assistant
export const sendChatMessage = async (history: {role: string, parts: {text: string}[]}[], newMessage: string) => {
    // Use Pro model for reasoning and complex financial advice
    const modelId = "gemini-3-pro-preview"; 
    
    try {
        const chat = ai.chats.create({
            model: modelId,
            history: history,
            config: {
                systemInstruction: "You are MedFin, an expert healthcare financial navigator. You help patients understand bills, insurance terms (deductibles, copays), and find financial assistance. Be empathetic, clear, and practical."
            }
        });

        const result = await chat.sendMessage({ message: newMessage });
        return result.text;
    } catch (error) {
        console.error("Chat Error", error);
        throw error;
    }
}
