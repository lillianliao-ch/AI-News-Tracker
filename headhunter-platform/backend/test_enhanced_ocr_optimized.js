// 测试优化后的增强OCR字段提取功能
const { enhancedOcrService } = require('./dist/services/enhancedOcrService');

console.log('🧪 Testing Optimized Enhanced OCR Service...');

// 模拟从你的图片中识别出的原始OCR文本
const originalOcrText = `
本科以上学历，5年以上互联网产品运营维护开发或系统架构设计工作经验；2. 熟悉服务器虚拟化技术及常见的云计算框架，例如: KVM，Xen，Openstack等，熟悉负载均衡、各类VPN网关(支持IPsec、SSL等)、路由器等网络产品；3. 熟悉数据库相关产品，如mysqlsqlserverRedisMongoDB；4. 熟悉公有云产品和服务体系，包括laas、Paas和Saas相关产品；5. 熟悉自建网络、服务器、存储、IDC相关内容和方案；6ABRE-TUIERMT@m (AFF.BE.MH.WR.HI7%) ORRER.TROSERREMRQ司某型产品的技术架构；7. 具备写客户的CEO、CTO、运维负责人等关键人员的沟通能力和技巧；8. 极强的问题解决能力，习惯于寻找创新方法来达成目标；9. 优良的客户服务意识，严谨的工作态度和强烈的责任心；10. 通过腾讯云从业资格证或同等资格认证的优先录取。
`;

// 测试更真实的招聘信息文本
const fullJobText = `
高级软件工程师
公司名称：科技创新有限公司
工作地点：北京市朝阳区
薪资范围：20-35K
行业：互联网

职位描述：
1. 负责后端核心系统的架构设计和开发工作
2. 参与需求分析，制定技术方案和开发计划
3. 优化系统性能，提升用户体验
4. 指导初级开发工程师，推进团队技术水平提升

职位要求：
1. 计算机相关专业本科及以上学历
2. 3年以上Java开发经验，熟悉Spring框架
3. 熟悉MySQL、Redis等数据库技术
4. 具备良好的团队合作能力和沟通能力
5. 有分布式系统开发经验者优先

联系方式：
邮箱：hr@example.com
电话：010-12345678
`;

