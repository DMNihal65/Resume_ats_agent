import { Card, Statistic, Row, Col, Progress, List, Tag } from 'antd';
import { CheckCircleOutlined, WarningOutlined } from '@ant-design/icons';

const Results = ({ analysis }) => {
  const { ats_score, keywords_added, sections_modified, improvements } = analysis;

  return (
    <Card title="Optimization Results" className="mb-6">
      <Row gutter={16}>
        <Col span={8}>
          <Card>
            <Statistic
              title="ATS Score"
              value={ats_score}
              suffix="%"
              prefix={<Progress type="circle" percent={ats_score} width={80} />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="Keywords Added"
              value={keywords_added}
              prefix={<CheckCircleOutlined className="text-green-500" />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="Sections Improved"
              value={sections_modified}
              prefix={<WarningOutlined className="text-yellow-500" />}
            />
          </Card>
        </Col>
      </Row>

      <List
        className="mt-6"
        header={<div className="font-semibold">Improvement Suggestions</div>}
        bordered
        dataSource={improvements}
        renderItem={item => (
          <List.Item
            extra={
              <Tag color={item.priority === 'high' ? 'red' : 'orange'}>
                {item.priority}
              </Tag>
            }
          >
            <List.Item.Meta
              title={item.title}
              description={item.description}
            />
          </List.Item>
        )}
      />
    </Card>
  );
};

export default Results; 