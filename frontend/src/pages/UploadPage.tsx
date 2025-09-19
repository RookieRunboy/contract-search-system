import { useEffect, useState } from 'react';
import type { FC } from 'react';
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
} from 'antd';
import { 
  InboxOutlined, DeleteOutlined, EyeOutlined, 
  DownloadOutlined, ReloadOutlined, FileTextOutlined, 
  CheckCircleOutlined, ExclamationCircleOutlined, ClockCircleOutlined,
  ExperimentOutlined
} from '@ant-design/icons';
import { API_BASE_URL, deleteDocument, getUploadedDocuments, extractMetadata, saveMetadata, getDocumentDetail } from '../services/api';
import MetadataEditModal from '../components/MetadataEditModal';
import type { ContractMetadata } from '../types';
import type { ColumnsType } from 'antd/es/table';
import type { UploadChangeParam } from 'antd/es/upload';
import type { UploadFile } from 'antd/es/upload/interface';

const { Title, Text, Paragraph } = Typography;
const { Dragger } = Upload;
const { Panel } = Collapse;


interface DocumentRecord {
  contractKey: string;
  name: string;
  fileName?: string;
  uploadTime: string;
  parseStatus: 'success' | 'processing' | 'failed' | 'pending';
  metadataExtracted: boolean;
  pageCount: number;
  fileSize?: string;
  hasStructuredData: boolean;
  actions: string[];
}

type UploadDocumentRaw = Record<string, unknown>;

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

interface DocumentDetail {
  contract_name: string;
  dataType?: string;
  totalPages?: number;
  totalChars?: number;
  extractionStatus?: string;
  uploadTime?: string;
  fileSize?: string;
  structuredData?: {
    signing_date?: string;
    party_a?: string;
    party_b?: string;
    customer_type?: string;
    contract_amount?: number;
    contract_content_summary?: string;
    positions?: string;
    personnel_list?: string;
  } | null;
  pages?: Array<{
    pageId?: number;
    text?: string;
    charCount?: number;
  }>;
}

interface DocumentDetailResponse {
  code: number;
  message: string;
  data: DocumentDetail | null;
}

