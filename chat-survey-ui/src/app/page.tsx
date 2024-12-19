'use client'

import { useState, useEffect } from "react"
import { MessageBubble } from "@/components/message-bubble"
import { DialecticSidebar } from "@/components/dialectic-sidebar"
import { ChatsSidebar } from "@/components/chats-sidebar"
import { InteractionDetail } from "@/components/interaction-detail"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { PanelLeftOpen, PanelRightOpen } from 'lucide-react'
import { AuthService } from "@/services/authService";
import { DialecticService } from "@/services/dialecticService";
import { v4 as uuidv4 } from 'uuid';
import type { Message, DialecticInteraction } from "@/types/chat"
import type { Belief, QuestionAnswerInteraction } from "@epistemicme/sdk"

// Define types to match the fixture data
interface StructuredMessage {
  role: 'user' | 'assistant'
  content: string
}

interface Conversation {
  participant_id: string
  participant_name: string
  messages: StructuredMessage[]
}

interface StructuredConversations {
  total_conversations: number
  average_messages: string
  conversations: Conversation[]
}

export default function ChatPage() {
  const [isLeftSidebarOpen, setLeftSidebarOpen] = useState(true)
  const [isRightSidebarOpen, setRightSidebarOpen] = useState(true)
  const [selectedInteraction, setSelectedInteraction] = useState<DialecticInteraction | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null)
  const [dialecticServices, setDialecticServices] = useState<Map<string, DialecticService>>(new Map());
  const [interactions, setInteractions] = useState<DialecticInteraction[]>([]);

  // Initialize auth
  useEffect(() => {
    AuthService.getInstance().initialize()
      .catch(console.error);
  }, []);

  // Load conversations
  useEffect(() => {
    const loadConversations = async () => {
      try {
        const response = await fetch('/fixtures/structured_conversations.json');
        const data: StructuredConversations = await response.json();
        
        const transformedConversations = data.conversations
          .filter(conv => conv.messages.length > 6)
          .map((conv, index) => ({
            ...conv,
            participant_id: `${conv.participant_id}-${index}`
          }));

        // Create self models for each conversation
        const services = new Map<string, DialecticService>();
        await Promise.all(
          transformedConversations.map(async (conv) => {
            const selfModelId = uuidv4();
            const service = new DialecticService(selfModelId);
            await service.createSelfModel();
            services.set(conv.participant_id, service);
          })
        );

        setDialecticServices(services);
        setConversations(transformedConversations);
        
        if (transformedConversations.length > 0) {
          setSelectedConversation(transformedConversations[0].participant_id);
          const initialMessages = transformedConversations[0].messages.map((msg, index) => ({
            id: index.toString(),
            type: msg.role === 'user' ? 'question' as const : 'answer' as const,
            content: msg.content,
            timestamp: new Date()
          }));
          setMessages(initialMessages);
        }
      } catch (error) {
        console.error('Error loading conversations:', error);
      }
    };

    loadConversations();
  }, []);

  // Handle conversation selection
  const handleConversationSelect = async (conversationId: string) => {
    setSelectedConversation(conversationId);
    setInteractions([]); // Clear previous interactions
    const conversation = conversations.find(c => c.participant_id === conversationId);
    const service = dialecticServices.get(conversationId);
    
    if (conversation && service) {
      // Create new dialectic
      const dialecticResponse = await service.createDialectic();
      const dialecticId = dialecticResponse.dialectic?.id;

      if (dialecticId) {
        // Process first few message pairs
        const maxPairs = 3;
        let processedPairs = 0;

        // Process pairs sequentially
        for (let i = 0; i < conversation.messages.length - 1 && processedPairs < maxPairs; i++) {
          const currentMsg = conversation.messages[i];
          const nextMsg = conversation.messages[i + 1];
          
          if (currentMsg.role === 'assistant' && nextMsg.role === 'user') {
            try {
              // Wait for each update to complete
              const response = await service.updateDialecticWithMessage(
                dialecticId,
                currentMsg.content,
                nextMsg.content
              );

              // Update interactions in UI
              if (response.dialectic?.userInteractions) {
                const newInteractions = response.dialectic.userInteractions.map((interaction) => {
                  const qa = interaction?.interaction?.value as QuestionAnswerInteraction;
                  const extractedBeliefs = qa?.extractedBeliefs || [];

                  console.log('Raw extracted beliefs:', extractedBeliefs);

                  const mappedBeliefs = extractedBeliefs.map((belief: Belief) => {
                    console.log('Processing belief:', belief);
                    console.log('Belief content:', belief.content);
                    
                    // Extract the raw string from the content array
                    const rawContent = Array.isArray(belief.content) && belief.content[0]?.rawStr 
                      ? belief.content[0].rawStr 
                      : '';

                    console.log('Extracted raw content:', rawContent);
                    
                    return {
                      id: belief.id || '',
                      content: rawContent
                    };
                  });

                  console.log('Mapped beliefs:', mappedBeliefs);

                  return {
                    id: interaction.id || uuidv4(),
                    question: qa?.question?.question || '',
                    answer: qa?.answer?.userAnswer || '',
                    beliefs: mappedBeliefs,
                    timestamp: new Date()
                  } as DialecticInteraction;
                });

                setInteractions(prev => [...prev, ...newInteractions]);
              }

              processedPairs++;
              // Wait before next update
              await new Promise(resolve => setTimeout(resolve, 2000));
            } catch (error) {
              console.error('Error updating dialectic:', error);
            }
          }
        }
      }

      // Update messages display
      const newMessages = conversation.messages.map((msg, index) => ({
        id: index.toString(),
        type: msg.role === 'user' ? 'question' as const : 'answer' as const,
        content: msg.content,
        timestamp: new Date()
      }));
      setMessages(newMessages);
    }
  };

  return (
    <div className="flex h-screen">
      {isLeftSidebarOpen && (
        <ChatsSidebar 
          onClose={() => setLeftSidebarOpen(false)}
          conversations={conversations}
          selectedConversation={selectedConversation}
          onSelectConversation={handleConversationSelect}
        />
      )}
      
      <div className="flex-1 flex flex-col">
        <header className="h-14 border-b flex items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setLeftSidebarOpen(!isLeftSidebarOpen)}
            >
              <PanelLeftOpen className="h-4 w-4" />
            </Button>
            <h1 className="font-semibold">
              {selectedConversation ? 
                conversations.find(c => c.participant_id === selectedConversation)?.participant_name || 'Dialectic Chat' 
                : 'Dialectic Chat'}
            </h1>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setRightSidebarOpen(!isRightSidebarOpen)}
          >
            <PanelRightOpen className="h-4 w-4" />
          </Button>
        </header>
        
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-4 max-w-2xl mx-auto">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
          </div>
        </ScrollArea>
        
        <div className="border-t p-4">
          <div className="max-w-2xl mx-auto flex gap-2">
            <Input placeholder="Type your message..." className="flex-1" />
            <Button>Send</Button>
          </div>
        </div>
      </div>
      
      {isRightSidebarOpen && (
        <DialecticSidebar
          interactions={interactions}
          onInteractionSelect={setSelectedInteraction}
          onClose={() => setRightSidebarOpen(false)}
        />
      )}
      
      <InteractionDetail
        interaction={selectedInteraction}
        onClose={() => setSelectedInteraction(null)}
      />
    </div>
  )
}

