import React, { useState, useEffect } from "react";
import {
  faDollarSign,
  faGlobe,
  faRocket,
  faTruck,
} from "@fortawesome/free-solid-svg-icons";
import StarterCard from "../components/StarterCard";

interface StartPageProps {
  onStarterClick: (message: string) => void;
  question: string;
  setQuestion: React.Dispatch<React.SetStateAction<string>>;
}

interface ProgressStep {
  step: number;
  detail: string;
}

const StartPage: React.FC<StartPageProps> = ({
  onStarterClick,
  question,
  setQuestion,
}) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState<ProgressStep[]>([]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setIsProcessing(true);
    setProgress([]);
    const question_text = question;
    const response = await fetch('http://localhost:18000/process', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        question: question_text,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to submit question');
    }
    const data = await response.json();
    const eventSource = new EventSource(`http://localhost:18000/progress/${data.uid}`);

    eventSource.onmessage = (event) => {
      const messageData = JSON.parse(event.data);
      setProgress((prevProgress) => [...prevProgress, { step: messageData.step, detail: messageData.detail }]);

      if (messageData.step === 6) {
        eventSource.close();
        setIsProcessing(false);
        console.log('Stream complete');
        window.location.href = `/view/${data.uid}`; // Navigate to the question page
        return;
      }
    };

    eventSource.onerror = (error) => {
      console.error("EventSource failed:", error);
      eventSource.close();
      setIsProcessing(false);
    };
  };

  const renderProgressStepper = () => {
    return (
      <div className="progress-stepper mt-4">
        {[1, 2, 3, 4, 5, 6].map((step) => {
          const currentStep = progress.find((p) => p.step === step);
          const isCompleted = currentStep !== undefined;
          const isActive = progress.length === step - 1;

          return (
            <div key={step} className={`step ${isCompleted ? 'completed' : ''} ${isActive ? 'active' : ''}`}>
              <div className="step-number">{step}</div>
              <div className="step-detail">{currentStep?.detail || `Step ${step}`}</div>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="form-container">
      <form onSubmit={handleSubmit}>
        <div style={{ display: "block", width:"100%" }}>
          <br/><br/>
          <h2 className="mb-4">Ask a Question</h2>
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Type your question here"
            required
            disabled={isProcessing}
          />
          <div className="gap-4">
            <button type="submit" disabled={isProcessing}>
              {isProcessing ? "Processing..." : "Submit"}
            </button>
          </div>
        </div>
      </form>

      {isProcessing && renderProgressStepper()}

      {!isProcessing && (
        <div className="starter-proposals grid grid-cols-1 md:grid-cols-2 gap-4">
          <StarterCard
            icon={faDollarSign}
            text="What are the latest funding rounds in the AI industry?"
            onClick={onStarterClick}
          />
          <StarterCard
            text="Who are the suppliers of Unilever ?"
            icon={faTruck}
            onClick={onStarterClick}
          />
          <StarterCard
            icon={faGlobe}
            text="What are the latest AI trends in the automotive industry?"
            onClick={onStarterClick}
          />
          <StarterCard
            icon={faRocket}
            text="What are the latest AI trends in the finance industry?"
            onClick={onStarterClick}
          />
        </div>
      )}
    </div>
  );
};

export default StartPage;