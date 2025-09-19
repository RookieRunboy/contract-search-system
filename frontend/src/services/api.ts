import axios from 'axios';
import type { ContractSearchResult, DocumentChunk } from '../types';

export const API_BASE_URL = import.meta.env.DEV ? '/api' : '';

// 创建 axios 实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60秒超时
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    // 统一向上抛出，由调用处/页面统一处理，避免重复打印日志
    return Promise.reject(error);
  }
);

// 文档搜索接口
interface RawSearchChunk {
  contract_name?: string;
  contractName?: string;
  score?: number;
  page_id?: number;
  pageId?: number;
  page_num?: number;
  pageNum?: number;
  text?: string;
  content?: string;
  highlights?: Record<string, unknown>;
  [key: string]: unknown;
}

const toNumber = (value: unknown, defaultValue = 0): number => {
  if (typeof value === 'number' && !Number.isNaN(value)) {
    return value;
  }

  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number(value);
    if (!Number.isNaN(parsed)) {
      return parsed;
    }
  }

  return defaultValue;
};

const toStringValue = (value: unknown): string | undefined => {
  return typeof value === 'string' && value.trim() !== '' ? value : undefined;
};

const normalizeSearchList = (rawList: unknown): ContractSearchResult[] => {
  if (!Array.isArray(rawList)) {
    return [];
  }

  const firstItem = rawList[0] as RawSearchChunk | undefined;

  if (firstItem && Array.isArray((firstItem as any).chunks)) {
    return rawList.map((item) => {
      const contractItem = item as RawSearchChunk & { chunks: RawSearchChunk[] };
      const contractName = toStringValue(contractItem.contract_name) ?? toStringValue(contractItem.contractName);
      return {
        contract_name: contractName ?? '未知合同',
        score: toNumber(contractItem.score),
        chunks: Array.isArray(contractItem.chunks)
          ? contractItem.chunks.map((chunk) => ({
            score: toNumber(chunk.score),
            page_id: toNumber(chunk.page_id ?? chunk.pageId ?? chunk.page_num ?? chunk.pageNum, 0),
            text: toStringValue(chunk.text ?? chunk.content) ?? '',
            highlights: (chunk.highlights && typeof chunk.highlights === 'object') ? (chunk.highlights as Record<string, any>) : {},
            })) as DocumentChunk[]
          : [],
      };
    });
  }

  const grouped = new Map<string, ContractSearchResult>();

  rawList.forEach((item) => {
    const record = item as RawSearchChunk;
    const contractName = toStringValue(record.contract_name) ?? toStringValue(record.contractName);
    if (!contractName) {
      return;
    }

    const chunk: DocumentChunk = {
      score: toNumber(record.score),
      page_id: toNumber(record.page_id ?? record.pageId ?? record.page_num ?? record.pageNum, 0),
      text: toStringValue(record.text ?? record.content) ?? '',
      highlights: (record.highlights && typeof record.highlights === 'object') ? (record.highlights as Record<string, any>) : {},
    };

    if (!grouped.has(contractName)) {
      grouped.set(contractName, {
        contract_name: contractName,
        score: chunk.score,
        chunks: [chunk],
      });
      return;
    }

    const existing = grouped.get(contractName)!;
    existing.score = Math.max(existing.score, chunk.score);
    existing.chunks.push(chunk);
  });

  return Array.from(grouped.values()).sort((a, b) => b.score - a.score);
};

export const searchDocuments = async (query: string, topK: number = 5): Promise<ContractSearchResult[]> => {
  // 改为 GET，并通过 query 参数传递
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
};

// 文档上传接口
export const uploadDocument = async (file: File, onProgress?: (progress: number) => void): Promise<any> => {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const result = await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const progress = progressEvent.loaded / progressEvent.total;
          onProgress(progress);
        }
      },
    });

    // 拦截器已解包，直接返回结果对象
    return result;
  } catch (error: any) {
    // 避免重复日志，直接抛出错误给调用方处理
    throw new Error(error.response?.data?.detail || error.message || '上传失败');
  }
};

// 获取已上传的文档列表（返回数组）
export const getUploadedDocuments = async (): Promise<any[]> => {
  try {
    const result: any = await api.get('/documents');
    // 兼容多种返回结构
    if (Array.isArray(result)) return result;
    if (Array.isArray(result?.data)) return result.data;
    if (Array.isArray(result?.results)) return result.results;
    return [];
  } catch (error: any) {
    // 避免重复日志，直接抛出错误给调用方处理
    throw new Error(error.response?.data?.detail || error.message || '获取文档列表失败');
  }
};

// 删除指定文档
export const deleteDocument = async (documentName: string): Promise<any> => {
  try {
    const result = await api.delete(`/documents/${encodeURIComponent(documentName)}`);
    return result;
  } catch (error: any) {
    // 避免重复日志，直接抛出错误给调用方处理
    throw new Error(error.response?.data?.detail || error.message || '删除文档失败');
  }
};

// 清空所有文档
export const clearAllDocuments = async (): Promise<any> => {
  try {
    const result = await api.delete('/clear-index');
    return result;
  } catch (error: any) {
    // 避免重复日志，直接抛出错误给调用方处理
    throw new Error(error.response?.data?.detail || error.message || '清空文档失败');
  }
};

// 下载文档
export const downloadDocument = async (documentName: string): Promise<Blob> => {
  try {
    // 直接使用axios而不是api实例，避免响应拦截器破坏Blob对象
    const response = await axios.get(`${API_BASE_URL}/document/download/${encodeURIComponent(documentName)}`, {
      responseType: 'blob',
      timeout: 60000
    });
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '文件下载失败');
  }
};

export default api;