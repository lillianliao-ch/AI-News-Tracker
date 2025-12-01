'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { HunterLogin, HunterQuickRegister } from '../components/HunterAuth';
import ShareButton from '../components/ShareButton';

interface Group {
  id: string;
  name: string;
  description: string;
  memberCount: number;
  latestMessage?: {
    type: 'job_seeking' | 'talent_recommendation';
    title: string;
    timeAgo: string;
  };
  unreadCount: number;
}

export default function HunterSharePage() {
  const router = useRouter();
  const [groups, setGroups] = useState<Group[]>([]);
  const [userStatus, setUserStatus] = useState<'guest' | 'registered' | 'verified'>('guest');
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Mock data for groups - 这里以后会从API获取
  const mockGroups: Group[] = [
    {
      id: '1',
      name: '互联网技术人才群',
      description: '专注互联网技术岗位',
      memberCount: 128,
      latestMessage: {
        type: 'job_seeking',
        title: '资深前端工程师',
        timeAgo: '14:32'
      },
      unreadCount: 3
    },
    {
      id: '2',
      name: '金融行业精英圈',
      description: '金融投资领域',
      memberCount: 85,
      latestMessage: {
        type: 'talent_recommendation',
        title: '量化研究员',
        timeAgo: '上午'
      },
      unreadCount: 0
    },
    {
      id: '3',
      name: 'AI & 算法专家',
      description: '人工智能方向',
      memberCount: 156,
      latestMessage: {
        type: 'job_seeking',
        title: '机器学习工程师',
        timeAgo: '昨天'
      },
      unreadCount: 1
    },
    {
      id: '4',
      name: '医疗健康人才库',
      description: '医疗健康行业',
      memberCount: 92,
      latestMessage: {
        type: 'talent_recommendation',
        title: '生物信息学专家',
        timeAgo: '周一'
      },
      unreadCount: 0
    },
    {
      id: '5',
      name: '新能源汽车圈',
      description: '新能源汽车领域',
      memberCount: 76,
      latestMessage: {
        type: 'job_seeking',
        title: '电池技术专家',
        timeAgo: '周日'
      },
      unreadCount: 0
    }
  ];

  useEffect(() => {
    // 模拟加载数据
    setGroups(mockGroups);
    
    // 检查用户状态 - 只在客户端执行
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('hunter_token');
      if (token) {
        setUserStatus('registered');
      }
    }
  }, []);

  const handleLoginSuccess = (token: string) => {
    setShowLoginModal(false);
    setShowRegisterModal(false);
    setUserStatus('registered');
  };

  const handleRegisterSuccess = (token: string) => {
    setShowLoginModal(false);
    setShowRegisterModal(false);
    setUserStatus('registered');
  };

  const formatRelativeTime = (timeStr: string) => {
    return timeStr;
  };

  const handleGroupClick = (groupId: string) => {
    router.push(`/group/${groupId}`);
  };

  // 根据群组名称生成图标和颜色方案
  const getGroupIconStyle = (groupName: string) => {
    const iconMap: Record<string, { emoji: string; gradient: string; bgColor: string }> = {
      '互联网': { emoji: '💻', gradient: 'from-blue-500 to-cyan-500', bgColor: 'bg-blue-50' },
      '金融': { emoji: '💰', gradient: 'from-amber-500 to-yellow-500', bgColor: 'bg-amber-50' },
      'AI': { emoji: '🤖', gradient: 'from-purple-500 to-pink-500', bgColor: 'bg-purple-50' },
      '算法': { emoji: '🧮', gradient: 'from-purple-500 to-indigo-500', bgColor: 'bg-purple-50' },
      '医疗': { emoji: '🏥', gradient: 'from-emerald-500 to-teal-500', bgColor: 'bg-emerald-50' },
      '健康': { emoji: '💚', gradient: 'from-green-500 to-emerald-500', bgColor: 'bg-green-50' },
      '新能源': { emoji: '⚡', gradient: 'from-orange-500 to-red-500', bgColor: 'bg-orange-50' },
      '汽车': { emoji: '🚗', gradient: 'from-slate-500 to-gray-600', bgColor: 'bg-slate-50' },
    };

    // 匹配关键词
    for (const [key, style] of Object.entries(iconMap)) {
      if (groupName.includes(key)) {
        return style;
      }
    }

    // 默认样式
    return { 
      emoji: '👥', 
      gradient: 'from-slate-500 to-gray-600', 
      bgColor: 'bg-slate-50' 
    };
  };

  return (
    <div className="min-h-screen bg-[#FAFAFA]">
      {/* Header - 高级深色设计 */}
      <div className="bg-[#1A1A1A] sticky top-0 z-10 border-b border-[#2A2A2A]/50">
        <div className="px-5 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-11 h-11 bg-gradient-to-br from-[#2A2A2A] to-[#1A1A1A] rounded-[14px] flex items-center justify-center border border-[#3A3A3A]/30 shadow-[0_2px_8px_rgba(0,0,0,0.3)]">
                <span className="text-xl">🤝</span>
              </div>
              <div>
                <h1 className="text-[18px] font-[600] text-white tracking-tight">猎头协作</h1>
                <p className="text-[11px] text-[#9CA3AF] font-medium mt-0.5">Professional Talent Network</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <ShareButton
                title="猎头协作 - 专业人才网络"
                description="加入猎头协作平台，发现更多优质人才和职位机会"
                className="px-3 py-2 bg-[#2A2A2A] rounded-full text-white hover:bg-[#333333] transition-all duration-200"
              />
              <button 
                onClick={() => router.push('/profile')}
                className="w-10 h-10 bg-[#2A2A2A] rounded-full flex items-center justify-center border border-[#3A3A3A]/30 hover:bg-[#333333] transition-all duration-200"
              >
                <span className="text-lg">👤</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="pb-28 px-4 pt-5">

        {/* Groups List - 高级卡片设计 */}
        <div className="space-y-2.5">
          {groups.map((group) => (
            <div 
              key={group.id} 
              className="bg-white rounded-[16px] p-4 border border-[#E5E7EB] shadow-[0_1px_3px_rgba(0,0,0,0.06)] hover:shadow-[0_4px_12px_rgba(0,0,0,0.08)] active:scale-[0.99] transition-all duration-200 cursor-pointer group"
              onClick={() => handleGroupClick(group.id)}
            >
              <div className="flex items-start space-x-3.5">
                {/* Group Avatar - 精致图标设计 */}
                <div className="relative flex-shrink-0">
                  {(() => {
                    const iconStyle = getGroupIconStyle(group.name);
                    return (
                      <div className={`w-14 h-14 bg-gradient-to-br ${iconStyle.gradient} rounded-[14px] flex items-center justify-center shadow-[0_2px_12px_rgba(0,0,0,0.15)] relative overflow-hidden`}>
                        {/* 背景装饰 */}
                        <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent"></div>
                        {/* 图标 */}
                        <span className="text-2xl relative z-10 drop-shadow-sm">{iconStyle.emoji}</span>
                        {/* 光泽效果 */}
                        <div className="absolute top-0 left-0 w-full h-1/2 bg-gradient-to-b from-white/30 to-transparent"></div>
                      </div>
                    );
                  })()}
                  {group.unreadCount > 0 && (
                    <div className="absolute -top-1 -right-1 w-5 h-5 bg-[#EF4444] rounded-full flex items-center justify-center border-2 border-white shadow-[0_2px_6px_rgba(239,68,68,0.4)] z-10">
                      <span className="text-[10px] text-white font-bold">
                        {group.unreadCount}
                      </span>
                    </div>
                  )}
                </div>

                {/* Group Info */}
                <div className="flex-1 min-w-0">
                  {/* Title and Time */}
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-[15px] font-bold text-[#111827] leading-snug tracking-tight pr-2">
                      {group.name}
                    </h3>
                    <span className="text-[11px] text-[#9CA3AF] font-medium whitespace-nowrap flex-shrink-0">
                      {group.latestMessage?.timeAgo}
                    </span>
                  </div>

                  {/* Description with icon */}
                  <div className="flex items-center space-x-2 mb-3">
                    <div className="flex items-center space-x-1 bg-[#F3F4F6] px-2 py-1 rounded-[8px] border border-[#E5E7EB]">
                      <span className="text-[10px]">👥</span>
                      <span className="text-[11px] font-semibold text-[#374151]">{group.memberCount}</span>
                    </div>
                    <span className="text-[12px] text-[#6B7280] truncate">{group.description}</span>
                  </div>

                  {/* Latest Message - 高级标签设计 */}
                  {group.latestMessage && (
                    <div className="flex items-center space-x-2 bg-[#F9FAFB] rounded-[10px] px-3 py-2 border border-[#E5E7EB]/50">
                      <span className={`px-2.5 py-1 rounded-[8px] text-[10px] font-bold tracking-wide ${
                        group.latestMessage.type === 'job_seeking' 
                          ? 'bg-[#111827] text-white' 
                          : 'bg-[#374151] text-white'
                      }`}>
                        {group.latestMessage.type === 'job_seeking' ? '找人' : '推人'}
                      </span>
                      <span className="text-[13px] text-[#111827] truncate font-medium">
                        {group.latestMessage.title}
                      </span>
                    </div>
                  )}
                </div>

                {/* Arrow Icon - 精致设计 */}
                <div className="flex items-center flex-shrink-0 pt-1">
                  <svg className="w-4 h-4 text-[#9CA3AF] group-hover:text-[#6B7280] transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Authentication Modals */}
      {showLoginModal && (
        <HunterLogin
          onSuccess={handleLoginSuccess}
          onCancel={() => setShowLoginModal(false)}
          onRegister={() => {
            setShowLoginModal(false);
            setShowRegisterModal(true);
          }}
        />
      )}

      {showRegisterModal && (
        <HunterQuickRegister
          onSuccess={handleRegisterSuccess}
          onCancel={() => setShowRegisterModal(false)}
        />
      )}

      {/* Bottom Navigation - 高级设计 */}
      <div className="fixed bottom-0 left-0 right-0 bg-white/95 backdrop-blur-xl border-t border-[#E5E7EB] shadow-[0_-2px_12px_rgba(0,0,0,0.06)]">
        <div className="flex px-3 py-2.5 max-w-md mx-auto">
          <button className="flex-1 py-2.5 text-center group">
            <div className="inline-flex flex-col items-center space-y-1">
              <div className="w-10 h-10 bg-[#111827] rounded-[12px] flex items-center justify-center shadow-[0_2px_6px_rgba(17,24,39,0.2)] group-hover:shadow-[0_4px_12px_rgba(17,24,39,0.3)] transition-all duration-200">
                <span className="text-lg">🏠</span>
              </div>
              <div className="text-[11px] text-[#111827] font-semibold">群组</div>
            </div>
          </button>
          <button 
            onClick={() => window.location.href = '/my-posts'}
            className="flex-1 py-2.5 text-center group"
          >
            <div className="inline-flex flex-col items-center space-y-1">
              <div className="w-10 h-10 bg-[#F3F4F6] rounded-[12px] flex items-center justify-center border border-[#E5E7EB] group-hover:bg-[#E5E7EB] transition-all duration-200">
                <span className="text-lg">📋</span>
              </div>
              <div className="text-[11px] text-[#6B7280] font-medium">我的发布</div>
            </div>
          </button>
          <div className="flex-1 py-2.5 text-center group">
            <div className="inline-flex flex-col items-center space-y-1">
              <ShareButton
                title="猎头协作 - 专业人才网络"
                description="加入猎头协作平台，发现更多优质人才和职位机会"
                className="w-10 h-10 bg-[#F3F4F6] rounded-[12px] flex items-center justify-center border border-[#E5E7EB] group-hover:bg-[#E5E7EB] transition-all duration-200 text-[#6B7280]"
              />
              <div className="text-[11px] text-[#6B7280] font-medium">分享</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
