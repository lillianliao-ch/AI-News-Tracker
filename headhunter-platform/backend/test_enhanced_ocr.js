const { enhancedOcrService } = require('./dist/services/enhancedOcrService');

async function testEnhancedOCR() {
  console.log('🧪 Testing Enhanced OCR Service...');
  
  try {
    // Test the text cleaning functionality
    console.log('\n1. Testing text cleaning:');
    const dirtyText = "职位要求：\n• 计算机相关专业本科及以上学历  • 计算机相关专业本科及以上学历\n• 3年以上Java开发经验\n• 熟悉Spring框架";
    const cleanedText = enhancedOcrService.cleanAndFormatText(dirtyText);
    console.log('Input:', dirtyText);
    console.log('Output:', cleanedText);
    
    // Test the field extraction
    console.log('\n2. Testing field extraction:');
    const testText = `
    招聘信息
    职位标题：高级软件工程师
    公司名称：科技有限公司
    工作地点：北京市朝阳区
    薪资范围：15000-25000元/月
    职位要求：
    • 计算机相关专业本科及以上学历
    • 3年以上Java开发经验
    • 熟悉Spring框架
    • 具备良好的团队合作能力
    `;
    
    const extractedFields = enhancedOcrService.extractJobFields(testText);
    console.log('Extracted fields:', JSON.stringify(extractedFields, null, 2));
    
    console.log('\n✅ Enhanced OCR Service test completed successfully!');
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  }
}

testEnhancedOCR();