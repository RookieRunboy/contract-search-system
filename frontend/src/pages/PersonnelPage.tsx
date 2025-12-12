import { useCallback, useEffect, useState } from 'react';
import type { FC } from 'react';
import {
    Card,
    Table,
    Typography,
    Space,
    message,
    Tag,
    Button,
    Modal,
    Input,
    Select,
    Empty,
} from 'antd';
import {
    CheckCircleOutlined,
    CloseCircleOutlined,
    UserOutlined,
    ReloadOutlined,
    ClockCircleOutlined,
    DownloadOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { RegistrationRequestSummary, UserRecord, UserRole, DownloadLogRecord } from '../types';
import {
    fetchPendingRegistrations,
    approveRegistration as approveRegistrationRequest,
    rejectRegistration as rejectRegistrationRequest,
    fetchAllUsers,
    updateUserRole,
    updateUserStatus,
    fetchUserDownloadLogs,
} from '../services/auth';
import { useAuth } from '../contexts/AuthContext';

const { Title, Text } = Typography;

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

const PersonnelPage: FC = () => {
    const { user } = useAuth();
    const isSuperAdmin = user?.role === 'superadmin';

    // Registration approval state
    const [registrationRequests, setRegistrationRequests] = useState<RegistrationRequestSummary[]>([]);
    const [registrationLoading, setRegistrationLoading] = useState(false);
    const [processingRequestId, setProcessingRequestId] = useState<string | null>(null);
    const [rejectModal, setRejectModal] = useState<{ open: boolean; requestId: string | null; reason: string }>({
        open: false,
        requestId: null,
        reason: '',
    });
    const [rejectSubmitting, setRejectSubmitting] = useState(false);

    // User management state
    const [users, setUsers] = useState<UserRecord[]>([]);
    const [usersLoading, setUsersLoading] = useState(false);
    const [roleUpdateModal, setRoleUpdateModal] = useState<{ open: boolean; userId: string | null; currentRole: UserRole | null }>({
        open: false,
        userId: null,
        currentRole: null,
    });
    const [newRole, setNewRole] = useState<UserRole>('normal');
    const [roleUpdateSubmitting, setRoleUpdateSubmitting] = useState(false);

    const resolveApiError = useCallback((error: unknown, fallback: string): string => {
        if (error && typeof error === 'object' && 'response' in error) {
            const response = (error as { response?: { data?: { detail?: string; message?: string } } }).response;
            const detailMessage = response?.data?.detail ?? response?.data?.message;
            if (typeof detailMessage === 'string' && detailMessage.trim()) {
                return detailMessage;
            }
        }
        if (error instanceof Error && error.message) {
            return error.message;
        }
        return fallback;
    }, []);

    // Fetch pending registrations
    const fetchRegistrations = useCallback(async () => {
        if (!isSuperAdmin) {
            setRegistrationRequests([]);
            return;
        }
        setRegistrationLoading(true);
        try {
            const response = await fetchPendingRegistrations();
            const rawList: unknown[] = Array.isArray((response as any)?.data)
                ? (response as any).data
                : Array.isArray(response)
                    ? response
                    : [];
            const normalized = rawList
                .filter((item): item is Record<string, any> => Boolean(item) && typeof item === 'object')
                .map((item) => ({
                    requestId: String(item.request_id ?? item.requestId ?? ''),
                    userId: String(item.user_id ?? item.userId ?? ''),
                    status: (item.status ?? 'pending') as RegistrationRequestSummary['status'],
                    submittedAt: item.submitted_at ?? item.submittedAt ?? null,
                    reviewer: item.reviewer ?? null,
                    reviewedAt: item.reviewed_at ?? item.reviewedAt ?? null,
                    decisionReason: item.decision_reason ?? item.decisionReason ?? null,
                }));
            setRegistrationRequests(normalized);
        } catch (error) {
            message.error(resolveApiError(error, '获取注册申请列表失败'));
        } finally {
            setRegistrationLoading(false);
        }
    }, [isSuperAdmin, resolveApiError]);

    // Fetch all users
    const fetchUsers = useCallback(async () => {
        if (!isSuperAdmin) {
            setUsers([]);
            return;
        }
        setUsersLoading(true);
        try {
            const response = await fetchAllUsers();
            const rawList: unknown[] = Array.isArray((response as any)?.data)
                ? (response as any).data
                : Array.isArray(response)
                    ? response
                    : [];
            const normalized = rawList
                .filter((item): item is Record<string, any> => Boolean(item) && typeof item === 'object')
                .map((item) => ({
                    userId: String(item.user_id ?? item.userId ?? ''),
                    role: (item.role ?? 'normal') as UserRole,
                    status: item.status ?? 'active',
                    createdAt: item.created_at ?? item.createdAt ?? null,
                }));
            setUsers(normalized);
        } catch (error) {
            message.error(resolveApiError(error, '获取用户列表失败'));
        } finally {
            setUsersLoading(false);
        }
    }, [isSuperAdmin, resolveApiError]);

    useEffect(() => {
        fetchRegistrations();
        fetchUsers();
    }, [fetchRegistrations, fetchUsers]);

    // Handle approve registration
    const handleApproveRegistration = async (request: RegistrationRequestSummary) => {
        setProcessingRequestId(request.requestId);
        try {
            await approveRegistrationRequest(request.requestId);
            message.success('已通过 ' + request.userId + ' 的注册申请');
            await Promise.all([fetchRegistrations(), fetchUsers()]);
        } catch (error) {
            message.error(resolveApiError(error, '审批失败，请稍后重试'));
        } finally {
            setProcessingRequestId(null);
        }
    };

    // Handle reject registration
    const openRejectModal = (request: RegistrationRequestSummary) => {
        setRejectModal({
            open: true,
            requestId: request.requestId,
            reason: '',
        });
    };

    const closeRejectModal = () => {
        setRejectModal({
            open: false,
            requestId: null,
            reason: '',
        });
    };

    const handleRejectSubmit = async () => {
        if (!rejectModal.requestId) {
            return;
        }
        setRejectSubmitting(true);
        try {
            await rejectRegistrationRequest(rejectModal.requestId, rejectModal.reason?.trim() || undefined);
            message.success('已拒绝注册申请');
            closeRejectModal();
            await fetchRegistrations();
        } catch (error) {
            message.error(resolveApiError(error, '操作失败，请稍后重试'));
        } finally {
            setRejectSubmitting(false);
        }
    };

    // Handle role update
    const openRoleUpdateModal = (userRecord: UserRecord) => {
        setRoleUpdateModal({
            open: true,
            userId: userRecord.userId,
            currentRole: userRecord.role,
        });
        setNewRole(userRecord.role);
    };

    const closeRoleUpdateModal = () => {
        setRoleUpdateModal({
            open: false,
            userId: null,
            currentRole: null,
        });
    };

    const handleRoleUpdateSubmit = async () => {
        if (!roleUpdateModal.userId) {
            return;
        }
        setRoleUpdateSubmitting(true);
        try {
            await updateUserRole(roleUpdateModal.userId, newRole);
            message.success('角色更新成功');
            closeRoleUpdateModal();
            await fetchUsers();
        } catch (error) {
            message.error(resolveApiError(error, '角色更新失败'));
        } finally {
            setRoleUpdateSubmitting(false);
        }
    };

    // Handle status toggle (disable/enable)
    const [statusUpdatingUserId, setStatusUpdatingUserId] = useState<string | null>(null);

    const handleToggleUserStatus = async (userRecord: UserRecord) => {
        const newStatus = userRecord.status === 'active' ? 'disabled' : 'active';
        setStatusUpdatingUserId(userRecord.userId);
        try {
            await updateUserStatus(userRecord.userId, newStatus);
            message.success(newStatus === 'disabled' ? '已禁用该账户' : '已启用该账户');
            await fetchUsers();
        } catch (error) {
            message.error(resolveApiError(error, '操作失败'));
        } finally {
            setStatusUpdatingUserId(null);
        }
    };

    // Handle download logs modal
    const [downloadLogsModal, setDownloadLogsModal] = useState<{
        open: boolean;
        userId: string | null;
        logs: DownloadLogRecord[];
        loading: boolean;
        page: number;
        pageSize: number;
        total: number;
    }>({
        open: false,
        userId: null,
        logs: [],
        loading: false,
        page: 1,
        pageSize: 10,
        total: 0,
    });

    const openDownloadLogsModal = async (userRecord: UserRecord) => {
        setDownloadLogsModal({
            open: true,
            userId: userRecord.userId,
            logs: [],
            loading: true,
            page: 1,
            pageSize: 10,
            total: 0,
        });

        try {
            const response = await fetchUserDownloadLogs(userRecord.userId, 1, 10);
            const responseData = response.data;
            setDownloadLogsModal((prev) => ({
                ...prev,
                logs: responseData?.logs || [],
                total: responseData?.total || 0,
                loading: false,
            }));
        } catch (error) {
            message.error(resolveApiError(error, '获取下载日志失败'));
            setDownloadLogsModal((prev) => ({ ...prev, loading: false }));
        }
    };

    const closeDownloadLogsModal = () => {
        setDownloadLogsModal({
            open: false,
            userId: null,
            logs: [],
            loading: false,
            page: 1,
            pageSize: 10,
            total: 0,
        });
    };

    const handleDownloadLogsPageChange = async (page: number, pageSize: number) => {
        if (!downloadLogsModal.userId) return;

        setDownloadLogsModal((prev) => ({ ...prev, loading: true, page, pageSize }));

        try {
            const response = await fetchUserDownloadLogs(downloadLogsModal.userId, page, pageSize);
            const responseData = response.data;
            setDownloadLogsModal((prev) => ({
                ...prev,
                logs: responseData?.logs || [],
                total: responseData?.total || 0,
                loading: false,
            }));
        } catch (error) {
            message.error(resolveApiError(error, '获取下载日志失败'));
            setDownloadLogsModal((prev) => ({ ...prev, loading: false }));
        }
    };

    // Download log columns
    const downloadLogColumns: ColumnsType<DownloadLogRecord> = [
        {
            title: '下载时间',
            dataIndex: 'download_time',
            key: 'download_time',
            width: '40%',
            render: (value: string) => <Text type="secondary">{formatDateTime(value)}</Text>,
        },
        {
            title: '合同名称',
            dataIndex: 'document_name',
            key: 'document_name',
            width: '60%',
            render: (text: string) => <Text>{text}</Text>,
        },
    ];

    // Format date
    const formatDateTime = (value?: string | null): string => {
        if (!value) {
            return '-';
        }
        const parsed = new Date(value);
        if (Number.isNaN(parsed.getTime())) {
            return value;
        }
        return parsed.toLocaleString();
    };

    // Registration request columns
    const registrationColumns: ColumnsType<RegistrationRequestSummary> = [
        {
            title: '用户 ID',
            dataIndex: 'userId',
            key: 'userId',
            width: '30%',
            render: (text: string) => (
                <Space>
                    <UserOutlined />
                    <Text strong>{text}</Text>
                </Space>
            ),
        },
        {
            title: '申请时间',
            dataIndex: 'submittedAt',
            key: 'submittedAt',
            width: '30%',
            render: (value: string | null) => <Text type="secondary">{formatDateTime(value)}</Text>,
        },
        {
            title: '状态',
            dataIndex: 'status',
            key: 'status',
            width: '15%',
            render: (status: string) => (
                <Tag color="orange" icon={<ClockCircleOutlined />}>
                    {status === 'pending' ? '待审批' : status}
                </Tag>
            ),
        },
        {
            title: '操作',
            key: 'actions',
            width: '25%',
            render: (_, record) => (
                <Space size="small">
                    <Button
                        type="primary"
                        size="small"
                        icon={<CheckCircleOutlined />}
                        loading={processingRequestId === record.requestId}
                        onClick={() => handleApproveRegistration(record)}
                    >
                        通过
                    </Button>
                    <Button
                        danger
                        size="small"
                        icon={<CloseCircleOutlined />}
                        onClick={() => openRejectModal(record)}
                    >
                        拒绝
                    </Button>
                </Space>
            ),
        },
    ];

    // User management columns
    const userColumns: ColumnsType<UserRecord> = [
        {
            title: '用户 ID',
            dataIndex: 'userId',
            key: 'userId',
            width: '30%',
            render: (text: string) => (
                <Space>
                    <UserOutlined />
                    <Text strong>{text}</Text>
                </Space>
            ),
        },
        {
            title: '注册时间',
            dataIndex: 'createdAt',
            key: 'createdAt',
            width: '25%',
            render: (value: string | null) => <Text type="secondary">{formatDateTime(value)}</Text>,
        },
        {
            title: '当前权限',
            dataIndex: 'role',
            key: 'role',
            width: '20%',
            render: (role: UserRole) => (
                <Tag color={ROLE_COLORS[role] || 'default'}>
                    {ROLE_LABELS[role] || role}
                </Tag>
            ),
        },
        {
            title: '状态',
            dataIndex: 'status',
            key: 'status',
            width: '10%',
            render: (status: string) => (
                <Tag color={status === 'active' ? 'green' : 'red'}>
                    {status === 'active' ? '正常' : '已禁用'}
                </Tag>
            ),
        },
        {
            title: '操作',
            key: 'actions',
            width: '25%',
            render: (_, record) => (
                <Space size="small">
                    <Button
                        type="link"
                        size="small"
                        onClick={() => openRoleUpdateModal(record)}
                        disabled={record.userId === user?.userId}
                    >
                        修改权限
                    </Button>
                    {record.role !== 'superadmin' && record.userId !== user?.userId && (
                        <Button
                            type="link"
                            size="small"
                            danger={record.status === 'active'}
                            loading={statusUpdatingUserId === record.userId}
                            onClick={() => handleToggleUserStatus(record)}
                        >
                            {record.status === 'active' ? '禁用' : '启用'}
                        </Button>
                    )}
                    <Button
                        type="link"
                        size="small"
                        icon={<DownloadOutlined />}
                        onClick={() => openDownloadLogsModal(record)}
                    >
                        下载日志
                    </Button>
                </Space>
            ),
        },
    ];

    if (!isSuperAdmin) {
        return (
            <div style={{ padding: 24, textAlign: 'center' }}>
                <Empty description="您没有权限访问此页面" />
            </div>
        );
    }

    return (
        <div style={{ padding: 24 }}>
            {/* Registration Approval Section */}
            <Card
                title={
                    <Space>
                        <Title level={5} style={{ margin: 0 }}>注册审批</Title>
                        <Tag color="blue">{registrationRequests.length} 待审批</Tag>
                    </Space>
                }
                extra={
                    <Button
                        icon={<ReloadOutlined />}
                        onClick={fetchRegistrations}
                        loading={registrationLoading}
                    >
                        刷新
                    </Button>
                }
                style={{ marginBottom: 24 }}
            >
                <Table
                    columns={registrationColumns}
                    dataSource={registrationRequests}
                    rowKey="requestId"
                    loading={registrationLoading}
                    pagination={false}
                    locale={{ emptyText: '暂无待审批的注册申请' }}
                />
            </Card>

            {/* User Management Section */}
            <Card
                title={
                    <Space>
                        <Title level={5} style={{ margin: 0 }}>用户管理</Title>
                        <Tag color="green">{users.length} 用户</Tag>
                    </Space>
                }
                extra={
                    <Button
                        icon={<ReloadOutlined />}
                        onClick={fetchUsers}
                        loading={usersLoading}
                    >
                        刷新
                    </Button>
                }
            >
                <Table
                    columns={userColumns}
                    dataSource={users}
                    rowKey="userId"
                    loading={usersLoading}
                    pagination={{ pageSize: 10, showSizeChanger: true, showTotal: (total) => '共 ' + total + ' 条' }}
                />
            </Card>

            {/* Reject Modal */}
            <Modal
                title="拒绝注册申请"
                open={rejectModal.open}
                onCancel={closeRejectModal}
                onOk={handleRejectSubmit}
                confirmLoading={rejectSubmitting}
                okText="确认拒绝"
                cancelText="取消"
            >
                <Input.TextArea
                    placeholder="请输入拒绝原因（可选）"
                    value={rejectModal.reason}
                    onChange={(e) => setRejectModal((prev) => ({ ...prev, reason: e.target.value }))}
                    rows={3}
                />
            </Modal>

            {/* Role Update Modal */}
            <Modal
                title="修改用户权限"
                open={roleUpdateModal.open}
                onCancel={closeRoleUpdateModal}
                onOk={handleRoleUpdateSubmit}
                confirmLoading={roleUpdateSubmitting}
                okText="确认修改"
                cancelText="取消"
            >
                <div style={{ marginBottom: 16 }}>
                    <Text>用户 ID：</Text>
                    <Text strong>{roleUpdateModal.userId}</Text>
                </div>
                <div style={{ marginBottom: 16 }}>
                    <Text>当前权限：</Text>
                    <Tag color={ROLE_COLORS[roleUpdateModal.currentRole || 'normal']}>
                        {ROLE_LABELS[roleUpdateModal.currentRole || 'normal']}
                    </Tag>
                </div>
                <div>
                    <Text>新权限：</Text>
                    <Select
                        value={newRole}
                        onChange={(value) => setNewRole(value)}
                        style={{ width: 200, marginLeft: 8 }}
                        options={[
                            { value: 'normal', label: '普通用户' },
                            { value: 'admin', label: '管理员' },
                            { value: 'superadmin', label: '超级管理员' },
                        ]}
                    />
                </div>
            </Modal>

            {/* Download Logs Modal */}
            <Modal
                title={`下载日志 - ${downloadLogsModal.userId || ''}`}
                open={downloadLogsModal.open}
                onCancel={closeDownloadLogsModal}
                footer={null}
                width={600}
            >
                <Table
                    columns={downloadLogColumns}
                    dataSource={downloadLogsModal.logs}
                    rowKey="log_id"
                    loading={downloadLogsModal.loading}
                    pagination={{
                        current: downloadLogsModal.page,
                        pageSize: downloadLogsModal.pageSize,
                        total: downloadLogsModal.total,
                        showSizeChanger: true,
                        showTotal: (total) => `共 ${total} 条`,
                        onChange: handleDownloadLogsPageChange,
                    }}
                    locale={{ emptyText: '暂无下载记录' }}
                    size="small"
                />
            </Modal>
        </div>
    );
};

export default PersonnelPage;
