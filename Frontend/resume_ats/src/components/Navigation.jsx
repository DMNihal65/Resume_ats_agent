import { Space, Button } from 'antd';
import useResumeStore from '../store/resumeStore';

const Navigation = ({ onBack, onNext, nextDisabled = false, nextText = "Continue" }) => {
  const { loading } = useResumeStore();

  return (
    <Space className="w-full justify-between mt-4">
      <Button 
        onClick={onBack}
        disabled={loading}
      >
        Back
      </Button>
      <Button 
        type="primary"
        onClick={onNext}
        loading={loading}
        disabled={nextDisabled}
      >
        {nextText}
      </Button>
    </Space>
  );
};

export default Navigation; 