const UploadPage: FC = () => {
  const [uploading, setUploading] = useState(false);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [metadataModalVisible, setMetadataModalVisible] = useState(false);
  const [extractingMetadata, setExtractingMetadata] = useState<string | null>(null);
  const [currentMetadata, setCurrentMetadata] = useState<ContractMetadata | null>(null);

  // 详情视图相关状态
  const [selectedContractKey, setSelectedContractKey] = useState<string | null>(null);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [detailData, setDetailData] = useState<DocumentDetail | null>(null);

  // 获取文档列表
  const fetchDocuments = async () => {
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
          const fileName = pickString(doc, ['file_name', 'fileName']) || (rawKey.endsWith('.pdf') ? rawKey : `${contractKey}.pdf`);
          const displayName = pickString(doc, ['display_name', 'name_display']) || fileName || rawKey;

          const rawUploadTime = pickString(doc, ['uploadTime', 'upload_time']);
          let uploadTime = '未知';
          if (rawUploadTime) {
            const parsed = Date.parse(rawUploadTime);
            uploadTime = Number.isNaN(parsed) ? rawUploadTime : new Date(parsed).toLocaleString();
          }

          const rawStatus = (pickString(doc, ['parseStatus', 'parse_status', 'status']) || 'success').toLowerCase();
          let parseStatus: DocumentRecord['parseStatus'] = 'success';
          if (rawStatus.includes('fail')) {
            parseStatus = 'failed';
          } else if (rawStatus.includes('process')) {
            parseStatus = 'processing';
          } else if (rawStatus.includes('pending')) {
            parseStatus = 'pending';
          }

          const metadataExtracted = pickBoolean(doc, ['has_metadata', 'metadataExtracted', 'metadata_extracted'], false);

          const pageCount = pickNumber(doc, ['pageCount', 'page_count', 'chunks_count', 'pages']) ?? 0;
          const fileSize = pickString(doc, ['fileSize', 'file_size']);
          const hasStructuredData = pickBoolean(doc, ['hasStructuredData', 'has_structured_data']);

          const actionsValue = doc['actions'];

          return {
            contractKey,
            name: displayName,
            fileName,
            uploadTime,
            parseStatus,
            metadataExtracted,
            pageCount,
            fileSize,
            hasStructuredData,
            actions: Array.isArray(actionsValue) ? (actionsValue as string[]) : [],
          };
        })
        .filter(Boolean) as DocumentRecord[];

      setDocuments(normalized);
    } catch (error) {
      console.error('获取文档列表失败:', error);
      message.error('获取文档列表失败');
    } finally {
      setLoading(false);
    }
  };

  const showDetail = async (record: DocumentRecord) => {
    setSelectedContractKey(record.contractKey);
    setDetailLoading(true);
    setDetailError(null);
    setDetailData(null);
    try {
      const resp: DocumentDetailResponse | any = await getDocumentDetail(record.contractKey);
      const detail: DocumentDetail | null = (resp && typeof resp === 'object') ? (resp.data ?? resp) : null;
      if (!detail) {
        throw new Error('未获取到文档详情');
      }
      setDetailData(detail);
    } catch (err: any) {
      console.error('获取文档详情失败:', err);
      setDetailError(err.message || '获取文档详情失败');
    } finally {
      setDetailLoading(false);
    }
  };

  // 删除文档
  const handleDelete = async (documentName: string) => {
    try {
      await deleteDocument(documentName);
      message.success('文档删除成功');
      fetchDocuments();
    } catch (error) {
      console.error('删除文档失败:', error);
      message.error('删除失败');
    }
  };

  // 提取元数据
  const handleExtractMetadata = async (contractKey: string) => {
    setExtractingMetadata(contractKey);
    try {
      const fileName = `${contractKey}.pdf`;
      const response = await extractMetadata(fileName);
      
      // 检查API响应结构
      if (response.code === 200 && response.data?.metadata) {
        // 确保合同名称使用文件名
        const metadata = {
          ...response.data.metadata,
          contract_name: fileName
        };
        setCurrentMetadata(metadata);
        setMetadataModalVisible(true);
        
        // 刷新文档列表以获取最新的提取状态
        await fetchDocuments();
        
        message.success('元数据提取成功');
      } else {
        throw new Error(response.message || '元数据提取失败');
      }
    } catch (error) {
      console.error('提取元数据失败:', error);
      message.error(error instanceof Error ? error.message : '提取元数据失败');
    } finally {
      setExtractingMetadata(null);
    }
  };

  // 关闭元数据弹窗
  const handleCloseMetadataModal = () => {
    setMetadataModalVisible(false);
    setCurrentMetadata(null);
  };

  // 保存元数据（修复：不再使用未定义的 activeContract）
  const handleSaveMetadata = async (metadata: ContractMetadata) => {
    try {
      const filename = metadata.contract_name;
      if (!filename) {
        message.error('缺少合同文件名，无法保存元数据');
        return;
      }
      await saveMetadata(filename, metadata);
      
      message.success('元数据保存成功');
      handleCloseMetadataModal();
      
      // 刷新文档列表以显示最新状态
      fetchDocuments();
    } catch (error: any) {
      console.error('保存元数据失败:', error);
      message.error(error.response?.data?.message || '保存失败，请重试');
    }
  };

  // 上传配置
  const uploadProps = {
    name: 'file',
    action: `${API_BASE_URL}/document/add`,
    accept: '.pdf',
    showUploadList: false,
    beforeUpload: (file: File) => {
      const isPDF = file.type === 'application/pdf';
      if (!isPDF) {
        message.error('只能上传PDF文件!');
        return false;
      }
      const isLt50M = file.size / 1024 / 1024 < 50;
      if (!isLt50M) {
        message.error('文件大小不能超过50MB!');
        return false;
      }
      return true;
    },
    onChange: (info: UploadChangeParam<UploadFile<unknown>>) => {
      const { status } = info.file;
      if (status === 'uploading') {
        setUploading(true);
      } else if (status === 'done') {
        setUploading(false);
        message.success(`${info.file.name} 上传成功`);
        fetchDocuments();
      } else if (status === 'error') {
        setUploading(false);
        message.error(`${info.file.name} 上传失败`);
      }
    },
  };

  // 状态标签渲染
  const renderStatus = (status: string) => {
    const statusMap = {
      success: { color: 'success', icon: <CheckCircleOutlined />, text: '解析成功' },
      processing: { color: 'processing', icon: <ClockCircleOutlined />, text: '处理中' },
      failed: { color: 'error', icon: <ExclamationCircleOutlined />, text: '解析失败' },
      pending: { color: 'default', icon: <ClockCircleOutlined />, text: '待处理' }
    };
    
    const config = statusMap[status as keyof typeof statusMap] || statusMap.success;
    
    return (
      <Tag color={config.color} icon={config.icon}>
        {config.text}
      </Tag>
    );
  };

  // 元数据提取状态标签
  const renderMetadataStatus = (extracted: boolean) => {
    return extracted ? (
      <Tag color="green" icon={<CheckCircleOutlined />}>已提取</Tag>
    ) : (
      <Tag color="orange" icon={<ClockCircleOutlined />}>未提取</Tag>
    );
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
      dataIndex: 'parseStatus',
      key: 'parseStatus',
      width: '12%',
      render: renderStatus,
    },
    {
      title: '元数据提取状态',
      dataIndex: 'metadataExtracted',
      key: 'metadataExtracted',
      width: '12%',
      render: renderMetadataStatus,
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
          {!record.metadataExtracted && (
            <Tooltip title="提取元数据" mouseEnterDelay={0.5} mouseLeaveDelay={0.1} destroyOnHidden trigger={["hover"]} getPopupContainer={() => document.body}>
              <Button 
                type="text" 
                icon={<ExperimentOutlined />} 
                loading={extractingMetadata === record.contractKey}
                onClick={() => handleExtractMetadata(record.contractKey)}
              />
            </Tooltip>
          )}
          <Tooltip title="下载文档" mouseEnterDelay={0.5} mouseLeaveDelay={0.1} destroyOnHidden trigger={["hover"]} getPopupContainer={() => document.body}>
            <Button 
              type="text" 
              icon={<DownloadOutlined />} 
              onClick={() => message.info('下载功能开发中')}
            />
          </Tooltip>
          <Popconfirm
            title="确定删除此文档吗？"
            onConfirm={() => handleDelete(record.contractKey)}
            okText="确定"
            cancelText="取消"
            placement="topRight"
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
  }, []);

  return (
    <div style={{ padding: '24px' }}>
      {/* 详情展示区域：顶部显示合同名称，中部按顺序展示 */}
      {selectedContractKey && (
        <Card style={{ marginBottom: 24 }}>
          {detailLoading ? (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 120 }}>
              <Spin tip="加载合同详情中..." />
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
              {detailData.structuredData ? (
                <Descriptions bordered size="small" column={2}>
                  <Descriptions.Item label="签订日期">{detailData.structuredData.signing_date || '-'}</Descriptions.Item>
                  <Descriptions.Item label="甲方">{detailData.structuredData.party_a || '-'}</Descriptions.Item>
                  <Descriptions.Item label="乙方">{detailData.structuredData.party_b || '-'}</Descriptions.Item>
                  <Descriptions.Item label="客户类型">{detailData.structuredData.customer_type || '-'}</Descriptions.Item>
                  <Descriptions.Item label="合同金额" span={2}>{detailData.structuredData.contract_amount ?? '-'}</Descriptions.Item>
                  <Descriptions.Item label="人员名单" span={2}>{detailData.structuredData.personnel_list || '-'}</Descriptions.Item>
                  <Descriptions.Item label="岗位信息" span={2}>{detailData.structuredData.positions || '-'}</Descriptions.Item>
                  <Descriptions.Item label="内容摘要" span={2}>
                    <Paragraph style={{ marginBottom: 0 }}>{detailData.structuredData.contract_content_summary || '-'}</Paragraph>
                  </Descriptions.Item>
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
          ) : null}
        </Card>
      )}

      {/* 上传区域 */}
      <Card style={{ marginBottom: '24px' }}>
        <Title level={4}>📁 上传合同文档</Title>
        <Dragger {...uploadProps} style={{ marginBottom: '16px' }}>
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            支持PDF格式，文件大小不超过50MB。上传后将自动进行LLM结构化提取。
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
              onClick={fetchDocuments}
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
          expandable={{
            expandedRowRender: (record) => (
              <div style={{ padding: '12px 16px' }}>
                <Space size="middle" wrap>
                  <Tooltip title="查看详情" mouseEnterDelay={0.5} mouseLeaveDelay={0.1} destroyOnHidden trigger={["hover"]} getPopupContainer={() => document.body}>
                    <Button type="default" icon={<EyeOutlined />} onClick={() => showDetail(record)}>
                      查看详情
                    </Button>
                  </Tooltip>
                  {!record.metadataExtracted && (
                    <Tooltip title="提取元数据" mouseEnterDelay={0.5} mouseLeaveDelay={0.1} destroyOnHidden trigger={["hover"]} getPopupContainer={() => document.body}>
                      <Button type="primary" icon={<ExperimentOutlined />} loading={extractingMetadata === record.contractKey} onClick={() => handleExtractMetadata(record.contractKey)}>
                        提取元数据
                      </Button>
                    </Tooltip>
                  )}
                  <Tooltip title="下载文档" mouseEnterDelay={0.5} mouseLeaveDelay={0.1} destroyOnHidden trigger={["hover"]} getPopupContainer={() => document.body}>
                    <Button icon={<DownloadOutlined />} onClick={() => message.info('下载功能开发中')}>
                      下载
                    </Button>
                  </Tooltip>
                  <Popconfirm
                    title="确定删除此文档吗？"
                    onConfirm={() => handleDelete(record.contractKey)}
                    okText="确定"
                    cancelText="取消"
                  >
                    <Button danger icon={<DeleteOutlined />}>删除</Button>
                  </Popconfirm>
                </Space>
              </div>
            ),
          }}
        />
      </Card>

      {/* 元数据编辑弹窗 */}
      <MetadataEditModal
        visible={metadataModalVisible}
        onCancel={handleCloseMetadataModal}
        filename={currentMetadata?.contract_name || ''}
        initialMetadata={currentMetadata}
        loading={extractingMetadata !== null}
        // 保存后：立即刷新当前行状态 + 重新拉取列表（以保证和后端完全一致）
        onSaved={(metadata) => {
          // 本地即时更新：将对应行的 metadataExtracted 标记为 true
          setDocuments((prev) => prev.map((doc) => {
            if (doc.fileName === metadata.contract_name || `${doc.contractKey}.pdf` === metadata.contract_name) {
              return { ...doc, metadataExtracted: true };
            }
            return doc;
          }));
          // 关闭弹窗
          handleCloseMetadataModal();
          // 再次拉取列表，确保状态与后端一致
          fetchDocuments();
        }}
      />
    </div>
  );
};

export default UploadPage;
