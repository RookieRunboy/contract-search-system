// 文档块类型
export interface DocumentChunk {
  score: number;
  page_id: number;
  text: string;
  highlights: Record<string, any>;
}

// 合同搜索结果类型
export interface ContractSearchResult {
  contract_name: string;
  score: number;
  chunks: DocumentChunk[];
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