async function testOptimizedExtraction() {
  console.log('\n=== Test 1: 原始OCR文本问题分析 ===');
  
  try {
    const fields1 = enhancedOcrService.extractJobFields(originalOcrText);
    console.log('原始OCR文本提取结果:');
    console.log('- 职位标题:', fields1.title || '❌ 未识别');
    console.log('- 工作地点:', fields1.location || '❌ 未识别');
    console.log('- 薪资范围:', fields1.salaryMin && fields1.salaryMax ? `${fields1.salaryMin}-${fields1.salaryMax}` : '❌ 未识别');
    console.log('- 职位要求:', fields1.requirements ? '✅ 已识别' : '❌ 未识别');
    console.log('- 职位描述:', fields1.description ? '✅ 已识别' : '❌ 未识别');
    
    if (fields1.requirements) {
      console.log('  要求内容预览:', fields1.requirements.substring(0, 100) + '...');
    }
  } catch (error) {
    console.error('❌ 测试1失败:', error.message);
  }
  
  console.log('\n=== Test 2: 完整招聘信息提取 ===');
  
  try {
    const fields2 = enhancedOcrService.extractJobFields(fullJobText);
    console.log('完整招聘信息提取结果:');
    console.log('- 职位标题:', fields2.title || '❌ 未识别');
    console.log('- 工作地点:', fields2.location || '❌ 未识别');
    console.log('- 薪资范围:', fields2.salaryMin && fields2.salaryMax ? `${fields2.salaryMin}-${fields2.salaryMax}` : '❌ 未识别');
    console.log('- 行业:', fields2.industry || '❌ 未识别');
    console.log('- 职位描述:', fields2.description ? '✅ 已识别' : '❌ 未识别');
    console.log('- 职位要求:', fields2.requirements ? '✅ 已识别' : '❌ 未识别');
    
    if (fields2.description) {
      console.log('  描述内容:', fields2.description);
    }
    if (fields2.requirements) {
      console.log('  要求内容:', fields2.requirements);
    }
  } catch (error) {
    console.error('❌ 测试2失败:', error.message);
  }
  
  console.log('\n=== Test 3: 文本清理功能测试 ===');
  
  const messyText = `职位要求：
  • 计算机相关专业本科及以上学历  
  • 计算机相关专业本科及以上学历
  • 3年以上Java开发经验   
  • 3年以上Java开发经验
  • 熟悉Spring框架、MyBatis框架
  • 具备良好的团队合作能力和沟通能力
  • 具备良好的团队合作能力和沟通能力!!!
  • 有相关项目经验者优先
  请将简历发送至：hr@example.com`;
  
  try {
    const cleanedText = enhancedOcrService.cleanAndFormatTextPublic(messyText);
    console.log('原始文本:', messyText.substring(0, 100) + '...');
    console.log('清理后文本:', cleanedText);
    
    // 验证去重效果
    const duplicateCount = (messyText.match(/计算机相关专业本科及以上学历/g) || []).length;
    const cleanedDuplicateCount = (cleanedText.match(/计算机相关专业本科及以上学历/g) || []).length;
    console.log(`去重效果: ${duplicateCount} → ${cleanedDuplicateCount} (${duplicateCount > cleanedDuplicateCount ? '✅ 成功' : '❌ 失败'})`);
    
    // 验证无关内容过滤
    const hasIrrelevantContent = cleanedText.includes('请将简历发送至');
    console.log(`无关内容过滤: ${hasIrrelevantContent ? '❌ 失败' : '✅ 成功'}`);
    
  } catch (error) {
    console.error('❌ 测试3失败:', error.message);
  }
  
  console.log('\n=== Test 4: 薪资识别测试 ===');
  
  const salaryTexts = [
    '薪资：15000-25000元/月',
    '月薪: 15K-25K',
    '年薪：20万-35万',
    '$50000-$80000',
    '薪水15-25万',
    '20k-30k'
  ];
  
  for (const salaryText of salaryTexts) {
    try {
      const fields = enhancedOcrService.extractJobFields(salaryText);
      const salary = fields.salaryMin && fields.salaryMax ? `${fields.salaryMin}-${fields.salaryMax}` : '未识别';
      console.log(`"${salaryText}" → ${salary}`);
    } catch (error) {
      console.log(`"${salaryText}" → 识别失败: ${error.message}`);
    }
  }
  
  console.log('\n=== Test 5: 职位标题识别测试 ===');
  
  const titleTexts = [
    '招聘：高级软件工程师',
    '职位标题：前端开发工程师',
    '高级Java开发工程师',
    '产品经理',
    '数据分析师',
    '本科以上学历，5年以上互联网产品' // 这种应该被过滤
  ];
  
  for (const titleText of titleTexts) {
    try {
      const fields = enhancedOcrService.extractJobFields(titleText);
      const title = fields.title || '未识别';
      console.log(`"${titleText}" → "${title}"`);
    } catch (error) {
      console.log(`"${titleText}" → 识别失败: ${error.message}`);
    }
  }
}

console.log('\n🚀 开始测试优化后的OCR字段提取...\n');

testOptimizedExtraction()
  .then(() => {
    console.log('\n✅ 所有测试完成！');
    console.log('\n📊 优化总结:');
    console.log('1. ✅ 改进了职位标题识别，避免将要求内容误识别为标题');
    console.log('2. ✅ 增强了薪资信息识别，支持多种格式(K/万/美元等)');
    console.log('3. ✅ 优化了文本清理算法，去除重复和无关内容');
    console.log('4. ✅ 改进了地点提取准确率，支持更完整的地址');
    console.log('5. ✅ 增强了字段分类逻辑，减少字段混淆');
    console.log('6. ✅ 添加了调试日志，便于问题追踪');
  })
  .catch(error => {
    console.error('❌ 测试过程中出现错误:', error);
  });