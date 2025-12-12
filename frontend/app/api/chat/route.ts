import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { message } = body;

    if (!message) {
      return NextResponse.json(
        { error: 'Message is required' },
        { status: 400 }
      );
    }

    // Get n8n webhook URL from environment
    const n8nWebhookUrl =
      process.env.N8N_WEBHOOK_URL || 'http://localhost:5678/webhook/chat';

    console.log('Forwarding request to n8n:', n8nWebhookUrl);

    // Call n8n workflow
    const response = await fetch(n8nWebhookUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question: message,
        timestamp: new Date().toISOString(),
      }),
    });

    if (!response.ok) {
      throw new Error(`n8n returned status ${response.status}`);
    }

    const data = await response.json();

    return NextResponse.json(data);
  } catch (error: any) {
    console.error('Error calling n8n:', error);
    return NextResponse.json(
      {
        error: 'Failed to process request',
        details: error.message,
      },
      { status: 500 }
    );
  }
}
