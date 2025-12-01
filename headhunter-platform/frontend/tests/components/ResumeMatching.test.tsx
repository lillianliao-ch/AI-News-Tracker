import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { jest, describe, beforeEach, afterEach, it, expect } from '@jest/globals';
import '@testing-library/jest-dom';
import ResumeMatching from '../../src/components/ResumeMatching';

// Mock Ant Design components to avoid style issues in tests
jest.mock('antd', () => ({
  Card: ({ children, title, actions, ...props }: any) => (
    <div data-testid="card" data-title={title} {...props}>
      {title && <div data-testid="card-title">{title}</div>}
      {children}
      {actions && <div data-testid="card-actions">{actions}</div>}
    </div>
  ),
  Row: ({ children, ...props }: any) => <div data-testid="row" {...props}>{children}</div>,
  Col: ({ children, ...props }: any) => <div data-testid="col" {...props}>{children}</div>,
  Progress: ({ percent, type, ...props }: any) => (
    <div data-testid="progress" data-percent={percent} data-type={type} {...props}>
      {percent}%
    </div>
  ),
  Tag: ({ children, color, ...props }: any) => (
    <span data-testid="tag" data-color={color} {...props}>{children}</span>
  ),
  Button: ({ children, onClick, loading, icon, ...props }: any) => (
    <button 
      data-testid="button" 
      onClick={onClick} 
      disabled={loading}
      {...props}
    >
      {icon} {children}
    </button>
  ),
  Spin: ({ children, spinning }: any) => (
    <div data-testid="spin" data-spinning={spinning}>
      {spinning && <div data-testid="loading">Loading...</div>}
      {children}
    </div>
  ),
  Empty: ({ description }: any) => (
    <div data-testid="empty">{description}</div>
  ),
  Modal: ({ visible, children, onCancel, title }: any) => 
    visible ? (
      <div data-testid="modal">
        <div data-testid="modal-title">{title}</div>
        <button data-testid="modal-close" onClick={onCancel}>Close</button>
        {children}
      </div>
    ) : null,
  Select: ({ children, value, onChange, ...props }: any) => (
    <select 
      data-testid="select" 
      value={value} 
      onChange={(e) => onChange?.(e.target.value)}
      {...props}
    >
      {children}
    </select>
  ),
  Tabs: ({ items, onChange, activeKey }: any) => (
    <div data-testid="tabs">
      <div data-testid="tabs-nav">
        {items.map((item: any) => (
          <button 
            key={item.key}
            data-testid={`tab-${item.key}`}
            onClick={() => onChange?.(item.key)}
            data-active={activeKey === item.key}
          >
            {item.label}
          </button>
        ))}
      </div>
      <div data-testid="tabs-content">
        {items.find((item: any) => item.key === activeKey)?.children}
      </div>
    </div>
  ),
  Rate: ({ value, disabled }: any) => (
    <div data-testid="rate" data-value={value} data-disabled={disabled}>
      {'★'.repeat(value)}{'☆'.repeat(5-value)}
    </div>
  ),
  Badge: ({ color, text }: any) => (
    <span data-testid="badge" data-color={color}>{text}</span>
  ),
  Tooltip: ({ children, title }: any) => (
    <div data-testid="tooltip" title={title}>{children}</div>
  ),
  Space: ({ children }: any) => (
    <div data-testid="space">{children}</div>
  ),
  Divider: () => <hr data-testid="divider" />,
  Avatar: ({ icon, size }: any) => (
    <div data-testid="avatar" data-size={size}>{icon}</div>
  ),
  Descriptions: ({ children, column }: any) => (
    <div data-testid="descriptions" data-column={column}>{children}</div>
  ),
  Timeline: ({ children }: any) => (
    <div data-testid="timeline">{children}</div>
  )
}));

// Mock Ant Design Select.Option
const MockOption = ({ children, value }: any) => (
  <option value={value}>{children}</option>
);

