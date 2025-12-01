import { MatchingResult } from './resumeMatchingService';

// 排序策略接口
export interface RankingStrategy {
  name: string;
  description: string;
  weight: (result: MatchingResult) => number;
}

// 排序配置
export interface RankingConfig {
  primaryStrategy: RankingStrategy;
  secondaryStrategies?: RankingStrategy[];
  filters?: MatchingFilter[];
  businessRules?: BusinessRule[];
}

// 过滤器接口
export interface MatchingFilter {
  name: string;
  condition: (result: MatchingResult) => boolean;
}

// 业务规则接口
export interface BusinessRule {
  name: string;
  priority: number;
  apply: (results: MatchingResult[]) => MatchingResult[];
}

// 增强的匹配结果
export interface EnhancedMatchingResult extends MatchingResult {
  finalScore: number;           // 最终综合得分
  rankingReasons: string[];     // 排序原因
  businessTags: string[];       // 业务标签
  priority: 'high' | 'medium' | 'low';
  recommendationStrength: number; // 推荐强度 0-100
}

export class MatchingRankingService {
  
  // 预定义排序策略
  private strategies: { [key: string]: RankingStrategy } = {
    // 1. 综合匹配度优先
    overall: {
      name: '综合匹配度',
      description: '基于所有维度的综合评分排序',
      weight: (result) => result.overallScore
    },

    // 2. 技能匹配优先
    skillFirst: {
      name: '技能优先',
      description: '优先考虑技能匹配度高的候选人',
      weight: (result) => result.dimensionScores.skills * 1.5 + result.overallScore * 0.5
    },

    // 3. 经验匹配优先
    experienceFirst: {
      name: '经验优先', 
      description: '优先考虑工作经验匹配的候选人',
      weight: (result) => result.dimensionScores.experience * 1.5 + result.overallScore * 0.5
    },

    // 4. 薪资匹配优先
    salaryFirst: {
      name: '薪资匹配',
      description: '优先考虑薪资期望合理的候选人',
      weight: (result) => result.dimensionScores.salary * 1.3 + result.overallScore * 0.7
    },

    // 5. 地域优先
    locationFirst: {
      name: '地域优先',
      description: '优先考虑地理位置匹配的候选人',
      weight: (result) => result.dimensionScores.location * 1.4 + result.overallScore * 0.6
    },

    // 6. 置信度优先
    confidenceFirst: {
      name: '置信度优先',
      description: '优先推荐数据完整、匹配可信度高的候选人',
      weight: (result) => result.confidence * 0.6 + result.overallScore * 0.4
    }
  };

  // 预定义过滤器
  private filters: { [key: string]: MatchingFilter } = {
    // 基础门槛过滤
    minimumScore: {
      name: '最低分数要求',
      condition: (result) => result.overallScore >= 30
    },

    // 技能门槛过滤
    minimumSkillMatch: {
      name: '最低技能匹配',
      condition: (result) => result.dimensionScores.skills >= 40
    },

    // 经验门槛过滤
    minimumExperience: {
      name: '最低经验要求',
      condition: (result) => result.dimensionScores.experience >= 30
    },

    // 高置信度过滤
    highConfidence: {
      name: '高置信度过滤',
      condition: (result) => result.confidence >= 60
    },

    // 薪资期望合理过滤
    reasonableSalary: {
      name: '薪资期望合理',
      condition: (result) => result.dimensionScores.salary >= 50
    },

    // 地域匹配过滤
    locationMatch: {
      name: '地域匹配',
      condition: (result) => result.dimensionScores.location >= 70
    }
  };

  // 预定义业务规则
  private businessRules: { [key: string]: BusinessRule } = {
    // 1. 技能完全匹配的候选人优先
    perfectSkillMatch: {
      name: '技能完全匹配优先',
      priority: 1,
      apply: (results) => {
        const perfect = results.filter(r => r.dimensionScores.skills >= 90);
        const others = results.filter(r => r.dimensionScores.skills < 90);
        return [...perfect, ...others];
      }
    },

    // 2. 内推候选人优先
    internalReferral: {
      name: '内推候选人优先',
      priority: 2,
      apply: (results) => {
        // 假设有内推标记的候选人
        const referrals = results.filter(r => r.businessTags?.includes('internal_referral'));
        const others = results.filter(r => !r.businessTags?.includes('internal_referral'));
        return [...referrals, ...others];
      }
    },

    // 3. 加急职位优先匹配
    urgentJob: {
      name: '加急职位优先匹配',
      priority: 3,
      apply: (results) => {
        // 为加急职位降低匹配门槛
        return results.map(result => ({
          ...result,
          finalScore: result.businessTags?.includes('urgent_job') ? 
            result.overallScore + 10 : result.overallScore
        }));
      }
    },

    // 4. 活跃候选人优先
    activeCandidates: {
      name: '活跃候选人优先',
      priority: 4,
      apply: (results) => {
        const active = results.filter(r => r.businessTags?.includes('active_candidate'));
        const inactive = results.filter(r => !r.businessTags?.includes('active_candidate'));
        return [...active, ...inactive];
      }
    },

    // 5. 历史成功率高的候选人优先
    highSuccessRate: {
      name: '历史成功率优先',
      priority: 5,
      apply: (results) => {
        return results.sort((a, b) => {
          const aSuccessRate = this.getCandidateSuccessRate(a.jobId);
          const bSuccessRate = this.getCandidateSuccessRate(b.jobId);
          return bSuccessRate - aSuccessRate;
        });
      }
    }
  };

