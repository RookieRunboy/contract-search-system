import { useState } from 'react';
import type { FC } from 'react';
import { Card, Form, Input, Button, Typography, Space, message } from 'antd';
import { UserAddOutlined, LockOutlined, UserOutlined } from '@ant-design/icons';
import { register as registerApi } from '../services/auth';

const { Title, Text } = Typography;

interface RegisterPageProps {
  onSwitchToLogin: () => void;
}

const RegisterPage: FC<RegisterPageProps> = ({ onSwitchToLogin }) => {
  const [form] = Form.useForm();
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitting(true);
      await registerApi(values.userId.trim(), values.password, values.confirmPassword);
      message.success('注册申请已提交，请等待管理员审批');
      onSwitchToLogin();
    } catch (error: any) {
      const detail = error?.response?.data?.detail || error?.response?.data?.message || error?.message || '注册失败，请稍后重试';
      message.error(detail);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0f172a' }}>
      <Card style={{ width: 460, borderRadius: 16, boxShadow: '0 20px 50px rgba(15, 23, 42, 0.3)' }}>
        <Space direction="vertical" size={8} style={{ width: '100%', marginBottom: 24 }}>
          <Title level={3} style={{ marginBottom: 0 }}>注册访问权限</Title>
          <Text type="secondary">提交申请后需等待管理员审核通过</Text>
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
            rules={[
              { required: true, message: '请输入账号' },
              { pattern: /^[A-Za-z0-9_.-]{3,50}$/, message: '账号需为3-50位字母、数字或._-' },
            ]}
          >
            <Input size="large" prefix={<UserOutlined />} placeholder="设置登录账号" autoComplete="username" />
          </Form.Item>
          <Form.Item
            label="密码"
            name="password"
            rules={[{ required: true, message: '请输入密码' }, { min: 8, message: '密码至少8位' }]}
          >
            <Input.Password size="large" prefix={<LockOutlined />} placeholder="设置登录密码" autoComplete="new-password" />
          </Form.Item>
          <Form.Item
            label="确认密码"
            name="confirmPassword"
            dependencies={['password']}
            rules={[
              { required: true, message: '请确认密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'));
                },
              }),
            ]}
          >
            <Input.Password size="large" prefix={<LockOutlined />} placeholder="再次输入登录密码" autoComplete="new-password" />
          </Form.Item>
          <Button
            type="primary"
            block
            size="large"
            icon={<UserAddOutlined />}
            htmlType="submit"
            loading={submitting}
          >
            提交注册申请
          </Button>
        </Form>
        <Space style={{ marginTop: 16 }}>
          <Text type="secondary">已有账号？</Text>
          <Button type="link" onClick={onSwitchToLogin} style={{ padding: 0 }}>
            返回登录
          </Button>
        </Space>
      </Card>
    </div>
  );
};

export default RegisterPage;
