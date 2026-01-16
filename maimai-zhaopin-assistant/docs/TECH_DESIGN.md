# 脉脉招聘助手 - 技术设计文档 (TDD)

## 🏗️ 系统架构设计

### 整体架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    Chrome Extension                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   UI Layer   │    │ Control Layer│    │  Data Layer  │  │
│  │              │    │              │    │              │  │
│  │  ┌─────────┐ │    │ ┌──────────┐ │    │ ┌──────────┐ │  │
│  │  │FloatPanel│ │◄──►│ │TaskEngine│ │◄──►│ │DataStore │ │  │
│  │  └─────────┘ │    │ └──────────┘ │    │ └──────────┘ │  │
│  └──────────────┘    │      │       │    │      │       │  │
│                      │      ▼       │    │      ▼       │  │
│  ┌──────────────┐    │ ┌──────────┐ │    │ ┌──────────┐ │  │
│  │Extract Layer │    │ │StateManager │    │ │ExportEngine │  │
│  │              │    │ └──────────┘ │    │ └──────────┘ │  │
│  │ ┌─────────┐  │    │      │       │    └──────────────┘  │
│  │ │PageParser│  │◄───┼──────┘       │                     │
│  │ └─────────┘  │    │              │                     │
│  │ ┌─────────┐  │    │ ┌──────────┐ │                     │
│  │ │InfoExtractor │  │ │NavController │                  │
│  │ └─────────┘  │    │ └──────────┘ │                     │
│  └──────────────┘    └──────────────┘                     │
│                              │                             │
├─────────────────────────────────────────────────────────────┤
│                   Browser DOM API                          │
└─────────────────────────────────────────────────────────────┘
```

### 技术选型

#### 核心技术栈
```yaml
框架: Chrome Extension Manifest V3
语言: TypeScript 5.0+
构建: Webpack 5 / Vite
测试: Jest + Chrome Extension Testing
代码规范: ESLint + Prettier
```

#### 依赖库选择
```yaml
Excel导出: SheetJS (xlsx)
DOM操作: 原生API + 自研工具库
状态管理: 自研轻量级状态机
存储: Chrome Extension Storage API + localStorage备份
工具函数: 自研（避免外部依赖）
```

## 📦 核心模块设计

### 1. TaskEngine (任务引擎)

**职责**: 核心业务流程编排，任务调度和生命周期管理

#### 接口定义
```typescript
interface ITaskEngine {
  // 任务控制
  startTask(config: TaskConfig): Promise<TaskResult>
  pauseTask(): Promise<void>
  resumeTask(): Promise<void>
  stopTask(): Promise<void>
  
  // 状态查询
  getTaskStatus(): TaskContext
  getCurrentProgress(): ProgressInfo
  
  // 事件通知
  onProgressUpdate(callback: (progress: ProgressInfo) => void): void
  onTaskComplete(callback: (result: TaskResult) => void): void
  onError(callback: (error: TaskError) => void): void
}
```

#### 核心算法
```typescript
class TaskEngine implements ITaskEngine {
  private async executeTaskPipeline(config: TaskConfig): Promise<TaskResult> {
    const pipeline = new ProcessingPipeline([
      new ScanStage(),      // 扫描人才卡片
      new ClickStage(),     // 点击打开详情
      new ExtractStage(),   // 提取信息
      new ValidateStage(),  // 验证数据质量
      new SaveStage()       // 保存数据
    ]);
    
    let processedCount = 0;
    const results: TalentProfile[] = [];
    
    while (this.hasMoreTargets()) {
      const batch = await this.getNextBatch(config.batchSize);
      
      for (const target of batch) {
        try {
          const result = await pipeline.process(target);
          results.push(result);
          processedCount++;
          
          this.notifyProgress({
            processed: processedCount,
            total: this.estimateTotal(),
            currentTarget: target.name
          });
          
          // 间隔控制
          await this.sleep(config.interval);
          
        } catch (error) {
          const recovery = await this.handleError(error, target);
          if (!recovery.canContinue) break;
        }
      }
      
      // 批次间内存清理
      this.cleanupMemory();
      
      // 检查是否需要翻页
      if (await this.needsNavigation()) {
        await this.navController.goToNextPage();
      }
    }
    
    return {
      status: 'SUCCESS',
      totalProcessed: processedCount,
      results: results
    };
  }
}
```

### 2. PageParser (页面解析器)

**职责**: DOM结构分析，元素定位和页面状态检测

#### 核心算法 - 多重选择器策略
```typescript
class PageParser implements IPageParser {
  private talentCardSelectors = [
    // 策略1: 通用类名选择器
    '.talent-card, .candidate-card, .user-card',
    
    // 策略2: 属性选择器
    '[data-testid*="talent"], [data-qa*="candidate"]',
    
    // 策略3: 结构特征选择器
    '.list-item:has(img[src*="avatar"]):has(.name)',
    
    // 策略4: 文本特征选择器
    'div:contains("年") + div:contains("经验")',
  ];
  
