import { Input, Button, Alert, Card } from 'antd';
import { useState } from 'react';
import useResumeStore from '../store/resumeStore';

const ApiKeySetup = ({ onComplete }) => {
  const [key, setKey] = useState('');
  const { validateApiKey, loading, error } = useResumeStore();

  const handleSubmit = async () => {
    try {
      await validateApiKey(key);
      onComplete();
    } catch (err) {
      // Error is handled by the store
    }
  };

  return (
    <Card title="Setup Gemini API Key" className="max-w-lg mx-auto">
      <div className="space-y-4">
        <p className="text-gray-600">
          Enter your Gemini API key to get started. You can get one from the
          Google AI Studio.
        </p>

        <Input.Password
          value={key}
          onChange={(e) => setKey(e.target.value)}
          placeholder="Enter your Gemini API key"
          className="w-full"
        />

        {error && (
          <Alert
            message="Error"
            description={error}
            type="error"
            showIcon
            className="mt-4"
          />
        )}

        <Button
          type="primary"
          onClick={handleSubmit}
          loading={loading}
          disabled={!key}
          className="w-full"
        >
          Validate & Continue
        </Button>
      </div>
    </Card>
  );
};

export default ApiKeySetup; 