import api from './api';

export interface SearchResult {
  contractName: string;
  pageNum: number;
  content: string;
  score: number;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
}

export interface SystemStatus {
  elasticsearch: {
    status: string;
    cluster_name: string;
    version: string;
  };
}

// 文档上传
export const uploadDocument = async (file: File): Promise<any> => {
  const formData = new FormData();
  formData.append('file', file);
  
  return api.post('/document/add', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 600000, // 10分钟超时，适合大文件上传
  });
};

// 文档搜索
export const searchDocuments = async (query: string, topK: number = 5): Promise<ContractSearchResult[]> => {
  try {
    const response = await api.get('/document/search', {
      params: { query, top_k: topK }
    });
    
    // 兼容不同后端返回结构：
    // 1) 直接返回数组
    // 2) { data: [...] }
    // 3) { results: [...] }
    // 4) { code: 200, data: [...] } (FastAPI格式)
    const raw: unknown = response;
    const list: unknown = Array.isArray(raw)
      ? raw
      : Array.isArray((raw as any)?.data)
        ? (raw as any).data
        : Array.isArray((raw as any)?.results)
          ? (raw as any).results
          : [];
    
    return normalizeSearchList(list);
  } catch (error: any) {
    console.error('搜索请求失败:', error);
    throw new Error(error.response?.data?.detail || error.message || '搜索失败');
  }
};

// 新增：支持元数据搜索的接口
export const searchDocumentsWithMetadata = async (
  queryContent?: string,
  queryMetadata?: string,
  searchMode: string = 'content',
  topK: number = 5
): Promise<ContractSearchResult[]> => {
  try {
    const params: any = {
      top_k: topK,
      search_mode: searchMode
    };
    
    if (queryContent) {
      params.query_content = queryContent;
    }
    if (queryMetadata) {
      params.query_metadata = queryMetadata;
    }
    
    const response = await api.get('/document/search', { params });
    
    // 处理后端返回的数据结构
    const raw: unknown = response;
    const list: unknown = Array.isArray(raw)
      ? raw
      : Array.isArray((raw as any)?.data)
        ? (raw as any).data
        : Array.isArray((raw as any)?.results)
          ? (raw as any).results
          : [];
    
    return normalizeSearchList(list);
  } catch (error: any) {
    console.error('元数据搜索请求失败:', error);
    throw new Error(error.response?.data?.detail || error.message || '搜索失败');
  }
};

// 删除文档
export const deleteDocument = async (filename: string): Promise<any> => {
  const params = new URLSearchParams();
  params.append('filename', filename);
  
  return api.delete(`/document/delete?${params.toString()}`);
};

// 系统状态检查
export const getSystemStatus = async (): Promise<SystemStatus> => {
  return api.get('/system/elasticsearch');
};