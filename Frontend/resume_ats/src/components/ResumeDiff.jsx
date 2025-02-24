import { Card, Tabs, Typography, Tag, Divider } from 'antd';
import { DiffOutlined } from '@ant-design/icons';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';

const { Title, Text } = Typography;

const ResumeDiff = ({ diffData }) => {
  if (!diffData) return null;

  return (
    <Card className="mb-6">
      <Title level={4}>
        <DiffOutlined className="mr-2" />
        Resume Changes
      </Title>

      <div className="mb-4">
        <Text>Sections Modified: </Text>
        {diffData.sections_changed.map(section => (
          <Tag key={section} color="blue" className="mr-2">
            {section}
          </Tag>
        ))}
      </div>

      <Tabs
        items={Object.entries(diffData.diff_details).map(([section, diff]) => ({
          key: section,
          label: section,
          children: (
            <div className="space-y-4">
              <div>
                <Text strong>Original:</Text>
                <SyntaxHighlighter
                  language="latex"
                  style={tomorrow}
                  className="text-sm"
                >
                  {diff.original}
                </SyntaxHighlighter>
              </div>
              
              <Divider />
              
              <div>
                <Text strong>Modified:</Text>
                <SyntaxHighlighter
                  language="latex"
                  style={tomorrow}
                  className="text-sm"
                >
                  {diff.modified}
                </SyntaxHighlighter>
              </div>
            </div>
          )
        }))}
      />
    </Card>
  );
};

export default ResumeDiff; 