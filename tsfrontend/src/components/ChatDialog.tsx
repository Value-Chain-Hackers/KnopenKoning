import React, { useState, useRef, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTimes, faComments } from '@fortawesome/free-solid-svg-icons';
import './ChatDialog.css';
import he from 'he';
interface ChatDialogProps {
  isOpen: boolean;
  sessionId?: string;
  onClose: () => void;
}

const ChatDialog: React.FC<ChatDialogProps> = ({ isOpen, sessionId, onClose }) => {
  const [messages, setMessages] = useState<string[]>([]);
  const [input, setInput] = useState<string>('');
  const [isReceiving, setIsReceiving] = useState<boolean>(false);
  const messageEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    if (messageEndRef.current) {
      messageEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (input.trim()) {
      setMessages((prevMessages) => [...prevMessages, `You: ${input}`, '']);
      await sendMessage(input);
      setInput('');
    }
  };

  const sendMessage = async (message: string) => {
    setIsReceiving(true);
    try {
      const response = await fetch(`https://backend.valuechainhackers.xyz/ai/ask/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({"message": message, "sessionId":sessionId }),
      });
      if (!response.body) {
        throw new Error('ReadableStream not supported.');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let result = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        result += decoder.decode(value);
        setMessages((prevMessages) => {
          const newMessages = [...prevMessages];
          newMessages[newMessages.length - 1] = result;
          return newMessages;
        });
      }
    } catch (error: any) {
      setMessages((prevMessages) => [...prevMessages, `Error: ${error.message}`]);
    } finally {
      setIsReceiving(false);
      scrollToBottom();
    }
  };

  return (
    <div className={`chat-dialog fixed top-0 right-0 h-full bg-gray-800 text-white transition-transform duration-300 ${isOpen ? 'w-80' : 'w-0'} overflow-hidden`}>
      <div className="chat-header bg-blue-500 p-4 flex justify-between items-center">
        <div className="flex items-center">
          <FontAwesomeIcon icon={faComments} className="mr-2" />
          <h2>Chat</h2>
        </div>
        <button onClick={onClose} className="text-white">
          <FontAwesomeIcon icon={faTimes} />
        </button>
      </div>
      <div className="chat-content p-4 flex flex-col h-full">
        <b>Session</b>
        <div className="messages flex-1 overflow-auto">
          {messages.map((msg, index) => (
            <div key={index} className="message mb-2">
            <div dangerouslySetInnerHTML={{ __html: he.decode(msg).replaceAll("\\n","<br />").replaceAll('"', '') }} />
            </div>
          ))}
          <div ref={messageEndRef} />
        </div>
        <form onSubmit={handleSubmit} className="mt-4 flex">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="flex-1 p-2 bg-gray-700 border border-gray-600 rounded-l text-white"
            placeholder="Type a message..."
          />
          <button type="submit" className="p-2 bg-blue-500 border border-blue-500 rounded-r text-white" disabled={isReceiving}>
            Send
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatDialog;
