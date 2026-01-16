# 脉脉招聘助手 - API接口规范文档

## 📋 接口设计原则

### 稳定性分级
- **Level 1 (核心契约)**: 永不变更，向后兼容
- **Level 2 (业务接口)**: 高稳定性，只能扩展不能破坏
- **Level 3 (扩展接口)**: 中等稳定性，可适度调整
- **Level 4 (实现接口)**: 低稳定性，可随需求变化

### 错误处理约定
- 所有异步操作返回 Promise
- 错误信息包含类型、消息、上下文
- 支持错误恢复和重试机制

## 🎯 核心数据模型 (Level 1 - 永不变更)

### TalentProfile (人才档案)
```typescript
interface TalentProfile {
  // 核心标识 - 永不变更
  readonly id: string;                    // 系统生成的唯一ID
  readonly sourceId: string;              // 脉脉平台的人才ID
  readonly extractTime: Date;             // 提取时间
  
  // 基础信息 - 高稳定性
  name: string;                           // 姓名
  location: string;                       // 工作地点
  experience: string;                     // 工作年限
  age: number | null;                     // 年龄
  educationLevel: string;                 // 最高学历
  
  // 详细信息 - 可扩展
  workHistory: WorkExperience[];          // 工作经历
  educationHistory: Education[];          // 教育经历
  skills: string[];                       // 技能标签
  industryTags?: string[];                // 行业标签 (可选)
  
  // 元数据 - 可扩展
  extractStatus: ExtractStatus;           // 提取状态
  sourceUrl: string;                      // 来源URL
  cardPosition: number;                   // 在列表中的位置
  accuracy: number;                       // 数据准确度评分 0-1
}

interface WorkExperience {
  company: string;                        // 公司名称
  position: string;                       // 职位
  duration: string;                       // 时间段
  description: string;                    // 工作描述
  industry?: string;                      // 行业 (可选)
}

interface Education {
  school: string;                         // 学校名称
  major: string;                          // 专业
  degree: string;                         // 学位
  duration: string;                       // 时间段
}

type ExtractStatus = 'SUCCESS' | 'PARTIAL' | 'FAILED' | 'PENDING';
```

### TaskContext (任务上下文)
```typescript
interface TaskContext {
  // 任务标识 - 永不变更
  readonly taskId: string;
  readonly startTime: Date;
  
  // 进度信息 - 高稳定性
  progress: ProgressInfo;
  
  // 配置信息 - 可扩展
  config: TaskConfig;
}

interface ProgressInfo {
  totalFound: number;                     // 发现的人才总数
  processed: number;                      // 已处理数量
  succeeded: number;                      // 成功提取数量
  failed: number;                         // 失败数量
  currentPage: number;                    // 当前页码
  hasNextPage: boolean;                   // 是否有下一页
}

interface TaskConfig {
  extractDetail: boolean;                 // 是否提取详细信息
  autoNextPage: boolean;                  // 是否自动翻页
  maxTargets?: number;                    // 最大处理数量限制
  interval: number;                       // 处理间隔(毫秒)
  retryCount: number;                     // 重试次数
}
```

### AppState (应用状态)
```typescript
interface AppState {
  // 运行状态 - 高稳定性
  status: ProcessStatus;
  currentTask: TaskContext | null;
  
  // 数据状态 - 可扩展
  talents: TalentProfile[];
  statistics: StatisticsInfo;
  
  // UI状态 - 低稳定性
  panelVisible: boolean;
  selectedExportFormat: ExportFormat;
}

type ProcessStatus = 'IDLE' | 'SCANNING' | 'EXTRACTING' | 'PAUSED' | 'FINISHED' | 'ERROR';
type ExportFormat = 'EXCEL' | 'CSV' | 'JSON';

interface StatisticsInfo {
  totalExtracted: number;
  successRate: number;
  avgExtractionTime: number;
}
```

## 🚀 核心业务接口 (Level 2 - 高稳定性)

### ITaskEngine (任务引擎) - 核心协调者

