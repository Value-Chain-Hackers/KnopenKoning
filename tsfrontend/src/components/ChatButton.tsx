import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faComments } from '@fortawesome/free-solid-svg-icons';
import './ChatButton.css';

interface ChatButtonProps {
  onClick: () => void;
}

const ChatButton: React.FC<ChatButtonProps> = ({ onClick }) => {
  return (
    <button className="chat-button fixed bottom-4 right-4 bg-blue-500 text-white rounded-full w-16 h-16 flex items-center justify-center z-50 hover:bg-blue-700" onClick={onClick}>
      <FontAwesomeIcon icon={faComments} size="lg" />
    </button>
  );
};

export default ChatButton;