  async getTalentCards(): Promise<TalentCard[]> {
    let cards: HTMLElement[] = [];
    
    // 逐个尝试选择器策略
    for (const selector of this.talentCardSelectors) {
      try {
        const elements = Array.from(document.querySelectorAll(selector)) as HTMLElement[];
        if (elements.length > 0) {
          cards = elements;
          console.log(`成功使用选择器: ${selector}, 找到 ${cards.length} 个卡片`);
          break;
        }
      } catch (error) {
        console.warn(`选择器失败: ${selector}`, error);
      }
    }
    
    // 如果所有策略都失败，使用智能启发式方法
    if (cards.length === 0) {
      cards = await this.heuristicCardDetection();
    }
    
    return this.convertToTalentCards(cards);
  }
  
  private async heuristicCardDetection(): Promise<HTMLElement[]> {
    // 基于内容特征的启发式检测
    const candidates = Array.from(document.querySelectorAll('div, li, article'));
    
    return candidates.filter(element => {
      const text = element.textContent || '';
      const hasNamePattern = /[\u4e00-\u9fa5]{2,4}|[A-Za-z\s]{2,20}/.test(text);
      const hasExperiencePattern = /\d+年|经验|\d+\s*-\s*\d+/.test(text);
      const hasLocationPattern = /北京|上海|广州|深圳|杭州/.test(text);
      
      return hasNamePattern && hasExperiencePattern && hasLocationPattern;
    }) as HTMLElement[];
  }
}
```

### 3. InfoExtractor (信息提取器)

**职责**: 结构化数据提取，数据清洗和标准化

#### 多策略提取算法
```typescript
class InfoExtractor implements IInfoExtractor {
  private extractionStrategies: Map<string, ExtractionStrategy> = new Map([
    ['name', new NameExtractionStrategy()],
    ['location', new LocationExtractionStrategy()],
    ['experience', new ExperienceExtractionStrategy()],
    ['workHistory', new WorkHistoryExtractionStrategy()],
    ['education', new EducationExtractionStrategy()]
  ]);
  
  async extractDetailInfo(): Promise<DetailInfo> {
    const result: Partial<TalentProfile> = {};
    const confidence: Record<string, number> = {};
    
    // 并行提取各字段
    const extractionPromises = Array.from(this.extractionStrategies.entries())
      .map(async ([field, strategy]) => {
        try {
          const extraction = await strategy.extract(document);
          result[field] = extraction.value;
          confidence[field] = extraction.confidence;
        } catch (error) {
          console.warn(`字段提取失败: ${field}`, error);
          confidence[field] = 0;
        }
      });
    
    await Promise.all(extractionPromises);
    
    // 计算整体置信度
    const overallConfidence = this.calculateOverallConfidence(confidence);
    
    // 如果置信度不足，尝试备选策略
    if (overallConfidence < 0.8) {
      await this.applyFallbackStrategies(result, confidence);
    }
    
    return {
      ...result as TalentProfile,
      accuracy: overallConfidence
    };
  }
}

// 姓名提取策略示例
class NameExtractionStrategy implements ExtractionStrategy {
  async extract(doc: Document): Promise<ExtractionResult> {
    const nameSelectors = [
      'h1, h2, h3',                    // 标题元素
      '.name, .username, .title',      // 类名选择器
      '[data-field="name"]',           // 数据属性
      '.detail-header .main-info'      // 结构位置
    ];
    
    for (const selector of nameSelectors) {
      const elements = doc.querySelectorAll(selector);
      
      for (const element of elements) {
        const text = element.textContent?.trim();
        
        if (text && this.isValidName(text)) {
          return {
            value: text,
            confidence: this.calculateNameConfidence(text, element),
            method: selector
          };
        }
      }
    }
    
    // 如果失败，使用正则表达式在全文中搜索
    return this.searchNameInFullText(doc);
  }
  
