import { Steps } from 'antd';
import { 
  KeyOutlined, 
  FileTextOutlined, 
  SearchOutlined, 
  EditOutlined 
} from '@ant-design/icons';

const StepsProgress = ({ currentStep }) => {
  const steps = [
    {
      title: 'API Setup',
      icon: <KeyOutlined />,
      description: 'Configure API key'
    },
    {
      title: 'Resume Upload',
      icon: <FileTextOutlined />,
      description: 'Upload LaTeX resume'
    },
    {
      title: 'Job Analysis',
      icon: <SearchOutlined />,
      description: 'Analyze job posting'
    },
    {
      title: 'Optimization',
      icon: <EditOutlined />,
      description: 'Review and optimize'
    }
  ];

  return (
    <div className="mb-8">
      <Steps
        current={currentStep}
        items={steps}
        responsive={true}
      />
    </div>
  );
};

export default StepsProgress; 