import React from 'react';
import ReactMarkdown from 'react-markdown';

interface TextContentProps {
  content?: string;
}

const TextContent: React.FC<TextContentProps> = ({ content }) => {
  return (
    <div style={{ padding: '20px', textAlign: 'left' }}>
      <ReactMarkdown>{content || ''}</ReactMarkdown>
    </div>
  );
};

export default TextContent;
