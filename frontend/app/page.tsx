'use client'

import { CopilotKit } from "@copilotkit/react-core"
import { CopilotPopup } from "@copilotkit/react-ui"
import "@copilotkit/react-ui/styles.css"
import Dashboard from "@/components/Dashboard"

export default function Home() {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit">
      <main>
        <Dashboard />
        <CopilotPopup
          instructions="You are an AI assistant for Salla merchant operations. Help merchants understand their daily operations report, pricing recommendations, and customer insights."
          labels={{
            title: "Salla Operations Assistant",
            initial: "Hi! I can help you run operations checks and explain your daily report. Try asking: 'Run today's operations check'"
          }}
        />
      </main>
    </CopilotKit>
  )
}
