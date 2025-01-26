import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { ScrollArea } from "@/components/ui/scroll-area"
import { DialecticalInteraction, QuestionAnswerValue } from "@/types/chat"

interface InteractionDetailProps {
  interaction: DialecticalInteraction | null
  onClose: () => void
}

function isQuestionAnswer(value: any): value is QuestionAnswerValue {
  return value?.type === 'questionAnswer';
}

export function InteractionDetail({ interaction, onClose }: InteractionDetailProps) {
  if (!interaction) return null;

  const value = interaction.interaction.type?.value;
  if (!isQuestionAnswer(value)) return null;

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
                {value.question}
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">Answer</h3>
              <p className="text-sm text-muted-foreground">
                {value.answer}
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">Extracted Beliefs</h3>
              <ul className="list-disc list-inside space-y-2">
                {value.extractedBeliefs?.map((belief) => (
                  <li key={belief.id} className="text-sm text-muted-foreground">
                    {Array.isArray(belief.content) 
                      ? belief.content[0]?.rawStr 
                      : belief.content}
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

