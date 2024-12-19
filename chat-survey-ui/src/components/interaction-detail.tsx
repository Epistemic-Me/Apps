import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { ScrollArea } from "@/components/ui/scroll-area"
import { DialecticInteraction } from "@/types/chat"

interface InteractionDetailProps {
  interaction: DialecticInteraction | null
  onClose: () => void
}

export function InteractionDetail({ interaction, onClose }: InteractionDetailProps) {
  if (!interaction) return null

  console.log('Interaction in detail:', interaction);
  console.log('Beliefs to render:', interaction.beliefs);

  return (
    <Dialog open={!!interaction} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl h-[600px]">
        <DialogHeader>
          <DialogTitle>Dialectic Interaction</DialogTitle>
        </DialogHeader>
        <ScrollArea className="h-full pr-4">
          <div className="space-y-6">
            <div>
              <h3 className="font-semibold mb-2">Question</h3>
              <p className="text-sm text-muted-foreground">{interaction.question}</p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">Answer</h3>
              <p className="text-sm text-muted-foreground">{interaction.answer}</p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">Beliefs</h3>
              <ul className="list-disc list-inside space-y-2">
                {interaction.beliefs.map((belief) => (
                  <li key={belief.id} className="text-sm text-muted-foreground">
                    {belief.content}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  )
}

