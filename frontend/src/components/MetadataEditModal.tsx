import React, { useState, useEffect } from 'react';
import { Modal, Form, Input, Select, InputNumber, Button, message, Spin } from 'antd';
import type { ContractMetadata } from '../types/index';
import { saveMetadata } from '../services/api';

const { TextArea } = Input;
const { Option } = Select;

interface MetadataEditModalProps {
  visible: boolean;
  onCancel: () => void;
  filename: string;
  initialMetadata: ContractMetadata | null;
  loading?: boolean;
}

const MetadataEditModal: React.FC<MetadataEditModalProps> = ({
  visible,
  onCancel,
  filename,
  initialMetadata,
  loading = false
}) => {
  const [form] = Form.useForm();
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (visible && initialMetadata) {
      form.setFieldsValue(initialMetadata);
    }
  }, [visible, initialMetadata, form]);

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      
      const metadata: ContractMetadata = {
        ...values,
      };
      
      await saveMetadata(filename, metadata);
      message.success('元数据保存成功！');
      onCancel();
    } catch (error: any) {
      console.error('保存元数据失败:', error);
      message.error(error.response?.data?.message || '保存失败，请重试');
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    form.resetFields();
    onCancel();
  };

  return (
    <Modal
      title={`编辑元数据 - ${filename}`}
      open={visible}
      onCancel={handleCancel}
      destroyOnHidden
      maskClosable={false}
      afterClose={() => form.resetFields()}
      width={800}
      footer={[
        <Button key="cancel" onClick={handleCancel}>
          取消
        </Button>,
        <Button
          key="save"
          type="primary"
          loading={saving}
          onClick={handleSave}
          disabled={loading}
        >
          保存
        </Button>,
      ]}
    >
      <Spin spinning={loading} tip="正在提取元数据...">
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            contract_type: null,
          }}
        >
          <div className="grid grid-cols-2 gap-4">
            <Form.Item label="合同名称" name="contract_name">
          <Input disabled placeholder="合同名称（自动使用文件名）" />
        </Form.Item>
        
        <Form.Item label="甲方" name="party_a">
          <Input placeholder="请输入甲方名称" />
        </Form.Item>

            <Form.Item label="乙方" name="party_b">
              <Input placeholder="请输入乙方名称" />
            </Form.Item>

            <Form.Item
              label="客户类型"
              name="contract_type"
              rules={[{ required: true, message: '请选择客户类型' }]}
            >
              <Select placeholder="请选择客户类型">
                <Option value="fp">固定价格合同</Option>
                <Option value="tm">时间材料合同</Option>
              </Select>
            </Form.Item>

            <Form.Item label="合同金额" name="contract_amount">
              <InputNumber
                placeholder="请输入合同金额"
                style={{ width: '100%' }}
                formatter={(value) => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                parser={(value) => value!.replace(/¥\s?|(,*)/g, '')}
              />
            </Form.Item>

            <Form.Item label="岗位" name="positions">
              <Input placeholder="请输入岗位信息" />
            </Form.Item>

            <Form.Item label="相关人员清单" name="personnel_list">
              <TextArea rows={2} placeholder="请输入相关人员清单" />
            </Form.Item>
          </div>

          <Form.Item label="合同内容" name="project_description">
            <TextArea rows={4} placeholder="请输入合同内容描述" />
          </Form.Item>
        </Form>
      </Spin>
    </Modal>
  );
};

export default MetadataEditModal;