  private isValidName(text: string): boolean {
    // 中文姓名：2-4个汉字
    const chineseNamePattern = /^[\u4e00-\u9fa5]{2,4}$/;
    // 英文姓名：2-20个字母和空格
    const englishNamePattern = /^[A-Za-z\s]{2,20}$/;
    
    return chineseNamePattern.test(text) || englishNamePattern.test(text);
  }
}
```

### 4. DataStore (数据存储)

**职责**: 数据持久化，CRUD操作和数据管理

#### 存储架构
```typescript
class DataStore implements IDataStore {
  private readonly STORAGE_KEYS = {
    TALENTS: 'talents',
    APP_STATE: 'app_state',
    TASK_PROGRESS: 'task_progress'
  };
  
  // 双重存储策略：Chrome Storage + localStorage备份
  async saveTalent(talent: TalentProfile): Promise<void> {
    try {
      // 主存储：Chrome Extension Storage
      await chrome.storage.local.set({
        [`talent_${talent.id}`]: talent
      });
      
      // 备份存储：localStorage
      this.saveToLocalStorage(talent);
      
    } catch (error) {
      console.error('存储失败:', error);
      
      // 如果Chrome Storage失败，至少保存到localStorage
      this.saveToLocalStorage(talent);
    }
  }
  
  // 批量操作优化
  async saveTalents(talents: TalentProfile[]): Promise<void> {
    const batchSize = 50; // Chrome Storage API 限制
    const batches = this.chunkArray(talents, batchSize);
    
    for (const batch of batches) {
      const storageData: Record<string, TalentProfile> = {};
      
      batch.forEach(talent => {
        storageData[`talent_${talent.id}`] = talent;
      });
      
      await chrome.storage.local.set(storageData);
    }
  }
  
  // 智能搜索
  async searchTalents(criteria: SearchCriteria): Promise<TalentProfile[]> {
    const allTalents = await this.getAllTalents();
    
    return allTalents.filter(talent => {
      // 姓名模糊匹配
      if (criteria.name && !talent.name.includes(criteria.name)) {
        return false;
      }
      
      // 地点匹配
      if (criteria.location && !talent.location.includes(criteria.location)) {
        return false;
      }
      
      // 技能标签匹配
      if (criteria.skills && criteria.skills.length > 0) {
        const hasMatchingSkills = criteria.skills.some(skill =>
          talent.skills.some(talentSkill => 
            talentSkill.toLowerCase().includes(skill.toLowerCase())
          )
        );
        if (!hasMatchingSkills) return false;
      }
      
      // 时间范围匹配
      if (criteria.extractTimeRange) {
        const extractTime = new Date(talent.extractTime);
        const [startTime, endTime] = criteria.extractTimeRange;
        if (extractTime < startTime || extractTime > endTime) {
          return false;
        }
      }
      
      return true;
    });
  }
}
```

### 5. ExportEngine (导出引擎)

**职责**: 数据导出，格式转换和文件生成

#### Excel导出实现
```typescript
class ExportEngine implements IExportEngine {
  async exportToExcel(talents: TalentProfile[], options: ExportOptions): Promise<Blob> {
    const XLSX = await import('xlsx');
    
    // 构建工作表数据
    const worksheetData = this.buildWorksheetData(talents, options);
    
    // 创建工作簿
    const workbook = XLSX.utils.book_new();
    const worksheet = XLSX.utils.aoa_to_sheet(worksheetData);
    
    // 设置列宽
    worksheet['!cols'] = this.calculateColumnWidths(worksheetData);
    
    // 设置样式
    this.applyWorksheetStyles(worksheet);
    
    // 添加工作表到工作簿
    XLSX.utils.book_append_sheet(workbook, worksheet, '人才数据');
    
    // 生成Excel文件
    const excelBuffer = XLSX.write(workbook, {
      bookType: 'xlsx',
      type: 'array'
    });
    
    return new Blob([excelBuffer], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    });
  }
  
  private buildWorksheetData(talents: TalentProfile[], options: ExportOptions): any[][] {
    // 动态表头生成
    const headers = this.buildHeaders(talents, options);
    const rows = [headers];
    
    // 数据行生成
    talents.forEach(talent => {
      const row = this.buildDataRow(talent, headers, options);
      rows.push(row);
    });
    
    return rows;
  }
  
  private buildHeaders(talents: TalentProfile[], options: ExportOptions): string[] {
    const baseHeaders = ['姓名', '地点', '工作年限', '年龄', '学历'];
    
    if (options.includeDetails) {
      // 动态计算最大工作经历数量
      const maxWorkHistory = Math.max(...talents.map(t => t.workHistory?.length || 0));
      
      // 添加工作经历列
      for (let i = 0; i < maxWorkHistory; i++) {
        baseHeaders.push(
          `工作经历${i + 1}-公司`,
          `工作经历${i + 1}-职位`,
          `工作经历${i + 1}-时间`
        );
      }
      
      // 动态计算最大教育经历数量
      const maxEducation = Math.max(...talents.map(t => t.educationHistory?.length || 0));
      
      // 添加教育经历列
      for (let i = 0; i < maxEducation; i++) {
        baseHeaders.push(
          `教育经历${i + 1}-学校`,
          `教育经历${i + 1}-专业`,
          `教育经历${i + 1}-学历`
        );
      }
      
      baseHeaders.push('技能标签', '提取时间', '数据准确度');
    }
    
    return baseHeaders;
  }
}
```

## 🔄 核心算法设计

### 1. 弹窗检测算法

**问题**: 脉脉详情弹窗无URL变化，需要可靠的检测机制

**解决方案**: 多维度组合检测
```typescript
class DetailPanelDetector {
  async detectPanelState(): Promise<PanelState> {
    const detectionResults = await Promise.all([
      this.checkDOMStructure(),      // DOM结构检测
      this.checkVisualCues(),        // 视觉特征检测
      this.checkZIndex(),            // 层级检测
      this.checkAnimationState(),    // 动画状态检测
      this.checkContentSignature()   // 内容特征检测
    ]);
    
    return this.consensusDecision(detectionResults);
  }
  