```typescript
interface ITaskEngine {
  // 任务控制 - 永不变更签名
  startTask(config: TaskConfig): Promise<TaskResult>;
  pauseTask(): Promise<void>;
  resumeTask(): Promise<void>;
  stopTask(): Promise<void>;
  
  // 状态查询 - 高稳定性
  getTaskStatus(): TaskContext;
  getCurrentProgress(): ProgressInfo;
  
  // 事件通知 - 可扩展
  onProgressUpdate(callback: (progress: ProgressInfo) => void): UnsubscribeFunction;
  onTaskComplete(callback: (result: TaskResult) => void): UnsubscribeFunction;
  onError(callback: (error: TaskError) => void): UnsubscribeFunction;
}

// 输入输出类型
interface TaskResult {
  status: 'SUCCESS' | 'PARTIAL' | 'FAILED';
  totalProcessed: number;
  successCount: number;
  errorCount: number;
  duration: number;                       // 执行时长(毫秒)
  errors: TaskError[];
  data?: TalentProfile[];                 // 可选的结果数据
}

interface TaskError {
  type: ErrorType;
  message: string;
  details: any;
  timestamp: Date;
  recoverable: boolean;
  context?: any;                          // 错误上下文
}

type ErrorType = 'NETWORK' | 'PARSING' | 'EXTRACTION' | 'STORAGE' | 'NAVIGATION' | 'UNKNOWN';
type UnsubscribeFunction = () => void;
```

### IDataStore (数据存储) - 稳定契约

```typescript
interface IDataStore {
  // CRUD操作 - 永不变更签名
  saveTalent(talent: TalentProfile): Promise<void>;
  getTalent(id: string): Promise<TalentProfile | null>;
  getAllTalents(): Promise<TalentProfile[]>;
  deleteTalent(id: string): Promise<void>;
  clearAllData(): Promise<void>;
  
  // 批量操作 - 高稳定性
  saveTalents(talents: TalentProfile[]): Promise<BatchResult>;
  searchTalents(criteria: SearchCriteria): Promise<TalentProfile[]>;
  
  // 状态管理 - 可扩展
  saveAppState(state: AppState): Promise<void>;
  loadAppState(): Promise<AppState | null>;
  
  // 统计查询 - 可扩展
  getStatistics(): Promise<StatisticsInfo>;
}

// 搜索条件
interface SearchCriteria {
  name?: string;
  location?: string;
  experience?: string;
  skills?: string[];
  extractTimeRange?: [Date, Date];
  minAccuracy?: number;                   // 最小准确度要求
}

// 批量操作结果
interface BatchResult {
  successCount: number;
  errorCount: number;
  errors: StorageError[];
}

interface StorageError {
  type: 'QUOTA_EXCEEDED' | 'ACCESS_DENIED' | 'CORRUPTION' | 'NETWORK';
  operation: string;
  itemId?: string;
  message: string;
}
```

## 🔍 提取层接口 (Level 3 - 中等稳定性)

### IPageParser (页面解析器)

```typescript
interface IPageParser {
  // 页面状态检测 - 高稳定性
  detectPageType(): Promise<PageType>;
  getTalentCards(): Promise<TalentCard[]>;
  isDetailPanelOpen(): Promise<PanelState>;
  hasNextPage(): Promise<boolean>;
  
  // 交互控制 - 中等稳定性
  clickTalentCard(index: number): Promise<ClickResult>;
  closeDetailPanel(): Promise<boolean>;
  goToNextPage(): Promise<NavigationResult>;
  scrollToLoadMore(): Promise<ScrollResult>;
  
  // 高级功能 - 可扩展
  waitForElement(selector: string, timeout?: number): Promise<HTMLElement>;
  getPageMetadata(): Promise<PageMetadata>;
}

// 输入输出类型
type PageType = 'TALENT_LIST' | 'DETAIL_PANEL' | 'ERROR_PAGE' | 'LOADING' | 'UNKNOWN';

interface TalentCard {
  index: number;
  element: HTMLElement;
  basicInfo: BasicInfo;
  clickable: boolean;
  visible: boolean;
}

interface BasicInfo {
  name: string;
  location: string;
  experience: string;
  age?: number;
  education?: string;
}

interface PanelState {
  isOpen: boolean;
  confidence: number;                     // 检测置信度 0-1
  panelType?: 'DETAIL' | 'ERROR' | 'LOADING';
  details: DetectionDetails;
}

interface DetectionDetails {
  domStructure: boolean;
  visualCues: boolean;
  contentSignature: boolean;
  animationState: boolean;
}

interface ClickResult {
  success: boolean;
  panelOpened: boolean;
  errorMessage?: string;
  retryRecommended: boolean;
}

interface NavigationResult {
  success: boolean;
  newPageLoaded: boolean;
  pageNumber?: number;
  errorMessage?: string;
}

interface ScrollResult {
  success: boolean;
  newContentLoaded: boolean;
  itemsAdded: number;
  reachedEnd: boolean;
}

interface PageMetadata {
  totalResults?: number;
  currentPage?: number;
  totalPages?: number;
  loadTime: number;
}
```

### IInfoExtractor (信息提取器)

