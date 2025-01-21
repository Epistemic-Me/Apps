'use client'

import React, { useState, useEffect, useCallback } from "react"
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
import type { Message, DialecticalInteraction } from "@/types/chat"
// import type { Belief, QuestionAnswerInteraction } from "@epistemicme/sdk"
import { ChatTabs } from "@/components/chat-tabs"
import { QAPairCard } from "@/components/qa-pair-card"

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
  const [selectedInteraction, setSelectedInteraction] = useState<DialecticalInteraction | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null)
  const [dialecticServices, setDialecticServices] = useState<Map<string, DialecticService>>(new Map());
  const [interactions, setInteractions] = useState<DialecticalInteraction[]>([]);
  const [activeTab, setActiveTab] = useState<'conversation' | 'qa'>('conversation')
  const [processedQA, setProcessedQA] = useState<Map<string, Message[]>>(new Map())
  const [isProcessingQA, setIsProcessingQA] = useState(false);
  const [processedPairs, setProcessedPairs] = useState<Set<string>>(new Set());

  // Initialize auth
  useEffect(() => {
    AuthService.getInstance().initialize()
      .catch(console.error);
  }, []);

  // First declare processQAPairs
  const processQAPairs = useCallback(async (conversationId: string, messages: StructuredMessage[]) => {
    console.log('Processing QA pairs for conversation:', conversationId);
    setIsProcessingQA(true);
    try {
      const service = dialecticServices.get(conversationId);
      if (!service) {
        console.log('No service found for conversation:', conversationId);
        return;
      }

      const processedMessages: Message[] = [];
      
      for (let i = 0; i < messages.length - 1; i++) {
        const currentMsg = messages[i];
        const nextMsg = messages[i + 1];
        
        if (currentMsg.role === 'assistant' && nextMsg.role === 'user') {
          try {
            console.log('Processing pair:', { 
              question: currentMsg.content.slice(0, 50), 
              answer: nextMsg.content.slice(0, 50) 
            });
            
            const response = await service.preprocessQuestionAnswer(
              currentMsg.content,
              nextMsg.content
            );

            console.log('Received QA pairs:', response.qaPairs);

            response.qaPairs.forEach((pair) => {
              processedMessages.push({
                id: `q-${processedMessages.length}`,
                type: 'question',
                content: pair.question,
                timestamp: new Date()
              });
              processedMessages.push({
                id: `a-${processedMessages.length}`,
                type: 'answer',
                content: pair.answer,
                timestamp: new Date()
              });
            });
          } catch (error) {
            console.error('Error processing Q&A:', error);
          }
        }
      }

      console.log('Setting processed messages:', processedMessages);
      setProcessedQA(prev => new Map(prev.set(conversationId, processedMessages)));
    } finally {
      setIsProcessingQA(false);
    }
  }, [dialecticServices]);

  // First effect to load conversations
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
          const firstConversation = transformedConversations[0];
          setSelectedConversation(firstConversation.participant_id);
          
          const initialMessages = firstConversation.messages.map((msg, index) => ({
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
  }, []); // No dependencies needed

  // Second effect to process initial Q&A
  useEffect(() => {
    const processInitialQA = async () => {
      if (selectedConversation && dialecticServices.size > 0 && !processedQA.has(selectedConversation)) {
        const conversation = conversations.find(c => c.participant_id === selectedConversation);
        if (conversation) {
          await processQAPairs(selectedConversation, conversation.messages);
        }
      }
    };

    processInitialQA();
  }, [selectedConversation, dialecticServices, processQAPairs, conversations, processedQA]);

  // Update conversation selection handler
  const handleConversationSelect = async (conversationId: string) => {
    console.log('Selecting conversation:', conversationId);
    setSelectedConversation(conversationId);
    const conversation = conversations.find(c => c.participant_id === conversationId);
    
    if (conversation) {
      // Update raw messages
      const newMessages = conversation.messages.map((msg, index) => ({
        id: index.toString(),
        type: msg.role === 'user' ? 'question' as const : 'answer' as const,
        content: msg.content,
        timestamp: new Date()
      }));
      setMessages(newMessages);

      // Process Q&A pairs if not already processed
      if (!processedQA.has(conversationId)) {
        await processQAPairs(conversationId, conversation.messages);
      }
    }
  };

  const extractBeliefs = useCallback(async (pair: { question: Message, answer: Message }) => {
    if (!selectedConversation) {
      console.log('No conversation selected');
      return;
    }
    
    const service = dialecticServices.get(selectedConversation);
    if (!service) {
      console.log('No service found for conversation');
      return;
    }

    try {
      console.log('Creating dialectic...');
      const dialectic = await service.createDialectic();
      if (!dialectic.dialectic?.id) {
        console.log('No dialectic ID returned');
        return;
      }

      console.log('Updating dialectic with message...');
      const response = await service.updateDialecticWithMessage(
        dialectic.dialectic.id,
        pair.question.content,
        pair.answer.content
      );

      console.log('Response from update:', response);
      if (response.dialectic?.userInteractions?.[0]) {
        const interaction = response.dialectic.userInteractions[0];
        console.log('New interaction:', interaction);
        setInteractions(prev => {
          console.log('Previous interactions:', prev);
          const updated = [...prev, interaction];
          console.log('Updated interactions:', updated);
          return updated;
        });
        return interaction;
      }
    } catch (error) {
      console.error('Error extracting beliefs:', error);
    }
  }, [selectedConversation, dialecticServices]);

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
        
        <ChatTabs activeTab={activeTab} onTabChange={setActiveTab} />
        
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-4 max-w-2xl mx-auto">
            {activeTab === 'conversation' ? (
              messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))
            ) : (
              // QA tab content
              (() => {
                console.log('Rendering QA tab:', {
                  selectedConversation,
                  hasProcessedQA: selectedConversation ? processedQA.has(selectedConversation) : false,
                  qaMessages: selectedConversation ? processedQA.get(selectedConversation) : undefined
                });
                
                if (isProcessingQA) {
                  return (
                    <div className="text-center text-muted-foreground">
                      Processing Q&A pairs...
                    </div>
                  );
                }

                const messages = selectedConversation ? processedQA.get(selectedConversation) : undefined;
                if (!messages) return null;

                // Group messages into pairs
                const pairs: { question: Message, answer: Message }[] = [];
                for (let i = 0; i < messages.length; i += 2) {
                  if (messages[i] && messages[i + 1]) {
                    pairs.push({
                      question: messages[i],
                      answer: messages[i + 1]
                    });
                  }
                }

                return (
                  <div className="space-y-4">
                    {pairs.map((pair, index) => (
                      <QAPairCard
                        key={`pair-${index}`}
                        question={pair.question}
                        answer={pair.answer}
                        hasBeliefs={processedPairs.has(`${pair.question.id}-${pair.answer.id}`)}
                        onExtractBeliefs={async () => {
                          const interaction = await extractBeliefs(pair);
                          if (interaction) {
                            setProcessedPairs(prev => new Set(prev).add(`${pair.question.id}-${pair.answer.id}`));
                          }
                        }}
                        onInspect={() => {
                          const interaction = interactions.find(i => 
                            i.interaction.type?.value?.question?.question === pair.question.content && 
                            i.interaction.type?.value?.answer?.userAnswer === pair.answer.content
                          );
                          if (interaction) {
                            setSelectedInteraction(interaction);
                          }
                        }}
                      />
                    ))}
                  </div>
                );
              })()
            )}
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