  /**
   * 智能排序主方法
   */
  public async rankMatchingResults(
    results: MatchingResult[],
    config?: Partial<RankingConfig>
  ): Promise<EnhancedMatchingResult[]> {
    console.log(`📊 开始智能排序 ${results.length} 个匹配结果...`);

    // 1. 应用过滤器
    const filteredResults = this.applyFilters(results, config?.filters);
    console.log(`🔍 过滤后剩余 ${filteredResults.length} 个结果`);

    // 2. 应用业务规则
    const businessEnhanced = this.applyBusinessRules(filteredResults, config?.businessRules);

    // 3. 计算最终得分
    const scoredResults = this.calculateFinalScores(businessEnhanced, config);

    // 4. 增强结果信息
    const enhancedResults = await this.enhanceResults(scoredResults);

    // 5. 最终排序
    const finalRanked = this.finalSort(enhancedResults);

    console.log(`✅ 排序完成，返回 ${finalRanked.length} 个推荐结果`);
    return finalRanked;
  }

  /**
   * 应用过滤器
   */
  private applyFilters(
    results: MatchingResult[], 
    customFilters?: MatchingFilter[]
  ): MatchingResult[] {
    const activeFilters = [
      this.filters.minimumScore,
      this.filters.minimumSkillMatch,
      ...(customFilters || [])
    ];

    return results.filter(result => 
      activeFilters.every(filter => filter.condition(result))
    );
  }

  /**
   * 应用业务规则
   */
  private applyBusinessRules(
    results: MatchingResult[],
    customRules?: BusinessRule[]
  ): MatchingResult[] {
    const activeRules = [
      this.businessRules.perfectSkillMatch,
      this.businessRules.urgentJob,
      ...(customRules || [])
    ].sort((a, b) => a.priority - b.priority);

    let processedResults = [...results];
    
    for (const rule of activeRules) {
      console.log(`📋 应用业务规则: ${rule.name}`);
      processedResults = rule.apply(processedResults);
    }

    return processedResults;
  }

  /**
   * 计算最终得分
   */
  private calculateFinalScores(
    results: MatchingResult[],
    config?: Partial<RankingConfig>
  ): (MatchingResult & { finalScore: number })[] {
    const strategy = config?.primaryStrategy || this.strategies.overall;
    
    return results.map(result => ({
      ...result,
      finalScore: this.calculateWeightedScore(result, strategy, config?.secondaryStrategies)
    }));
  }

  /**
   * 计算加权得分
   */
  private calculateWeightedScore(
    result: MatchingResult,
    primaryStrategy: RankingStrategy,
    secondaryStrategies?: RankingStrategy[]
  ): number {
    let finalScore = primaryStrategy.weight(result) * 0.7;

    if (secondaryStrategies?.length) {
      const secondaryScore = secondaryStrategies.reduce(
        (sum, strategy) => sum + strategy.weight(result),
        0
      ) / secondaryStrategies.length;
      
      finalScore += secondaryScore * 0.3;
    }

    // 置信度调整
    finalScore = finalScore * (result.confidence / 100);

    return Math.round(finalScore);
  }

  /**
   * 增强结果信息
   */
  private async enhanceResults(
    results: (MatchingResult & { finalScore: number })[]
  ): Promise<EnhancedMatchingResult[]> {
    return results.map(result => ({
      ...result,
      rankingReasons: this.generateRankingReasons(result),
      businessTags: this.generateBusinessTags(result),
      priority: this.determinePriority(result),
      recommendationStrength: this.calculateRecommendationStrength(result)
    }));
  }

  /**
   * 最终排序
   */
  private finalSort(results: EnhancedMatchingResult[]): EnhancedMatchingResult[] {
    return results.sort((a, b) => {
      // 1. 优先级排序
      if (a.priority !== b.priority) {
        const priorityOrder = { 'high': 3, 'medium': 2, 'low': 1 };
        return priorityOrder[b.priority] - priorityOrder[a.priority];
      }
      
      // 2. 最终得分排序
      if (Math.abs(a.finalScore - b.finalScore) > 5) {
        return b.finalScore - a.finalScore;
      }
      
      // 3. 推荐强度排序
      return b.recommendationStrength - a.recommendationStrength;
    });
  }

