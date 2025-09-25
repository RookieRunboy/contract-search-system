// 文档块类型
export interface DocumentChunk {
  score: number;
  page_id: number;
  text: string;
  highlights: Record<string, any>;
  metadata_highlights?: Record<string, string[]>; // 元数据高亮信息
}

// 合同搜索结果类型
export interface ContractSearchResult {
  contract_name: string;
  score: number;
  chunks: DocumentChunk[];
  metadata_info?: ContractMetadata; // 合同元数据信息
  metadata_score?: number; // 元数据匹配分数
}

// 搜索结果类型（保持向后兼容）
export interface SearchResult {
  contractName: string;
  pageNum: number;
  content: string;
  score: number;
}

// 搜索响应类型
export interface SearchResponse {
  results: SearchResult[];
  total: number;
}

// 系统状态类型
export interface SystemStatus {
  elasticsearch: {
    status: string;
    cluster_name: string;
    version: string;
  };
}

// 上传文件状态
export interface UploadFileStatus {
  uid: string;
  name: string;
  status: 'uploading' | 'done' | 'error';
  response?: any;
  error?: any;
  percent?: number;
}

// 菜单项类型
export interface MenuItem {
  key: string;
  icon?: React.ReactNode;
  label: string;
  path: string;
}

// 合同元数据类型（精简版，只包含必要的6个字段）
export interface ContractMetadata {
  contract_name: string; // 合同名称（使用上传文件名）
  party_a: string | null; // 甲方
  party_b: string | null; // 乙方
  contract_type: string | null; // 合同方向
  contract_amount: number | null; // 合同金额
  signing_date?: string | null; // 签订日期，YYYY-MM-DD
  project_description: string | null; // 项目描述
  positions: string | null; // 岗位
  personnel_list: string | null; // 人员清单
  extracted_at: string; // 提取时间
  contractKey?: string; // 合同键值，用于状态更新匹配
  fileName?: string; // 文件名，用于状态更新匹配
}

// 元数据提取响应类型
export interface MetadataExtractionResponse {
  code: number;
  message: string;
  data: {
    filename: string;
    metadata: ContractMetadata;
    document_length: number;
    raw_response?: string;
  } | null;
}

// 搜索筛选参数类型
export interface SearchFilters {
  amountMin?: number;
  amountMax?: number;
  dateStart?: string; // YYYY-MM-DD格式
  dateEnd?: string; // YYYY-MM-DD格式
}
