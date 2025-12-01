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
            {[1, 2, 3, 4, 5, 6].map((item) => (
              <div key={item} className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  AI技术文章标题 {item}
                </h3>
                <p className="text-gray-600 mb-4">
                  这里是文章的简短描述，介绍主要内容和核心观点...
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
              <p className="text-gray-600">AI产品策略规划、技术架构设计评审、团队技术能力提升</p>
            </div>
            <div className="text-center p-8">
              <div className="text-4xl mb-4">👥</div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">招聘服务</h3>
              <p className="text-gray-600">AI人才精准匹配、简历优化面试指导、薪资谈判策略</p>
            </div>
          </div>
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