  /**
   * 生成排序原因
   */
  private generateRankingReasons(result: MatchingResult & { finalScore: number }): string[] {
    const reasons: string[] = [];

    if (result.dimensionScores.skills >= 90) {
      reasons.push('技能高度匹配');
    } else if (result.dimensionScores.skills >= 70) {
      reasons.push('技能较好匹配');
    }

    if (result.dimensionScores.experience >= 80) {
      reasons.push('工作经验符合要求');
    }

    if (result.dimensionScores.location >= 80) {
      reasons.push('地理位置优势');
    }

    if (result.dimensionScores.salary >= 80) {
      reasons.push('薪资期望合理');
    }

    if (result.confidence >= 80) {
      reasons.push('匹配可信度高');
    }

    if (result.finalScore >= 85) {
      reasons.push('综合匹配度优秀');
    } else if (result.finalScore >= 70) {
      reasons.push('综合匹配度良好');
    }

    return reasons;
  }

  /**
   * 生成业务标签
   */
  private generateBusinessTags(result: MatchingResult): string[] {
    const tags: string[] = [];

    // 匹配度标签
    if (result.overallScore >= 90) tags.push('perfect_match');
    else if (result.overallScore >= 80) tags.push('excellent_match');
    else if (result.overallScore >= 70) tags.push('good_match');

    // 技能标签
    if (result.dimensionScores.skills >= 90) tags.push('skill_expert');
    if (result.matchDetails.matchedSkills.some(s => s.isKeySkill)) tags.push('key_skills_match');

    // 经验标签
    if (result.dimensionScores.experience >= 85) tags.push('experienced_professional');
    if (result.matchDetails.experienceMatch.industryMatch) tags.push('industry_experience');

    // 薪资标签
    if (result.matchDetails.salaryFit.expectationMet) tags.push('salary_fit');
    if (result.matchDetails.salaryFit.currentVsOffered > 20) tags.push('salary_upgrade');

    // 地域标签
    if (result.dimensionScores.location >= 90) tags.push('local_candidate');

    // 特殊标签
    if (result.confidence >= 90) tags.push('high_confidence');
    if (result.matchDetails.missingSkills.length === 0) tags.push('no_skill_gaps');

    return tags;
  }

  /**
   * 确定优先级
   */
  private determinePriority(result: MatchingResult & { finalScore: number }): 'high' | 'medium' | 'low' {
    if (result.finalScore >= 85 && result.confidence >= 80) {
      return 'high';
    } else if (result.finalScore >= 70 && result.confidence >= 60) {
      return 'medium';
    } else {
      return 'low';
    }
  }

  /**
   * 计算推荐强度
   */
  private calculateRecommendationStrength(result: MatchingResult & { finalScore: number }): number {
    let strength = result.finalScore;

    // 技能匹配加权
    if (result.dimensionScores.skills >= 90) strength += 5;
    if (result.matchDetails.matchedSkills.length >= 5) strength += 3;

    // 经验匹配加权
    if (result.dimensionScores.experience >= 85) strength += 5;

    // 置信度加权
    strength = strength * (result.confidence / 100);

    // 业务标签加权
    const businessTags = this.generateBusinessTags(result);
    if (businessTags.includes('perfect_match')) strength += 10;
    if (businessTags.includes('key_skills_match')) strength += 8;
    if (businessTags.includes('no_skill_gaps')) strength += 5;

    return Math.min(Math.round(strength), 100);
  }

  /**
   * 获取候选人历史成功率（模拟）
   */
  private getCandidateSuccessRate(candidateId: string): number {
    // 这里应该从数据库查询真实的历史成功率
    // 暂时返回模拟数据
    return Math.random() * 100;
  }

  /**
   * 自定义排序策略
   */
  public createCustomStrategy(
    name: string,
    description: string,
    weightFunction: (result: MatchingResult) => number
  ): RankingStrategy {
    return {
      name,
      description,
      weight: weightFunction
    };
  }

  /**
   * 获取推荐解释
   */
  public generateRecommendationExplanation(result: EnhancedMatchingResult): string {
    const reasons = result.rankingReasons;
    const tags = result.businessTags;
    
    let explanation = `该候选人综合匹配度为 ${result.finalScore}%，`;
    
    if (result.priority === 'high') {
      explanation += '强烈推荐。';
    } else if (result.priority === 'medium') {
      explanation += '推荐考虑。';
    } else {
      explanation += '可作为备选。';
    }

    if (reasons.length > 0) {
      explanation += ` 主要优势：${reasons.join('、')}。`;
    }

    if (tags.includes('perfect_match')) {
      explanation += ' 这是一个完美匹配的候选人！';
    } else if (tags.includes('key_skills_match')) {
      explanation += ' 关键技能高度匹配。';
    }

    return explanation;
  }

  /**
   * 批量排序多个岗位的候选人
   */
  public async batchRankCandidates(
    jobCandidateMap: Map<string, MatchingResult[]>,
    globalConfig?: Partial<RankingConfig>
  ): Promise<Map<string, EnhancedMatchingResult[]>> {
    const results = new Map<string, EnhancedMatchingResult[]>();

    for (const [jobId, candidates] of jobCandidateMap) {
      console.log(`📊 为岗位 ${jobId} 排序 ${candidates.length} 个候选人`);
      
      const ranked = await this.rankMatchingResults(candidates, globalConfig);
      results.set(jobId, ranked);
    }

    return results;
  }
}

export const matchingRankingService = new MatchingRankingService();