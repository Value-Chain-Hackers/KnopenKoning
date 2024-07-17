import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import Graph from '../components/Graph';
import TabControl from '../components/TabControl';

interface Question {
  uid: string;
  company: string;
  question: string;
  // Add other fields as necessary
}

const QuestionPage: React.FC = () => {
  const { uid } = useParams<{ uid: string }>();
  const [question, setQuestion] = useState<Question | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchQuestion = async () => {
    //   try {
    //     const response = await fetch(`http://localhost:18000/view/${uid}`);
    //     if (!response.ok) {
    //      // throw new Error('Failed to fetch question details');
    //     }
    //     const data: Question = await response.json();
    //     setQuestion(data);
    //   } catch (err: any) {
    //     setError(err.message);
    //   }
    };

    fetchQuestion();
  }, [uid]);

  if (error) {
    return <div>Error: {error}</div>;
  }

//   if (!question) {
//     return <div>Loading...</div>;
//   }

  return (
    <TabControl url='/tabs.json' sessionId={uid} />
  );
};

export default QuestionPage;