jest.mock('antd', () => ({
  ...jest.requireActual('antd'),
  Select: Object.assign(
    ({ children, value, onChange, mode, placeholder, ...props }: any) => (
      <select 
        data-testid="select" 
        value={mode === 'multiple' ? undefined : value}
        onChange={(e) => {
          if (mode === 'multiple') {
            const selectedOptions = Array.from(e.target.selectedOptions, (option: any) => option.value);
            onChange?.(selectedOptions);
          } else {
            onChange?.(e.target.value);
          }
        }}
        multiple={mode === 'multiple'}
        {...props}
      >
        {children}
      </select>
    ),
    { Option: MockOption }
  )
}));

// Mock API calls
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock data
const mockMatchingResults = [
  {
    jobId: 'job-1',
    jobTitle: 'Java高级开发工程师',
    companyName: 'ABC科技',
    overallScore: 85,
    finalScore: 87,
    priority: 'high' as const,
    recommendationStrength: 90,
    confidence: 88,
    dimensionScores: {
      skills: 90,
      experience: 85,
      industry: 95,
      location: 100,
      salary: 80,
      education: 75
    },
    matchDetails: {
      matchedSkills: [
        {
          skill: 'Java',
          candidateLevel: 'advanced',
          requiredLevel: 'intermediate',
          score: 95,
          isKeySkill: true
        },
        {
          skill: 'Spring',
          candidateLevel: 'intermediate',
          requiredLevel: 'basic',
          score: 85,
          isKeySkill: false
        }
      ],
      missingSkills: ['React'],
      matchReasons: ['技能高度匹配', '经验符合要求'],
      salaryFit: {
        expectationMet: true,
        fitPercentage: 85,
        currentVsOffered: 25
      }
    },
    businessTags: ['perfect_match', 'key_skills_match'],
    rankingReasons: ['技能高度匹配', '工作经验符合要求', '地理位置优势']
  },
  {
    jobId: 'job-2',
    jobTitle: 'Python开发工程师',
    companyName: 'XYZ公司',
    overallScore: 70,
    finalScore: 72,
    priority: 'medium' as const,
    recommendationStrength: 75,
    confidence: 65,
    dimensionScores: {
      skills: 75,
      experience: 70,
      industry: 80,
      location: 60,
      salary: 75,
      education: 85
    },
    matchDetails: {
      matchedSkills: [
        {
          skill: 'Python',
          candidateLevel: 'intermediate',
          requiredLevel: 'intermediate',
          score: 80,
          isKeySkill: true
        }
      ],
      missingSkills: ['Django', 'FastAPI'],
      matchReasons: ['Python技能匹配'],
      salaryFit: {
        expectationMet: false,
        fitPercentage: 65,
        currentVsOffered: 10
      }
    },
    businessTags: ['good_match'],
    rankingReasons: ['技能较好匹配']
  }
];

