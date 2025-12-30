import React from 'react';
import { Select } from 'antd';
import '../FilterBar.css';

interface EntityFilterInputProps {
    value: string | null;
    options: string[];
    onChange: (value: string | null) => void;
}

const EntityFilterInput: React.FC<EntityFilterInputProps> = ({ value, options, onChange }) => {
    return (
        <Select
            value={value}
            onChange={(val) => onChange(val || null)}
            placeholder="请选择我方实体"
            className="entity-filter-select"
            allowClear
            showSearch
            options={options.map(opt => ({ label: opt, value: opt }))}
            filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
            }
        />
    );
};

export default EntityFilterInput;
