import React from 'react';

interface FollowUpQuestionsProps {
  followup: string[];
}

const FollowUpQuestions: React.FC<FollowUpQuestionsProps> = ({ followup }) => {
  return (
    <div className="followUpQuestions bg-gray-800 rounded-lg p-6 mt-8 shadow-md">
      <h3 className="text-xl font-semibold text-gray-200 mb-4">Follow-up questions</h3>
      {followup && followup.length > 0 ? (
        <ul className="space-y-2">
          {followup.map((question, index) => (
            <li key={`followup-${index}`} className="transition-all duration-200 ease-in-out hover:translate-x-1">
              <a
                href={`?question=${encodeURIComponent(question)}`}
                className="text-white-600 flex items-center"
              >
                <svg
                  className="w-4 h-4 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
                {question}
              </a>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-gray-600 italic">No follow-up questions available.</p>
      )}
    </div>
  );
};

export default FollowUpQuestions;