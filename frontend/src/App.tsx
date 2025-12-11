import { useEffect, useMemo, useState } from 'react';
import { Layout, Menu, Typography, Space, Button, Spin, Tag } from 'antd';
import { FileSearchOutlined, UploadOutlined, LogoutOutlined, TeamOutlined } from '@ant-design/icons';
import SearchPage from './pages/SearchPage';
import UploadPage from './pages/UploadPage';
import PersonnelPage from './pages/PersonnelPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import { useAuth } from './contexts/AuthContext';
import type { UserRole } from './types';
import './App.css';

const { Sider, Header, Content } = Layout;
const { Title, Text } = Typography;

type NavKey = 'search' | 'upload' | 'personnel';

const ROLE_LABELS: Record<UserRole, string> = {
  superadmin: '超级管理员',
  admin: '管理员',
  normal: '普通用户',
};

const ROLE_COLORS: Record<UserRole, string> = {
  superadmin: 'purple',
  admin: 'blue',
  normal: 'green',
};

function App() {
  const { user, logout, initializing } = useAuth();
  const [selectedKey, setSelectedKey] = useState<NavKey>('search');
  const [authView, setAuthView] = useState<'login' | 'register'>('login');

  useEffect(() => {
    // Redirect to search if user doesn't have access to current page
    if (user) {
      const role = user.role;
      if (selectedKey === 'upload' && role !== 'admin' && role !== 'superadmin') {
        setSelectedKey('search');
      }
      if (selectedKey === 'personnel' && role !== 'superadmin') {
        setSelectedKey('search');
      }
    }
  }, [selectedKey, user]);

  const menuItems = useMemo(() => {
    const items = [
      {
        key: 'search',
        icon: <FileSearchOutlined style={{ fontSize: 16 }} />,
        label: <span style={{ fontSize: 14, fontWeight: 500 }}>文档搜索</span>,
      },
    ];
    // Admin and superadmin can access document management
    if (user?.role === 'admin' || user?.role === 'superadmin') {
      items.push({
        key: 'upload',
        icon: <UploadOutlined style={{ fontSize: 16 }} />,
        label: <span style={{ fontSize: 14, fontWeight: 500 }}>文档管理</span>,
      });
    }
    // Only superadmin can access personnel management
    if (user?.role === 'superadmin') {
      items.push({
        key: 'personnel',
        icon: <TeamOutlined style={{ fontSize: 16 }} />,
        label: <span style={{ fontSize: 14, fontWeight: 500 }}>人员管理</span>,
      });
    }
    return items;
  }, [user?.role]);

  const handleMenuClick = ({ key }: { key: string }) => {
    setSelectedKey(key as NavKey);
  };

  const handleLogout = () => {
    logout();
    setSelectedKey('search');
    setAuthView('login');
  };

  const renderContent = () => {
    if (!user) {
      if (authView === 'register') {
        return <RegisterPage onSwitchToLogin={() => setAuthView('login')} />;
      }
      return <LoginPage onSwitchToRegister={() => setAuthView('register')} />;
    }

    switch (selectedKey) {
      case 'personnel':
        return user.role === 'superadmin' ? <PersonnelPage /> : <SearchPage />;
      case 'upload':
        return (user.role === 'admin' || user.role === 'superadmin') ? <UploadPage /> : <SearchPage />;
      case 'search':
      default:
        return <SearchPage />;
    }
  };

  const roleLabel = ROLE_LABELS[user?.role ?? 'normal'];
  const roleTagColor = ROLE_COLORS[user?.role ?? 'normal'];

  if (initializing) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!user) {
    return renderContent();
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={260} theme="dark">
        <div style={{
          padding: '24px 16px',
          textAlign: 'center',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          marginBottom: '16px'
        }}>
          <Space direction="vertical" size={8}>
            <Title level={4} style={{ color: 'white', margin: 0 }}>合同智能检索</Title>
            <Text style={{ color: 'rgba(255, 255, 255, 0.65)' }}>AI-Powered Contract Search</Text>
          </Space>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          onClick={handleMenuClick}
          items={menuItems}
        />
      </Sider>
      <Layout>
        <Header className="app-header">
          <div className="app-user-meta">
            <Text strong className="app-user-name">{user.userId}</Text>
            <div className="app-user-role">
              <Text type="secondary">当前角色：</Text>
              <Tag color={roleTagColor}>
                {roleLabel}
              </Tag>
            </div>
          </div>
          <Button type="text" icon={<LogoutOutlined />} onClick={handleLogout}>
            退出登录
          </Button>
        </Header>
        <Content>
          {renderContent()}
        </Content>
      </Layout>
    </Layout>
  );
}

export default App;
