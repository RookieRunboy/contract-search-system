import { useState } from 'react';
import { Layout, Menu, Typography, Space, Modal, Input, message } from 'antd';
import { FileSearchOutlined, UploadOutlined, RobotOutlined } from '@ant-design/icons';
import SearchPage from './pages/SearchPage';
import UploadPage from './pages/UploadPage';
import './App.css';

const { Sider, Content } = Layout;
const { Title, Text } = Typography;

function App() {
  const [selectedKey, setSelectedKey] = useState('search');
  const [uploadPassword, setUploadPassword] = useState<string | null>(null);
  const [uploadAccessGranted, setUploadAccessGranted] = useState(false);
  const [passwordModalVisible, setPasswordModalVisible] = useState(false);
  const [passwordInput, setPasswordInput] = useState('');
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [pendingNavKey, setPendingNavKey] = useState<string | null>(null);

  const handleMenuClick = ({ key }: { key: string }) => {
    if (key === 'upload' && !uploadAccessGranted) {
      setPendingNavKey(key);
      setPasswordModalVisible(true);
      return;
    }
    setSelectedKey(key);
  };

  const handlePasswordConfirm = () => {
    const trimmed = passwordInput.trim();
    if (!trimmed) {
      setPasswordError('请输入上传密码');
      return;
    }

    setUploadPassword(trimmed);
    setUploadAccessGranted(true);
    setPasswordModalVisible(false);
    setPasswordInput('');
    setPasswordError(null);

    if (pendingNavKey) {
      setSelectedKey(pendingNavKey);
      setPendingNavKey(null);
    } else {
      setSelectedKey('upload');
    }
  };

  const handlePasswordCancel = () => {
    setPasswordModalVisible(false);
    setPasswordInput('');
    setPasswordError(null);
    setPendingNavKey(null);

    if (!uploadAccessGranted) {
      setSelectedKey('search');
    }
  };

  const handlePasswordInvalid = () => {
    setUploadAccessGranted(false);
    setUploadPassword(null);
    setPendingNavKey('upload');
    setPasswordModalVisible(true);
    message.warning('上传密码已失效，请重新输入');
  };

  const renderContent = () => {
    switch (selectedKey) {
      case 'search':
        return <SearchPage />;
      case 'upload':
        return uploadAccessGranted ? (
          <UploadPage
            uploadPassword={uploadPassword}
            onPasswordInvalid={handlePasswordInvalid}
          />
        ) : (
          <div style={{
            padding: '48px',
            textAlign: 'center',
          }}
          >
            <Title level={3}>文档上传已锁定</Title>
            <Text type="secondary">请通过左侧导航并输入上传密码后继续。</Text>
          </div>
        );
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
          onClick={handleMenuClick}
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
        <Content>
          {renderContent()}
        </Content>
      </Layout>
      <Modal
        title="请输入上传密码"
        open={passwordModalVisible}
        onOk={handlePasswordConfirm}
        onCancel={handlePasswordCancel}
        okText="确认"
        cancelText="取消"
        maskClosable={false}
        destroyOnClose
      >
        <Input.Password
          placeholder="请输入上传密码"
          value={passwordInput}
          autoFocus
          onChange={(event) => {
            setPasswordInput(event.target.value);
            if (passwordError) {
              setPasswordError(null);
            }
          }}
          onPressEnter={handlePasswordConfirm}
        />
        {passwordError ? (
          <Text type="danger" style={{ display: 'block', marginTop: 8 }}>{passwordError}</Text>
        ) : null}
      </Modal>
    </Layout>
  );
}

export default App;
