# Frontend - Salla Merchant Operations UI

Next.js application with CopilotKit integration for merchant operations management.

## Features

- 🤖 AI-powered chat interface with CopilotKit
- 📊 Real-time operations dashboard
- 💰 Pricing recommendations visualization
- 🎧 Customer sentiment analysis display
- 🚨 Alert system for anomalies
- 📈 Interactive reports

## Tech Stack

- **Next.js 15** - React framework
- **TypeScript** - Type safety
- **CopilotKit** - AI chat integration
- **CSS Modules** - Scoped styling

## Getting Started

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

```bash
cp .env.local.example .env.local
```

Edit `.env.local`:
```env
OPENAI_API_KEY=your_openai_key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Run Development Server

```bash
npm run dev
```

Open http://localhost:3000

## Project Structure

```
frontend/
├── app/
│   ├── api/
│   │   └── copilotkit/
│   │       └── route.ts          # CopilotKit API endpoint
│   ├── layout.tsx                # Root layout
│   ├── page.tsx                  # Home page with CopilotKit
│   └── globals.css               # Global styles
├── components/
│   ├── Dashboard.tsx             # Main dashboard component
│   └── Dashboard.module.css      # Dashboard styles
├── package.json
├── tsconfig.json
└── next.config.js
```

## CopilotKit Integration

### Chat Interface

The CopilotPopup provides an AI assistant that can:
- Trigger operations checks
- Explain report data
- Answer merchant questions
- Provide recommendations

### Custom Actions

Defined in `Dashboard.tsx`:

```typescript
useCopilotAction({
  name: "runOperationsCheck",
  description: "Run daily operations check",
  handler: async ({ merchantId }) => {
    // Calls backend API
    // Returns formatted response
  }
})
```

### Readable Context

```typescript
useCopilotReadable({
  description: "Current operations report",
  value: report
})
```

This makes the report data available to the AI for answering questions.

## Components

### Dashboard

Main component that:
- Displays operations report
- Triggers backend API calls
- Shows pricing actions
- Displays recommendations
- Handles loading/error states

### Report Sections

1. **Summary Stats** - Key metrics grid
2. **Support Analysis** - Sentiment and velocity
3. **Pricing Actions** - Table of price changes
4. **Recommendations** - Actionable insights
5. **Warnings** - Issues requiring attention

## Styling

Uses CSS Modules for scoped styling:
- Responsive design
- Gradient backgrounds
- Card-based layout
- Status badges
- Alert boxes

## API Integration

Connects to backend at `NEXT_PUBLIC_API_URL`:

```typescript
const response = await fetch(`${apiUrl}/api/run`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ merchant_id })
})
```

## Building for Production

```bash
npm run build
npm start
```

## Docker

Build and run with Docker:

```bash
docker build -t salla-frontend .
docker run -p 3000:3000 salla-frontend
```

## Customization

### Changing Colors

Edit `app/globals.css` and `Dashboard.module.css`:
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### Adding New Sections

1. Add to report interface in `Dashboard.tsx`
2. Create new section in render
3. Style in `Dashboard.module.css`

### Modifying AI Instructions

Edit in `app/page.tsx`:
```typescript
<CopilotPopup
  instructions="Your custom instructions..."
  labels={{
    title: "Your Title",
    initial: "Your greeting"
  }}
/>
```

## Troubleshooting

### CopilotKit not loading
- Check OPENAI_API_KEY in .env.local
- Verify API route at /api/copilotkit
- Check browser console for errors

### Backend connection failed
- Ensure backend is running on port 8000
- Check NEXT_PUBLIC_API_URL is correct
- Verify CORS is enabled on backend

### Styles not applying
- Clear .next folder: `rm -rf .next`
- Restart dev server
- Check CSS module imports

## Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [CopilotKit Documentation](https://docs.copilotkit.ai)
- [React Documentation](https://react.dev)
