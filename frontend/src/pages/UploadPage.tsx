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
} from '@ant-design/icons';
import { API_BASE_URL, deleteDocument, getUploadedDocuments, getDocumentDetail, downloadDocument } from '../services/api';
import MetadataEditModal from '../components/MetadataEditModal';
import type { ContractMetadata } from '../types';
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
}

type UploadDocumentRaw = Record<string, unknown>;

const STATUS_LABELS: Record<string, string> = {
  pending: '待解析',
  parsing: '正在转化为文本',
  vectorizing: '正在向量化',
  metadata_extracting: '正在提取元数据',
  completed: '解析成功',
  failed: '解析失败',
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
          };
        })
        .filter(Boolean) as DocumentRecord[];

      setDocuments(normalized);
    } catch (error) {
      console.error('获取文档列表失败:', error);
      if (!silent) {
        message.error(error instanceof Error ? error.message : '获取文档列表失败');
      }
    } finally {
      setLoading(false);
    }
  }, []);

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
        message.success(`${info.file.name} 上传成功`);
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
    const statusMap: Record<string, { color: string; icon: ReactNode; text: string }> = {
      pending: { color: 'default', icon: <ClockCircleOutlined />, text: STATUS_LABELS.pending },
      parsing: { color: 'processing', icon: <SyncOutlined spin />, text: STATUS_LABELS.parsing },
      vectorizing: { color: 'processing', icon: <CloudUploadOutlined />, text: STATUS_LABELS.vectorizing },
      metadata_extracting: { color: 'processing', icon: <ExperimentOutlined />, text: STATUS_LABELS.metadata_extracting },
      completed: { color: 'success', icon: <CheckCircleOutlined />, text: STATUS_LABELS.completed },
      failed: { color: 'error', icon: <ExclamationCircleOutlined />, text: STATUS_LABELS.failed },
      processing: { color: 'processing', icon: <SyncOutlined spin />, text: '处理中' },
    };

    const config = statusMap[normalizedStatus] || statusMap.processing;
    const label = record.statusDisplay || config.text;

    let progressText = '';
    if (normalizedStatus === 'vectorizing' && record.totalPages && record.totalPages > 0) {
      const processed = record.processedPages ?? 0;
      progressText = ` (${processed}/${record.totalPages}页)`;
    }

    return (
      <Tag color={config.color} icon={config.icon}>
        {label}
        {progressText}
      </Tag>
    );
  };

  // 元数据提取状态标签
  const renderMetadataStatus = (record: DocumentRecord) => {
    const status = record.metadataStatus?.toLowerCase();
    if (record.metadataExtracted || status === 'extracted' || status === 'success' || status === 'completed') {
      return <Tag color="green" icon={<CheckCircleOutlined />}>已提取</Tag>;
    }
    if (status === 'metadata_extracting' || status === 'extracting') {
      return <Tag color="processing" icon={<SyncOutlined spin />}>提取中</Tag>;
    }
    if (status === 'empty') {
      return <Tag color="orange" icon={<ClockCircleOutlined />}>暂无数据</Tag>;
    }
    if (status === 'skipped') {
      return <Tag color="default">已跳过</Tag>;
    }
    if (status === 'failed') {
      return <Tag color="error" icon={<ExclamationCircleOutlined />}>提取失败</Tag>;
    }
    return <Tag color="orange" icon={<ClockCircleOutlined />}>未提取</Tag>;
  };

  // 表格列定义
  const columns: ColumnsType<DocumentRecord> = [
    {
      title: '合同名称',
      dataIndex: 'name',
      key: 'name',
      width: '35%',
      render: (text: string) => (
        <Space>
          <FileTextOutlined />
          <Text strong>{text}</Text>
        </Space>
      ),
    },
    {
      title: '上传时间',
      dataIndex: 'uploadTime',
      key: 'uploadTime',
      width: '15%',
      render: (text: string) => <Text type="secondary">{text}</Text>,
    },
    {
      title: '解析状态',
      dataIndex: 'status',
      key: 'status',
      width: '18%',
      render: (_: string, record) => renderStatus(record),
    },
    {
      title: '元数据提取状态',
      dataIndex: 'metadataStatus',
      key: 'metadataStatus',
      width: '14%',
      render: (_: string | undefined, record) => renderMetadataStatus(record),
    },
    {
      title: '页数',
      dataIndex: 'pageCount',
      key: 'pageCount',
      width: '8%',
      render: (count: number) => <Badge count={count} color="blue" />,
    },
    {
      title: '文件大小',
      dataIndex: 'fileSize',
      key: 'fileSize',
      width: '10%',
      render: (size: string) => <Text type="secondary">{size}</Text>,
    },
    {
      title: '操作',
      key: 'actions',
      width: '10%',
      render: (_, record) => (
        <Space size="small">
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
      ),
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
      </Card>

      {/* 文档列表 */}
      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <Title level={4}>📋 合同列表</Title>
          <Space>
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
