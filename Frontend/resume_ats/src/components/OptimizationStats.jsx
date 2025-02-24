import { Card, Progress, List, Typography, Tag } from 'antd';
import { CheckCircleOutlined, WarningOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

const OptimizationStats = ({ stats }) => {
  if (!stats) return null;

  return (
    <Card className="mb-6">
      <Title level={4}>Optimization Statistics</Title>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="text-center">
          <Progress
            type="circle"
            percent={stats.ats_score}
            format={percent => (
              <div>
                <div className="text-lg font-bold">{percent}</div>
                <div className="text-xs">ATS Score</div>
              </div>
            )}
          />
        </div>

        <div className="text-center">
          <div className="text-3xl font-bold text-blue-500">
            {stats.keywords_added}
          </div>
          <div className="text-sm text-gray-600">Keywords Added</div>
        </div>

        <div className="text-center">
          <div className="text-3xl font-bold text-green-500">
            {stats.sections_modified}
          </div>
          <div className="text-sm text-gray-600">Sections Improved</div>
        </div>
      </div>

      <List
        header={<Text strong>Improvement Suggestions</Text>}
        dataSource={stats.improvement_suggestions}
        renderItem={suggestion => (
          <List.Item>
            <List.Item.Meta
              avatar={
                suggestion.type === 'warning' ? 
                <WarningOutlined className="text-yellow-500" /> :
                <CheckCircleOutlined className="text-green-500" />
              }
              title={suggestion.title}
              description={suggestion.description}
            />
            {suggestion.priority && (
              <Tag color={suggestion.priority === 'high' ? 'red' : 'orange'}>
                {suggestion.priority}
              </Tag>
            )}
          </List.Item>
        )}
      />
    </Card>
  );
};

export default OptimizationStats; 