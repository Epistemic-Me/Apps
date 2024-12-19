import { ScrollArea } from "@/components/ui/scroll-area"
import { Button } from "@/components/ui/button"
import { X } from 'lucide-react'

interface Conversation {
  participant_id: string
  participant_name: string
  messages: {
    role: 'user' | 'assistant'
    content: string
  }[]
}

interface ChatsSidebarProps {
  onClose: () => void
  conversations: Conversation[]
  selectedConversation: string | null
  onSelectConversation: (conversationId: string) => void
}

export function ChatsSidebar({ 
  onClose, 
  conversations,
  selectedConversation,
  onSelectConversation 
}: ChatsSidebarProps) {
  console.log('Rendering ChatsSidebar with conversations:', conversations)
  
  const handleClick = (conversation: Conversation, index: number) => {
    console.log('Clicked conversation:', conversation, 'at index:', index)
    onSelectConversation(conversation.participant_id)
  }

  return (
    <div className="w-80 border-r bg-background">
      <div className="h-14 border-b flex items-center justify-between px-4">
        <h2 className="font-semibold">Chats</h2>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>
      <ScrollArea className="h-[calc(100vh-3.5rem)] p-2">
        <div className="space-y-2">
          {conversations.map((conversation, index) => (
            <Button
              key={index}
              variant={selectedConversation === conversation.participant_id ? "secondary" : "ghost"}
              className="w-full justify-start"
              onClick={() => handleClick(conversation, index)}
            >
              <div className="flex flex-col items-start">
                <span className="font-medium">
                  {conversation.participant_name === 'Anonymous' 
                    ? `Anonymous (${index + 1})`
                    : conversation.participant_name}
                </span>
                <span className="text-sm text-muted-foreground truncate">
                  {conversation.messages.length} messages
                </span>
              </div>
            </Button>
          ))}
        </div>
      </ScrollArea>
    </div>
  )
}

