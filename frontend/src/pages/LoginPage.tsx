import { useState } from 'react';
import type { FC } from 'react';
import { Card, Form, Input, Button, Typography, Space } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';

const { Title, Text } = Typography;

interface LoginPageProps {
  onSwitchToRegister: () => void;
}

const LoginPage: FC<LoginPageProps> = ({ onSwitchToRegister }) => {
  const { login, authenticating } = useAuth();
  const [form] = Form.useForm();
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitting(true);
      await login(values.userId.trim(), values.password);
    } catch (error) {
      // 错误信息已在 AuthProvider 中处理
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0f172a' }}>
      <Card style={{ width: 420, borderRadius: 16, boxShadow: '0 20px 50px rgba(15, 23, 42, 0.3)' }}>
        <Space direction="vertical" size={8} style={{ width: '100%', marginBottom: 24 }}>
          <Title level={3} style={{ marginBottom: 0 }}>合同智能检索</Title>
          <Text type="secondary">请登录以使用文档搜索与管理功能</Text>
        </Space>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          requiredMark={false}
        >
          <Form.Item
            label="账号"
            name="userId"
            rules={[{ required: true, message: '请输入账号' }]}
          >
            <Input size="large" prefix={<UserOutlined />} placeholder="请输入账号" autoComplete="username" />
          </Form.Item>
          <Form.Item
            label="密码"
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password size="large" prefix={<LockOutlined />} placeholder="请输入密码" autoComplete="current-password" />
          </Form.Item>
          <Button
            type="primary"
            block
            size="large"
            htmlType="submit"
            loading={submitting || authenticating}
          >
            登录
          </Button>
        </Form>
        <Space style={{ marginTop: 16 }}>
          <Text type="secondary">还没有账号？</Text>
          <Button type="link" onClick={onSwitchToRegister} style={{ padding: 0 }}>
            立即注册
          </Button>
        </Space>
      </Card>
    </div>
  );
};

export default LoginPage;
