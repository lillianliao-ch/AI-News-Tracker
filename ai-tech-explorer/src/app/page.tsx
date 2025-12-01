import React from 'react';
import Link from 'next/link';

// 极简版本的AI Tech Explorer
export default function SimplePage() {
  return (
    <div className="min-h-screen bg-white">
      {/* 简洁的导航栏 */}
      <nav className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">AI Tech Explorer</h1>
          <div className="flex space-x-6">
            <Link href="/blog" className="text-gray-600 hover:text-blue-600">博客</Link>
            <Link href="/about" className="text-gray-600 hover:text-blue-600">关于</Link>
            <Link href="/contact" className="text-gray-600 hover:text-blue-600">联系</Link>
          </div>
        </div>
      </nav>

      {/* 简洁的主页内容 */}
      <main className="max-w-6xl mx-auto px-6 py-16">
        {/* Hero Section */}
        <div className="text-center py-20">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            AI技术专家 & 人才连接者
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            专注于大语言模型、AI工具评测和技术招聘服务，帮助AI从业者提升技术能力和职业发展
          </p>
          <div className="flex justify-center space-x-4">
            <Link 
              href="/blog" 
              className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 transition-colors"
            >
              探索技术博客
            </Link>
            <Link 
              href="/contact" 
              className="border border-blue-600 text-blue-600 px-8 py-3 rounded-lg hover:bg-blue-50 transition-colors"
            >
              联系合作
            </Link>
          </div>
        </div>

        {/* 文章列表 */}
        <div className="py-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-8">最新文章</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              "理解大语言模型的注意力机制",
              "2024年AI工具深度评测对比", 
              "AI工程师职业发展指南 2025",
              "Transformer架构详解",
              "BERT模型原理与应用",
              "GPT系列模型对比分析"
            ].map((title, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {title}
                </h3>
                <p className="text-gray-600 mb-4">
                  深入解析AI技术原理和实践经验，为从业者提供有价值的技术洞察...
                </p>
                <div className="flex items-center justify-between text-sm text-gray-500">
                  <span>Lillian Liao</span>
                  <span>2024-12-15</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 服务介绍 */}
        <div className="py-16 border-t border-gray-200">
          <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">我的服务</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="text-center p-8">
              <div className="text-4xl mb-4">🤖</div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">技术咨询</h3>
              <p className="text-gray-600 mb-4">AI产品策略规划、技术架构设计评审、团队技术能力提升</p>
              <div className="text-sm text-blue-600 font-medium">500-2000元/小时</div>
            </div>
            <div className="text-center p-8">
              <div className="text-4xl mb-4">👥</div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">招聘服务</h3>
              <p className="text-gray-600 mb-4">AI人才精准匹配、简历优化面试指导、薪资谈判策略</p>
              <div className="text-sm text-blue-600 font-medium">年薪15-25%</div>
            </div>
          </div>
        </div>

        {/* 联系方式 */}
        <div className="py-16 bg-blue-50 rounded-lg text-center">
          <h3 className="text-2xl font-bold text-gray-900 mb-4">开始合作</h3>
          <p className="text-gray-600 mb-6">准备好提升你的AI技术能力或寻找顶级AI人才了吗？</p>
          <Link 
            href="/contact" 
            className="inline-block bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 transition-colors"
          >
            立即联系
          </Link>
        </div>
      </main>

      {/* 简洁的页脚 */}
      <footer className="bg-gray-50 border-t border-gray-200 py-12">
        <div className="max-w-6xl mx-auto px-6 text-center">
          <p className="text-gray-600">© 2024 AI Tech Explorer. Lillian Liao. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}