```typescript
interface IInfoExtractor {
  // 核心提取功能 - 高稳定性
  extractBasicInfo(card: TalentCard): Promise<ExtractionResult<BasicInfo>>;
  extractDetailInfo(): Promise<ExtractionResult<DetailInfo>>;
  
  // 质量控制 - 高稳定性
  validateExtractedData(data: TalentProfile): Promise<ValidationResult>;
  
  // 策略控制 - 可扩展
  setExtractionStrategy(strategy: ExtractionStrategy): void;
  getExtractionConfidence(): Promise<number>;
  
  // 高级功能 - 可扩展
  extractCustomFields(fields: FieldDefinition[]): Promise<Record<string, any>>;
}

// 提取结果类型
interface ExtractionResult<T> {
  data: T;
  confidence: number;                     // 置信度 0-1
  method: string;                         // 提取方法
  duration: number;                       // 提取耗时(毫秒)
  warnings: string[];                     // 警告信息
}

interface DetailInfo {
  workHistory: WorkExperience[];
  educationHistory: Education[];
  skills: string[];
  industryTags: string[];
  summary?: string;                       // 个人简介
  contactInfo?: ContactInfo;              // 联系方式(如可获取)
}

interface ContactInfo {
  email?: string;
  phone?: string;
  linkedin?: string;
  github?: string;
}

interface ValidationResult {
  isValid: boolean;
  accuracy: number;                       // 综合准确度 0-1
  fieldAccuracies: Record<string, number>; // 各字段准确度
  missingFields: string[];
  invalidFields: string[];
  suggestions: string[];                  // 改进建议
}

type ExtractionStrategy = 'FAST' | 'ACCURATE' | 'COMPREHENSIVE' | 'CONSERVATIVE';

interface FieldDefinition {
  name: string;
  selector: string[];                     // 多个候选选择器
  validator: (value: any) => boolean;
  transformer?: (value: any) => any;
}
```

## 📤 导出层接口 (Level 3 - 中等稳定性)

### IExportEngine (导出引擎)

```typescript
interface IExportEngine {
  // 核心导出功能 - 高稳定性
  exportToExcel(talents: TalentProfile[], options?: ExportOptions): Promise<Blob>;
  exportToCSV(talents: TalentProfile[], options?: ExportOptions): Promise<string>;
  exportToJSON(talents: TalentProfile[]): Promise<string>;
  
  // 格式配置 - 可扩展
  setExportTemplate(format: ExportFormat, template: ExportTemplate): void;
  getAvailableFormats(): ExportFormat[];
  
  // 高级功能 - 可扩展
  previewExport(talents: TalentProfile[], format: ExportFormat): Promise<PreviewData>;
  validateExportData(talents: TalentProfile[]): Promise<ExportValidation>;
}

interface ExportOptions {
  includeDetails: boolean;                // 是否包含详细信息
  fields?: string[];                      // 指定导出字段
  filename?: string;                      // 文件名
  dateFormat?: string;                    // 日期格式
  encoding?: 'UTF-8' | 'GBK';            // 字符编码
  maxRows?: number;                       // 最大行数限制
}

interface ExportTemplate {
  headers: string[];                      // 表头
  fieldMapping: Record<string, string>;   // 字段映射
  formatters: Record<string, (value: any) => string>; // 格式化器
  styles?: ExportStyles;                  // 样式定义
}

interface ExportStyles {
  headerStyle?: CellStyle;
  dataStyle?: CellStyle;
  columnWidths?: number[];
}

interface CellStyle {
  fontWeight?: 'bold' | 'normal';
  backgroundColor?: string;
  textAlign?: 'left' | 'center' | 'right';
}

interface PreviewData {
  headers: string[];
  sampleRows: any[][];                   // 前几行示例数据
  estimatedFileSize: number;             // 预估文件大小(字节)
  rowCount: number;
  columnCount: number;
}

interface ExportValidation {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  estimatedDuration: number;             // 预估导出时长(毫秒)
}
```

## 🎛️ 控制层接口 (Level 2-3)

### IStateManager (状态管理器)

```typescript
interface IStateManager {
  // 状态操作 - 高稳定性
  getState(): AppState;
  updateState(updates: Partial<AppState>): void;
  resetState(): void;
  
  // 持久化 - 高稳定性
  saveState(): Promise<void>;
  loadState(): Promise<void>;
  
  // 订阅机制 - 中等稳定性
  subscribe(callback: StateChangeCallback): UnsubscribeFunction;
  subscribeToField<K extends keyof AppState>(
    field: K, 
    callback: (value: AppState[K]) => void
  ): UnsubscribeFunction;
  
  // 历史和回滚 - 可扩展
  getStateHistory(): AppState[];
  rollback(steps?: number): void;
  
  // 验证和调试 - 可扩展
  validateState(state: AppState): ValidationResult;
  exportStateSnapshot(): string;
  importStateSnapshot(snapshot: string): void;
}

type StateChangeCallback = (state: AppState, previousState: AppState) => void;
```

