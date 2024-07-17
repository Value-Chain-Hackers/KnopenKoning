// src/components/StarterCard.tsx
import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { IconDefinition } from '@fortawesome/fontawesome-svg-core';

interface StarterCardProps {
  icon: IconDefinition;
  text: string;
  color?: string;
  onClick: (message: string) => void;
}

const StarterCard: React.FC<StarterCardProps> = ({ icon, text, onClick, color = "yellow" }) => {
    return (
      <div
        className="starter-card p-4 border rounded bg-gray-700 cursor-pointer"
        onClick={() => onClick(text)}
      >
        <FontAwesomeIcon icon={icon} className={`text-${color}-500 mr-2`} style={{ color: color }} size='lg'/>
        <span className='text-white'>{text}</span>
      </div>
    );
  };

export default StarterCard;
