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
  Modal,
  Tooltip,
  Popconfirm,
  Descriptions,
  Spin,
  Collapse,
  Empty,
  Divider,
  Alert,
} from 'antd';
import { 
  InboxOutlined, DeleteOutlined, EyeOutlined, 
  DownloadOutlined, ReloadOutlined, FileTextOutlined, 
  CheckCircleOutlined, ExclamationCircleOutlined, ClockCircleOutlined 
} from '@ant-design/icons';
import { API_BASE_URL, deleteDocument, getUploadedDocuments } from '../services/api';
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
  dataType: 'structured' | 'legacy';
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
  const [detailVisible, setDetailVisible] = useState(false);
  const [activeContract, setActiveContract] = useState<string | null>(null);
  const [currentDetail, setCurrentDetail] = useState<DocumentDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);

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

          const rawDataType = pickString(doc, ['dataType', 'data_type']) || 'legacy';
          const dataType: DocumentRecord['dataType'] = rawDataType === 'structured' ? 'structured' : 'legacy';

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
            dataType,
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

  const fetchDocumentDetail = async (documentName: string): Promise<DocumentDetail> => {
    const response = await fetch(`${API_BASE_URL}/documents/${encodeURIComponent(documentName)}/detail`);
    if (!response.ok) {
      throw new Error('获取文档详情失败');
    }
    const result: DocumentDetailResponse = await response.json();
    if (result.code === 200 && result.data) {
      return result.data;
    }
    throw new Error(result.message || '获取文档详情失败');
  };

  const handleCloseDetail = () => {
    setDetailVisible(false);
    setActiveContract(null);
    setCurrentDetail(null);
    setDetailError(null);
    setDetailLoading(false);
  };

  const showDetail = (record: DocumentRecord) => {
    setActiveContract(record.contractKey);
    setDetailVisible(true);
  };

  useEffect(() => {
    if (!detailVisible || !activeContract) {
      return;
    }

    let cancelled = false;

    const loadDetail = async () => {
      setDetailLoading(true);
      setDetailError(null);
      setCurrentDetail(null);

      try {
        const detail = await fetchDocumentDetail(activeContract);
        if (!cancelled) {
          setCurrentDetail(detail);
        }
      } catch (error) {
        if (!cancelled) {
          console.error('获取文档详情失败:', error);
          setDetailError(error instanceof Error ? error.message : '获取文档详情失败');
          message.error('获取文档详情失败');
        }
      } finally {
        if (!cancelled) {
          setDetailLoading(false);
        }
      }
    };

    loadDetail();

    return () => {
      cancelled = true;
    };
  }, [detailVisible, activeContract]);

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

  // 数据类型标签
  const renderDataType = (dataType: string) => {
    switch(dataType) {
      case 'structured':
        return <Tag color="blue">结构化</Tag>;
      case 'legacy':
        return <Tag color="orange">旧格式</Tag>;
      default:
        return <Tag color="gray">未知</Tag>;
    }
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
      title: '数据类型',
      dataIndex: 'dataType',
      key: 'dataType',
      width: '10%',
      render: renderDataType,
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
          <Tooltip title="查看详情" mouseEnterDelay={0.5} mouseLeaveDelay={0}>
            <Button 
              type="text" 
              icon={<EyeOutlined />} 
              onClick={() => showDetail(record)}
            />
          </Tooltip>
          <Tooltip title="下载文档" mouseEnterDelay={0.5} mouseLeaveDelay={0}>
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
        />
      </Card>

      {/* 详情弹窗 */}
      <Modal
        title={
          <Space>
            <FileTextOutlined />
            合同详细信息
          </Space>
        }
        open={detailVisible}
        onCancel={handleCloseDetail}
        width={900}
        destroyOnClose
        maskClosable={false}
        bodyStyle={{ maxHeight: '70vh', overflowY: 'auto' }}
        footer={[
          <Button key="close" onClick={handleCloseDetail}>
            关闭
          </Button>,
          <Button
            key="download"
            type="primary"
            icon={<DownloadOutlined />}
            disabled={!currentDetail}
            onClick={() => {
              if (currentDetail) {
                message.info(`下载功能开发中: ${currentDetail.contract_name}`);
              }
            }}
          >
            下载原文
          </Button>,
        ]}
      >
        {detailLoading ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin size="large" />
            <div style={{ marginTop: '16px' }}>加载详情中...</div>
          </div>
        ) : detailError ? (
          <Alert type="error" message="加载详情失败" description={detailError} showIcon />
        ) : currentDetail ? (
          <Space direction="vertical" size={16} style={{ width: '100%' }}>
            <Card bordered={false} style={{ background: '#f8f9ff' }}>
              <Space direction="vertical" size={12} style={{ width: '100%' }}>
                <Space align="center" size={12} wrap>
                  <FileTextOutlined style={{ fontSize: 20, color: '#667eea' }} />
                  <Title level={4} style={{ margin: 0 }}>
                    {currentDetail.contract_name}
                  </Title>
                  {currentDetail.dataType ? renderDataType(currentDetail.dataType) : null}
                  {currentDetail.extractionStatus && (
                    <Tag color={currentDetail.extractionStatus === '已提取' ? 'success' : 'warning'}>
                      {currentDetail.extractionStatus}
                    </Tag>
                  )}
                </Space>
                <Divider style={{ margin: '12px 0' }} />
                <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
                  <div>
                    <Text type="secondary">总页数</Text>
                    <div style={{ fontSize: 18, fontWeight: 600 }}>
                      {currentDetail.totalPages ?? 0}
                    </div>
                  </div>
                  <div>
                    <Text type="secondary">总字符数</Text>
                    <div style={{ fontSize: 18, fontWeight: 600 }}>
                      {(currentDetail.totalChars ?? 0).toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <Text type="secondary">客户类型</Text>
                    <div style={{ fontSize: 18, fontWeight: 600 }}>
                      {currentDetail.structuredData?.customer_type || '未分类'}
                    </div>
                  </div>
                </div>
              </Space>
            </Card>

            <Card title="基本信息" bordered={false}>
              <Descriptions bordered column={2} size="small">
                <Descriptions.Item label="数据类型">
                  {currentDetail.dataType ? renderDataType(currentDetail.dataType) : <Tag color="gray">未知</Tag>}
                </Descriptions.Item>
                <Descriptions.Item label="客户类型">
                  <Tag color="blue">{currentDetail.structuredData?.customer_type || '未分类'}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="签订日期">
                  {currentDetail.structuredData?.signing_date || '未提取'}
                </Descriptions.Item>
                <Descriptions.Item label="合同金额">
                  {currentDetail.structuredData?.contract_amount !== undefined
                    ? `¥${currentDetail.structuredData.contract_amount.toLocaleString()}`
                    : '未提取'}
                </Descriptions.Item>
                <Descriptions.Item label="甲方">
                  {currentDetail.structuredData?.party_a || '未提取'}
                </Descriptions.Item>
                <Descriptions.Item label="乙方">
                  {currentDetail.structuredData?.party_b || '未提取'}
                </Descriptions.Item>
                <Descriptions.Item label="关键岗位" span={2}>
                  {currentDetail.structuredData?.positions || '未提取'}
                </Descriptions.Item>
                <Descriptions.Item label="人员清单" span={2}>
                  {currentDetail.structuredData?.personnel_list || '未提取'}
                </Descriptions.Item>
              </Descriptions>
            </Card>

            <Card title="合同摘要" bordered={false}>
              <Paragraph style={{ marginBottom: 0 }}>
                {currentDetail.structuredData?.contract_content_summary || '暂无摘要'}
              </Paragraph>
            </Card>

            <Card title="页面内容" bordered={false}>
              {currentDetail.pages && currentDetail.pages.length > 0 ? (
                <Collapse accordion>
                  {currentDetail.pages.map((page, index) => (
                    <Panel
                      key={`page-${page.pageId ?? index}`}
                      header={`第 ${page.pageId ?? index + 1} 页`}
                    >
                      <Paragraph style={{ whiteSpace: 'pre-wrap' }}>
                        {page.text || '无内容'}
                      </Paragraph>
                      <Text type="secondary">
                        字符数: {(page.text ?? '').length}
                      </Text>
                    </Panel>
                  ))}
                </Collapse>
              ) : (
                <Empty description="暂无页面内容" />
              )}
            </Card>
          </Space>
        ) : (
          <Empty description="暂无合同详情" />
        )}
      </Modal>
    </div>
  );
};

export default UploadPage;
