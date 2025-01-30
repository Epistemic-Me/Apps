import { ScrollArea } from "@/components/ui/scroll-area"
import { Button } from "@/components/ui/button"
import { ChevronDown, X } from 'lucide-react'
import { DialecticalInteraction, QuestionAnswerValue } from "@/types/chat"

interface DialecticSidebarProps {
  interactions: DialecticalInteraction[]
  onInteractionSelect: (interaction: DialecticalInteraction) => void
  onClose: () => void
}

function isQuestionAnswer(value: any): value is QuestionAnswerValue {
  return value?.type === 'questionAnswer';
}

export function DialecticSidebar({ 
  interactions, 
  onInteractionSelect,
  onClose 
}: DialecticSidebarProps) {
  return (
    <div className="w-[320px] border-l">
      <div className="flex items-center justify-between border-b p-4">
        <div className="space-y-1">
          <h2 className="text-sm font-semibold">Chat Controls</h2>
          <p className="text-xs text-muted-foreground">
            Dialectic Interactions ({interactions.length})
          </p>
        </div>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>
      <ScrollArea className="h-[calc(100vh-64px)]">
        <div className="p-4 space-y-4">
          {interactions.map((interaction) => {
            const value = interaction.interaction.type?.value;
            if (!isQuestionAnswer(value)) return null;

            return (
              <Button
                key={interaction.id}
                variant="ghost"
                className="w-full justify-start text-left"
                onClick={() => onInteractionSelect(interaction)}
              >
                <div className="space-y-1">
                  <div className="flex items-center">
                    <span className="font-medium truncate">
                      {value.question}
                    </span>
                    <ChevronDown className="ml-auto h-4 w-4" />
                  </div>
                  <p className="text-xs text-muted-foreground line-clamp-2">
                    {value.extractedBeliefs?.length || 0} beliefs extracted
                  </p>
                </div>
              </Button>
            );
          })}
        </div>
      </ScrollArea>
    </div>
  )
}