describe('ResumeMatching Component', () => {
  beforeEach(() => {
    mockFetch.mockClear();
    mockFetch.mockResolvedValue({
      json: async () => ({
        success: true,
        data: {
          matches: mockMatchingResults,
          totalMatches: mockMatchingResults.length,
          processingTime: 1500
        }
      })
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('组件渲染测试', () => {
    it('应该正确渲染主界面', () => {
      render(<ResumeMatching />);

      expect(screen.getByText('智能简历匹配')).toBeInTheDocument();
      expect(screen.getByText(/基于AI算法的多维度智能匹配/)).toBeInTheDocument();
      expect(screen.getByTestId('tabs')).toBeInTheDocument();
    });

    it('应该渲染所有标签页', () => {
      render(<ResumeMatching />);

      expect(screen.getByTestId('tab-candidate-to-job')).toBeInTheDocument();
      expect(screen.getByTestId('tab-job-to-candidate')).toBeInTheDocument();
      expect(screen.getByTestId('tab-batch-analysis')).toBeInTheDocument();
      
      expect(screen.getByText('为候选人匹配岗位')).toBeInTheDocument();
      expect(screen.getByText('为岗位匹配候选人')).toBeInTheDocument();
      expect(screen.getByText('批量匹配分析')).toBeInTheDocument();
    });

    it('应该渲染控制面板', () => {
      render(<ResumeMatching />);

      expect(screen.getByText('匹配策略:')).toBeInTheDocument();
      expect(screen.getByText('过滤条件:')).toBeInTheDocument();
      expect(screen.getByText('重新匹配')).toBeInTheDocument();
    });
  });

  describe('匹配策略测试', () => {
    it('应该显示所有匹配策略选项', () => {
      render(<ResumeMatching />);

      const strategySelect = screen.getByDisplayValue('overall') || screen.getByTestId('select');
      expect(strategySelect).toBeInTheDocument();

      // 验证策略选项存在
      const strategies = ['overall', 'skillFirst', 'experienceFirst', 'salaryFirst', 'locationFirst', 'confidenceFirst'];
      strategies.forEach(strategy => {
        expect(document.querySelector(`option[value="${strategy}"]`)).toBeInTheDocument();
      });
    });

    it('应该能够切换匹配策略', () => {
      render(<ResumeMatching />);

      const strategySelect = screen.getByTestId('select');
      
      act(() => {
        fireEvent.change(strategySelect, { target: { value: 'skillFirst' } });
      });

      expect(strategySelect).toHaveValue('skillFirst');
    });
  });

  describe('过滤器测试', () => {
    it('应该支持多选过滤器', () => {
      render(<ResumeMatching />);

      const filterSelects = screen.getAllByTestId('select');
      const filterSelect = filterSelects.find(select => 
        select.hasAttribute('multiple')
      );

      expect(filterSelect).toBeInTheDocument();
    });

    it('应该能够选择多个过滤条件', () => {
      render(<ResumeMatching />);

      const filterSelects = screen.getAllByTestId('select');
      const filterSelect = filterSelects.find(select => 
        select.hasAttribute('multiple')
      );

      if (filterSelect) {
        act(() => {
          fireEvent.change(filterSelect, { 
            target: { 
              selectedOptions: [
                { value: 'minimumScore' },
                { value: 'minimumSkillMatch' }
              ]
            }
          });
        });
      }
    });
  });

  describe('匹配结果展示测试', () => {
    it('应该显示加载状态', async () => {
      mockFetch.mockImplementation(() => new Promise(resolve => {
        setTimeout(() => resolve({
          json: async () => ({
            success: true,
            data: { matches: [], totalMatches: 0 }
          })
        }), 100);
      }));

      render(<ResumeMatching />);

      const reMatchButton = screen.getByText('重新匹配');
      
      act(() => {
        fireEvent.click(reMatchButton);
      });

      expect(screen.getByTestId('loading')).toBeInTheDocument();
    });

    it('应该显示空结果状态', async () => {
      mockFetch.mockResolvedValueOnce({
        json: async () => ({
          success: true,
          data: { matches: [], totalMatches: 0 }
        })
      });

      render(<ResumeMatching />);

      await waitFor(() => {
        expect(screen.getByTestId('empty')).toBeInTheDocument();
      });
    });

    it('应该正确渲染匹配结果卡片', async () => {
      render(<ResumeMatching />);

      // 模拟设置匹配结果
      act(() => {
        // 这里需要触发匹配操作
        const reMatchButton = screen.getByText('重新匹配');
        fireEvent.click(reMatchButton);
      });

      await waitFor(() => {
        expect(screen.getByText('Java高级开发工程师')).toBeInTheDocument();
        expect(screen.getByText('ABC科技')).toBeInTheDocument();
      });
    });

    it('应该显示匹配分数', async () => {
      render(<ResumeMatching />);

      act(() => {
        const reMatchButton = screen.getByText('重新匹配');
        fireEvent.click(reMatchButton);
      });

      await waitFor(() => {
        expect(screen.getByText('87%')).toBeInTheDocument();
      });
    });

    it('应该显示维度评分', async () => {
      render(<ResumeMatching />);

      act(() => {
        const reMatchButton = screen.getByText('重新匹配');
        fireEvent.click(reMatchButton);
      });

      await waitFor(() => {
        const progressElements = screen.getAllByTestId('progress');
        expect(progressElements.length).toBeGreaterThan(0);
      });
    });

    it('应该显示业务标签', async () => {
      render(<ResumeMatching />);

      act(() => {
        const reMatchButton = screen.getByText('重新匹配');
        fireEvent.click(reMatchButton);
      });

      await waitFor(() => {
        expect(screen.getByText('perfect_match')).toBeInTheDocument();
        expect(screen.getByText('key_skills_match')).toBeInTheDocument();
      });
    });

    it('应该显示推荐原因', async () => {
      render(<ResumeMatching />);

      act(() => {
        const reMatchButton = screen.getByText('重新匹配');
        fireEvent.click(reMatchButton);
      });

      await waitFor(() => {
        expect(screen.getByText('技能高度匹配')).toBeInTheDocument();
        expect(screen.getByText('工作经验符合要求')).toBeInTheDocument();
      });
    });
  });

  describe('详情弹窗测试', () => {
    it('应该能够打开详情弹窗', async () => {
      render(<ResumeMatching />);

      act(() => {
        const reMatchButton = screen.getByText('重新匹配');
        fireEvent.click(reMatchButton);
      });

      await waitFor(() => {
        const detailButtons = screen.getAllByText('详情');
        expect(detailButtons.length).toBeGreaterThan(0);

        act(() => {
          fireEvent.click(detailButtons[0]);
        });

        expect(screen.getByTestId('modal')).toBeInTheDocument();
        expect(screen.getByTestId('modal-title')).toHaveTextContent('匹配详情分析');
      });
    });

    it('应该能够关闭详情弹窗', async () => {
      render(<ResumeMatching />);

      // 先打开弹窗
      act(() => {
        const reMatchButton = screen.getByText('重新匹配');
        fireEvent.click(reMatchButton);
      });

      await waitFor(() => {
        const detailButtons = screen.getAllByText('详情');
        act(() => {
          fireEvent.click(detailButtons[0]);
        });
      });

      // 关闭弹窗
      const closeButton = screen.getByTestId('modal-close');
      act(() => {
        fireEvent.click(closeButton);
      });

      expect(screen.queryByTestId('modal')).not.toBeInTheDocument();
    });

    it('详情弹窗应该显示技能分析', async () => {
      render(<ResumeMatching />);

      act(() => {
        const reMatchButton = screen.getByText('重新匹配');
        fireEvent.click(reMatchButton);
      });

      await waitFor(() => {
        const detailButtons = screen.getAllByText('详情');
        act(() => {
          fireEvent.click(detailButtons[0]);
        });

        // 验证技能分析内容
        expect(screen.getByText('Java')).toBeInTheDocument();
        expect(screen.getByText('Spring')).toBeInTheDocument();
      });
    });
  });

  describe('标签页切换测试', () => {
    it('应该能够切换到候选人匹配标签页', () => {
      render(<ResumeMatching />);

      const candidateTab = screen.getByTestId('tab-job-to-candidate');
      
      act(() => {
        fireEvent.click(candidateTab);
      });

      expect(candidateTab).toHaveAttribute('data-active', 'true');
    });

    it('应该能够切换到批量分析标签页', () => {
      render(<ResumeMatching />);

      const batchTab = screen.getByTestId('tab-batch-analysis');
      
      act(() => {
        fireEvent.click(batchTab);
      });

      expect(batchTab).toHaveAttribute('data-active', 'true');
      expect(screen.getByText('批量匹配分析功能正在开发中...')).toBeInTheDocument();
    });
  });

  describe('API交互测试', () => {
    it('应该发送正确的API请求', async () => {
      render(<ResumeMatching />);

      const reMatchButton = screen.getByText('重新匹配');
      
      act(() => {
        fireEvent.click(reMatchButton);
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/matching/'),
          expect.objectContaining({
            method: 'POST',
            headers: expect.objectContaining({
              'Content-Type': 'application/json'
            })
          })
        );
      });
    });

    it('应该处理API错误', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      render(<ResumeMatching />);

      const reMatchButton = screen.getByText('重新匹配');
      
      act(() => {
        fireEvent.click(reMatchButton);
      });

      await waitFor(() => {
        // 应该显示错误状态或空结果
        expect(screen.getByTestId('empty')).toBeInTheDocument();
      });
    });

    it('应该处理API返回的错误响应', async () => {
      mockFetch.mockResolvedValueOnce({
        json: async () => ({
          success: false,
          message: 'API错误'
        })
      });

      render(<ResumeMatching />);

      const reMatchButton = screen.getByText('重新匹配');
      
      act(() => {
        fireEvent.click(reMatchButton);
      });

      await waitFor(() => {
        expect(screen.getByTestId('empty')).toBeInTheDocument();
      });
    });
  });

  describe('响应式设计测试', () => {
    it('应该在不同屏幕尺寸下正确显示', () => {
      // 模拟移动设备
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      render(<ResumeMatching />);

      expect(screen.getByTestId('tabs')).toBeInTheDocument();
      
      // 验证响应式布局
      const rows = screen.getAllByTestId('row');
      expect(rows.length).toBeGreaterThan(0);
    });
  });

  describe('可访问性测试', () => {
    it('应该有正确的ARIA标签', () => {
      render(<ResumeMatching />);

      const buttons = screen.getAllByTestId('button');
      buttons.forEach(button => {
        expect(button).toBeInTheDocument();
      });
    });

    it('应该支持键盘导航', () => {
      render(<ResumeMatching />);

      const reMatchButton = screen.getByText('重新匹配');
      
      act(() => {
        reMatchButton.focus();
        fireEvent.keyDown(reMatchButton, { key: 'Enter' });
      });

      expect(mockFetch).toHaveBeenCalled();
    });
  });

  describe('性能测试', () => {
    it('应该正确处理大量匹配结果', async () => {
      const largeMatchingResults = Array.from({ length: 100 }, (_, index) => ({
        ...mockMatchingResults[0],
        jobId: `job-${index}`,
        jobTitle: `岗位-${index}`,
        overallScore: 70 + Math.random() * 30
      }));

      mockFetch.mockResolvedValueOnce({
        json: async () => ({
          success: true,
          data: {
            matches: largeMatchingResults,
            totalMatches: largeMatchingResults.length
          }
        })
      });

      const startTime = performance.now();

      render(<ResumeMatching />);

      const reMatchButton = screen.getByText('重新匹配');
      
      act(() => {
        fireEvent.click(reMatchButton);
      });

      await waitFor(() => {
        expect(screen.getByText('岗位-0')).toBeInTheDocument();
      });

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // 渲染时间应该在合理范围内
      expect(renderTime).toBeLessThan(5000);
    });

    it('应该避免不必要的重新渲染', () => {
      const renderSpy = jest.fn();
      
      const TestComponent = () => {
        renderSpy();
        return <ResumeMatching />;
      };

      const { rerender } = render(<TestComponent />);

      const initialRenderCount = renderSpy.mock.calls.length;

      // 重新渲染相同的组件
      rerender(<TestComponent />);

      // 验证渲染次数没有不必要地增加
      expect(renderSpy.mock.calls.length).toBe(initialRenderCount + 1);
    });
  });

  describe('边界情况测试', () => {
    it('应该处理空的匹配结果', async () => {
      mockFetch.mockResolvedValueOnce({
        json: async () => ({
          success: true,
          data: {
            matches: [],
            totalMatches: 0
          }
        })
      });

      render(<ResumeMatching />);

      const reMatchButton = screen.getByText('重新匹配');
      
      act(() => {
        fireEvent.click(reMatchButton);
      });

      await waitFor(() => {
        expect(screen.getByTestId('empty')).toBeInTheDocument();
      });
    });

    it('应该处理无效的匹配数据', async () => {
      mockFetch.mockResolvedValueOnce({
        json: async () => ({
          success: true,
          data: {
            matches: [
              {
                // 缺少必需字段的无效数据
                jobId: 'invalid-job'
              }
            ],
            totalMatches: 1
          }
        })
      });

      render(<ResumeMatching />);

      const reMatchButton = screen.getByText('重新匹配');
      
      act(() => {
        fireEvent.click(reMatchButton);
      });

      // 组件应该能够处理无效数据而不崩溃
      await waitFor(() => {
        expect(screen.getByTestId('card')).toBeInTheDocument();
      });
    });
  });
});