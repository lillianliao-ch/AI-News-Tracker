'use client';

import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Progress, 
  Tag, 
  Button, 
  Spin, 
  Empty, 
  Tooltip, 
  Modal,
  Select,
  Slider,
  Radio,
  Space,
  Divider,
  Avatar,
  Rate,
  Badge,
  Descriptions,
  Timeline,
  Tabs
} from 'antd';
import { 
  UserOutlined, 
  TrophyOutlined, 
  StarOutlined, 
  EnvironmentOutlined,
  DollarOutlined,
  BulbOutlined,
  SearchOutlined,
  FilterOutlined,
  DownloadOutlined,
  ShareAltOutlined,
  HeartOutlined,
  EyeOutlined
} from '@ant-design/icons';
import type { TabsProps } from 'antd';

const { Option } = Select;
const { TabPane } = Tabs;

// 匹配结果接口
interface MatchingResult {
  jobId: string;
  candidateId?: string;
  jobTitle?: string;
  candidateName?: string;
  companyName?: string;
  overallScore: number;
  finalScore: number;
  priority: 'high' | 'medium' | 'low';
  recommendationStrength: number;
  confidence: number;
  dimensionScores: {
    skills: number;
    experience: number;
    industry: number;
    location: number;
    salary: number;
    education: number;
  };
  matchDetails: {
    matchedSkills: SkillMatch[];
    missingSkills: string[];
    matchReasons: string[];
    salaryFit: {
      expectationMet: boolean;
      fitPercentage: number;
      currentVsOffered: number;
    };
  };
  businessTags: string[];
  rankingReasons: string[];
}

interface SkillMatch {
  skill: string;
  candidateLevel: string;
  requiredLevel: string;
  score: number;
  isKeySkill: boolean;
}

// 匹配策略选项
const MATCHING_STRATEGIES = [
  { value: 'overall', label: '综合匹配', description: '基于所有维度的综合评分' },
  { value: 'skillFirst', label: '技能优先', description: '优先考虑技能匹配度' },
  { value: 'experienceFirst', label: '经验优先', description: '优先考虑工作经验' },
  { value: 'salaryFirst', label: '薪资匹配', description: '优先考虑薪资期望' },
  { value: 'locationFirst', label: '地域优先', description: '优先考虑地理位置' },
  { value: 'confidenceFirst', label: '置信度优先', description: '优先推荐可信度高的' }
];

// 过滤器选项
const FILTER_OPTIONS = [
  { value: 'minimumScore', label: '最低分数要求' },
  { value: 'minimumSkillMatch', label: '最低技能匹配' },
  { value: 'minimumExperience', label: '最低经验要求' },
  { value: 'highConfidence', label: '高置信度过滤' },
  { value: 'reasonableSalary', label: '薪资期望合理' },
  { value: 'locationMatch', label: '地域匹配' }
];

