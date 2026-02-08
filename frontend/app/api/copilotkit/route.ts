import {
  CopilotRuntime,
  OpenAIAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import OpenAI from "openai";
import { NextRequest } from "next/server";

export const POST = async (req: NextRequest) => {
  const apiKey = process.env.OPENAI_API_KEY;
  
  if (!apiKey) {
    console.error("❌ OpenAI API key missing in environment variables.");
    return new Response(
      JSON.stringify({ error: "OpenAI API key missing" }), 
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }

  try {
    console.log("🔌 Initializing OpenAI Adapter");

    // Initialize standard OpenAI client
    const openai = new OpenAI({
      apiKey: apiKey,
    });

    // Create OpenAI adapter
    const serviceAdapter = new OpenAIAdapter({
      openai,
    });
    
    const runtime = new CopilotRuntime();

    const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
      runtime,
      serviceAdapter,
      endpoint: "/api/copilotkit",
    });

    return handleRequest(req);
  } catch (error) {
    console.error("❌ Error initializing CopilotKit:", error);
    return new Response(
      JSON.stringify({ error: "Internal Server Error" }), 
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
};
