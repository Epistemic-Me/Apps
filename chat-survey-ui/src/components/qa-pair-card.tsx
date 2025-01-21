import { Message } from "@/types/chat"
import { MessageBubble } from "./message-bubble"
import { Button } from "./ui/button"
import { Info, Plus } from "lucide-react"
import { useState } from "react"

interface QAPairCardProps {
  question: Message
  answer: Message
  onInspect?: () => void
  onExtractBeliefs?: () => Promise<void>
  hasBeliefs?: boolean
}

export function QAPairCard({ 
  question, 
  answer, 
  onInspect, 
  onExtractBeliefs,
  hasBeliefs 
}: QAPairCardProps) {
  const [isExtracting, setIsExtracting] = useState(false);

  const handleExtract = async () => {
    if (!onExtractBeliefs) return;
    setIsExtracting(true);
    try {
      await onExtractBeliefs();
    } finally {
      setIsExtracting(false);
    }
  };

  return (
    <div className="border rounded-lg p-4 space-y-2 bg-background/50">
      <div className="flex justify-between items-start">
        <div className="flex-1 space-y-2">
          <MessageBubble message={question} />
          <MessageBubble message={answer} />
        </div>
        <div className="flex flex-col gap-2 ml-2">
          {onExtractBeliefs && !hasBeliefs && (
            <Button 
              variant="outline" 
              size="icon"
              onClick={handleExtract}
              disabled={isExtracting}
            >
              {isExtracting ? (
                <div className="animate-spin">⟳</div>
              ) : (
                <Plus className="h-4 w-4" />
              )}
            </Button>
          )}
          {hasBeliefs && (
            <Button 
              variant="ghost" 
              size="icon"
              onClick={onInspect}
            >
              <Info className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
} 