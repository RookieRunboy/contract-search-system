import { useState } from 'react';
import { Layout, Menu, Typography, Space } from 'antd';
import { FileSearchOutlined, UploadOutlined, RobotOutlined } from '@ant-design/icons';
import SearchPage from './pages/SearchPage';
import UploadPage from './pages/UploadPage';
import './App.css';

const { Header, Sider, Content } = Layout;
const { Title } = Typography;

function App() {
  const [selectedKey, setSelectedKey] = useState('search');

  const renderContent = () => {
    switch (selectedKey) {
      case 'search':
        return <SearchPage />;
      case 'upload':
        return <UploadPage />;
      default:
        return <SearchPage />;
    }
  };

  return (
    <Layout>
      <Sider width={280} theme="dark">
        <div style={{ 
          padding: '24px 16px', 
          textAlign: 'center',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          marginBottom: '16px'
        }}>
          <Space direction="vertical" size={8}>
            <RobotOutlined style={{ 
              fontSize: '32px', 
              color: '#667eea',
              filter: 'drop-shadow(0 4px 8px rgba(102, 126, 234, 0.3))'
            }} />
            <Title level={4} style={{ 
              color: 'white', 
              margin: 0,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              fontWeight: 600
            }}>
              合同智能检索
            </Title>
            <div style={{
              fontSize: '12px',
              color: 'rgba(255, 255, 255, 0.6)',
              fontWeight: 300
            }}>
              AI-Powered Contract Search
            </div>
          </Space>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          onClick={({ key }) => setSelectedKey(key)}
          style={{ paddingTop: '8px' }}
          items={[
            {
              key: 'search',
              icon: <FileSearchOutlined style={{ fontSize: '16px' }} />,
              label: <span style={{ fontSize: '14px', fontWeight: 500 }}>文档搜索</span>,
            },
            {
              key: 'upload',
              icon: <UploadOutlined style={{ fontSize: '16px' }} />,
              label: <span style={{ fontSize: '14px', fontWeight: 500 }}>文档上传</span>,
            },
          ]}
        />
      </Sider>
      <Layout>
        <Header style={{ display: 'flex', alignItems: 'center' }}>
          <Title level={3} style={{ 
            margin: 0, 
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            fontWeight: 600
          }}>
            {selectedKey === 'search' ? '🔍 智能文档搜索' : '📋 合同管理'}
          </Title>
        </Header>
        <Content>
          {renderContent()}
        </Content>
      </Layout>
    </Layout>
  );
}

export default App;
