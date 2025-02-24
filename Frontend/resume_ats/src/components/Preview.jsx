import { useState, useEffect } from 'react';
import { Button, Card, Alert, Tabs, Input, Spin } from 'antd';
import useResumeStore from '../store/resumeStore';
import ResumeDiff from './ResumeDiff';
import OptimizationStats from './OptimizationStats';

const { TextArea } = Input;

const Preview = () => {
  const [diffData, setDiffData] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const { 
    generateModifiedResume,
    getResumeDiff,
    getResumeStats,
    modifiedResume,
    resumeContent,
    error 
  } = useResumeStore();

  const handleGenerate = async () => {
    try {
      setLoading(true);
      await generateModifiedResume();
      
      // Get diff and stats
      const [diffResult, statsResult] = await Promise.all([
        getResumeDiff(),
        getResumeStats()
      ]);
      
      setDiffData(diffResult);
      setStats(statsResult);
    } catch (err) {
      // Error handled by store
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    const blob = new Blob([modifiedResume], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${companyName}_resume.tex`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  return (
    <div className="space-y-6">
      <Card title="Resume Preview">
        <Button
          type="primary"
          onClick={handleGenerate}
          loading={loading}
          className="mb-4"
        >
          Generate Optimized Resume
        </Button>

        {error && (
          <Alert
            message="Error"
            description={error}
            type="error"
            showIcon
            className="mb-4"
          />
        )}

        {loading ? (
          <div className="text-center py-8">
            <Spin size="large" />
            <div className="mt-4 text-gray-600">
              Optimizing your resume...
            </div>
          </div>
        ) : (
          <>
            {stats && <OptimizationStats stats={stats} />}
            {diffData && <ResumeDiff diffData={diffData} />}
            
            {modifiedResume && (
              <Tabs
                items={[
                  {
                    key: 'original',
                    label: 'Original Resume',
                    children: (
                      <TextArea
                        value={resumeContent}
                        readOnly
                        rows={20}
                        className="font-mono"
                      />
                    ),
                  },
                  {
                    key: 'modified',
                    label: 'Modified Resume',
                    children: (
                      <TextArea
                        value={modifiedResume}
                        readOnly
                        rows={20}
                        className="font-mono"
                      />
                    ),
                  },
                ]}
              />
            )}
          </>
        )}
      </Card>
    </div>
  );
};

export default Preview; 