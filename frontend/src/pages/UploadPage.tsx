import { useCallback, useEffect, useState } from 'react';
import type { FC, ReactNode } from 'react';
import {
  Upload,
  Button,
  Card,
  Table,
  Typography,
  Space,
  message,
  Progress,
  Badge,
  Tag,
  Tooltip,
  Popconfirm,
  Descriptions,
  Divider,
  Collapse,
  Spin,
  Modal,
  Popover,
} from 'antd';
import {
  InboxOutlined,
  DeleteOutlined,
  EyeOutlined,
  DownloadOutlined,
  ReloadOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  ExperimentOutlined,
  SyncOutlined,
  CloudUploadOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import { API_BASE_URL, deleteDocument, batchDeleteDocuments, getUploadedDocuments, getDocumentDetail, downloadDocument, getUploadQueueStatus, retryUpload } from '../services/api';
import MetadataEditModal from '../components/MetadataEditModal';
import ProgressStepper from '../components/ProgressStepper';
import type { ContractMetadata, UploadQueueStatus } from '../types';
import type { ColumnsType } from 'antd/es/table';
import type { UploadChangeParam } from 'antd/es/upload';
import type { UploadFile } from 'antd/es/upload/interface';
import { useAuth } from '../contexts/AuthContext';

const { Title, Text, Paragraph } = Typography;
const { Dragger } = Upload;
const { Panel } = Collapse;


interface DocumentRecord {
  contractKey: string;
  name: string;
  fileName?: string;
  uploadTime: string;
  parseStatus: 'success' | 'processing' | 'failed' | 'pending';
  status: string;
  statusDisplay?: string;
  metadataExtracted: boolean;
  metadataStatus?: string;
  pageCount: number;
  fileSize?: string;
  hasStructuredData: boolean;
  actions: string[];
  processedPages?: number;
  totalPages?: number;
  uploadId?: string;
  contractCode?: string;
  cirCode?: string;
  error?: string;
  message?: string;
}

type UploadDocumentRaw = Record<string, unknown>;

const STATUS_LABELS: Record<string, string> = {
  pending: '待解析',
  parsing: '正在转化为文本',
  parsing_images: '正在转化为图片',
  parsing_ocr: '正在OCR识别',
  vectorizing: '正在向量化',
  metadata_extracting: '正在提取元数据',
  completed: '解析成功',
  failed: '解析失败',
  failed_images: '图片转换失败',
  failed_ocr: 'OCR识别失败',
  failed_vector: '向量化失败',
  failed_metadata: '元数据提取失败',
};

const asString = (value: unknown): string | undefined => {
  return typeof value === 'string' && value.trim() !== '' ? value : undefined;
};

const asNumber = (value: unknown): number | undefined => {
  if (typeof value === 'number' && !Number.isNaN(value)) {
    return value;
  }
  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number(value);
    if (!Number.isNaN(parsed)) {
      return parsed;
    }
  }
  return undefined;
};

const asBoolean = (value: unknown): boolean | undefined => {
  if (typeof value === 'boolean') {
    return value;
  }
  if (typeof value === 'string') {
    if (value.toLowerCase() === 'true') {
      return true;
    }
    if (value.toLowerCase() === 'false') {
      return false;
    }
  }
  return undefined;
};

const pickString = (source: UploadDocumentRaw, keys: string[]): string | undefined => {
  for (const key of keys) {
    const candidate = asString(source[key]);
    if (candidate !== undefined) {
      return candidate;
    }
  }
  return undefined;
};

const pickNumber = (source: UploadDocumentRaw, keys: string[]): number | undefined => {
  for (const key of keys) {
    const candidate = asNumber(source[key]);
    if (candidate !== undefined) {
      return candidate;
    }
  }
  return undefined;
};

const pickBoolean = (source: UploadDocumentRaw, keys: string[], defaultValue = false): boolean => {
  for (const key of keys) {
    const candidate = asBoolean(source[key]);
    if (candidate !== undefined) {
      return candidate;
    }
  }
  return defaultValue;
};

const sanitizeTextValue = (value: unknown): string | null => {
  if (typeof value === 'string') {
    const trimmed = value.trim();
    return trimmed === '' ? null : trimmed;
  }
  return null;
};

const parseContractAmount = (value: unknown): number | null => {
  if (typeof value === 'number' && !Number.isNaN(value)) {
    return value;
  }
  if (typeof value === 'string') {
    const sanitized = value.replace(/[^\d.-]/g, '');
    if (sanitized.trim() === '') {
      return null;
    }
    const parsed = Number.parseFloat(sanitized);
    return Number.isNaN(parsed) ? null : parsed;
  }
  return null;
};