  private async checkContentSignature(): Promise<boolean> {
    // 检测特征内容是否出现
    const signatures = [
      '工作经历', '教育经历', '职业技能',
      '个人简介', '联系方式'
    ];
    
    const detectedSignatures = signatures.filter(signature =>
      document.body.textContent?.includes(signature)
    );
    
    // 如果检测到3个以上特征，认为详情面板已打开
    return detectedSignatures.length >= 3;
  }
  
  private consensusDecision(results: boolean[]): PanelState {
    const trueCount = results.filter(r => r).length;
    const confidence = trueCount / results.length;
    
    return {
      isOpen: confidence > 0.6,
      confidence: confidence,
      details: results
    };
  }
}
```

### 2. 批量处理优化算法

**问题**: 500+规模处理时的性能和稳定性

**解决方案**: 自适应批次处理
```typescript
class AdaptiveBatchProcessor {
  private performanceMetrics = new PerformanceMonitor();
  private batchSize = 20; // 初始批次大小
  
  async processBatches(targets: any[]): Promise<any[]> {
    const results: any[] = [];
    let currentIndex = 0;
    
    while (currentIndex < targets.length) {
      const batchStartTime = Date.now();
      
      // 动态调整批次大小
      const adjustedBatchSize = this.calculateOptimalBatchSize();
      const batch = targets.slice(currentIndex, currentIndex + adjustedBatchSize);
      
      try {
        const batchResults = await this.processBatch(batch);
        results.push(...batchResults);
        currentIndex += adjustedBatchSize;
        
        // 更新性能指标
        const batchTime = Date.now() - batchStartTime;
        this.performanceMetrics.recordBatchPerformance(adjustedBatchSize, batchTime);
        
      } catch (error) {
        // 批次失败时减小批次大小重试
        if (adjustedBatchSize > 5) {
          this.batchSize = Math.max(5, Math.floor(adjustedBatchSize / 2));
          continue;
        } else {
          throw error;
        }
      }
      
      // 批次间清理和休息
      await this.cleanupAndRest();
    }
    
    return results;
  }
  
  private calculateOptimalBatchSize(): number {
    const metrics = this.performanceMetrics.getRecentMetrics();
    
    // 基于内存使用率调整
    if (metrics.memoryUsage > 80) {
      this.batchSize = Math.max(5, Math.floor(this.batchSize * 0.8));
    } else if (metrics.memoryUsage < 50 && metrics.averageProcessTime < 3000) {
      this.batchSize = Math.min(50, Math.floor(this.batchSize * 1.2));
    }
    
    return this.batchSize;
  }
}
```

### 3. 准确率保障算法

**问题**: 确保95%的数据提取准确率

**解决方案**: 多重验证和自动修正
```typescript
class AccuracyGuard {
  private validators: DataValidator[] = [
    new FormatValidator(),      // 格式验证
    new ConsistencyValidator(), // 一致性验证
    new CompletenessValidator() // 完整性验证
  ];
  
