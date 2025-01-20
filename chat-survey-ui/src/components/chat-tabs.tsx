import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface ChatTabsProps {
  activeTab: 'conversation' | 'qa'
  onTabChange: (tab: 'conversation' | 'qa') => void
}

export function ChatTabs({ activeTab, onTabChange }: ChatTabsProps) {
  return (
    <div className="flex space-x-1 border-b px-4">
      <Button
        variant="ghost"
        className={cn(
          "relative h-9 rounded-none border-b-2 border-transparent",
          activeTab === 'conversation' && "border-primary"
        )}
        onClick={() => onTabChange('conversation')}
      >
        Conversation
      </Button>
      <Button
        variant="ghost"
        className={cn(
          "relative h-9 rounded-none border-b-2 border-transparent",
          activeTab === 'qa' && "border-primary"
        )}
        onClick={() => onTabChange('qa')}
      >
        Q&A Pairs
      </Button>
    </div>
  )
} 