export const ResumeMatching: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [matchingResults, setMatchingResults] = useState<MatchingResult[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState('overall');
  const [selectedFilters, setSelectedFilters] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState('candidate-to-job');
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedMatch, setSelectedMatch] = useState<MatchingResult | null>(null);

  // 获取匹配结果
  const fetchMatchingResults = async (type: 'candidate-to-job' | 'job-to-candidate', id: string) => {
    setLoading(true);
    try {
      const endpoint = type === 'candidate-to-job' 
        ? '/api/v1/matching/jobs-for-candidate'
        : '/api/v1/matching/candidates-for-job';
      
      const body = type === 'candidate-to-job'
        ? { candidateId: id, strategy: selectedStrategy, filters: selectedFilters }
        : { jobId: id, strategy: selectedStrategy, filters: selectedFilters };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      const data = await response.json();
      if (data.success) {
        setMatchingResults(data.data.matches);
      }
    } catch (error) {
      console.error('获取匹配结果失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 渲染匹配分数圆环
  const renderScoreCircle = (score: number, size: 'small' | 'default' = 'default') => {
    const getScoreColor = (score: number) => {
      if (score >= 85) return '#52c41a';
      if (score >= 70) return '#1890ff';
      if (score >= 50) return '#faad14';
      return '#ff4d4f';
    };

    return (
      <Progress
        type="circle"
        percent={score}
        size={size === 'small' ? 60 : 80}
        strokeColor={getScoreColor(score)}
        format={(percent) => (
          <span style={{ fontSize: size === 'small' ? '12px' : '16px', fontWeight: 'bold' }}>
            {percent}%
          </span>
        )}
      />
    );
  };

  // 渲染维度评分雷达图
  const renderDimensionScores = (scores: MatchingResult['dimensionScores']) => {
    const dimensions = [
      { key: 'skills', label: '技能', score: scores.skills, icon: <BulbOutlined /> },
      { key: 'experience', label: '经验', score: scores.experience, icon: <TrophyOutlined /> },
      { key: 'industry', label: '行业', score: scores.industry, icon: <StarOutlined /> },
      { key: 'location', label: '地点', score: scores.location, icon: <EnvironmentOutlined /> },
      { key: 'salary', label: '薪资', score: scores.salary, icon: <DollarOutlined /> },
      { key: 'education', label: '学历', score: scores.education, icon: <UserOutlined /> }
    ];

    return (
      <Row gutter={[8, 8]}>
        {dimensions.map(dim => (
          <Col key={dim.key} span={8}>
            <div style={{ textAlign: 'center', padding: '8px' }}>
              <div style={{ marginBottom: '4px' }}>
                {dim.icon} {dim.label}
              </div>
              <Progress
                percent={dim.score}
                size="small"
                strokeColor={dim.score >= 70 ? '#52c41a' : dim.score >= 50 ? '#1890ff' : '#faad14'}
                showInfo={false}
              />
              <div style={{ fontSize: '12px', marginTop: '2px' }}>
                {dim.score}%
              </div>
            </div>
          </Col>
        ))}
      </Row>
    );
  };

  // 渲染技能匹配详情
  const renderSkillsMatch = (matchedSkills: SkillMatch[], missingSkills: string[]) => (
    <div>
      <div style={{ marginBottom: '12px' }}>
        <strong>匹配技能 ({matchedSkills.length})</strong>
        <div style={{ marginTop: '8px' }}>
          {matchedSkills.map((skill, index) => (
            <Tag
              key={index}
              color={skill.isKeySkill ? 'red' : skill.score >= 80 ? 'green' : 'blue'}
              style={{ marginBottom: '4px' }}
            >
              {skill.skill} 
              {skill.isKeySkill && <StarOutlined style={{ marginLeft: '4px' }} />}
              <span style={{ marginLeft: '4px' }}>({skill.score}%)</span>
            </Tag>
          ))}
        </div>
      </div>
      
      {missingSkills.length > 0 && (
        <div>
          <strong>缺失技能 ({missingSkills.length})</strong>
          <div style={{ marginTop: '8px' }}>
            {missingSkills.map((skill, index) => (
              <Tag key={index} color="orange" style={{ marginBottom: '4px' }}>
                {skill}
              </Tag>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  // 渲染匹配卡片
  const renderMatchCard = (match: MatchingResult) => {
    const getPriorityColor = (priority: string) => {
      switch (priority) {
        case 'high': return '#52c41a';
        case 'medium': return '#1890ff';
        case 'low': return '#faad14';
        default: return '#d9d9d9';
      }
    };

    const getPriorityText = (priority: string) => {
      switch (priority) {
        case 'high': return '强烈推荐';
        case 'medium': return '推荐';
        case 'low': return '可考虑';
        default: return '一般';
      }
    };

    return (
      <Card
        key={match.jobId || match.candidateId}
        style={{ marginBottom: '16px' }}
        hoverable
        actions={[
          <Button key="detail" type="link" onClick={() => {
            setSelectedMatch(match);
            setDetailModalVisible(true);
          }}>
            <EyeOutlined /> 详情
          </Button>,
          <Button key="save" type="link">
            <HeartOutlined /> 收藏
          </Button>,
          <Button key="share" type="link">
            <ShareAltOutlined /> 分享
          </Button>
        ]}
      >
        <Row gutter={16} align="middle">
          {/* 基础信息 */}
          <Col span={8}>
            <div>
              <Avatar size={48} icon={<UserOutlined />} style={{ marginRight: '12px' }} />
              <div style={{ display: 'inline-block', verticalAlign: 'top' }}>
                <h4 style={{ margin: '0 0 4px 0' }}>
                  {match.jobTitle || match.candidateName}
                </h4>
                <p style={{ margin: '0', color: '#666', fontSize: '14px' }}>
                  {match.companyName || '候选人'}
                </p>
              </div>
            </div>
          </Col>

          {/* 综合评分 */}
          <Col span={4} style={{ textAlign: 'center' }}>
            {renderScoreCircle(match.finalScore, 'small')}
            <div style={{ marginTop: '8px' }}>
              <Badge 
                color={getPriorityColor(match.priority)} 
                text={getPriorityText(match.priority)}
              />
            </div>
          </Col>

          {/* 维度评分 */}
          <Col span={8}>
            {renderDimensionScores(match.dimensionScores)}
          </Col>

          {/* 推荐标签 */}
          <Col span={4}>
            <div>
              <Rate 
                disabled 
                value={Math.round(match.recommendationStrength / 20)} 
                style={{ fontSize: '16px' }}
              />
              <div style={{ marginTop: '8px' }}>
                <Tooltip title={`置信度: ${match.confidence}%`}>
                  <Progress 
                    percent={match.confidence} 
                    size="small" 
                    showInfo={false}
                    strokeColor="#722ed1"
                  />
                </Tooltip>
              </div>
              <div style={{ marginTop: '8px' }}>
                {match.businessTags.slice(0, 2).map(tag => (
                  <Tag key={tag} size="small" color="blue">
                    {tag}
                  </Tag>
                ))}
              </div>
            </div>
          </Col>
        </Row>

        {/* 匹配亮点 */}
        <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
          <Space size="small" wrap>
            {match.rankingReasons.slice(0, 3).map((reason, index) => (
              <Tag key={index} color="green">
                {reason}
              </Tag>
            ))}
          </Space>
        </div>
      </Card>
    );
  };

  // 渲染控制面板
  const renderControlPanel = () => (
    <Card style={{ marginBottom: '16px' }}>
      <Row gutter={16} align="middle">
        <Col span={6}>
          <label style={{ fontWeight: 'bold', marginRight: '8px' }}>匹配策略:</label>
          <Select
            value={selectedStrategy}
            onChange={setSelectedStrategy}
            style={{ width: '100%' }}
          >
            {MATCHING_STRATEGIES.map(strategy => (
              <Option key={strategy.value} value={strategy.value}>
                <Tooltip title={strategy.description}>
                  {strategy.label}
                </Tooltip>
              </Option>
            ))}
          </Select>
        </Col>

        <Col span={8}>
          <label style={{ fontWeight: 'bold', marginRight: '8px' }}>过滤条件:</label>
          <Select
            mode="multiple"
            value={selectedFilters}
            onChange={setSelectedFilters}
            placeholder="选择过滤条件"
            style={{ width: '100%' }}
          >
            {FILTER_OPTIONS.map(filter => (
              <Option key={filter.value} value={filter.value}>
                {filter.label}
              </Option>
            ))}
          </Select>
        </Col>

        <Col span={4}>
          <Button
            type="primary"
            icon={<SearchOutlined />}
            onClick={() => {
              // 重新执行匹配
              if (activeTab === 'candidate-to-job') {
                // fetchMatchingResults('candidate-to-job', currentCandidateId);
              } else {
                // fetchMatchingResults('job-to-candidate', currentJobId);
              }
            }}
            loading={loading}
          >
            重新匹配
          </Button>
        </Col>

        <Col span={6}>
          <Space>
            <Button icon={<DownloadOutlined />}>导出报告</Button>
            <Button icon={<FilterOutlined />}>高级筛选</Button>
          </Space>
        </Col>
      </Row>
    </Card>
  );

  // 渲染详情弹窗
  const renderDetailModal = () => (
    <Modal
      title="匹配详情分析"
      visible={detailModalVisible}
      onCancel={() => setDetailModalVisible(false)}
      width={800}
      footer={[
        <Button key="close" onClick={() => setDetailModalVisible(false)}>
          关闭
        </Button>
      ]}
    >
      {selectedMatch && (
        <div>
          <Tabs defaultActiveKey="overview">
            <TabPane tab="总体概况" key="overview">
              <Row gutter={16}>
                <Col span={12}>
                  <Card title="综合评分">
                    <div style={{ textAlign: 'center' }}>
                      {renderScoreCircle(selectedMatch.finalScore)}
                      <div style={{ marginTop: '16px' }}>
                        <Descriptions column={1} size="small">
                          <Descriptions.Item label="推荐强度">
                            <Rate 
                              disabled 
                              value={Math.round(selectedMatch.recommendationStrength / 20)} 
                            />
                          </Descriptions.Item>
                          <Descriptions.Item label="匹配置信度">
                            {selectedMatch.confidence}%
                          </Descriptions.Item>
                          <Descriptions.Item label="推荐优先级">
                            <Tag color={selectedMatch.priority === 'high' ? 'red' : 'blue'}>
                              {selectedMatch.priority}
                            </Tag>
                          </Descriptions.Item>
                        </Descriptions>
                      </div>
                    </div>
                  </Card>
                </Col>
                <Col span={12}>
                  <Card title="维度评分">
                    {renderDimensionScores(selectedMatch.dimensionScores)}
                  </Card>
                </Col>
              </Row>
            </TabPane>

            <TabPane tab="技能分析" key="skills">
              <Card>
                {renderSkillsMatch(
                  selectedMatch.matchDetails.matchedSkills,
                  selectedMatch.matchDetails.missingSkills
                )}
              </Card>
            </TabPane>

            <TabPane tab="薪资分析" key="salary">
              <Card>
                <Descriptions column={2}>
                  <Descriptions.Item label="期望满足">
                    <Tag color={selectedMatch.matchDetails.salaryFit.expectationMet ? 'green' : 'red'}>
                      {selectedMatch.matchDetails.salaryFit.expectationMet ? '是' : '否'}
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="匹配度">
                    {selectedMatch.matchDetails.salaryFit.fitPercentage}%
                  </Descriptions.Item>
                  <Descriptions.Item label="涨幅">
                    {selectedMatch.matchDetails.salaryFit.currentVsOffered > 0 ? '+' : ''}
                    {selectedMatch.matchDetails.salaryFit.currentVsOffered.toFixed(1)}%
                  </Descriptions.Item>
                </Descriptions>
              </Card>
            </TabPane>

            <TabPane tab="匹配原因" key="reasons">
              <Timeline>
                {selectedMatch.rankingReasons.map((reason, index) => (
                  <Timeline.Item key={index} color="green">
                    {reason}
                  </Timeline.Item>
                ))}
              </Timeline>
            </TabPane>
          </Tabs>
        </div>
      )}
    </Modal>
  );

  const tabItems: TabsProps['items'] = [
    {
      key: 'candidate-to-job',
      label: '为候选人匹配岗位',
      children: (
        <div>
          {renderControlPanel()}
          <Spin spinning={loading}>
            {matchingResults.length > 0 ? (
              <div>
                <div style={{ marginBottom: '16px', textAlign: 'right' }}>
                  <span style={{ color: '#666' }}>
                    共找到 {matchingResults.length} 个匹配岗位
                  </span>
                </div>
                {matchingResults.map(renderMatchCard)}
              </div>
            ) : (
              <Empty description="暂无匹配结果" />
            )}
          </Spin>
        </div>
      ),
    },
    {
      key: 'job-to-candidate',
      label: '为岗位匹配候选人',
      children: (
        <div>
          {renderControlPanel()}
          <Spin spinning={loading}>
            {matchingResults.length > 0 ? (
              <div>
                <div style={{ marginBottom: '16px', textAlign: 'right' }}>
                  <span style={{ color: '#666' }}>
                    共找到 {matchingResults.length} 个匹配候选人
                  </span>
                </div>
                {matchingResults.map(renderMatchCard)}
              </div>
            ) : (
              <Empty description="暂无匹配结果" />
            )}
          </Spin>
        </div>
      ),
    },
    {
      key: 'batch-analysis',
      label: '批量匹配分析',
      children: (
        <div>
          <Card>
            <p>批量匹配分析功能正在开发中...</p>
          </Card>
        </div>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <h2>智能简历匹配</h2>
        <p style={{ color: '#666' }}>
          基于AI算法的多维度智能匹配，为您找到最合适的候选人和岗位
        </p>
      </div>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
      />

      {renderDetailModal()}
    </div>
  );
};

export default ResumeMatching;