const normalizeContractMetadata = (raw: Record<string, unknown> | null | undefined, fileName: string): ContractMetadata => {
  const categoryLevel1Raw = sanitizeTextValue(raw?.['customer_category_level1'])
    ?? sanitizeTextValue(raw?.['customerCategoryLevel1'])
    ?? sanitizeTextValue(raw?.['category_level1'])
    ?? sanitizeTextValue(raw?.['categoryLevel1']);
  const categoryLevel2Raw = sanitizeTextValue(raw?.['customer_category_level2'])
    ?? sanitizeTextValue(raw?.['customerCategoryLevel2'])
    ?? sanitizeTextValue(raw?.['category_level2'])
    ?? sanitizeTextValue(raw?.['categoryLevel2']);
  const contractTypeRaw = sanitizeTextValue(raw?.['contract_type'])
    ?? sanitizeTextValue(raw?.['contractType'])
    ?? sanitizeTextValue(raw?.['customer_type'])
    ?? sanitizeTextValue(raw?.['customerType']);
  const projectDescription = sanitizeTextValue(raw?.['project_description'])
    ?? sanitizeTextValue(raw?.['projectDescription'])
    ?? sanitizeTextValue(raw?.['contract_content_summary'])
    ?? sanitizeTextValue(raw?.['contractContentSummary']);
  const contractAmountRaw = raw?.['contract_amount'] ?? raw?.['contractAmount'];
  const customerNameRaw = raw?.['customer_name']
    ?? raw?.['customerName']
    ?? raw?.['party_a']
    ?? raw?.['partyA'];
  const ourEntityRaw = raw?.['our_entity']
    ?? raw?.['ourEntity']
    ?? raw?.['party_b']
    ?? raw?.['partyB'];
  const positionsRaw = raw?.['positions'] ?? raw?.['position'];
  const personnelRaw = raw?.['personnel_list'] ?? raw?.['personnelList'];
  const signingDateRaw = sanitizeTextValue(raw?.['signing_date'])
    ?? sanitizeTextValue(raw?.['signingDate'])
    ?? sanitizeTextValue(raw?.['sign_date'])
    ?? sanitizeTextValue(raw?.['signDate']);
  const extractedAtRaw = raw?.['extracted_at'] ?? raw?.['extractedAt'];

  return {
    contract_name: fileName,
    customer_name: sanitizeTextValue(customerNameRaw),
    our_entity: sanitizeTextValue(ourEntityRaw),
    customer_category_level1: categoryLevel1Raw,
    customer_category_level2: categoryLevel2Raw,
    contract_type: contractTypeRaw,
    contract_amount: parseContractAmount(contractAmountRaw),
    signing_date: signingDateRaw,
    project_description: projectDescription,
    positions: sanitizeTextValue(positionsRaw),
    personnel_list: sanitizeTextValue(personnelRaw),
    extracted_at: sanitizeTextValue(extractedAtRaw) ?? '',
  };
};

const formatCustomerCategory = (level1?: string | null, level2?: string | null): string => {
  const parts = [level1, level2].filter((part): part is string => Boolean(part));
  return parts.length > 0 ? parts.join(' / ') : '未匹配';
};

