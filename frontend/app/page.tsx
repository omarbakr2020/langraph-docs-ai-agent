'use client';

import { useState } from 'react';
import ChatInterface from '@/components/ChatInterface';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 bg-gradient-to-b from-gray-50 to-gray-100">
      <div className="w-full max-w-4xl">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            🤖 LangGraph Documentation Chatbot
          </h1>
          <p className="text-gray-600">
            Ask me anything about LangGraph! Powered by RAG & n8n
          </p>
        </div>

        <ChatInterface />

        <div className="mt-6 text-center text-sm text-gray-500">
          <p>Built with Next.js → n8n → Python RAG Service</p>
        </div>
      </div>
    </main>
  );
}
