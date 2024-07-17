import React from 'react';

interface TextContentProps {
  content?: string;
}

const TextContent: React.FC<TextContentProps> = ({ content }) => {
  return (
    <div>
      <p>{content}</p>
    </div>
  );
};

export default TextContent;