  async validateAndImprove(data: TalentProfile): Promise<ValidationResult> {
    let currentData = { ...data };
    let overallScore = 0;
    const issues: ValidationIssue[] = [];
    
    // 多轮验证和修正
    for (let round = 0; round < 3; round++) {
      const validationResults = await Promise.all(
        this.validators.map(validator => validator.validate(currentData))
      );
      
      overallScore = this.calculateScore(validationResults);
      
      if (overallScore >= 0.95) {
        break; // 达到目标准确率
      }
      
      // 尝试自动修正
      const corrections = await this.generateCorrections(validationResults);
      currentData = this.applyCorrections(currentData, corrections);
    }
    
    return {
      data: currentData,
      accuracy: overallScore,
      issues: issues,
      needsManualReview: overallScore < 0.90
    };
  }
  
  private async generateCorrections(validationResults: ValidationResult[]): Promise<Correction[]> {
    const corrections: Correction[] = [];
    
    validationResults.forEach(result => {
      if (!result.passed) {
        switch (result.issue.type) {
          case 'INVALID_FORMAT':
            corrections.push(this.createFormatCorrection(result.issue));
            break;
          case 'MISSING_DATA':
            corrections.push(this.createDataRecoveryCorrection(result.issue));
            break;
          case 'INCONSISTENT_DATA':
            corrections.push(this.createConsistencyCorrection(result.issue));
            break;
        }
      }
    });
    
    return corrections;
  }
}
```

## 🛡️ 错误处理机制

### 分层错误处理策略
```typescript
class ErrorHandlingSystem {
  private errorHandlers = new Map([
    ['NETWORK_ERROR', new NetworkErrorHandler()],
    ['DOM_ERROR', new DOMErrorHandler()],
    ['EXTRACTION_ERROR', new ExtractionErrorHandler()],
    ['STORAGE_ERROR', new StorageErrorHandler()]
  ]);
  
  async handleError(error: Error, context: any): Promise<RecoveryAction> {
    // 错误分类
    const errorType = this.classifyError(error);
    const handler = this.errorHandlers.get(errorType);
    
    if (handler) {
      return await handler.handle(error, context);
    }
    
    // 默认错误处理
    return {
      action: 'SKIP',
      reason: 'Unknown error type',
      retryable: false
    };
  }
}

// 网络错误处理器示例
class NetworkErrorHandler implements ErrorHandler {
  async handle(error: Error, context: any): Promise<RecoveryAction> {
    const retryCount = context.retryCount || 0;
    
    if (retryCount < 3) {
      return {
        action: 'RETRY',
        delay: this.calculateBackoffDelay(retryCount),
        retryable: true
      };
    }
    
    return {
      action: 'SKIP',
      reason: 'Max retries exceeded',
      retryable: false
    };
  }
  
  private calculateBackoffDelay(retryCount: number): number {
    // 指数退避算法
    return Math.min(1000 * Math.pow(2, retryCount), 10000);
  }
}
```

## 📊 性能优化策略

### 1. 内存管理
```typescript
class MemoryManager {
  private readonly MAX_MEMORY_USAGE = 100 * 1024 * 1024; // 100MB
  private elementCache = new WeakMap();
  
  async monitorAndOptimize(): Promise<void> {
    const memoryInfo = await this.getMemoryUsage();
    
    if (memoryInfo.usedJSHeapSize > this.MAX_MEMORY_USAGE * 0.8) {
      await this.performCleanup();
    }
  }
  
  private async performCleanup(): Promise<void> {
    // 清理DOM引用
    this.elementCache = new WeakMap();
    
    // 触发垃圾回收（如果可用）
    if ('gc' in window) {
      (window as any).gc();
    }
    
    // 清理事件监听器
    this.removeOrphanedEventListeners();
  }
}
```

### 2. DOM操作优化
```typescript
class DOMOptimizer {
  private queryCache = new Map<string, HTMLElement>();
  
  // 缓存频繁查询的元素
  getCachedElement(selector: string): HTMLElement | null {
    if (!this.queryCache.has(selector)) {
      const element = document.querySelector(selector) as HTMLElement;
      if (element) {
        this.queryCache.set(selector, element);
      }
    }
    return this.queryCache.get(selector) || null;
  }
  
  // 批量DOM操作
  async batchDOMOperations(operations: DOMOperation[]): Promise<void> {
    const fragment = document.createDocumentFragment();
    
    // 将所有操作在DocumentFragment中进行
    operations.forEach(operation => {
      operation.execute(fragment);
    });
    
    // 一次性添加到实际DOM
    document.body.appendChild(fragment);
  }
}
```

---

**文档版本**: v1.0  
**更新时间**: 2024-12-21  
**负责人**: Tech Team  
**审核状态**: 待审核