import ReactMarkdown from 'react-markdown'
import { Message } from "@/types/chat"
import { cn } from "@/lib/utils"

interface MessageBubbleProps {
  message: Message
}

// Define component props type
type MarkdownComponentProps = {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  node?: any
  children?: React.ReactNode
  className?: string
}

export function MessageBubble({ message }: MessageBubbleProps) {
  return (
    <div
      className={cn(
        "flex w-full",
        message.type === "answer" ? "justify-start" : "justify-end"
      )}
    >
      <div
        className={cn(
          "rounded-lg px-4 py-2 max-w-[80%]",
          message.type === "answer" 
            ? "bg-muted" 
            : "bg-primary text-primary-foreground"
        )}
      >
        <ReactMarkdown
          className={cn(
            "prose prose-sm",
            message.type === "answer" 
              ? "prose-neutral" 
              : "prose-invert"
          )}
          components={{
            h1: ({children, ...props}: MarkdownComponentProps) => 
              <h1 className="text-xl font-bold mt-2 mb-4" {...props}>{children}</h1>,
            h2: ({children, ...props}: MarkdownComponentProps) => 
              <h2 className="text-lg font-bold mt-2 mb-3" {...props}>{children}</h2>,
            h3: ({children, ...props}: MarkdownComponentProps) => 
              <h3 className="text-md font-bold mt-2 mb-2" {...props}>{children}</h3>,
            p: ({children, ...props}: MarkdownComponentProps) => 
              <p className="mb-2" {...props}>{children}</p>,
            ul: ({children, ...props}: MarkdownComponentProps) => 
              <ul className="list-disc ml-4 mb-2" {...props}>{children}</ul>,
            ol: ({children, ...props}: MarkdownComponentProps) => 
              <ol className="list-decimal ml-4 mb-2" {...props}>{children}</ol>,
            li: ({children, ...props}: MarkdownComponentProps) => 
              <li className="mb-1" {...props}>{children}</li>,
            strong: ({children, ...props}: MarkdownComponentProps) => 
              <strong className="font-bold" {...props}>{children}</strong>,
            em: ({children, ...props}: MarkdownComponentProps) => 
              <em className="italic" {...props}>{children}</em>,
            hr: (props: MarkdownComponentProps) => 
              <hr className="my-4 border-t" {...props} />,
          }}
        >
          {message.content}
        </ReactMarkdown>
      </div>
    </div>
  )
}

