import { useState, useEffect } from 'react';
import type { FC } from 'react';
import { Input, Button, Card, List, Space, Typography, Empty, Spin, message, Badge, Tag, Checkbox, Progress, Tooltip, Collapse } from 'antd';
import { FileTextOutlined, ThunderboltOutlined, DownloadOutlined, CaretRightOutlined, SearchOutlined } from '@ant-design/icons';
import { searchDocuments, downloadDocument, getCustomerCategories, smartParse } from '../services/api';
import type { ContractSearchResult, ContractMetadata } from '../types/index';
import type { SearchFilters, SmartParseResult } from '../services/api';
import MetadataEditModal from '../components/MetadataEditModal';
import FilterBar from '../components/FilterBar';
import dayjs from 'dayjs';
import '../styles/compact-date-picker.css';
import { useAuth } from '../contexts/AuthContext';

const { Title, Text } = Typography;

const CHINASOFT_ENTITY_NAMES = [
  '中软国际科技服务有限公司',
  '上海中软华腾软件系统有限公司',
  '北京中软国际信息技术有限公司',
  '深圳中软国际科技服务有限公司',
  '北京中软国际科技服务有限公司',
  '中软国际（上海）科技服务有限公司',
  '中软国际科技服务（湖南）有限公司',
  'Chinasoft International Technology Service (Hong Kong) Limited',
];

