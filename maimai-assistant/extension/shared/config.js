// Maimai Assistant 配置文件
// 消息模板变量说明：
// {name} - 候选人姓名
// {company} - 当前公司
// {position} - 当前职位
// {location} - 所在地
// {experience} - 工作年限
// {education} - 学历
// {skills} - 技能标签 (最多3个)

const MaimaiConfig = {
    // 默认消息模板
    messageTemplates: {
        // 通用模板
        default: '您好{name}，我是XX公司的HR，看到您在{company}的工作经历很优秀，想和您聊聊新的机会，方便吗？',

        // AI/算法岗位模板
        ai_engineer: '您好{name}，我这边有AI/算法相关的岗位机会，看到您在{company}担任{position}，有{experience}经验，非常契合我们的岗位需求。想了解下您对新机会的想法，方便聊聊吗？',

        // 技术管理岗位模板
        tech_lead: '您好{name}，我们正在寻找技术管理人才，看到您在{company}的管理经验，想和您聊聊我们的核心技术团队负责人机会，感兴趣的话可以约个时间详聊～',

        // 高端人才模板
        senior: '您好{name}，冒昧打扰！我这边有一个很有潜力的创业项目/知名企业的核心岗位，看到您在{company}的{position}经历非常出色，想向您介绍一下，方便的话可以先加个微信？',

        // 简短模板
        short: '您好{name}，看到您的简历很优秀，想和您聊聊新的机会，方便吗？'
    },

    // API设置
    api: {
        baseUrl: 'http://localhost:8502',
        timeout: 30000
    },

    // 批量操作设置
    batch: {
        defaultCount: 10,
        maxCount: 100,
        delayMin: 5000,  // 最小延迟 (ms)
        delayMax: 10000  // 最大延迟 (ms)
    }
};

// 导出到全局
if (typeof window !== 'undefined') {
    window.MaimaiConfig = MaimaiConfig;
}

console.log('✅ Maimai Config 加载完成');
