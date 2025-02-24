import { Button, Card, Alert, List, Tag, Divider } from 'antd';
import useResumeStore from '../store/resumeStore';
import Navigation from './Navigation';

const Optimization = ({ onComplete, onBack }) => {
  const { 
    comparison, 
    generateModifiedResume, 
    loading, 
    error,
    setCurrentStep 
  } = useResumeStore();

  const handleGenerateModified = async () => {
    try {
      if (!comparison) {
        throw new Error("Missing comparison data");
      }
      await generateModifiedResume();
      if (onComplete) onComplete();
    } catch (err) {
      // Error is already handled by store
    }
  };

  return (
    <Card title="Resume Optimization" className="max-w-2xl mx-auto">
      <div className="space-y-4">
        {comparison ? (
          <>
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold mb-2">Missing Keywords</h3>
                <div className="flex flex-wrap gap-2">
                  {comparison.missing_keywords?.map((keyword) => (
                    <Tag key={keyword} color="red">{keyword}</Tag>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold mb-2">Matching Keywords</h3>
                <div className="flex flex-wrap gap-2">
                  {comparison.existing_keywords?.map((keyword) => (
                    <Tag key={keyword} color="green">{keyword}</Tag>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold mb-2">Improvement Suggestions</h3>
                <List
                  dataSource={comparison.improvement_suggestions || []}
                  renderItem={(suggestion) => (
                    <List.Item>
                      <List.Item.Meta
                        title={suggestion.title}
                        description={suggestion.description}
                      />
                    </List.Item>
                  )}
                />
              </div>

              <Button
                type="primary"
                onClick={handleGenerateModified}
                loading={loading}
                className="w-full"
              >
                Generate Modified Resume
              </Button>
            </div>
          </>
        ) : (
          <Alert
            message="No comparison data"
            description="Please complete the job analysis first"
            type="warning"
            showIcon
          />
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

        <Navigation
          onBack={onBack}
          onNext={handleGenerateModified}
          nextDisabled={!comparison || loading}
          nextText="Generate Modified Resume"
        />
      </div>
    </Card>
  );
};

export default Optimization; 