const SearchPage: FC = () => {
  const { user } = useAuth();
  const canDownload = Boolean(user);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<ContractSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  // 批量选择相关状态
  const [selectedDocuments, setSelectedDocuments] = useState<Set<string>>(new Set());
  const [batchDownloading, setBatchDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [metadataModalVisible, setMetadataModalVisible] = useState(false);
  const [currentMetadata, setCurrentMetadata] = useState<ContractMetadata | null>(null);
  const [currentFilename, setCurrentFilename] = useState<string>('');

  const [categoryHierarchy, setCategoryHierarchy] = useState<Record<string, string[]>>({});
  // New filter state managed by FilterBar
  const [currentFilters, setCurrentFilters] = useState<SearchFilters>({});

  // Load customer categories on mount
  useEffect(() => {
    const loadCategories = async () => {
      const hierarchy = await getCustomerCategories();
      setCategoryHierarchy(hierarchy);
    };
    loadCategories();
  }, []);

  // 转换智能解析的筛选条件
  const convertSmartFilters = (filters: SmartParseResult['filters']): SearchFilters => {
    const result: SearchFilters = {};
    if (filters.date_start) result.dateStart = filters.date_start;
    if (filters.date_end) result.dateEnd = filters.date_end;
    if (filters.amount_min != null) result.amountMin = filters.amount_min;
    if (filters.amount_max != null) result.amountMax = filters.amount_max;
    if (filters.our_entity) result.ourEntity = filters.our_entity;
    if (filters.customer_category_level1) result.customerCategoryLevel1 = [filters.customer_category_level1];
    if (filters.customer_category_level2) result.customerCategoryLevel2 = [filters.customer_category_level2];
    return result;
  };

  // 智能解析并搜索
  const handleSmartSearch = async () => {
    const trimmedQuery = searchQuery.trim();
    if (!trimmedQuery) {
      message.warning('请输入要智能解析的内容');
      return;
    }

    setLoading(true);
    try {
      // 1. 调用智能解析
      const result = await smartParse(trimmedQuery);

      // 2. 更新筛选条件
      const newFilters = convertSmartFilters(result.filters);
      // 合并当前已有的手动筛选条件（可选，或者覆盖？用户说"直接变成...对应的筛选条件"，可能意味着覆盖或增量）
      // 这里选择增量更新，保留用户之前手动选的但AI没覆盖的？
      // 或者更符合直觉的是：AI分析出的条件应用到FilterBar上。
      setCurrentFilters(prev => ({ ...prev, ...newFilters }));

      // 3. 更新搜索框关键词
      const extractedKeywords = result.keywords.join(' ');

      // 注意：如果提取出的关键词为空，可能意味着用户想看"所有符合条件的"，此时搜索框应该清空还是保留原话？
      // 用户说"把框里的词变成对应的关键词"。
      setSearchQuery(extractedKeywords);

      // 4. 触发搜索
      // 使用提取出的关键词和新的筛选条件进行搜索
      const topK = 99;
      // 注意: searchDocuments 使用的 filters 参数应该是合并后的
      const searchToRun = extractedKeywords; // 如果为空字符串，后端会作为 query_content="" 处理

      // 由于 react state 更新是异步的，我们需要用计算出的值直接调用
      const mergedFilters = { ...currentFilters, ...newFilters };

      const searchResults = await searchDocuments(searchToRun, topK, mergedFilters);
      setSearchResults(searchResults);

      if (searchResults.length === 0) {
        message.info('未找到相关文档');
      } else {
        message.success(`智能解析完成，已找到 ${searchResults.length} 篇文档`);
      }

    } catch (error) {
      console.error('智能搜索失败:', error);
      message.error('智能解析失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };


  const handleSearch = async () => {
    const trimmedQuery = searchQuery.trim();
    if (!trimmedQuery) {
      message.warning('请输入搜索关键词');
      return;
    }
    if (trimmedQuery.length < 2) {
      message.warning('搜索关键词至少需要2个字符');
      return;
    }

    setLoading(true);
    try {
      // Default topK to 99 as requested
      const topK = 99;
      const results = await searchDocuments(searchQuery, topK, currentFilters);
      console.log('前端收到的搜索结果:', results);
      setSearchResults(results);
      if (results.length === 0) {
        message.info('未找到相关文档');
      }
    } catch (error) {
      // console.error('搜索失败:', error);
      message.error('搜索失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const highlightText = (text: string, query: string) => {
    if (!query) return text;

    // 字符级高亮逻辑：提取查询词中的所有有效字符（去重、去空格）
    // 过滤掉空格、标点符号等无意义字符，避免满屏高亮
    const validChars = new Set(
      query.split('').filter(char => /[a-zA-Z0-9\u4e00-\u9fa5]/.test(char))
    );

    if (validChars.size === 0) return text;

    // 构建正则：使用字符类 [chars]+ 匹配一个或多个连续的有效字符
    const pattern = Array.from(validChars)
      .map(char => char.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
      .join('');

    const regex = new RegExp(`([${pattern}]+)`, 'gi');
    const parts = text.split(regex);

    // 判断一个片段是否应该高亮：检查其所有字符是否都在有效字符集中
    // 避免使用 regex.test()，因为带 g 标志的正则会有 lastIndex 陷阱
    // 注意：单个字符不高亮，减少视觉噪音（至少需要连续2个字符才高亮）
    const shouldHighlight = (part: string): boolean => {
      if (!part || part.length < 2) return false; // 单个字符不高亮
      for (const char of part) {
        if (!validChars.has(char)) return false;
      }
      return true;
    };

    return parts.map((part, index) =>
      shouldHighlight(part) ? (
        <span key={index} className="highlight">{part}</span>
      ) : (
        part
      )
    );
  };

  // 元数据高亮函数
  const highlightMetadataText = (text: string, highlights?: string[]) => {
    if (!highlights || highlights.length === 0) return text;

    let highlightedText = text;
    highlights.forEach((keyword) => {
      const regex = new RegExp(`(${keyword})`, 'gi');
      highlightedText = highlightedText.replace(regex, '<mark style="background-color: #fff2e6; color: #d46b08; padding: 1px 2px; border-radius: 2px;">$1</mark>');
    });

    return <span dangerouslySetInnerHTML={{ __html: highlightedText }} />;
  };

  // 获取元数据字段的高亮关键词
  const getMetadataHighlights = (contract: ContractSearchResult, fieldName: string): string[] => {
    // 从chunks中收集该字段的高亮信息
    const highlights: string[] = [];
    contract.chunks.forEach(chunk => {
      if (chunk.metadata_highlights && chunk.metadata_highlights[fieldName]) {
        highlights.push(...chunk.metadata_highlights[fieldName]);
      }
    });
    return [...new Set(highlights)]; // 去重
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return '#52c41a';
    if (score >= 0.6) return '#faad14';
    return '#ff4d4f';
  };

  const getScoreTag = (score: number) => {
    if (score >= 0.8) return { color: 'success', text: '高度相关' };
    if (score >= 0.6) return { color: 'warning', text: '中度相关' };
    return { color: 'error', text: '低度相关' };
  };

  const normalizeAmountValue = (value: unknown): number | null => {
    if (typeof value === 'number' && !Number.isNaN(value)) {
      return value;
    }
    if (typeof value === 'string') {
      const cleaned = value.replace(/[,\s]/g, '');
      if (!cleaned) {
        return null;
      }
      const parsed = Number(cleaned);
      return Number.isNaN(parsed) ? null : parsed;
    }
    return null;
  };

  const formatAmountDisplay = (amount: number | null): string => {
    if (amount === null || amount === undefined || Number.isNaN(amount)) {
      return '暂无签订金额';
    }
    return `¥${amount.toLocaleString('zh-CN', { maximumFractionDigits: 2 })}`;
  };

  const normalizeSigningDate = (value: unknown): string | null => {
    if (typeof value === 'string' && value.trim() !== '') {
      return value.trim();
    }
    return null;
  };

  const formatSigningDateDisplay = (value: string | null): string => {
    if (!value) {
      return '暂无签订时间';
    }
    const parsed = dayjs(value);
    if (parsed.isValid()) {
      return parsed.format('YYYY-MM-DD');
    }
    return value;
  };

  const handleDownload = async (contractName: string) => {
    if (!canDownload) {
      message.warning('请先登录后再下载合同。');
      return;
    }
    try {
      // 确保文件名包含.pdf扩展名
      const fileName = contractName.endsWith('.pdf') ? contractName : `${contractName}.pdf`;
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
      console.error('下载失败:', error);
      message.error('文件下载失败，请稍后重试');
    }
  };



  // 关闭元数据弹窗
  const handleCloseMetadataModal = () => {
    setMetadataModalVisible(false);
    setCurrentMetadata(null);
    setCurrentFilename('');
  };

  // 批量选择相关函数
  const handleSelectDocument = (contractName: string, checked: boolean) => {
    const newSelected = new Set(selectedDocuments);
    if (checked) {
      newSelected.add(contractName);
    } else {
      newSelected.delete(contractName);
    }
    setSelectedDocuments(newSelected);
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      const allDocuments = new Set(searchResults.map(item => item.contract_name));
      setSelectedDocuments(allDocuments);
    } else {
      setSelectedDocuments(new Set());
    }
  };

  const handleBatchDownload = async () => {
    if (selectedDocuments.size === 0) {
      message.warning('请先选择要下载的文档');
      return;
    }
    if (!canDownload) {
      message.warning('请先登录后再下载合同。');
      return;
    }

    setBatchDownloading(true);
    setDownloadProgress(0);

    try {
      const documentsArray = Array.from(selectedDocuments);
      const total = documentsArray.length;

      for (let i = 0; i < total; i++) {
        const contractName = documentsArray[i];
        try {
          const fileName = contractName.endsWith('.pdf') ? contractName : `${contractName}.pdf`;
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

          // 更新进度
          setDownloadProgress(Math.round(((i + 1) / total) * 100));

          // 添加延迟避免浏览器阻止多个下载
          if (i < total - 1) {
            await new Promise(resolve => setTimeout(resolve, 500));
          }
        } catch (error) {
          console.error(`下载文件 ${contractName} 失败:`, error);
          message.error(`文件 ${contractName} 下载失败`);
        }
      }

      message.success(`成功下载 ${total} 个文件`);
      setSelectedDocuments(new Set()); // 清空选中状态
    } catch (error) {
      console.error('批量下载失败:', error);
      message.error('批量下载失败，请稍后重试');
    } finally {
      setBatchDownloading(false);
      setDownloadProgress(0);
    }
  };

  // 获取唯一文档名列表（去重）
  const getUniqueDocuments = () => {
    const uniqueNames = new Set(searchResults.map(item => item.contract_name));
    return Array.from(uniqueNames);
  };

  const isAllSelected = searchResults.length > 0 && getUniqueDocuments().every(name => selectedDocuments.has(name));
  const isIndeterminate = selectedDocuments.size > 0 && !isAllSelected;

  return (
    <div className="search-container">
      <style>{`
        /* 响应式设计 */
        @media (max-width: 768px) {
          .search-container {
            padding: 16px;
          }
          
          .search-card {
            margin-bottom: 16px;
            border-radius: 12px;
          }
          
          .search-header-content {
            gap: 12px;
          }
          
          .search-icon {
            font-size: 36px;
          }
          
          .search-title {
            font-size: 24px !important;
          }
          
          .search-subtitle {
            font-size: 14px;
          }
          
          .search-input-container {
            max-width: 100%;
          }
          
          .search-button {
            height: 40px;
            font-size: 14px;
          }
          
          .search-input {
            font-size: 14px;
          }
          
          .slider-container {
            max-width: 100%;
          }
          
          .results-header {
            flex-direction: column;
            gap: 12px;
            align-items: flex-start;
          }
          
          .result-title-container {
            flex-direction: column;
            align-items: flex-start;
            gap: 8px;
          }
          
          .result-content {
            font-size: 14px;
            line-height: 1.6;
          }
          
          .loading-card {
            border-radius: 12px;
          }
          
          .results-card {
            border-radius: 12px;
          }
          
          .empty-card {
            border-radius: 12px;
            padding: 32px 16px;
          }
        }
        
        @media (max-width: 480px) {
          .search-container {
            padding: 12px;
          }
          
          .search-header {
            margin-bottom: 24px;
          }
          
          .search-icon {
            font-size: 32px;
          }
          
          .search-title {
            font-size: 20px !important;
          }
          
          .search-subtitle {
            font-size: 12px;
          }
          
          .search-button {
            height: 36px;
            font-size: 12px;
            padding: 0 12px;
          }
          
          .search-input {
            font-size: 12px;
          }
          
          .slider-header {
            flex-direction: column;
            gap: 8px;
            align-items: flex-start;
          }
          
          .result-item {
            padding: 12px 0;
            margin-bottom: 12px;
          }
          
          .result-card {
            padding: 12px;
          }
          
          .result-title-text {
            font-size: 14px;
          }
          
          .result-content {
            font-size: 13px;
            min-height: 40px;
          }
          
          .empty-title {
            font-size: 16px;
          }
          
          .empty-subtitle {
            font-size: 12px;
          }
        }
      `}</style>
      {/* 搜索区域 */}
      <Card className="search-card">
        <div style={{ width: '100%' }}>
          <div className="search-header">
            <div className="search-header-content">
              <div className="search-icon">🔍</div>
              <Title level={2} className="search-title">智能文档搜索</Title>
              <Text type="secondary" className="search-subtitle">基于AI技术的合同文档智能检索系统</Text>
            </div>
          </div>

          <div className="search-input-container">
            <div style={{ display: 'flex', gap: '8px' }}>
              <Input
                placeholder="请输入搜索内容..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onPressEnter={handleSearch}
                size="large"
                className="search-input"
                style={{ flex: 1 }}
              />
              <Button
                type="primary"
                icon={<SearchOutlined />}
                size="large"
                onClick={handleSearch}
                loading={loading}
              >
                普通搜索
              </Button>
              <Tooltip title="AI会自动提取关键词并设置筛选条件">
                <Button
                  className="smart-search-btn"
                  icon={<ThunderboltOutlined />}
                  size="large"
                  onClick={handleSmartSearch}
                  loading={loading}
                  style={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    borderColor: 'transparent',
                    color: 'white'
                  }}
                >
                  智能搜索
                </Button>
              </Tooltip>
            </div>
          </div>


          {/* 筛选区域 - Intel风格纵向筛选器列表 */}
          <div style={{ marginTop: '16px' }}>
            <FilterBar
              categoryHierarchy={categoryHierarchy}
              entityOptions={CHINASOFT_ENTITY_NAMES}
              onFiltersChange={setCurrentFilters}
            />
          </div>
        </div>
      </Card>

      {/* 加载状态 */}
      {loading && (
        <Card className="loading-card">
          <div className="loading-content">
            <Spin size="large" />
            <div className="loading-text">AI正在分析文档内容...</div>
          </div>
        </Card>
      )}

      {/* 搜索结果 */}
      {!loading && searchResults.length > 0 && (
        <Card className="results-card">
          <div className="results-header">
            <Title level={4} className="results-title">
              <FileTextOutlined style={{ marginRight: '8px', color: '#667eea' }} />
              搜索结果
            </Title>
            <Badge
              count={`${searchResults.length} 条结果`}
              className="results-badge"
            />
          </div>

          {/* 批量操作控制区域 */}
          <div style={{
            marginBottom: '16px',
            padding: '12px',
            background: '#f8f9fa',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '12px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <Checkbox
                indeterminate={isIndeterminate}
                checked={isAllSelected}
                onChange={(e) => handleSelectAll(e.target.checked)}
              >
                全选
              </Checkbox>
              <Text type="secondary">
                已选择 {selectedDocuments.size} / {getUniqueDocuments().length} 个文档
              </Text>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {batchDownloading && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: '120px' }}>
                  <Progress
                    percent={downloadProgress}
                    size="small"
                    style={{ minWidth: '80px' }}
                  />
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    {downloadProgress}%
                  </Text>
                </div>
              )}
              <Tooltip title={canDownload ? undefined : '请先登录后下载合同'}>
                <Button
                  type="primary"
                  icon={<DownloadOutlined />}
                  onClick={handleBatchDownload}
                  disabled={!canDownload || selectedDocuments.size === 0 || batchDownloading}
                  loading={batchDownloading}
                >
                  批量导出 ({selectedDocuments.size})
                </Button>
              </Tooltip>
            </div>
          </div>
          <List
            dataSource={searchResults}
            renderItem={(contract) => {
              const scoreTag = getScoreTag(contract.score);
              const amountSource = contract.contract_amount ?? contract.metadata_info?.contract_amount ?? null;
              const signingDateSource = contract.signing_date ?? contract.metadata_info?.signing_date ?? null;
              const normalizedAmount = normalizeAmountValue(amountSource);
              const normalizedSigningDate = normalizeSigningDate(signingDateSource);
              const amountDisplay = formatAmountDisplay(normalizedAmount);
              const signingDateDisplay = formatSigningDateDisplay(normalizedSigningDate);
              return (
                <List.Item className="result-item">
                  <Card className="result-card"
                    title={
                      <div className="result-title-container">
                        <div
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '12px',
                            flexWrap: 'wrap',
                            flex: '1 1 auto'
                          }}
                        >
                          <Checkbox
                            checked={selectedDocuments.has(contract.contract_name)}
                            onChange={(e) => handleSelectDocument(contract.contract_name, e.target.checked)}
                          />
                          <Space>
                            <Text strong className="result-title-text">
                              {contract.contract_name}
                            </Text>
                            <Tag color="green">{contract.chunks.length} 个相关段落</Tag>
                            {contract.metadata_score && contract.metadata_score > 0 && (
                              <Tag color="purple">元数据匹配</Tag>
                            )}
                          </Space>
                        </div>
                        <Tooltip title={canDownload ? undefined : '请先登录后下载合同'}>
                          <Button
                            type="primary"
                            size="small"
                            icon={<DownloadOutlined />}
                            onClick={() => handleDownload(contract.contract_name)}
                            style={{ marginLeft: 'auto' }}
                            disabled={!canDownload}
                          >
                            导出合同
                          </Button>
                        </Tooltip>
                        <Space
                          wrap
                          size={[4, 4]}
                          style={{
                            width: '100%',
                            justifyContent: 'flex-start',
                            alignItems: 'center'
                          }}
                        >
                          <Tag
                            color={scoreTag.color}
                            className="result-score-tag"
                          >
                            {scoreTag.text}
                          </Tag>
                          <Text
                            className="result-score-text"
                            style={{ color: getScoreColor(contract.score) }}
                          >
                            {contract.score.toFixed(1)}
                          </Text>
                          <Tag color="blue" className="result-score-tag">
                            签订时间: {signingDateDisplay}
                          </Tag>
                          <Tag color="geekblue" className="result-score-tag">
                            合同金额: {amountDisplay}
                          </Tag>
                          {contract.metadata_score && contract.metadata_score > 0 && (
                            <Text
                              style={{ color: '#722ed1', fontSize: '12px' }}
                            >
                              (元数据: {contract.metadata_score.toFixed(1)})
                            </Text>
                          )}
                        </Space>
                      </div>
                    }
                  >
                    {/* 元数据信息展示区域 */}
                    {contract.metadata_info && (
                      <div style={{
                        marginBottom: '16px',
                        padding: '12px',
                        background: '#f8f9fa',
                        borderRadius: '8px',
                        border: '1px solid #e9ecef'
                      }}>
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          marginBottom: '8px',
                          gap: '8px'
                        }}>
                          <Text strong style={{ color: '#722ed1' }}>📋 合同信息</Text>
                          {contract.metadata_score && contract.metadata_score > 0 && (
                            <Tag color="purple" style={{ fontSize: '12px', padding: '2px 6px' }}>
                              匹配度: {contract.metadata_score.toFixed(1)}
                            </Tag>
                          )}
                        </div>
                        <div style={{
                          display: 'grid',
                          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                          gap: '8px',
                          fontSize: '13px'
                        }}>
                          {(contract.metadata_info.customer_name || contract.metadata_info.party_a) && (
                            <div>
                              <Text type="secondary">客户名称：</Text>
                              <Text>
                                {highlightMetadataText(
                                  contract.metadata_info.customer_name ?? contract.metadata_info.party_a ?? '',
                                  Array.from(new Set([
                                    ...getMetadataHighlights(contract, 'customer_name'),
                                    ...getMetadataHighlights(contract, 'party_a'),
                                  ]))
                                )}
                              </Text>
                            </div>
                          )}
                          {(contract.metadata_info.our_entity || contract.metadata_info.party_b) && (
                            <div>
                              <Text type="secondary">我方实体：</Text>
                              <Text>
                                {highlightMetadataText(
                                  contract.metadata_info.our_entity ?? contract.metadata_info.party_b ?? '',
                                  Array.from(new Set([
                                    ...getMetadataHighlights(contract, 'our_entity'),
                                    ...getMetadataHighlights(contract, 'party_b'),
                                  ]))
                                )}
                              </Text>
                            </div>
                          )}
                          {(contract.metadata_info.customer_category_level1 || contract.metadata_info.customer_category_level2 || contract.metadata_info.contract_type) && (
                            <div>
                              <Text type="secondary">客户分类：</Text>
                              <Text>
                                {(() => {
                                  const parts = [
                                    contract.metadata_info.customer_category_level1 ?? contract.metadata_info.contract_type,
                                    contract.metadata_info.customer_category_level2 || undefined,
                                  ].filter((item): item is string => Boolean(item));
                                  const text = parts.length > 0 ? parts.join(' / ') : '未匹配';
                                  const highlights = Array.from(new Set([
                                    ...getMetadataHighlights(contract, 'customer_category_level1'),
                                    ...getMetadataHighlights(contract, 'customer_category_level2'),
                                    ...getMetadataHighlights(contract, 'contract_type'),
                                  ]));
                                  return highlightMetadataText(text, highlights);
                                })()}
                              </Text>
                            </div>
                          )}
                          {contract.metadata_info.contract_amount && (
                            <div>
                              <Text type="secondary">合同金额：</Text>
                              <Text>
                                {highlightMetadataText(
                                  String(contract.metadata_info.contract_amount),
                                  getMetadataHighlights(contract, 'contract_amount')
                                )}
                              </Text>
                            </div>
                          )}
                          {contract.metadata_info.project_description && (
                            <div style={{ gridColumn: '1 / -1' }}>
                              <Text type="secondary">项目描述：</Text>
                              <Text>
                                {highlightMetadataText(
                                  contract.metadata_info.project_description,
                                  getMetadataHighlights(contract, 'project_description')
                                )}
                              </Text>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                    <Collapse
                      ghost
                      expandIcon={({ isActive }) => <CaretRightOutlined rotate={isActive ? 90 : 0} />}
                      defaultActiveKey={['0']}
                      items={[
                        {
                          key: '0',
                          label: `查看相关段落 (${contract.chunks.length}个)`,
                          children: (
                            <List
                              dataSource={contract.chunks}
                              renderItem={(chunk) => (
                                <List.Item style={{ padding: '8px 0', borderBottom: '1px solid #f0f0f0' }}>
                                  <div style={{ width: '100%' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                                      <Tag color="blue">第 {chunk.page_id} 页</Tag>
                                      <Text type="secondary">相关度: {chunk.score.toFixed(2)}</Text>
                                    </div>
                                    <div className="result-content">
                                      {highlightText(chunk.text, searchQuery)}
                                    </div>
                                  </div>
                                </List.Item>
                              )}
                            />
                          )
                        }
                      ]}
                    />
                  </Card>
                </List.Item>
              );
            }}
          />
        </Card>
      )}

      {/* 空状态 */}
      {!loading && searchQuery && searchResults.length === 0 && (
        <Card className="empty-card">
          <Empty
            description={
              <div>
                <div className="empty-title">
                  未找到与 "{searchQuery}" 相关的文档
                </div>
                <div className="empty-subtitle">
                  请尝试使用其他关键词或检查拼写
                </div>
              </div>
            }
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        </Card>
      )}

      <MetadataEditModal
        visible={metadataModalVisible}
        onCancel={handleCloseMetadataModal}
        filename={currentFilename}
        initialMetadata={currentMetadata}
        loading={false}
      />
    </div>
  );
};

export default SearchPage;
