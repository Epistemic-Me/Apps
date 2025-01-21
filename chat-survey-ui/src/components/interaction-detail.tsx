import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { ScrollArea } from "@/components/ui/scroll-area"
import { DialecticalInteraction } from "@/types/chat"

interface InteractionDetailProps {
  interaction: DialecticalInteraction | null
  onClose: () => void
}

export function InteractionDetail({ interaction, onClose }: InteractionDetailProps) {
  console.log('Detail interaction:', {
    id: interaction?.id,
    question: interaction?.interaction?.type?.value?.question?.question,
    answer: interaction?.interaction?.type?.value?.answer?.userAnswer,
    beliefs: interaction?.interaction?.type?.value?.extractedBeliefs
  });
  if (!interaction) return null

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
              <p className="text-sm text-muted-foreground">
                {interaction.interaction.type?.value?.question?.question}
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">Answer</h3>
              <p className="text-sm text-muted-foreground">
                {interaction.interaction.type?.value?.answer?.userAnswer}
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">Extracted Beliefs</h3>
              <ul className="list-disc list-inside space-y-2">
                {interaction.interaction.type?.value?.extractedBeliefs?.map((belief) => (
                  <li key={belief.id} className="text-sm text-muted-foreground">
                    {belief.content?.[0]?.rawStr}
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

