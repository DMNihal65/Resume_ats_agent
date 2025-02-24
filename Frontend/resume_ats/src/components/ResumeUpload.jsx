import { Upload, Button, Card, Alert, Space, message } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import useResumeStore from '../store/resumeStore';
import { useState } from 'react';

const { Dragger } = Upload;

const ResumeUpload = ({ onComplete, onBack }) => {
  const { uploadResume, resumeContent, loading, error, setCurrentStep } = useResumeStore();
  const [fileList, setFileList] = useState([]);

  const uploadProps = {
    name: 'file',
    multiple: false,
    accept: '.tex',
    fileList,
    beforeUpload: (file) => {
      if (!file.name.endsWith('.tex')) {
        message.error('Only .tex files are allowed!');
        return false;
      }
      return true;
    },
    customRequest: async ({ file, onSuccess, onError }) => {
      try {
        await uploadResume(file);
        onSuccess();
        message.success('Resume uploaded successfully!');
      } catch (err) {
        onError(err);
        message.error(err.response?.data?.detail || 'Failed to upload resume');
      }
    },
    onChange: (info) => {
      setFileList(info.fileList.slice(-1));
      if (info.file.status === 'done') {
        setCurrentStep(2);
      }
    },
    onRemove: () => {
      setFileList([]);
    }
  };

  return (
    <Card title="Upload LaTeX Resume" className="max-w-lg mx-auto">
      <div className="space-y-4">
        <p className="text-gray-600">
          Upload your LaTeX resume file (.tex) to begin the optimization process.
        </p>

        <Dragger {...uploadProps} disabled={loading}>
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">
            Click or drag your LaTeX resume file here
          </p>
          <p className="ant-upload-hint">
            Only .tex files are supported
          </p>
        </Dragger>

        {error && (
          <Alert
            message="Error"
            description={error}
            type="error"
            showIcon
            closable
          />
        )}

        {resumeContent && (
          <Alert
            message="Success"
            description="Resume uploaded successfully!"
            type="success"
            showIcon
          />
        )}

        <Space className="w-full justify-between">
          <Button onClick={onBack}>
            Back
          </Button>
          <Button 
            type="primary"
            onClick={onComplete}
            disabled={!resumeContent || loading}
          >
            Continue
          </Button>
        </Space>
      </div>
    </Card>
  );
};

export default ResumeUpload; 