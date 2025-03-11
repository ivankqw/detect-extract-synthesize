import React, { ReactNode, useEffect, useRef } from 'react';
import { useChat } from "ai/react";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import { usePageNavigation } from '../_hooks/PageNavigationContext';

interface ChatProps {
    docId: string;
}

interface ChatOptions {
    api: string;
    headers: {
        "Content-Type": string;
    };
    body?: Object;
}

const options: ChatOptions = {
    api: "/backend/ask",
    headers: {
        "Content-Type": "application/json",
    },
};

const Chat: React.FC<ChatProps> = ({ docId }) => {
    // add docId to the options as body
    options.body = { doc_id: docId };
    const { messages, input, handleInputChange, handleSubmit } = useChat(options);
    const { navigateToPage } = usePageNavigation();
    const messagesContainerRef = useRef<HTMLDivElement>(null);
    
    useEffect(() => {
        if (messagesContainerRef.current) {
          messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
        }
      }, [messages]);

    // Custom component for handling page numbers and answers
    const PageNumberComponent = ({ children }: { children: ReactNode }) => {
        if (typeof children === 'string') {
            const parts = children.split(/Page number: (\d+)/);
            const text = parts[0];
            const pageNumber = parts[1] || '';
            const answer = parts[2] || '';
            // check if answer can be split with "Answer: "
            if (answer) {
                const answerParts = answer.split(/Answer: /);
                if (answerParts.length > 1) {
                    return (
                        <>
                            {text}
                            {pageNumber && (
                                <span
                                    className="text-sky-400 hover:underline cursor-pointer"
                                    onClick={() => navigateToPage(parseInt(pageNumber, 10) + 1)}
                                >
                                    Page number: {parseInt(pageNumber, 10) + 1}
                                </span>
                            )}
                            <br></br>
                            {answerParts[1]}
                        </>
                    );
                }
            }
            return (
                <>
                    {text}
                    {pageNumber && (
                        <span
                            className="text-sky-400 hover:underline cursor-pointer prose break-words dark:prose-invert prose-p:leading-relaxed prose-pre:p-0 whitespace-pre-line"
                            onClick={() => navigateToPage(parseInt(pageNumber, 10) + 1)}
                        >
                            Page number: {parseInt(pageNumber, 10) + 1}
                        </span>
                    )}
                    <br></br>
                    {answer}
                </>
            );
        }
    };

    return (
        <div className="bg-gray-800 text-white p-4 m-4 rounded-lg flex flex-col border border-gray-600 h-4/5">
            <div ref={messagesContainerRef} className="flex-grow overflow-auto mb-4 p-2 max-h-screen">
                {messages.map(m => (
                    <div key={m.id} className="p-2 rounded bg-gray-700 mb-2">
                        <span className="font-bold">
                            {m.role === 'user' ? 'User: ' : 'AI: '}
                        </span>
                        <ReactMarkdown
                            className="prose break-words dark:prose-invert prose-p:leading-relaxed prose-pre:p-0 whitespace-pre-line"
                            remarkPlugins={[remarkGfm, remarkMath]}
                            components={{
                                // Override the p component to check for "Page number" pattern
                                p: ({ node, ...props }) => {
                                    console.log('Node:', node);
                                    if (node && node.children) {
                                        const newChildren = node.children.map((child, index) => {
                                            if (child.type === 'text' && typeof child.value === 'string') {
                                                return <PageNumberComponent key={index}>{child.value}</PageNumberComponent>;
                                            } 
                                            return null;
                                        }).filter(Boolean);
                                        return <p {...props}>{newChildren}</p>;
                                    }
                                    return <p {...props} />;
                                },
                                ul: ({ node, ...props }) => <ul className="list-disc pl-5 space-y-2 dark:list-disc" {...props} />,
                                ol: ({ node, ...props }) => <ol className="list-decimal pl-5 space-y-2 dark:list-decimal" {...props} />,
                                li: ({ node, ...props }) => <li className="pl-2 dark:pl-2" {...props} />,
                            }}
                        >
                            {m.content}
                        </ReactMarkdown>
                    </div>
                ))}
            </div>
            <div className="mt-auto">
                <form onSubmit={handleSubmit} className="flex flex-col">
                    <label htmlFor="ask-input" className="sr-only">Say something...</label>
                    <input
                        id="ask-input"
                        type="text"
                        value={input}
                        onChange={handleInputChange}
                        placeholder="Type your message..."
                        className="w-full p-2 mb-2 text-gray-900 rounded bg-gray-50"
                    />
                    <button type="submit" className="w-full p-2 text-gray-900 bg-blue-500 rounded hover:bg-blue-600">
                        Send
                    </button>
                </form>
            </div>
        </div>
    );
};

export default Chat;