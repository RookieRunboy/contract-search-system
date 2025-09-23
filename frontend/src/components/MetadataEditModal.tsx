import React, { useState, useEffect, useCallback } from 'react';
import { Modal, Form, Input, Select, InputNumber, Button, message, Spin } from 'antd';
import { ExperimentOutlined } from '@ant-design/icons';
import type { ContractMetadata } from '../types/index';
import { saveMetadata, extractMetadata } from '../services/api';

const { TextArea } = Input;
const { Option } = Select;

interface MetadataEditModalProps {
  visible: boolean;
  onCancel: () => void;
  filename: string;
  initialMetadata: ContractMetadata | null;
  loading?: boolean;
  // 新增：保存成功回调
  onSaved?: (metadata: ContractMetadata) => void;
}

const MetadataEditModal: React.FC<MetadataEditModalProps> = ({
  visible,
  onCancel,
  filename,
  initialMetadata,
  loading = false,
  onSaved,
}) => {
  const [form] = Form.useForm();
  const [saving, setSaving] = useState(false);
  const [extracting, setExtracting] = useState(false);

  const normalizeTextValue = (value: unknown): string | null => {
    if (typeof value === 'string') {
      const trimmed = value.trim();
      return trimmed === '' ? null : trimmed;
    }
    return null;
  };

  const normalizeAmountValue = (value: unknown): number | null => {
    if (typeof value === 'number' && !Number.isNaN(value)) {
      return value;
    }
    if (typeof value === 'string' && value.trim() !== '') {
      const parsed = Number.parseFloat(value.replace(/[^\d.-]/g, ''));
      return Number.isNaN(parsed) ? null : parsed;
    }
    return null;
  };

  const resolveErrorMessage = (error: unknown, fallback: string): string => {
    if (error && typeof error === 'object' && 'response' in error) {
      const response = (error as { response?: { data?: { message?: string; detail?: string } } }).response;
      const detailMessage = response?.data?.message ?? response?.data?.detail;
      if (detailMessage) {
        return detailMessage;
      }
    }

    if (error instanceof Error && error.message) {
      return error.message;
    }

    return fallback;
  };

  const populateFormFields = useCallback((metadata: ContractMetadata | null) => {
    form.setFieldsValue({
      contract_name: filename,
      party_a: metadata?.party_a ?? '',
      party_b: metadata?.party_b ?? '',
      contract_type: metadata?.contract_type ?? undefined,
      contract_amount: metadata?.contract_amount ?? null,
      project_description: metadata?.project_description ?? '',
      positions: metadata?.positions ?? '',
      personnel_list: metadata?.personnel_list ?? '',
    });
  }, [form, filename]);

  useEffect(() => {
    if (!visible) {
      return;
    }

    const timer = setTimeout(() => {
      if (initialMetadata) {
        populateFormFields(initialMetadata);
      } else {
        populateFormFields(null);
      }
    }, 0);

    return () => {
      clearTimeout(timer);
    };
  }, [visible, initialMetadata, populateFormFields]);

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);

      const metadata: ContractMetadata = {
        contract_name: filename,
        party_a: normalizeTextValue(values.party_a),
        party_b: normalizeTextValue(values.party_b),
        contract_type: values.contract_type ?? null,
        contract_amount: normalizeAmountValue(values.contract_amount),
        project_description: normalizeTextValue(values.project_description),
        positions: normalizeTextValue(values.positions),
        personnel_list: normalizeTextValue(values.personnel_list),
        extracted_at: initialMetadata?.extracted_at ?? '',
      };

      await saveMetadata(filename, metadata);
      message.success('元数据保存成功！');
      // 调用父组件回调以便刷新列表
      onSaved?.(metadata);
      onCancel();
    } catch (error) {
      console.error('保存元数据失败:', error);
      message.error(resolveErrorMessage(error, '保存失败，请重试'));
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    form.resetFields();
    onCancel();
  };

  const handleExtractMetadata = async () => {
    try {
      setExtracting(true);
      const response = await extractMetadata(filename);
      
      if (response.code === 200 && response.data?.metadata) {
        const metadata: ContractMetadata = {
          contract_name: filename,
          party_a: normalizeTextValue(response.data.metadata.party_a),
          party_b: normalizeTextValue(response.data.metadata.party_b),
          contract_type: response.data.metadata.contract_type ?? null,
          contract_amount: normalizeAmountValue(response.data.metadata.contract_amount),
          project_description: normalizeTextValue(response.data.metadata.project_description),
          positions: normalizeTextValue(response.data.metadata.positions),
          personnel_list: normalizeTextValue(response.data.metadata.personnel_list),
          extracted_at: response.data.metadata.extracted_at ?? '',
        };
        populateFormFields(metadata);
        message.success('元数据提取成功！');
      } else {
        throw new Error(response.message || '元数据提取失败');
      }
    } catch (error) {
      console.error('提取元数据失败:', error);
      message.error(resolveErrorMessage(error, '提取元数据失败，请重试'));
    } finally {
      setExtracting(false);
    }
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
          key="extract"
          icon={<ExperimentOutlined />}
          loading={extracting}
          onClick={handleExtractMetadata}
          disabled={loading || saving}
        >
          提取元数据
        </Button>,
        <Button
          key="save"
          type="primary"
          loading={saving}
          onClick={handleSave}
          disabled={loading || extracting}
        >
          保存
        </Button>,
      ]}
    >
      <Spin spinning={loading || extracting} tip={extracting ? "正在提取元数据..." : "加载中..."}>
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
              label="合同方向"
              name="contract_type"
              rules={[{ required: true, message: '请选择合同方向' }]}
            >
              <Select placeholder="请选择合同方向">
                <Option value="金融方向">金融方向</Option>
                <Option value="互联网方向">互联网方向</Option>
                <Option value="电信方向">电信方向</Option>
                <Option value="其他">其他</Option>
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