### INavController (导航控制器)

```typescript
interface INavController {
  // 基础导航 - 高稳定性
  goToNextPage(): Promise<NavigationResult>;
  goToPreviousPage(): Promise<NavigationResult>;
  scrollToLoadMore(): Promise<ScrollResult>;
  refreshCurrentPage(): Promise<void>;
  
  // 智能导航 - 中等稳定性
  estimateTotalPages(): Promise<number>;
  jumpToPage(pageNumber: number): Promise<NavigationResult>;
  autoNavigateToEnd(): Promise<NavigationSummary>;
  
  // 监控和控制 - 可扩展
  setNavigationStrategy(strategy: NavigationStrategy): void;
  getNavigationState(): NavigationState;
  onNavigationEvent(callback: NavigationEventCallback): UnsubscribeFunction;
}

interface NavigationSummary {
  totalPagesVisited: number;
  totalItemsFound: number;
  duration: number;
  errors: NavigationError[];
}

interface NavigationState {
  currentPage: number;
  totalPages: number;
  canGoNext: boolean;
  canGoPrevious: boolean;
  isLoading: boolean;
}

interface NavigationError {
  page: number;
  type: 'TIMEOUT' | 'NOT_FOUND' | 'NETWORK' | 'BLOCKED';
  message: string;
  timestamp: Date;
}

type NavigationStrategy = 'CONSERVATIVE' | 'AGGRESSIVE' | 'SMART';
type NavigationEventCallback = (event: NavigationEvent) => void;

interface NavigationEvent {
  type: 'PAGE_CHANGED' | 'CONTENT_LOADED' | 'SCROLL_END' | 'ERROR';
  data: any;
  timestamp: Date;
}
```

## 🛠️ 工具接口 (Level 4 - 低稳定性)

### ILogger (日志记录器)

```typescript
interface ILogger {
  debug(message: string, data?: any): void;
  info(message: string, data?: any): void;
  warn(message: string, data?: any): void;
  error(message: string, error?: Error, data?: any): void;
  
  // 结构化日志
  logExtraction(talent: TalentProfile, duration: number): void;
  logNavigation(from: number, to: number, success: boolean): void;
  logPerformance(operation: string, metrics: PerformanceMetrics): void;
  
  // 日志管理
  setLogLevel(level: LogLevel): void;
  exportLogs(): Promise<string>;
  clearLogs(): void;
}

type LogLevel = 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';

interface PerformanceMetrics {
  duration: number;
  memoryUsage: number;
  cpuUsage?: number;
  itemsProcessed: number;
}
```

### IConfigManager (配置管理器)

```typescript
interface IConfigManager {
  // 配置读写
  getConfig<T>(key: string, defaultValue?: T): T;
  setConfig<T>(key: string, value: T): void;
  resetConfig(key?: string): void;
  
  // 配置验证
  validateConfig(): ConfigValidation;
  
  // 配置导入导出
  exportConfig(): string;
  importConfig(configString: string): void;
}

interface ConfigValidation {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}
```

## 📊 事件系统

### 事件类型定义
```typescript
type EventMap = {
  'task:started': { taskId: string; config: TaskConfig };
  'task:progress': { progress: ProgressInfo };
  'task:completed': { result: TaskResult };
  'task:error': { error: TaskError };
  'task:paused': { taskId: string };
  'task:resumed': { taskId: string };
  
  'extraction:started': { target: TalentCard };
  'extraction:completed': { result: TalentProfile };
  'extraction:failed': { target: TalentCard; error: ExtractionError };
  
  'navigation:page-changed': { from: number; to: number };
  'navigation:scroll-end': { itemsLoaded: number };
  'navigation:error': { error: NavigationError };
  
  'storage:saved': { count: number };
  'storage:error': { error: StorageError };
  
  'ui:panel-toggled': { visible: boolean };
  'ui:export-requested': { format: ExportFormat };
};
```

### 事件发射器接口
```typescript
interface IEventEmitter {
  on<K extends keyof EventMap>(event: K, listener: (data: EventMap[K]) => void): UnsubscribeFunction;
  off<K extends keyof EventMap>(event: K, listener: (data: EventMap[K]) => void): void;
  emit<K extends keyof EventMap>(event: K, data: EventMap[K]): void;
  once<K extends keyof EventMap>(event: K, listener: (data: EventMap[K]) => void): UnsubscribeFunction;
}
```

---

**文档版本**: v1.0  
**创建时间**: 2024-12-21  
**维护团队**: Architecture Team  
**下次评审**: 2024-12-28