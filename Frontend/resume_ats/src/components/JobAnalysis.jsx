import { Input, Button, Card, Alert, List, Tag, Typography, Space, Steps } from 'antd';
import { useState } from 'react';
import useResumeStore from '../store/resumeStore';
import Navigation from './Navigation';

const { Title, Text } = Typography;
const { Step } = Steps;

const JobAnalysis = ({ onComplete, onBack }) => {
  const [url, setUrl] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [analysisStep, setAnalysisStep] = useState(0);
  const { 
    analyzeJobUrl, 
    compareResume,
    jobAnalysis, 
    comparison,
    loading, 
    error,
    setCurrentStep
  } = useResumeStore();

  const handleUrlAnalysis = async () => {
    try {
      await analyzeJobUrl(url, companyName);
      setAnalysisStep(1);
    } catch (err) {
      // Error handled by store
    }
  };

  const handleComparison = async () => {
    try {
      await compareResume();
      setAnalysisStep(2);
    } catch (err) {
      // Error handled by store
    }
  };

  const handleContinue = () => {
    setCurrentStep(3);
    if (onComplete) onComplete();
  };

  return (
    <div className="space-y-6">
      <Card title="Job Description Analysis" className="max-w-2xl mx-auto">
        <Steps size="small" current={analysisStep} className="mb-8">
          <Step title="Extract Job Details" />
          <Step title="Analyze Requirements" />
          <Step title="Compare Resume" />
        </Steps>

        <div className="space-y-4">
          {analysisStep === 0 && (
            <>
              <Space direction="vertical" className="w-full">
                <Input
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="Enter job posting URL"
                  className="w-full"
                />
                <Input
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  placeholder="Enter company name (optional)"
                  className="w-full"
                />
              </Space>

              <Button
                type="primary"
                onClick={handleUrlAnalysis}
                loading={loading}
                disabled={!url}
                className="w-full"
              >
                Start Analysis
              </Button>
            </>
          )}

          {analysisStep >= 1 && jobAnalysis && (
            <div className="space-y-4">
              <Title level={4}>Job Requirements</Title>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card size="small" title="Technical Skills">
                  {jobAnalysis.technical_skills.map(skill => (
                    <Tag key={skill} color="blue" className="m-1">{skill}</Tag>
                  ))}
                </Card>
                <Card size="small" title="Soft Skills">
                  {jobAnalysis.soft_skills.map(skill => (
                    <Tag key={skill} color="green" className="m-1">{skill}</Tag>
                  ))}
                </Card>
              </div>

              {analysisStep === 1 && (
                <Button
                  type="primary"
                  onClick={handleComparison}
                  loading={loading}
                  className="w-full"
                >
                  Compare with Resume
                </Button>
              )}
            </div>
          )}

          {analysisStep === 2 && comparison && (
            <div className="space-y-4">
              <Card title="Analysis Results">
                <List
                  size="small"
                  header={<Text strong>Missing Keywords</Text>}
                  dataSource={comparison.missing_keywords}
                  renderItem={keyword => (
                    <List.Item>
                      <Tag color="red">{keyword}</Tag>
                    </List.Item>
                  )}
                />
                <List
                  size="small"
                  header={<Text strong>Matching Keywords</Text>}
                  dataSource={comparison.existing_keywords}
                  renderItem={keyword => (
                    <List.Item>
                      <Tag color="green">{keyword}</Tag>
                    </List.Item>
                  )}
                />
              </Card>

              <Navigation
                onBack={() => setAnalysisStep(1)}
                onNext={handleContinue}
                nextText="Continue to Optimization"
                nextDisabled={!comparison}
              />
            </div>
          )}

          {error && (
            <Alert
              message="Error"
              description={error}
              type="error"
              showIcon
              closable
            />
          )}
        </div>
      </Card>
    </div>
  );
};

export default JobAnalysis; 