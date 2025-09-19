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
export const searchDocuments = async (
  query: string,
  topK: number = 5
): Promise<SearchResponse> => {
  const params = new URLSearchParams();
  params.append('query', query);
  params.append('top_k', topK.toString());
  
  return api.get(`/document/search?${params.toString()}`);
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