const formatAmountDisplay = (amount?: number | null): string => {
  if (typeof amount === 'number' && !Number.isNaN(amount)) {
    return `¥${amount.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
  }
  return '-';
};

const formatDateTimeDisplay = (value?: string | null): string => {
  if (!value) {
    return '-';
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString();
};

const formatDateDisplay = (value?: string | null): string => {
  if (!value) {
    return '-';
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleDateString();
};

interface DocumentDetail {
  contract_name: string;
  dataType?: string;
  totalPages?: number;
  totalChars?: number;
  extractionStatus?: string;
  uploadTime?: string;
  fileSize?: string;
  metadataStatus?: string;
  metadata_status?: string;
  structuredData?: {
    signing_date?: string;
    customer_name?: string;
    our_entity?: string;
    party_a?: string;
    party_b?: string;
    customer_category_level1?: string;
    customer_category_level2?: string;
    contract_type?: string;
    contract_amount?: number;
    contract_content_summary?: string;
    positions?: string;
    personnel_list?: string;
  } | null;
  document_metadata?: Record<string, unknown> | null;
  pages?: Array<{
    pageId?: number;
    text?: string;
    charCount?: number;
  }>;
}

const UploadPage: FC = () => {
  const { token, logout } = useAuth();
  const [uploading, setUploading] = useState(false);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentMetadata, setCurrentMetadata] = useState<ContractMetadata | null>(null);
  const [metadataModalVisible, setMetadataModalVisible] = useState(false);

  // 详情视图相关状态
  const [selectedContractKey, setSelectedContractKey] = useState<string | null>(null);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [detailData, setDetailData] = useState<DocumentDetail | null>(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [deletePopoverKey, setDeletePopoverKey] = useState<string | null>(null);
  const [deleteLoadingKey, setDeleteLoadingKey] = useState<string | null>(null);
  const [downloadingKey, setDownloadingKey] = useState<string | null>(null);
  const [retryLoadingKey, setRetryLoadingKey] = useState<string | null>(null);

  // 批量选择状态
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [batchDeleteLoading, setBatchDeleteLoading] = useState(false);

  // 队列状态
  const [queueStatus, setQueueStatus] = useState<UploadQueueStatus | null>(null);

  // 获取文档列表
  const fetchDocuments = useCallback(async (silent = false) => {
    setLoading(true);
    try {
      const response = await getUploadedDocuments();
      const normalized: DocumentRecord[] = (response || [])
        .map((item) => {
          const doc = item as UploadDocumentRaw;
          const rawKey = pickString(doc, ['name', 'contract_name', 'file_name', 'fileName']);
          if (!rawKey) {
            return null;
          }

          const contractKey = rawKey.replace(/\.pdf$/i, '');
          const fileName = pickString(doc, ['file_name', 'fileName']) || (rawKey.toLowerCase().endsWith('.pdf') ? rawKey : `${contractKey}.pdf`);
          const displayName = pickString(doc, ['display_name', 'name_display']) || fileName || rawKey;

          const rawUploadTime = pickString(doc, ['uploadTime', 'upload_time', 'created_at']);
          let uploadTime = '未知';
          if (rawUploadTime) {
            const parsed = Date.parse(rawUploadTime);
            uploadTime = Number.isNaN(parsed) ? rawUploadTime : new Date(parsed).toLocaleString();
          }

          const rawStatusValue = pickString(doc, ['status', 'parseStatus', 'parse_status']);
          const normalizedStatus = (rawStatusValue || 'completed').toLowerCase().replace(/-/g, '_');
          let parseStatus: DocumentRecord['parseStatus'] = 'success';
          if (normalizedStatus === 'failed' || normalizedStatus.includes('fail')) {
            parseStatus = 'failed';
          } else if (normalizedStatus === 'pending') {
            parseStatus = 'pending';
          } else if (normalizedStatus === 'completed') {
            parseStatus = 'success';
          } else {
            parseStatus = 'processing';
          }

          const metadataStatusRaw = pickString(doc, ['metadata_status', 'metadataStatus']);
          const metadataStatus = metadataStatusRaw ? metadataStatusRaw.toLowerCase() : undefined;
          const metadataExtracted = pickBoolean(doc, ['has_metadata', 'metadataExtracted', 'metadata_extracted'], false)
            || (metadataStatus !== undefined && ['completed', 'extracted', 'success'].includes(metadataStatus));

          const totalPages = pickNumber(doc, ['total_pages', 'page_count', 'pages']);
          const processedPages = pickNumber(doc, ['processed_pages']);
          const pageCount = totalPages ?? pickNumber(doc, ['pageCount', 'chunks_count']) ?? 0;
          const fileSize = pickString(doc, ['file_size', 'fileSize']);
          const hasStructuredData = pickBoolean(doc, ['hasStructuredData', 'has_structured_data'], metadataExtracted);
          const uploadId = pickString(doc, ['upload_id', 'uploadId']);
          const statusDisplay = pickString(doc, ['status_display', 'statusLabel'])
            || STATUS_LABELS[normalizedStatus as keyof typeof STATUS_LABELS]
            || '解析成功';

          const actionsValue = doc['actions'];
          const contractCode = pickString(doc, ['contract_code', 'contractCode']);
          const cirCode = pickString(doc, ['cir_code', 'cirCode']);

          const error = pickString(doc, ['error']);
          const message = pickString(doc, ['message']);

          return {
            contractKey,
            name: displayName,
            fileName,
            uploadTime,
            parseStatus,
            status: normalizedStatus,
            statusDisplay,
            metadataExtracted,
            metadataStatus,
            pageCount,
            fileSize: fileSize || '-',
            hasStructuredData,
            actions: Array.isArray(actionsValue) ? (actionsValue as string[]) : [],
            processedPages: processedPages !== undefined ? processedPages : undefined,
            totalPages: totalPages !== undefined ? totalPages : undefined,
            uploadId,
            contractCode,
            cirCode,
            error,
            message,
          };
        })
        .filter(Boolean) as DocumentRecord[];

      setDocuments(normalized);

      // 并行获取队列状态
      try {
        const status = await getUploadQueueStatus();
        setQueueStatus(status);
      } catch {
        // 队列状态获取失败不影响主流程
      }
    } catch (error) {
      console.error('获取文档列表失败:', error);
      if (!silent) {
        message.error(error instanceof Error ? error.message : '获取文档列表失败');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  const handleRetry = async (record: DocumentRecord) => {
    if (!record.uploadId) {
      message.error('无法重试：缺少任务ID');
      return;
    }
    setRetryLoadingKey(record.contractKey);
    try {
      await retryUpload(record.uploadId);
      message.success('任务已提交重试');
      await fetchDocuments();
    } catch (error) {
      console.error('重试失败:', error);
      message.error(error instanceof Error ? error.message : '重试任务失败');
    } finally {
      setRetryLoadingKey(null);
    }
  };

  const showDetail = async (record: DocumentRecord) => {
    setSelectedContractKey(record.contractKey);
    setDetailModalVisible(true);
    setDetailLoading(true);
    setDetailError(null);
    setDetailData(null);
    try {
      const resp = await getDocumentDetail(record.contractKey);
      const detail: DocumentDetail | null = (resp && typeof resp === 'object')
        ? ((resp as { data?: DocumentDetail | null }).data ?? (resp as DocumentDetail | null))
        : null;
      if (!detail) {
        throw new Error('未获取到文档详情');
      }
      setDetailData(detail);
    } catch (err) {
      console.error('获取文档详情失败:', err);
      const fallback = err instanceof Error ? err.message : '获取文档详情失败';
      setDetailError(fallback);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCloseDetailModal = () => {
    setDetailModalVisible(false);
    setSelectedContractKey(null);
    setDetailLoading(false);
    setDetailError(null);
    setDetailData(null);
  };

  // 删除文档
  const handleDelete = async (record: DocumentRecord) => {
    const contractKey = record.contractKey;
    const deleteIdentifier = record.fileName ?? `${contractKey}.pdf`;
    setDeleteLoadingKey(contractKey);
    try {
      await deleteDocument(deleteIdentifier);
      message.success('文档删除成功');
      setDeletePopoverKey((current) => (current === contractKey ? null : current));
      if (selectedContractKey === contractKey) {
        setSelectedContractKey(null);
        setDetailData(null);
        setDetailError(null);
      }
      setDocuments((prev) => prev.filter((item) => item.contractKey !== contractKey));
      await fetchDocuments();
    } catch (error) {
      console.error('删除文档失败:', error);
      message.error(error instanceof Error ? error.message : '删除失败');
    } finally {
      setDeleteLoadingKey((current) => (current === contractKey ? null : current));
    }
  };

  // 批量删除文档
  const handleBatchDelete = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要删除的合同');
      return;
    }

    setBatchDeleteLoading(true);
    try {
      // 获取选中的文件名列表
      const filenames = selectedRowKeys.map((key) => {
        const doc = documents.find((d) => d.contractKey === key);
        return doc?.fileName ?? `${key}.pdf`;
      });

      const result = await batchDeleteDocuments(filenames);

      // 显示结果消息
      if (result.success_count > 0) {
        message.success(`成功删除 ${result.success_count} 个合同`);
      }
      if (result.failed_count > 0) {
        const failedNames = result.failed.map((f) => f.filename).join(', ');
        message.warning(`${result.failed_count} 个合同删除失败: ${failedNames}`);
      }

      // 清空选择
      setSelectedRowKeys([]);

      // 刷新列表
      await fetchDocuments();
    } catch (error) {
      console.error('批量删除失败:', error);
      message.error(error instanceof Error ? error.message : '批量删除失败');
    } finally {
      setBatchDeleteLoading(false);
    }
  };

  // 查看元数据
  const handleViewMetadata = async (contractKey: string) => {
    try {
      const fileName = `${contractKey}.pdf`;

      // 找到对应的文档记录，获取准确的文件名信息
      const documentRecord = documents.find(d => d.contractKey === contractKey);
      const actualFileName = documentRecord?.fileName || fileName;

      // 先尝试获取文档详情，看是否已有元数据
      const detailResponse = await getDocumentDetail(contractKey);
      const detail = detailResponse?.data ?? detailResponse;
      const rawMetadata = detail?.document_metadata ?? detail?.structuredData ?? detail?.structured_data;
      const metadataObject = (rawMetadata && typeof rawMetadata === 'object') ? rawMetadata as Record<string, unknown> : null;
      const normalizedMetadata = normalizeContractMetadata(metadataObject, actualFileName);

      // 确保元数据包含正确的contractKey信息，用于onSaved回调匹配
      if (normalizedMetadata) {
        normalizedMetadata.contractKey = contractKey;
        normalizedMetadata.fileName = actualFileName;
      }

      setCurrentMetadata(normalizedMetadata);
      setMetadataModalVisible(true);
    } catch (error) {
      console.error('获取元数据失败:', error);
      message.error('获取元数据失败');
    }
  };

  const handleDownloadDocument = async (record: DocumentRecord) => {
    const rawName = record.fileName ?? `${record.contractKey}.pdf`;
    const fileName = rawName.toLowerCase().endsWith('.pdf') ? rawName : `${rawName}.pdf`;

    setDownloadingKey(record.contractKey);
    try {
      const blob = await downloadDocument(fileName);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      message.success('文件下载成功');
    } catch (error) {
      console.error('下载文档失败:', error);
      message.error('文件下载失败，请稍后重试');
    } finally {
      setDownloadingKey((current) => (current === record.contractKey ? null : current));
    }
  };

  // 关闭元数据弹窗
  const handleCloseMetadataModal = () => {
    setMetadataModalVisible(false);
    setCurrentMetadata(null);
  };

  // 上传配置
  const uploadProps = {
    name: 'files',
    action: `${API_BASE_URL}/document/add`,
    accept: '.pdf',
    multiple: true,
    showUploadList: false,
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    beforeUpload: (file: File) => {
      const isPDF = file.type === 'application/pdf';
      if (!isPDF) {
        message.error('只能上传PDF文件!');
        return Upload.LIST_IGNORE;
      }
      const isLt50M = file.size / 1024 / 1024 < 50;
      if (!isLt50M) {
        message.error('文件大小不能超过50MB!');
        return Upload.LIST_IGNORE;
      }
      if (!token) {
        message.error('登录状态已失效，请重新登录');
        logout();
        return Upload.LIST_IGNORE;
      }
      return true;
    },
    onChange: (info: UploadChangeParam<UploadFile<unknown>>) => {
      const { status } = info.file;

      if (status === 'uploading') {
        setUploading(true);
        return;
      }

      if (status === 'done') {
        const hasUploading = info.fileList.some((item) => item.status === 'uploading');

        // 检查响应是否包含重复文件信息
        const response = info.file.response as {
          code?: number;
          message?: string;
          data?: {
            success?: Array<{ pdf_name: string }>;
            failed?: Array<{ pdf_name: string; error: string }>;
            rejected?: Array<{
              pdf_name: string;
              reason: string;
              reason_display: string;
              existing_file: string;
              message: string;
            }>;
          };
        } | undefined;

        const rejectedFiles = response?.data?.rejected || [];
        const successFiles = response?.data?.success || [];

        // 显示成功消息
        if (successFiles.length > 0) {
          message.success(`已加入解析队列 ${successFiles.length} 个文件`);
        }

        // 为每个被拒绝的重复文件显示警告
        rejectedFiles.forEach((rejected) => {
          const reasonText = rejected.reason_display || '重复';
          const existingFile = rejected.existing_file ? ` (与 ${rejected.existing_file} 重复)` : '';
          message.warning(`${rejected.pdf_name}: ${reasonText}${existingFile}`);
        });

        setUploading(hasUploading);

        if (!hasUploading) {
          fetchDocuments();
        }
        return;
      }

      if (status === 'error') {
        const hasUploading = info.fileList.some((item) => item.status === 'uploading');
        const responseDetail = (info.file.response as { detail?: string; message?: string } | undefined)?.detail
          || (info.file.response as { message?: string } | undefined)?.message;
        const errorMessage = responseDetail || `${info.file.name} 上传失败`;
        message.error(errorMessage);
        const httpStatus = (info.file.error as { status?: number } | undefined)?.status;
        if (httpStatus === 401 || httpStatus === 403) {
          logout();
        }
        setUploading(hasUploading);
      }
    },
  };

  // 状态标签渲染
  const renderStatus = (record: DocumentRecord) => {
    const normalizedStatus = (record.status || 'completed').toLowerCase();
    const metadataStatus = (record.metadataStatus || '').toLowerCase();

    let color = 'default';
    let icon: ReactNode = <ClockCircleOutlined />;
    let text = '未知状态';
    let spin = false;

    // 基础状态判断
    if (normalizedStatus === 'failed') {
      color = 'error';
      icon = <ExclamationCircleOutlined />;
      text = STATUS_LABELS.failed || '解析失败';
    } else if (normalizedStatus === 'pending') {
      color = 'default';
      icon = <ClockCircleOutlined />;
      text = STATUS_LABELS.pending || '待解析';
    } else if (['parsing', 'processing'].includes(normalizedStatus)) {
      color = 'processing';
      icon = <SyncOutlined spin />;
      text = STATUS_LABELS.parsing || '正在解析';
      text = STATUS_LABELS.parsing || '正在解析';
      spin = true;
    } else if (normalizedStatus === 'parsing_images') {
      color = 'processing';
      icon = <SyncOutlined spin />;
      text = '正在转图片';
      spin = true;
    } else if (normalizedStatus === 'parsing_ocr') {
      color = 'processing';
      icon = <SyncOutlined spin />;
      text = '正在识别文本';
      spin = true;
    } else if (normalizedStatus === 'vectorizing') {
      color = 'processing';
      icon = <CloudUploadOutlined />;
      text = STATUS_LABELS.vectorizing || '正在向量化';
    } else if (normalizedStatus === 'metadata_extracting' || metadataStatus === 'metadata_extracting' || metadataStatus === 'extracting') {
      color = 'processing';
      color = 'processing';
      icon = <ExperimentOutlined spin={true} />;
      text = STATUS_LABELS.metadata_extracting || '正在提取元数据';
      // Given the previous code used <SyncOutlined spin />, distinct icons are good.
      // Let's stick to simple composition.
      icon = <ExperimentOutlined />;
      text = STATUS_LABELS.metadata_extracting || '正在提取元数据';
      // If we want it to look active, color processing is usually enough.
    } else if (normalizedStatus === 'completed') {
      if (metadataStatus === 'failed') {
        color = 'warning';
        icon = <ExclamationCircleOutlined />;
        text = '元数据提取失败';
      } else if (['extracted', 'success', 'completed'].includes(metadataStatus) || record.metadataExtracted) {
        color = 'success';
        icon = <CheckCircleOutlined />;
        text = '已完成';
      } else {
        // 默认完成
        color = 'success';
        icon = <CheckCircleOutlined />;
        text = '已完成';
      }
    } else {
      // 其他情况
      text = record.statusDisplay || normalizedStatus;
    }

    let progressText = '';
    if (normalizedStatus === 'vectorizing' && record.totalPages && record.totalPages > 0) {
      const processed = record.processedPages ?? 0;
      progressText = ` (${processed}/${record.totalPages}页)`;
    }

    return (
      <Popover
        title={<Space><FileTextOutlined /> 解析进度详情</Space>}
        content={
          <div style={{ minWidth: 500, padding: '12px 0' }}>
            <ProgressStepper
              status={record.status}
              errorMessage={record.error || record.message}
              size="small"
            />
            {record.message && !record.error && (
              <div style={{ marginTop: 8, color: '#1890ff' }}>
                <InfoCircleOutlined /> {record.message}
              </div>
            )}
          </div>
        }
        destroyTooltipOnHide
      >
        <Tag color={color} icon={spin ? <SyncOutlined spin /> : icon} style={{ cursor: 'pointer' }}>
          {text}
          {progressText}
        </Tag>
      </Popover>
    );
  };



  // Click-to-copy component for codes
  const ClickToCopy: FC<{ text: string }> = ({ text }) => {
    const [hover, setHover] = useState(false);

    const handleCopy = (e: React.MouseEvent) => {
      e.stopPropagation();
      navigator.clipboard.writeText(text);
      message.success('已复制到剪贴板');
    };

    return (
      <div
        onClick={handleCopy}
        onMouseEnter={() => setHover(true)}
        onMouseLeave={() => setHover(false)}
        style={{
          cursor: 'pointer',
          padding: '2px 6px',
          borderRadius: '4px',
          border: `1px solid ${hover ? '#1677ff' : 'transparent'}`,
          backgroundColor: hover ? '#f0f5ff' : 'transparent',
          transition: 'all 0.2s',
          display: 'inline-block',
          maxWidth: '100%',
          wordBreak: 'break-all'
        }}
        title="点击复制"
      >
        {text}
      </div>
    );
  };

  // 表格列定义
  const columns: ColumnsType<DocumentRecord> = [
    {
      title: '合同名称',
      dataIndex: 'name',
      key: 'name',
      width: undefined, // Allow flex width
      minWidth: 200, // Ensure minimum readable width on small screens
      render: (text: string) => (
        <Space align="start">
          <FileTextOutlined style={{ marginTop: '4px' }} />
          <Text strong style={{ wordBreak: 'break-all', whiteSpace: 'normal' }}>{text}</Text>
        </Space>
      ),
    },
    {
      title: '合同编码',
      dataIndex: 'contractCode',
      key: 'contractCode',
      width: 130,
      render: (code: string | undefined) => (
        code ? <ClickToCopy text={code} /> : <Text type="secondary">-</Text>
      ),
    },
    {
      title: '合同注册编码',
      dataIndex: 'cirCode',
      key: 'cirCode',
      width: 140,
      render: (code: string | undefined) => (
        code ? <ClickToCopy text={code} /> : <Text type="secondary">-</Text>
      ),
    },
    {
      title: '上传时间',
      dataIndex: 'uploadTime',
      key: 'uploadTime',
      width: 140,
      render: (text: string) => <Text type="secondary">{text}</Text>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 130,
      render: (_: string, record) => renderStatus(record),
    },
    {
      title: '页数',
      dataIndex: 'pageCount',
      key: 'pageCount',
      width: 80,
      render: (count: number) => <Badge count={count} color="blue" />,
    },
    {
      title: '文件大小',
      dataIndex: 'fileSize',
      key: 'fileSize',
      width: 100,
      render: (size: string) => <Text type="secondary">{size}</Text>,
    },
    {
      title: '操作',
      key: 'actions',
      width: 140,
      render: (_, record) => {
        // 判断是否允许重试：失败状态允许重试
        const allowRetry = record.status.startsWith('failed') || record.status === 'failed';

        return (
          <Space size="small">
            {allowRetry && (
              <Tooltip title="重试任务" mouseEnterDelay={0.5} getPopupContainer={() => document.body}>
                <Button
                  type="text"
                  icon={<ReloadOutlined />}
                  loading={retryLoadingKey === record.contractKey}
                  onClick={() => handleRetry(record)}
                  style={{ color: '#faad14' }}
                />
              </Tooltip>
            )}

            <Tooltip title="查看详情" mouseEnterDelay={0.5} mouseLeaveDelay={0.1} destroyOnHidden trigger={["hover"]} getPopupContainer={() => document.body}>
              <Button
                type="text"
                icon={<EyeOutlined />}
                onClick={() => showDetail(record)}
              />
            </Tooltip>
            <Tooltip title="查看元数据" mouseEnterDelay={0.5} mouseLeaveDelay={0.1} destroyOnHidden trigger={["hover"]} getPopupContainer={() => document.body}>
              <Button
                type="text"
                icon={<ExperimentOutlined />}
                onClick={() => handleViewMetadata(record.contractKey)}
              />
            </Tooltip>
            <Tooltip title="下载文档" mouseEnterDelay={0.5} mouseLeaveDelay={0.1} destroyOnHidden trigger={["hover"]} getPopupContainer={() => document.body}>
              <Button
                type="text"
                icon={<DownloadOutlined />}
                loading={downloadingKey === record.contractKey}
                onClick={() => handleDownloadDocument(record)}
              />
            </Tooltip>
            <Popconfirm
              title="确定删除此文档吗？"
              okText="确定"
              cancelText="取消"
              placement="topRight"
              open={deletePopoverKey === record.contractKey}
              okButtonProps={{ loading: deleteLoadingKey === record.contractKey }}
              onOpenChange={(visible) => {
                setDeletePopoverKey(visible ? record.contractKey : null);
              }}
              onConfirm={() => handleDelete(record)}
            >
              <Button
                type="text"
                icon={<DeleteOutlined />}
                danger
                title="删除文档"
              />
            </Popconfirm>
          </Space>
        );
      },
    },
  ];


  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  useEffect(() => {
    if (!documents.length) {
      return undefined;
    }
    const hasInProgress = documents.some((doc) => ['pending', 'parsing', 'processing', 'vectorizing', 'metadata_extracting'].includes(doc.status));
    if (!hasInProgress) {
      return undefined;
    }
    const timer = window.setInterval(() => {
      fetchDocuments(true).catch(() => {
        // ignore polling errors
      });
    }, 5000);
    return () => window.clearInterval(timer);
  }, [documents, fetchDocuments]);

  const detailMetadataRaw = detailData && typeof detailData === 'object'
    ? (
      detailData.document_metadata && typeof detailData.document_metadata === 'object'
        ? detailData.document_metadata
        : detailData.structuredData ?? (detailData as unknown as Record<string, unknown>)?.['structured_data']
    )
    : null;

  const detailMetadataSource = detailMetadataRaw && typeof detailMetadataRaw === 'object'
    ? detailMetadataRaw as Record<string, unknown>
    : null;

  const detailMetadata = detailMetadataSource
    ? normalizeContractMetadata(detailMetadataSource, detailData?.contract_name || `${selectedContractKey ?? ''}.pdf`)
    : null;

  const detailMetadataStatus = detailData?.metadataStatus?.toLowerCase()
    ?? detailData?.metadata_status?.toLowerCase();

  const detailMetadataReady = Boolean(detailMetadataSource && (
    detailMetadataStatus === 'completed' || detailMetadataStatus === 'extracted'
    || Object.entries(detailMetadataSource).some(([key, value]) => (
      key !== 'extraction_status' && key !== 'extracted_at'
        ? value !== null && value !== undefined && value !== ''
        : false
    ))
  ));

  return (
    <div style={{ padding: '24px' }}>
      <Modal
        title="合同详情"
        open={detailModalVisible}
        onCancel={handleCloseDetailModal}
        footer={null}
        width={960}
        destroyOnHidden
        styles={{ body: { maxHeight: '70vh', overflowY: 'auto' } }}
      >
        {detailLoading ? (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 120 }}>
            <Spin tip="加载合同详情中..." spinning>
              <div style={{ minHeight: 24 }} />
            </Spin>
          </div>
        ) : detailError ? (
          <Text type="danger">{detailError}</Text>
        ) : detailData ? (
          <div>
            {/* 页面顶部：完整显示合同名称 */}
            <Title level={3} style={{ marginTop: 0, marginBottom: 12 }}>
              {detailData.contract_name}
            </Title>

            {/* 中部 1：合同所有元数据信息 */}
            <Divider orientation="left">合同元数据信息</Divider>
            {detailMetadataReady && detailMetadata ? (
              <Descriptions bordered size="small" column={2}>
                <Descriptions.Item label="客户名称">
                  {detailMetadata.customer_name ?? detailMetadata.party_a ?? '-'}
                </Descriptions.Item>
                <Descriptions.Item label="我方实体">
                  {detailMetadata.our_entity ?? detailMetadata.party_b ?? '-'}
                </Descriptions.Item>
                <Descriptions.Item label="客户分类">
                  {formatCustomerCategory(
                    detailMetadata.customer_category_level1 ?? detailMetadata.contract_type,
                    detailMetadata.customer_category_level2 ?? undefined
                  )}
                </Descriptions.Item>
                <Descriptions.Item label="合同金额">{formatAmountDisplay(detailMetadata.contract_amount)}</Descriptions.Item>
                <Descriptions.Item label="签订日期">{formatDateDisplay(detailMetadata.signing_date)}</Descriptions.Item>
                <Descriptions.Item label="岗位信息" span={2}>{detailMetadata.positions ?? '-'}</Descriptions.Item>
                <Descriptions.Item label="人员清单" span={2}>{detailMetadata.personnel_list ?? '-'}</Descriptions.Item>
                <Descriptions.Item label="合同内容" span={2}>
                  <Paragraph style={{ marginBottom: 0 }}>{detailMetadata.project_description ?? '-'}</Paragraph>
                </Descriptions.Item>
                <Descriptions.Item label="提取时间">{formatDateTimeDisplay(detailMetadata.extracted_at)}</Descriptions.Item>
              </Descriptions>
            ) : (
              <Text type="secondary">暂无已保存的元数据信息</Text>
            )}

            {/* 中部 2：合同总页数、上传时间 */}
            <Divider orientation="left">文档信息</Divider>
            <Descriptions size="small" column={3}>
              <Descriptions.Item label="总页数">{detailData.totalPages ?? '-'}</Descriptions.Item>
              <Descriptions.Item label="上传时间">{detailData.uploadTime ?? '-'}</Descriptions.Item>
              <Descriptions.Item label="文件大小">{detailData.fileSize ?? '-'}</Descriptions.Item>
            </Descriptions>

            {/* 中部 3：OCR 文档块文本内容（按页）*/}
            <Divider orientation="left">OCR 文本（按页）</Divider>
            {Array.isArray(detailData.pages) && detailData.pages.length > 0 ? (
              <Collapse accordion>
                {detailData.pages.map((p, idx) => (
                  <Panel header={`第 ${p.pageId ?? idx + 1} 页`} key={String(p.pageId ?? idx)}>
                    <Paragraph style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', background: '#fafafa', padding: 12, borderRadius: 6, border: '1px solid #f0f0f0' }}>
                      {p.text || '（无文本）'}
                    </Paragraph>
                  </Panel>
                ))}
              </Collapse>
            ) : (
              <Text type="secondary">暂无OCR文本内容</Text>
            )}
          </div>
        ) : (
          <Text type="secondary">未选择合同</Text>
        )}
      </Modal>

      {/* 上传区域 */}
      <Card style={{ marginBottom: '24px' }}>
        <Title level={4}>📁 上传合同文档</Title>
        <Dragger {...uploadProps} style={{ marginBottom: '16px' }}>
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            支持选择多个PDF文件，单个文件大小不超过50MB。上传后将自动进行LLM结构化提取。
          </p>
        </Dragger>
        {uploading && <Progress percent={50} status="active" />}

        {/* 上传后显示排队提示 */}
        {documents.some(d => d.parseStatus === 'pending' || d.parseStatus === 'processing') && (
          <div style={{ marginTop: 12, padding: '8px 12px', background: '#e6f7ff', borderRadius: 6, border: '1px solid #91d5ff' }}>
            <Text type="secondary">
              <SyncOutlined spin style={{ marginRight: 8 }} />
              您的文件已加入处理队列，将按顺序处理
            </Text>
          </div>
        )}
      </Card>

      {/* 队列状态展示 */}
      {queueStatus && (queueStatus.pending_count > 0 || queueStatus.processing_count > 0 || queueStatus.memory_is_low) && (
        <Card style={{ marginBottom: '24px' }} size="small">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
            <Space size="large">
              <Tooltip title="等待处理的任务">
                <span>
                  <ClockCircleOutlined style={{ marginRight: 4 }} />
                  待处理: <Text strong>{queueStatus.pending_count}</Text>
                </span>
              </Tooltip>
              <Tooltip title="正在处理的任务">
                <span>
                  <SyncOutlined spin={queueStatus.processing_count > 0} style={{ marginRight: 4 }} />
                  处理中: <Text strong>{queueStatus.processing_count}</Text> / {queueStatus.max_concurrent}
                </span>
              </Tooltip>
              <Tooltip title="今日已完成">
                <span>
                  <CheckCircleOutlined style={{ marginRight: 4, color: '#52c41a' }} />
                  今日完成: <Text type="success">{queueStatus.completed_today}</Text>
                </span>
              </Tooltip>
              {queueStatus.failed_today > 0 && (
                <Tooltip title="今日失败">
                  <span>
                    <ExclamationCircleOutlined style={{ marginRight: 4, color: '#ff4d4f' }} />
                    失败: <Text type="danger">{queueStatus.failed_today}</Text>
                  </span>
                </Tooltip>
              )}
            </Space>

            <Space>
              <Tooltip title={`总内存: ${queueStatus.memory_total_mb}MB, 可用: ${queueStatus.memory_available_mb}MB`}>
                <span>
                  内存:
                  <Progress
                    percent={queueStatus.memory_percent_used}
                    size="small"
                    style={{ width: 100, marginLeft: 8 }}
                    status={queueStatus.memory_is_low ? 'exception' : 'normal'}
                    format={(pct) => `${pct}%`}
                  />
                </span>
              </Tooltip>
              {queueStatus.memory_is_low && (
                <Tag color="error" icon={<ExclamationCircleOutlined />}>
                  内存不足
                </Tag>
              )}
            </Space>
          </div>
        </Card>
      )}

      {/* 文档列表 */}
      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <Space>
            <Title level={4} style={{ margin: 0 }}>📋 合同列表</Title>
            {selectedRowKeys.length > 0 && (
              <Text type="secondary">
                已选择 {selectedRowKeys.length} 项
              </Text>
            )}
          </Space>
          <Space>
            {selectedRowKeys.length > 0 && (
              <Popconfirm
                title="确定批量删除选中的合同吗？"
                description={`即将删除 ${selectedRowKeys.length} 个合同，此操作不可撤销。`}
                okText="确定删除"
                cancelText="取消"
                okButtonProps={{ danger: true, loading: batchDeleteLoading }}
                onConfirm={handleBatchDelete}
              >
                <Button
                  danger
                  icon={<DeleteOutlined />}
                  loading={batchDeleteLoading}
                >
                  批量删除
                </Button>
              </Popconfirm>
            )}
            <Button
              icon={<ReloadOutlined />}
              onClick={() => {
                void fetchDocuments();
              }}
              loading={loading}
            >
              刷新
            </Button>
          </Space>
        </div>

        <Table
          columns={columns}
          dataSource={documents}
          rowKey="contractKey"
          loading={loading}
          scroll={{ x: 1100 }}
          rowSelection={{
            selectedRowKeys,
            onChange: (keys) => setSelectedRowKeys(keys),
            preserveSelectedRowKeys: true,
          }}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 个文档`,
          }}
        />
      </Card>

      {/* 元数据编辑弹窗 */}
      <MetadataEditModal
        visible={metadataModalVisible}
        initialMetadata={currentMetadata}
        filename={currentMetadata?.contract_name || ''}
        onCancel={handleCloseMetadataModal}
        onSaved={(m) => {
          // 立即更新对应行的提取状态，避免按钮不消失
          if (m) {
            setDocuments((prev) => prev.map((d) => {
              // 优先使用contractKey进行精确匹配
              if (m.contractKey && d.contractKey === m.contractKey) {
                return { ...d, metadataExtracted: true, metadataStatus: 'extracted' };
              }

              // 备用匹配方式：通过文件名匹配
              if (m.fileName && (d.fileName === m.fileName || d.contractKey === m.fileName.replace(/\.pdf$/i, ''))) {
                return { ...d, metadataExtracted: true, metadataStatus: 'extracted' };
              }

              // 最后尝试通过contract_name匹配
              if (m.contract_name) {
                const isMatch =
                  d.fileName === m.contract_name ||
                  d.name === m.contract_name ||
                  d.contractKey === m.contract_name.replace(/\.pdf$/i, '');

                if (isMatch) {
                  return { ...d, metadataExtracted: true, metadataStatus: 'extracted' };
                }
              }

              return d;
            }));
          }
          // 再拉一次后端，确保状态一致
          fetchDocuments();
        }}
      />
    </div>
  );
};

export default UploadPage;
