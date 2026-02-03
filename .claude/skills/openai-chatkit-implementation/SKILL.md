---
name: openai-chatkit-implementation
description: Implements OpenAI ChatKit as the frontend chat interface according to the official documentation. Replaces any custom chat UI and ensures the frontend communicates exclusively through the ChatKit protocol. Designed for Next.js (App Router) projects with ChatKit packages already installed, and a ChatKit-compatible backend endpoint.
---

# OpenAI ChatKit Implementation

This skill implements OpenAI ChatKit as the frontend chat interface according to the official documentation. It replaces any custom chat UI and ensures the frontend communicates exclusively through the ChatKit protocol.

## Prerequisites

Before implementing ChatKit, ensure the following:
- Project uses Next.js (App Router)
- ChatKit packages are installed (`@openai/chatkit`)
- Backend exposes a ChatKit-compatible chat endpoint
- Authentication is handled externally (Better Auth or equivalent)

## Pre-Implementation Validation

1. **Check project structure**:
   - Verify Next.js App Router setup (`app/` directory)
   - Confirm ChatKit packages are in package.json
   - Identify existing chat components that need replacement

2. **Verify backend compatibility**:
   - Confirm backend exposes ChatKit-compatible endpoints
   - Check authentication integration
   - Verify API routes are properly configured

## Implementation Process

### Phase 1: Install and Configure ChatKit

1. **Verify ChatKit installation**:
   ```bash
   npm install @openai/chatkit
   # Or if using yarn
   yarn add @openai/chatkit
   ```

2. **Configure environment variables** (if needed):
   - Check for any ChatKit-specific environment variables
   - Ensure API keys are properly configured

### Phase 2: Create ChatKit Provider Wrapper

1. **Create a ChatProvider component** at `components/ChatProvider.tsx`:
   ```tsx
   'use client';

   import { ChatProvider as OpenAIChatProvider } from '@openai/chatkit';
   import { PropsWithChildren, useState, useEffect } from 'react';

   export function ChatProvider({ children }: PropsWithChildren) {
     const [token, setToken] = useState<string | null>(null);

     // Get authentication token from your auth system
     useEffect(() => {
       const fetchToken = async () => {
         // Retrieve the token from your auth system (Better Auth, etc.)
         // This is an example - adapt to your auth implementation
         const authToken = localStorage.getItem('auth-token');
         setToken(authToken);
       };

       fetchToken();
     }, []);

     if (!token) {
       return <div>Loading...</div>; // Or your loading component
     }

     return (
       <OpenAIChatProvider
         options={{
           // Configure your ChatKit backend endpoint
           serverUrl: process.env.NEXT_PUBLIC_CHATKIT_SERVER_URL || '/api/chatkit',
           token: token,
         }}
       >
         {children}
       </OpenAIChatKit.Provider>
     );
   }
   ```

2. **Wrap your application** with the ChatProvider in your root layout:
   ```tsx
   // app/layout.tsx
   import { ChatProvider } from '@/components/ChatProvider';

   export default function RootLayout({
     children,
   }: {
     children: React.ReactNode;
   }) {
     return (
       <html lang="en">
         <body>
           <ChatProvider>
             {children}
           </ChatProvider>
         </body>
       </html>
     );
   }
   ```

### Phase 3: Implement Chat Interface Component

1. **Create the main chat component** at `components/ChatInterface.tsx`:
   ```tsx
   'use client';

   import {
     useChat,
     MessageList,
     MessageInput,
     ThreadList,
     ThreadComposer,
     ThreadViewer,
     useThread
   } from '@openai/chatkit';
   import { useEffect, useState } from 'react';

   interface ChatInterfaceProps {
     threadId?: string;
   }

   export default function ChatInterface({ threadId }: ChatInterfaceProps) {
     const [selectedThreadId, setSelectedThreadId] = useState<string | undefined>(threadId);
     const { thread, isLoading: threadLoading } = useThread(selectedThreadId);

     if (threadLoading) {
       return <div>Loading thread...</div>;
     }

     return (
       <div className="flex h-full flex-col">
         <div className="flex-1 overflow-y-auto mb-4">
           {selectedThreadId ? (
             <MessageList threadId={selectedThreadId} />
           ) : (
             <div className="p-4 text-center text-gray-500">
               Select or create a conversation
             </div>
           )}
         </div>
         <div className="mt-auto">
           {selectedThreadId ? (
             <MessageInput threadId={selectedThreadId} />
           ) : (
             <ThreadComposer onCreate={(threadId) => setSelectedThreadId(threadId)} />
           )}
         </div>
       </div>
     );
   }
   ```

### Phase 4: Replace Custom Chat UI

1. **Identify and remove custom chat components**:
   - Locate all custom chat UI components
   - Remove any custom message lists, input boxes, etc.
   - Remove custom streaming implementations

2. **Replace with ChatKit components**:
   - Replace custom message lists with `<MessageList>`
   - Replace custom input with `<MessageInput>`
   - Replace custom composers with `<ThreadComposer>`
   - Update any custom styling to work with ChatKit components

### Phase 5: Implement Protocol Compliance

1. **Use ChatKit hooks properly**:
   - Replace any custom state management for messages with `useChat`
   - Use `useThread` for thread-specific operations
   - Implement thread switching functionality with ChatKit's thread management

2. **Ensure tool call support**:
   - Configure ChatKit to handle tool calls from the backend
   - Verify that tool call responses are properly displayed

3. **Support multi-turn conversations**:
   - Implement proper thread management
   - Handle conversation history correctly
   - Maintain context across multiple messages

### Phase 6: Add Required UI Elements

1. **Implement loading indicators**:
   - Add loading states for message sending/receiving
   - Show typing indicators when assistant is responding
   - Handle connection status indicators

2. **Add error handling UI**:
   - Display error messages when API calls fail
   - Show connection errors
   - Handle authentication failures gracefully

3. **Style ChatKit components**:
   - Apply your application's design system to ChatKit components
   - Customize appearance while maintaining functionality
   - Ensure responsive design for all screen sizes

### Phase 7: Integrate with Existing Features

1. **Connect authentication**:
   - Ensure the ChatProvider receives valid authentication tokens
   - Handle token refresh if needed
   - Implement proper logout functionality

2. **Link with user profiles**:
   - Connect user identity to ChatKit threads
   - Implement user avatars and names in messages
   - Handle user preferences for chat

3. **Connect with notifications**:
   - Implement unread message indicators
   - Add desktop notifications if needed
   - Link with existing notification system

## Post-Implementation Validation

1. **Test core functionality**:
   - Verify message sending and receiving works
   - Test thread creation and switching
   - Confirm streaming responses work properly
   - Test error handling scenarios

2. **Validate protocol compliance**:
   - Ensure all communication goes through ChatKit protocol
   - Verify no direct API calls bypass ChatKit
   - Check that all features use ChatKit-provided components

3. **Performance testing**:
   - Test with multiple concurrent threads
   - Verify performance with long conversation histories
   - Check memory usage and cleanup

4. **Cross-browser compatibility**:
   - Test in supported browsers
   - Verify mobile responsiveness
   - Check accessibility features