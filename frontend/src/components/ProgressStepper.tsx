import React from 'react';
import { Steps, Tooltip } from 'antd';
import {
    CloudUploadOutlined,
    FileImageOutlined,
    ScanOutlined,
    DatabaseOutlined,
    ExperimentOutlined,
    CheckCircleOutlined,
    CloseCircleOutlined,
    LoadingOutlined
} from '@ant-design/icons';
import type { DocumentParseStatus } from '../types';

const { Step } = Steps;

interface ProgressStepperProps {
    status: DocumentParseStatus | string;
    errorMessage?: string;
    size?: 'default' | 'small';
}

const STEP_CONFIG = [
    {
        key: 'pending',
        title: '已上传',
        icon: <CloudUploadOutlined />,
        description: '文件进入队列'
    },
    {
        key: 'parsing_images',
        title: '格式转换',
        icon: <FileImageOutlined />,
        description: 'PDF转图片'
    },
    {
        key: 'parsing_ocr',
        title: 'OCR识别',
        icon: <ScanOutlined />,
        description: '提取全量文本'
    },
    {
        key: 'vectorizing',
        title: '向量化',
        icon: <DatabaseOutlined />,
        description: '生成索引向量'
    },
    {
        key: 'metadata_extracting',
        title: '提取元数据',
        icon: <ExperimentOutlined />,
        description: 'LLM结构化提取'
    },
    {
        key: 'completed',
        title: '完成',
        icon: <CheckCircleOutlined />,
        description: '所有处理已就绪'
    }
];

// 状态到步骤索引的映射
const getStepInfo = (status: string) => {
    const normalize = status.toLowerCase();

    // 简化的旧状态映射
    if (normalize === 'parsing') return { index: 2, status: 'process' }; // 假设旧parsing对应ocr
    if (normalize === 'processing') return { index: 1, status: 'process' };

    // 失败状态检查
    if (normalize.startsWith('failed')) {
        if (normalize === 'failed_images') return { index: 1, status: 'error' };
        if (normalize === 'failed_ocr') return { index: 2, status: 'error' };
        if (normalize === 'failed_vector') return { index: 3, status: 'error' };
        if (normalize === 'failed_metadata') return { index: 4, status: 'error' };
        return { index: 0, status: 'error' }; // 通用失败只能算第一步挂了或者无法确定
    }

    const idx = STEP_CONFIG.findIndex(s => s.key === normalize);
    if (idx !== -1) {
        if (normalize === 'completed') return { index: 5, status: 'finish' };
        return { index: idx, status: 'process' };
    }

    return { index: 0, status: 'wait' };
};

const ProgressStepper: React.FC<ProgressStepperProps> = ({ status, errorMessage, size = 'default' }) => {
    const { index: currentIndex, status: stepStatus } = getStepInfo(status as string);

    return (
        <Steps
            current={currentIndex}
            status={stepStatus as 'process' | 'wait' | 'finish' | 'error'}
            size={size}
        >
            {STEP_CONFIG.map((step, idx) => {
                const isCurrent = idx === currentIndex;
                const isError = stepStatus === 'error' && isCurrent;

                // 动态图标：进行中显示Loading
                let icon = step.icon;
                if (isCurrent && stepStatus === 'process') {
                    icon = <LoadingOutlined />;
                } else if (isError) {
                    icon = <CloseCircleOutlined />;
                }

                // 详情Tooltip
                let description: React.ReactNode = step.description;
                if (isError && errorMessage) {
                    description = (
                        <Tooltip title={errorMessage}>
                            <span style={{ color: '#ff4d4f', cursor: 'pointer', textDecoration: 'underline' }}>
                                失败: {errorMessage.slice(0, 10)}...
                            </span>
                        </Tooltip>
                    );
                }

                return (
                    <Step
                        key={step.key}
                        title={step.title}
                        icon={icon}
                        description={description}
                    />
                );
            })}
        </Steps>
    );
};

export default ProgressStepper;
